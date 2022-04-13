import serial
import time
import sys
import requests
import argparse
import os
import sqlite3
import pandas as pd


def getResponse(ser):
    ser.flushInput()
    ser.flushOutput()
    response = ser.readline()  # comment this line if echo off
    response = ser.readlines()
    return response


####################################

parser = argparse.ArgumentParser(description='Receive SMS spot messages and post them to ParksnPeaks.')
parser.add_argument('-u','--pnp_api_user_name', type=str, help='API user name for the submission.', required=True)
parser.add_argument('-k','--pnp_api_key', type=str, help='API key for the submission.', required=True)
parser.add_argument('-url','--pnp_api_url', type=str, help='API URL to use.', required=True)
parser.add_argument('-db','--users_db_dir', type=str, help='Directory of the users database.', required=True)
args = parser.parse_args()

valid_modes = ['SSB','CW','AM','FM','DATA','PSK','RTTY']

# check the users database exists
USERS_DB_NAME = "{}/psg-users.sqlite".format(args.users_db_dir)
if not os.path.isfile(USERS_DB_NAME):
    print("The users database is required but doesn't exist: {}".format(USERS_DB_NAME))
    sys.exit(1)

# load the registered users
db_conn = sqlite3.connect(USERS_DB_NAME)
# read the users
users_df = pd.read_sql_query('select email,token from users', db_conn)
db_conn.close()
print("loaded {} users from {}".format(len(users_df), USERS_DB_NAME))

# set up the serial connection
gsm_ser = serial.Serial()
gsm_ser.port = '/dev/ttyTHS1'
gsm_ser.baudrate = 115200
gsm_ser.timeout = 0.5
gsm_ser.xonxoff = False
gsm_ser.rtscts = False
gsm_ser.bytesize = serial.EIGHTBITS
gsm_ser.parity = serial.PARITY_NONE
gsm_ser.stopbits = serial.STOPBITS_ONE

# open the port
try:
    gsm_ser.open()
    gsm_ser.flushInput()
    gsm_ser.flushOutput()
except:
    print('cannot open serial port')

# check registered on the mobile network
gsm_ser.write('AT+CREG?\r'.encode('utf-8'))
print('check registration on the network: {}'.format(getResponse(gsm_ser)))

# put into text mode
gsm_ser.write('AT+CMGF=1\r'.encode('utf-8'))
resp = getResponse(gsm_ser)
if len(resp) > 0:
    print('set text mode: {}'.format(resp[0].rstrip().decode("utf-8")))

# show text mode parameters
gsm_ser.write('AT+CSDH=1\r'.encode('utf-8'))
resp = getResponse(gsm_ser)
if len(resp) > 0:
    print('show extra parameters: {}'.format(resp[0].rstrip().decode("utf-8")))

# read all messages
msgs = []
gsm_ser.write('AT+CMGL="ALL"\r'.encode('utf-8'))
msg = getResponse(gsm_ser)
if len(msg) == 0:
    print("no messages found")
else:
    print('reading messages')

for idx,m in enumerate(msg):
    m_str = m.rstrip().decode("utf-8")
    if 'CMGL:' in m_str:
        # parse header
        header = m_str.replace('"','')
        header_items = header.split(',')
        if len(header_items) >= 6:
            sender_number = header_items[2]
            sent_date = header_items[4]
            sent_time = header_items[5]
            # parse body
            body = msg[idx+1].rstrip().decode("utf-8")
            body_items = body.split(' ')
            if len(body_items) >= 7:
                callsign = body_items[0]
                program = body_items[1]
                site = body_items[2]
                frequency_mhz = body_items[3]
                mode = body_items[4]
                if mode in valid_modes:
                    token = body_items[5]
                    if token in users_df.token.to_list():
                        comments = " ".join(body_items[6:])
                        comments = comments.split('- ')[0].rstrip()  # remove the sender's name that postfixes the inReach message
                        # add it to the list
                        msgs.append({'sender_number':sender_number, 'sent_date':sent_date, 'sent_time':sent_time, 'callsign':callsign, 'program':program, 'site':site, 'frequency_mhz':frequency_mhz, 'mode':mode, 'comments':comments})
                        print('adding: {}'.format(msgs[-1]))
                    else:
                        print('invalid token: {}'.format(token))
                else:
                    print('invalid mode: {}'.format(mode))
            else:
                print('invalid body: {}'.format(body))
        else:
            print('invalid header: {}'.format(header))
print()

# delete all messages
gsm_ser.write('AT+CMGD=,4\r'.encode('utf-8'))
resp = getResponse(gsm_ser)
if len(resp) > 0:
    print('clear message buffer: {}'.format(resp[0].rstrip().decode("utf-8")))

# close the connection
print('closing the serial connection')
gsm_ser.close()

# set up the request header
headers = {
    'User-Agent': 'curl/7.77.0',
    'Content-Type': 'application/json'
}

# send the messages to PnP
print('sending {} messages to PnP'.format(len(msgs)))
for idx,m in enumerate(msgs):
    # set the PnP URL
    if 'debug' in m['comments']:
        pnp_url = '{}/DEBUG'.format(args.pnp_api_url)
    else:
        pnp_url = args.pnp_api_url
    # post the spot
    r = requests.post(pnp_url, headers=headers, json={'actClass':m['program'], 'actCallsign':m['callsign'], 'actSite':['site'], 'mode':m['mode'], 'freq':m['frequency_mhz'], 'comments':m['comments'], 'userID':args.pnp_api_user_name, 'APIKey':args.pnp_api_key})
    print(r.text)
    if r.status_code == 200:
        print('message {} was successfully submitted'.format(idx+1))
    else:
        print('message {} submission failed'.format(idx+1))
    print('------------------------------------------------')

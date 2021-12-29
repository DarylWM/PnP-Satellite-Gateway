import serial
import time
import sys
import requests
import argparse


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
args = parser.parse_args()


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
print('check registration on the network: '.format(getResponse(gsm_ser)))

# put into text mode
gsm_ser.write('AT+CMGF=1\r'.encode('utf-8'))
print('set text mode: '.format(getResponse(gsm_ser)))

# show text mode parameters
gsm_ser.write('AT+CSDH=1\r'.encode('utf-8'))
print('show extra parameters: '.format(getResponse(gsm_ser)))

# read all messages
print('reading messages')
msgs = []
gsm_ser.write('AT+CMGL="ALL"\r'.encode('utf-8'))
msg = getResponse(gsm_ser)
for idx,m in enumerate(msg):
    m_str = m.rstrip().decode("utf-8")
    if 'CMGL:' in m_str:
        # parse header
        items = m_str.replace('"','').split(',')
        sender_number = items[2]
        sent_date = items[4]
        sent_time = items[5]
        # parse body
        body = msg[idx+1].rstrip().decode("utf-8")
        items = body.split(' ')
        callsign = items[0]
        program = items[1]
        site = items[2]
        frequency_mhz = items[3]
        mode = items[4]
        comments = " ".join(items[5:])
        comments = comments.split('- ')[0].rstrip()  # remove the sender's name that postfixes the inReach message
        # add it to the list
        msgs.append({'sender_number':sender_number, 'sent_date':sent_date, 'sent_time':sent_time, 'callsign':callsign, 'program':program, 'site':site, 'frequency_mhz':frequency_mhz, 'mode':mode, 'comments':comments})
print(msgs)
print()

# delete all messages
gsm_ser.write('AT+CMGD=,4\r'.encode('utf-8'))
print('delete all messages: '.format(getResponse(gsm_ser)))

# close the connection
print('closing the serial connection')
gsm_ser.close()

# send the messages to PnP
print('sending {} messages to PnP'.format(len(msgs)))
for idx,m in enumerate(msgs):
    r = requests.post(args.pnp_api_url, json={'actClass':m['program'], 'actCallsign':m['callsign'], 'actSite':['site'], 'mode':m['mode'], 'freq':m['frequency_mhz'], 'comments':m['comments'], 'userID':args.pnp_api_user_name, 'APIKey':args.pnp_api_key})
    if r.status_code == 200:
        print('message {} was successfully submitted'.format(idx))
    else:
        print('message {} submission failed'.format(idx))

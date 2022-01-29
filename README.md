# PnP-Satellite-Gateway

The PnP-Satellite-Gateway is a combination of off-the-shelf hardware and custom software I wrote for portable amateur radio operations in remote locations. It solves the problem of not being able to [self-spot](https://vk5pas.org/2018/07/17/spotting-and-alerting/) on [Parks'n'Peaks (PnP)](https://parksnpeaks.org/ParksnPeaksHelp.php) from the top of a mountain ([SOTA](https://www.sota.org.uk)) or from a remote National Park ([WWFF](https://www.wwffaustralia.com)/[POTA](https://parksontheair.com)) that is outside coverage of the mobile phone network. Not being able to send an SMS to the PnP SMS gateway, an operator can self-spot using their [Garmin inReach](https://discover.garmin.com/en-US/inreach/personal/) to send a message via Iridium satellite to the PnP-Satellite-Gateway running on a single-board computer (SBC) sitting on their desk at home. The SBC can be a [Raspberry Pi](https://www.raspberrypi.com) or the [Jetson Nano](https://developer.nvidia.com/embedded-computing), snugly within the mobile phone network and also connected to the operator's internet connection. Attached to the SBC is a [4G LTE module](https://www.waveshare.com/wiki/SIM7600E-H_4G_HAT). The 4G LTE connection is enabled by a SIM that provides authorisation to connect to the carrier's network. The 4G LTE module only receives, so it doesn't require a data allowance and can be on [a minimal, long-expiry plan](https://www.aldimobile.com.au/products/payg). In Australia, an ALDImobile SIM is a good choice because they are very cheap and use the Telstra network under the hood.

The software runs every N minutes as a `cron` job. It polls the 4G LTE module to find out if it has received any messages. If there are new messages, it performs some checks to make sure the message is from a registered user and in the correct format, and extracts the information required to post a spot on PnP through the PnP API.

Only messages from users registered with the PnP-Satellite-Gateway are accepted and posted to PnP. User registrations are stored in a SQLite database. The schema for the database is shown below. To create the table and insert the registered users (needs at least one user), it's easiest to use a database browser like [DB Browser for SQLite](https://sqlitebrowser.org). Another option is running `sqlite` on the command line.

```
CREATE TABLE "users" (
	"email"	TEXT NOT NULL,
	"token"	TEXT NOT NULL,
	"callsign"	TEXT,
	PRIMARY KEY("email")
)
```

The token is an MD5 hash (truncated) of the user's email address, and this token must be provided in the inReach message.

The format of the inReach to the SIM's mobile number is:

`<my call> <program ID> <program site ID> <frequency in mhz> <mode> <token> <free text message>`

For example:

`VK3MCB/P WWFF VKFF-0556 7.032 CW 46de2f8b39 Last calls rain approaching`



#### Command line arguments

| short form | long form | type | meaning | required |
| ---------- | --------- | ---- | ------- | -------- |
| -u | --pnp_api_user_name | str | API user name for the submission. | True |
| -k | --pnp_api_key | str | API key for the submission. | True |
| -url | --pnp_api_url | str | API URL to use. | True |
| -db | --users_db_dir | str | Directory of the users database. | True |
| -debug | --debug_mode | flag | Post to PnP as a debug message. | False |


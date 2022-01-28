# PnP-Satellite-Gateway

The PnP-Satellite-Gateway is a combination of off-the-shelf hardware and custom software I wrote for portable amateur radio operations in remote locations. It solves the problem of not being to self-spot on [Parks'n'Peaks (PnP)](https://parksnpeaks.org/ParksnPeaksHelp.php) from the top of a mountain ([SOTA](https://www.sota.org.uk)) or from a remote National Park ([WWFF](https://www.wwffaustralia.com)/[POTA](https://parksontheair.com)) that is outside coverage of the mobile phone network. Not being able to send an SMS to the PnP SMS gateway, an operator can use their [Garmin inReach](https://discover.garmin.com/en-US/inreach/personal/) to send a message via Iridium satellite to the PnP-Satellite-Gateway running on a single-board computer (SBC) sitting on their desk at home. The SBC can be a [Raspberry Pi](https://www.raspberrypi.com) or the [Jetson Nano](https://developer.nvidia.com/embedded-computing), snugly within the mobile phone network and also connected to the operator's internet connection. Attached to the SBC is a [4G LTE module](https://www.waveshare.com/wiki/SIM7600E-H_4G_HAT). The 4G LTE connection is enabled by a SIM that provides authorisation to connect to the carrier's network. The 4G LTE module only receives, so it doesn't require a data allowance and can be on [a minimal, long-expiry plan](https://www.aldimobile.com.au/products/payg). In Australia, an ALDImobile SIM is a good choice because they are very cheap and use the Telstra network under the hood.

The software runs every N minutes as a `cron` job. It polls the 4G LTE module to find out if it has received any messages. If so, it performs some checks to make sure the message of the correct format, and extracts the information required to post a spot on PnP through the PnP API.


| short form | long form | type | meaning | required |
| ---------- | --------- | ---- | ------- | -------- |
| -u | --pnp_api_user_name | str | API user name for the submission. | True |
| -k | --pnp_api_key | str | API key for the submission. | True |
| -url | --pnp_api_url | str | API URL to use. | True |
| -db | --users_db_dir | str | Directory of the users database. | True |
| -debug | --debug_mode | flag | Post to PnP as a debug message. | False |
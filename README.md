# inreach2aprs
Yet another Garmin Inreach to APRS utility. This time, one that actually generates APRS positions properly, instead of dropping leading zeros.

For reference - The Delorme API is documented at https://files.delorme.com/support/inreachwebdocs/KML%20Feeds.pdf

## Requirements
```
$ pip install -r requirements.txt
```

## Goal

Send inReach positions to APRSIS ✅

      usage: inreach2aprs.py [-h] [--mapshare_url MAPSHARE_URL]
                             [--mapshare_password MAPSHARE_PASSWORD]
                             aprs_callsign aprs_ssid aprs_password

      inreach2aprs

      positional arguments:
        aprs_callsign         Your callsign; VK2GPL
        aprs_ssid             ARPS SSID or none; eg "-6"; see
                              http://www.aprs.net.au/general/standard-ssids/
        aprs_password         APRS Passcode

      optional arguments:
        -h, --help            show this help message and exit
        --mapshare_url MAPSHARE_URL
                              inReach MapShare URL; see
                              https://support.garmin.com/en-
                              AU/?faq=p2lncMOzqh71P06VifrQE7
        --mapshare_password MAPSHARE_PASSWORD
                              OPTIONAL - inReach MapShare password

## Nice to haves

* Support public MapShare links - probably works but not tested yet
* Support authenticated MapShare links ✅
* Handle deduplicating rather than relying on APRSIS to handle dupes ✅

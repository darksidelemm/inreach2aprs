#!/usr/bin/env python3

# It's super dodgy but this will give you something to run via cron at least with a zero return for success ...

import os, sys
import aprslib
import datetime
import pprint
import argparse
import requests
# Requires hacks from http://installfights.blogspot.com/2018/04/how-to-run-pykml-in-python3.html
from pykml import parser as kmlparser
from urllib.parse import urlparse
from io import BytesIO
import sqlite3

parser = argparse.ArgumentParser(description='inreach2aprs')
# default=os.environ.get('I2A', None)
parser.add_argument('aprs_callsign', help='Your callsign; VK2GPL')
parser.add_argument('aprs_ssid', help='ARPS SSID or none; eg "-6"; see http://www.aprs.net.au/general/standard-ssids/')
parser.add_argument('aprs_password', help='APRS Passcode')
parser.add_argument('--mapshare_url', help='inReach MapShare URL; see https://support.garmin.com/en-AU/?faq=p2lncMOzqh71P06VifrQE7')
parser.add_argument('--mapshare_password', help='OPTIONAL - inReach MapShare password')
parser.add_argument('--comment', default="inreach2aprs-0.1.0", help='OPTIONAL - APRS position comment')

# This should be brought out as command-line options.
# Refer: http://wa8lmf.net/aprs/APRS_symbols.htm
APRS_SYMBOL_TABLE = "/"
APRS_SYMBOL = "v"

args = parser.parse_args()
if not args.aprs_callsign:
    exit(parser.print_usage())


pp = pprint.PrettyPrinter()
o = urlparse(args.mapshare_url)
# print(o.path.strip("/"), args.mapshare_password)

try:
    conn = sqlite3.connect('inreach2aprs.db')
    c = conn.cursor()
    c.execute("CREATE TABLE positions (callsign text, ts text, lat text, long text)")
    conn.commit()
except sqlite3.OperationalError:
    print("INFO: Database already exists and is initialised")
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise


try:
    r = requests.get(args.mapshare_url, auth=(o.path.strip("/"), args.mapshare_password))
    r.raise_for_status()
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise

kml = kmlparser.parse(BytesIO(r.content)).getroot()

# Maps as per https://files.delorme.com/support/inreachwebdocs/KML%20Feeds.pdf and with inreach.kml example
#0 - Id int
#1 - Time UTC str
#2 - Time str
#3 - Name str
#4 - Map Display Name str
#5 - Device Type str
#6 - IMEI str
#7 - Incident Id str
#8 - Latitude float
#9 - Longitude float
#10 - Elevation str
#11 - Velocity str
#12 - Course str
#13 - Valid GPS Fix bool
#14 - In Emergency bool
#15 - Text str
#16 - Event str

d = datetime.datetime.strptime(str(kml.Document.Folder.Placemark[0].TimeStamp.when),'%Y-%m-%dT%H:%M:%SZ')
aprs_timestamp = d.strftime("%d%H%Mz")

inreach_lat = float(kml.Document.Folder.Placemark[0].ExtendedData.Data[8].value)
# print(inreach_lat)
inreach_lon = float(kml.Document.Folder.Placemark[0].ExtendedData.Data[9].value)
# print(inreach_lon)

# Convert float latitude to APRS format (DDMM.MM)
lat = float(inreach_lat)
lat_degree = abs(int(lat))
lat_minute = abs(lat - int(lat)) * 60.0
lat_min_str = ("%02.4f" % lat_minute).zfill(7)[:5]
lat_dir = "S"
if lat > 0.0:
    lat_dir = "N"
lat_str = "%02d%s" % (lat_degree, lat_min_str) + lat_dir

# Convert float longitude to APRS format (DDDMM.MM)
lon = float(inreach_lon)
lon_degree = abs(int(lon))
lon_minute = abs(lon - int(lon)) * 60.0
lon_min_str = ("%02.4f" % lon_minute).zfill(7)[:5]
lon_dir = "E"
if lon < 0.0:
    lon_dir = "W"
lon_str = "%03d%s" % (lon_degree, lon_min_str) + lon_dir


position_report = args.aprs_callsign + args.aprs_ssid + ">"+ "APZ001,TCPIP*:/" + aprs_timestamp + lat_str + APRS_SYMBOL_TABLE + lon_str + APRS_SYMBOL + args.comment

params = (args.aprs_callsign + args.aprs_ssid,aprs_timestamp,lat_str,lon_str)
c.execute(
    "SELECT * FROM positions WHERE callsign=? AND ts=? AND lat=? AND long=?", params
)

if c.fetchone() == None:
    # (?, ?)", (who, age)
    params = (args.aprs_callsign + args.aprs_ssid, aprs_timestamp, lat_str, lon_str)
    pp.pprint(params)
    c.execute(
        """insert into positions values (?,?,?,?)""", params
    )
    try:
        AIS = aprslib.IS(args.aprs_callsign, passwd=args.aprs_password, port=14580)
        AIS.connect()
        AIS.sendall(position_report)
        sent = True
    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise

    if sent:
        conn.commit()
        print("INFO: Sent packet \n")
        print(position_report)
        pp.pprint(aprslib.parse(position_report))
        conn.close()
        sys.exit(0)
    else:
        print("ERROR: Sending packet failed")
        sys.exit(1)

else:
    print("WARN: Not sending duplicate report")
    print(position_report)
    pp.pprint(aprslib.parse(position_report))
    sys.exit(1)

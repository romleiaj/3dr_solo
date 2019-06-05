#!/usr/bin/env python

'''
example program to extract GPS data from a mavlink log, and create a GPX
file, for loading into google earth
Modified by Adam Romlein to look at GLOBAL_POSITION_INT messages
'''
from __future__ import print_function

import time

from pymavlink import mavutil


def mav_to_gpx(infilename, outfilename):
    '''convert a mavlink log file to a GPX file'''

    mlog = mavutil.mavlink_connection(infilename)
    outf = open(outfilename, mode='w+')

    def process_packet(timestamp, lat, lon, alt, hdg, v):
        t = time.gmtime(timestamp) # in UTC so exiftool geotagging works
        outf.write('''<trkpt lat="%s" lon="%s">
  <ele>%s</ele>
  <time>%s</time>
  <course>%s</course>
  <speed>%s</speed>
  <fix>3d</fix>
</trkpt>
''' % (lat, lon, alt,
       time.strftime("%Y-%m-%dT%H:%M:%SZ", t),
       hdg, v))

    def add_header():
        outf.write('''<?xml version="1.0" encoding="UTF-8"?>
<gpx
  version="1.0"
  creator="pymavlink"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xmlns="http://www.topografix.com/GPX/1/0"
  xsi:schemaLocation="http://www.topografix.com/GPX/1/0 http://www.topografix.com/GPX/1/0/gpx.xsd">
<trk>
<trkseg>
''')

    def add_footer():
        outf.write('''</trkseg>
</trk>
</gpx>
''')

    add_header()

    count=0
    lat=0
    lon=0
    fix=0
    v=0
    while True:
        m = mlog.recv_match(type=['GLOBAL_POSITION_INT', 'GPS', 'GPS2'])
        if m is None:
            break
        if m.get_type() == 'GPS_RAW_INT':
            lat = m.lat/1.0e7
            lon = m.lon/1.0e7
            alt = m.alt/1.0e3
            v = m.vel/100.0
            hdg = m.cog/100.0
            timestamp = m._timestamp
            fix = m.fix_type
        elif m.get_type() == 'GPS_RAW':
            lat = m.lat
            lon = m.lon
            alt = m.alt
            v = m.v
            hdg = m.hdg
            timestamp = m._timestamp
            fix = m.fix_type
        elif m.get_type() == 'GPS' or m.get_type() == 'GPS2':
            lat = m.Lat
            lon = m.Lng
            alt = m.Alt
            v = m.Spd
            hdg = m.GCrs
            timestamp = m._timestamp
            fix = m.Status
        elif m.get_type() == 'GLOBAL_POSITION_INT':
            lat = m.lat/1.0e7
            lon = m.lon/1.0e7
            alt = m.alt/1.0e3
            hdg = m.hdg/100.0
            timestamp = m._timestamp
        else:
            pass

        if lat == 0.0 or lon == 0.0:
            continue
        process_packet(timestamp, lat, lon, alt, hdg, v)
        count += 1
    add_footer()
    if (count == 0):
        print("Error: no valid gps points found in %s." % outf)
        raise SystemExit
    print("Created %s with %u points" % (outfilename, count))

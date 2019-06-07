# 3DR-Solo

Scripts to utilize 3DR solo. The script `geotag.py` takes an MP4 (from goPro), a .tlog telemetry file from an aligning Solo flight, and a timeshift calculated by taking a picture of an atomic clock, and generates a directory of geotagged images from that flight
Must download both scripts, as mavtogpx.py is called from geotag.py.
#### Required Binaries
* ffprobe
* exiftool
#### Required Python Packages
* pymavlink
* av
* shlex
* json 
* datetime
* argparse
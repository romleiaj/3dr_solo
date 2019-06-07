#!/usr/bin/python

# __required__ exiftool, ffprobe

import argparse
import av
import os
import time
import subprocess
import shlex
import json
import glob
import datetime

# Script imports
from mavtogpx import mav_to_gpx

class Geotag():
    def __init__(self, tlog_path, mp4_path, offset):
        self.tlog = tlog_path
        self.mp4 = mp4_path
        self.offset = offset
        self.fps = 0.0

    def split_frames(self, vid_fname, output_dir):
        cap = av.open(vid_fname)
        cap.streams.video[0].thread_type = 'AUTO'
        self.fps = cap.streams.video[0].framerate
        #for frame in cap.decode(video=0): 
        #    frame.to_image().save(output_dir + ("/frame%07d.jpg" % frame.index)) 
        print("Average fps is: %s." % self.fps)
        #print("%s images written to %s." % (frame.index, output_dir))

    def get_start_time(self, mp4_path):
    # connection to find the resolution of the input video file
        cmd = "ffprobe -v quiet -print_format json -show_streams"
        args = shlex.split(cmd)
        args.append(mp4_path)
        # run the ffprobe process, decode stdout into utf-8 & convert to JSON
        ffprobeOutput = subprocess.check_output(args).decode('utf-8')
        ffprobeOutput = json.loads(ffprobeOutput)

        # extract time, date and timecode
        t = ffprobeOutput['streams'][0]['tags']['creation_time']
        timecode = ffprobeOutput['streams'][0]['tags']['timecode']
        fps = ffprobeOutput['streams'][0]['avg_frame_rate']
        frame = int(str(timecode)[9:11])
        print("MP4 Start time is: %s and start frame is: %s." % 
                (t.replace("T", " ").split(".")[0], frame))
        return t, frame

    def tag_images(self):
        print("Creating gpx file...")
        gpx_fname = self.tlog + ".gpx"
        #mav_to_gpx(self.tlog, gpx_fname)
        
        print("Creating directory of jpegs from %s..." % self.mp4)
        try:
            os.mkdir(os.path.abspath(self.mp4).split('.')[0] + "_geotagged")
        except:
            print("Geotag directory already exists, overwriting.")
            pass
        output_dir = (os.path.abspath(self.mp4).split('.')[0] + "_geotagged")
        self.split_frames(self.mp4, output_dir)
        
        print("Getting %s start time..." % self.mp4)
        t, frame = self.get_start_time(self.mp4)
        h, m, s = [int(i) for i in t.split('T')[1][:-8].split(':')]
        y, mon, d = [int(j) for j in t.split('T')[0].split('-')]
        start_time = datetime.datetime(y, mon, d, h, m, s)
        
        print("Timestamping images...")
        int_offset = int(self.offset)
        frame_offset = int((self.offset - int_offset) * self.fps)
        frame = (frame_offset + frame)
        if (frame > self.fps):
            int_offset += 1
            frame = int(round(frame - self.fps))
        timestamp = start_time + datetime.timedelta(seconds=int_offset)
        timestring = timestamp.strftime("%Y:%m:%d %H:%M:%S")
        for img in sorted(glob.glob(output_dir + "/*.jpg")):
            stamp_cmd = ['exiftool', '-S', '-overwrite_original_in_place',
                    "-DateTimeOriginal='%s'" % (timestring), img]
            p = subprocess.Popen(stamp_cmd)
            if (frame % int(round(self.fps)) == 0):
                timestamp =  timestamp + datetime.timedelta(seconds=1)
                timestring = timestamp.strftime("%Y:%m:%d %H:%M:%S")
            print("Timestamped %s." % img)
            time.sleep(0.1)
            frame += 1
        p.wait()
        
        print("Geotagging images...")

        tag_cmd = ['exiftool', '-overwrite_original_in_place', '-geotag', 
                gpx_fname, output_dir]
        p = subprocess.call(tag_cmd)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Geotag images from a GoPro"
    " with 3DR Solo tlogs.")
    parser.add_argument('tlog_path', type=str, help="Path to Solo generated tlog file.")
    parser.add_argument('mp4_path', type=str, help="Path to GoPro generated MP4.")
    parser.add_argument('time_offset', type=float, help="Time offset of Atomic clock - GoPro clock.")
    args = parser.parse_args()
    if args.mp4_path.split(".")[-1] not in  ["mp4", "avi", "mov", "MP4"]:
        print("Invalid second argument, must be a video file.")
        raise SystemExit
    solo = Geotag(args.tlog_path, args.mp4_path, args.time_offset)
    solo.tag_images()
    print("Finished geotagging.")

Medicine Scheduler for the Raspberry Pi
=======================================

Requirements
------------
- apscheduler (in emulation too)
- jsonschema (in emulation too)
- opencv
- zbar
- PIL


To Run
------

Use on the RPI. Ensure the uv4l driver is installed so that opencv will work with the RPI webcam. If not started yet, initiate the driver with 
```sh
uv4l --sched-rr --driver raspicam --encoding yuv420 --auto-video_nr --width 320 --height 240 --nopreview yes
```
or just run the script
```sh
./uvl_start.sh
```


Emulation mode
--------------

To test out the UI without actually developing on the RPI,
edit the entry in config.py

```python
EMULATE = False # change to True
```

Notes:
- Control with the num pad (2468 are the direction keys, 5 to select, 0 to go back)
- Recording is not supported in emulation mode


Schedule Printer (for pharmacies)
=================================

Requirements
------------
- PyQt4

A proof-of-concept, just encodes some basic scheduling information into a jpg that can be printed onto a sticker or something.


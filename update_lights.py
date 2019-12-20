# open a microphone in pyAudio and listen for taps

import pyaudio
import struct
import math
import numpy as np
import sys
import time
from rpi_ws281x import *
import time 
import os

led_count = 150
bar_size = 4
counter = 0
switch = True
heads = []

strip = Adafruit_NeoPixel(led_count, 18, 800000, 5, False, 255)

def clear_lights(strip):
    for light in range(led_count):
        strip.setPixelColorRGB(light, 0, 0, 0)
    strip.show()

def send_line():
    print("strip sent")
    global switch
    if switch:
        heads.append([0, (255, 0, 0)])
    else:
        heads.append([0, (0, 0, 255)])
    switch = not switch


def update_lines(strip):
    global heads
    for head in heads:
        print(head)
        for i in range(bar_size):
            idx = head[0] - i
            if 0 <= idx < led_count:
                strip.setPixelColorRGB(idx, head[1][0], head[1][1], head[1][2]) 
        strip.setPixelColorRGB(max(0, head[0] - bar_size) , 0, 0, 0)
    strip.show()
    for i in range(len(heads)):
        heads[i][0] += 1
    if heads[0][0] == led_count + bar_size:
        del heads[0]



strip.begin()
try:
    while(True):
        counter += 1
        if counter == 40:
            counter = 0
            send_line()
        if len(heads) > 0:
            update_lines(strip)
except KeyboardInterrupt:
    # close the stream gracefully
    clear_lights(strip)



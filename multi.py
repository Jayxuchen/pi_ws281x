import pyaudio
import struct
import math
import numpy as np
import sys
import time
from rpi_ws281x import *
import time 
import os
import multiprocessing
import queue 
from process import Process

np.set_printoptions(threshold=sys.maxsize)

INITIAL_TAP_THRESHOLD = 0.010
FORMAT = pyaudio.paInt16 
SHORT_NORMALIZE = (1.0/32768.0)
CHANNELS = 2
RATE = 44100  
INPUT_BLOCK_TIME = 0.05
CHUNK = int(RATE*INPUT_BLOCK_TIME)
LAST = 0


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

def update_lines(strip, q):
    global heads
    try:
        while True:
            try:
                new_head = q.get(False)
                heads.append(new_head)
            except queue.Empty:
                pass 
            if len(heads) > 0:
                #print(heads)
                for head in heads:
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
    except KeyboardInterrupt:
        clear_lights(strip)
        

def get_freq (stream, q):
    global LAST
    global switch
    data = np.fromstring(stream.read(CHUNK),dtype=np.int16)
    data = data * np.hanning(len(data)) # smooth the FFT by windowing data
    fft = abs(np.fft.fft(data).real)
    fft = fft[:int(len(fft)/2)] # keep only first half
    freq = np.fft.fftfreq(CHUNK,1.0/RATE)
    freq = freq[:int(len(freq)/2)] # keep only first half
    freqPeak = freq[np.where(fft==np.max(fft))[0][0]]+1
    if abs(freqPeak - LAST) > 120 and freqPeak > 200:
        print("last = %d peak frequency: %d Hz"% (LAST, freqPeak))
        if switch:
            q.put([0, (255, 0, 0)])
        else:
            q.put([0, (0, 0, 255)])
        switch = not switch
        LAST = freqPeak

class AudioCap(object):
    def __init__(self):
        self.pa = pyaudio.PyAudio()
        self.stream = self.open_mic_stream()
        self.quietcount = 0 
        self.errorcount = 0

    def stop(self):
        self.stream.close()

    def find_input_device(self):
        device_index = None            
        for i in range( self.pa.get_device_count() ):     
            devinfo = self.pa.get_device_info_by_index(i)   
            #print( "Device %d: %s"%(i,devinfo["name"]) )

            for keyword in ["mic","input"]:
                if keyword in devinfo["name"].lower():
                    device_index = i
                    return device_index

       # if device_index == None:
           # print( "No preferred input found; using default input device." )
        return device_index

    def open_mic_stream( self ):
        device_index = self.find_input_device()

        stream = self.pa.open(   format = FORMAT,
                                 channels = CHANNELS,
                                 rate = RATE,
                                 input = True,
                                 input_device_index = device_index,
                                 frames_per_buffer = CHUNK)

        return stream

    def listen(self):
        strip.begin()
        q = multiprocessing.Queue()
        p = Process(target=update_lines, args=(strip, q,))
        p.start()
        try:
            while(True):
                get_freq(self.stream, q)
        except KeyboardInterrupt:
            # close the stream gracefully
            self.stream.stop_stream()
            self.stream.close()
            self.pa.terminate()
            if p.exception:
                error, traceback = p.exception
                print(traceback)

            print("Ending Recording")


if __name__ == '__main__':
    tt = AudioCap()
    tt.listen() 

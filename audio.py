
# open a microphone in pyAudio and listen for taps

import pyaudio
import struct
import math
import numpy as np
import sys
import matplotlib.pyplot as plt
import time
from rpi_ws281x import *
import time 


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
head = 0

heads = []

strip = Adafruit_NeoPixel(led_count, 18, 800000, 5, False, 255)

def clear_lights(strip):
    for light in range(led_count):
        strip.setPixelColorRGB(light, 0, 0, 0)
    strip.show()

def send_line():
    heads.append(0)

def update_lines(strip):
#    print(heads)
    for index, head in enumerate(heads):
        for i in range(bar_size):
            idx = head - i
            if 0 <= idx < led_count:
                strip.setPixelColorRGB(idx , 255 if index % 2 == 0 else 0,
                                        0, 255 if index % 2 == 1 else 0)
        strip.setPixelColorRGB(max(0, head - bar_size) , 0, 0, 0)
    strip.show()
    for i in range(len(heads)):
        heads[i] += 1
    if heads[0] == led_count + bar_size:
        del heads[0]

def get_rms( block ):
    # RMS amplitude is defined as the square root of the 
    # mean over time of the square of the amplitude.
    # so we need to convert this string of bytes into 
    # a string of 16-bit samples...

    # we will get one short out for each 
    # two chars in the string.
    count = len(block)/2
    format = "%dh"%(count)
    shorts = struct.unpack( format, block )

    # iterate over the block.
    sum_squares = 0.0
    for sample in shorts:
        # sample is a signed short in +/- 32768. 
        # normalize it to 1.0
        n = sample * SHORT_NORMALIZE
        sum_squares += n*n
    return math.sqrt( sum_squares / count )

def get_freq (stream):
    global LAST
    data = np.fromstring(stream.read(CHUNK),dtype=np.int16)
    data = data * np.hanning(len(data)) # smooth the FFT by windowing data
    fft = abs(np.fft.fft(data).real)
    fft = fft[:int(len(fft)/2)] # keep only first half
    freq = np.fft.fftfreq(CHUNK,1.0/RATE)
    freq = freq[:int(len(freq)/2)] # keep only first half
    freqPeak = freq[np.where(fft==np.max(fft))[0][0]]+1
    if abs(freqPeak - LAST) > 120 and freqPeak > 200:
        print("last = %d peak frequency: %d Hz"% (LAST, freqPeak))
        send_line()
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
            print( "Device %d: %s"%(i,devinfo["name"]) )

            for keyword in ["mic","input"]:
                if keyword in devinfo["name"].lower():
                    device_index = i
                    return device_index

        if device_index == None:
            print( "No preferred input found; using default input device." )
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

    #def toRGB(self, amplitude):
        

    def listen(self):

        strip.begin()
        try:
            send_line()
            while(True):
                if len(heads) > 0:
                    update_lines(strip)
#                block = self.stream.read(CHUNK)
#                amplitude = round(get_rms(block)*100)
#                if(amplitude >= 5):
#                    send_line()
                get_freq(self.stream)
        except KeyboardInterrupt:
            # close the stream gracefully
            self.stream.stop_stream()
            self.stream.close()
            self.pa.terminate()
            clear_lights(strip)

            print("Ending Recording")
        
if __name__ == "__main__":
    tt = AudioCap()
    tt.listen() 

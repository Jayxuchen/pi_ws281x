from rpi_ws281x import *
import time 
led_count = 150

bar_size = 5
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
    for head in heads:
        for i in range(bar_size):
            idx = head - i
            if 0 <= idx < led_count:
                strip.setPixelColorRGB(idx , 255, 0, 0)
        strip.setPixelColorRGB(max(0, head - bar_size) , 0, 0, 0)
    strip.show()
    for i in range(len(heads)):
        heads[i] += 1
    if heads[0] == led_count + bar_size:
        del heads[0]
    if len(heads) == 0:
        return False
    return True


strip.begin()

try:
    send_line()
    while(True):
        time.sleep(0.01)
        if not update_lines(strip):
            break
        if heads[-1] == 30:
            send_line()

except KeyboardInterrupt:
    clear_lights(strip)


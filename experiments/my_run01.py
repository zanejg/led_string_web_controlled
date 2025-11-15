import time
import math
#import numpy as np

from rpi_ws281x import *

import argparse

from pulse_array import pulse_array


LED_COUNT      = 65     

LED_PIN        =  18      

LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)

LED_DMA        = 10      # DMA channel to use for generating a signal (try 10)

LED_BRIGHTNESS = 65      # Set to 0 for darkest and 255 for brightest

LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)

LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53

def colorWipe(strip, color, wait_ms=50):

    """Wipe color across display a pixel at a time."""

    for i in range(strip.numPixels()):

        strip.setPixelColor(i, color)

        strip.show()

        time.sleep(wait_ms/1000.0)

def theaterChase(strip, color, wait_ms=50, iterations=10):

    """Movie theater light style chaser animation."""

    for j in range(iterations):

        for q in range(3):

            for i in range(0, strip.numPixels(), 3):

                strip.setPixelColor(i+q, color)

            strip.show()

            time.sleep(wait_ms/1000.0)

            for i in range(0, strip.numPixels(), 3):

                strip.setPixelColor(i+q, 0)

def wheel(pos):

    """Generate rainbow colors across 0-255 positions."""

    if pos < 85:

        return Color(pos * 3, 255 - pos * 3, 0)

    elif pos < 170:

        pos -= 85

        return Color(255 - pos * 3, 0, pos * 3)

    else:

        pos -= 170

        return Color(0, pos * 3, 255 - pos * 3)

def rainbow(strip, wait_ms=20, iterations=1):

    """Draw rainbow that fades across all pixels at once."""

    for j in range(256*iterations):

        for i in range(strip.numPixels()):

            strip.setPixelColor(i, wheel((i+j) & 255))

        strip.show()

        time.sleep(wait_ms/1000.0)

def rainbowCycle(strip, wait_ms=20, iterations=5):

    """Draw rainbow that uniformly distributes itself across all pixels."""

    for j in range(256*iterations):

        for i in range(strip.numPixels()):

            strip.setPixelColor(i, wheel((int(i * 256 / strip.numPixels()) + j) & 255))

        strip.show()

        time.sleep(wait_ms/1000.0)

def theaterChaseRainbow(strip, wait_ms=50):

    """Rainbow movie theater light style chaser animation."""

    for j in range(256):

        for q in range(3):

            for i in range(0, strip.numPixels(), 3):

                strip.setPixelColor(i+q, wheel((i+j) % 255))

            strip.show()

            time.sleep(wait_ms/1000.0)

            for i in range(0, strip.numPixels(), 3):

                strip.setPixelColor(i+q, 0)

class frange():
    """
    Inputs are all floats.
    start: the start of the sequence
    end: the ending value. Not achieved will only return values below it.
    step: the size of the steps
    """
    def __init__(self,start, end, step):
        self.start = float(start)
        self.end = float(end)
        self.step = float(step)
        
    def __iter__(self):
        self.this = self.start
        return self
    
    def __next__(self):
        if self.this < self.end:
            x = self.this
            self.this += self.step
            return x
        else:
            raise StopIteration 

def make_pixarray(numpix, maxval):
    """
    maxval: the maximum value of the pulse_array
    numpix: the number of pixels to be lit
    """
    rawret = []
    ret = []
    array_step = int(len(pulse_array)/numpix)

    for i in range(0, numpix):
        rawret.append(pulse_array[int(i*array_step)])

    peak = max(rawret)
    ret = [int((x/peak)*maxval) for x in rawret]
    


    return ret
    


def pulsing_areas(strip, color):

    """ Ranges of pixels will pulse"""

    pix_count = 10
    the_max =200

    pulse_wait = 10

    #import pdb; pdb.set_trace()

    red = color.r
    green = color.g
    blue = color.b


    for max in range(0, 200, 2):
        pix_array = make_pixarray(pix_count, max)


    
        for i in range(0, strip.numPixels() - pix_count ,pix_count):
            for j,val in enumerate(pix_array):
                #print(f"Val={val}")
                try:
                    strip.setPixelColor(i+j, Color(int(red * (val/max)) if max != 0 else 0,
                                                   int(green * (val/max))if max != 0 else 0,
                                                   int(blue * (val/max))if max != 0 else 0  ))
                except OverflowError:
                    #import pdb; pdb.set_trace()
                    raise
            
        strip.show()

        time.sleep(pulse_wait/1000.0)
    
    for max in range(200,0, -2):
        pix_array = make_pixarray(pix_count, max)


    
        for i in range(0, strip.numPixels() - pix_count ,pix_count):
            for j,val in enumerate(pix_array):
                #print(f"Val={val}")
                try:
                    strip.setPixelColor(i+j, Color(int(red * (val/max)) if max != 0 else 0,
                                                   int(green * (val/max))if max != 0 else 0,
                                                   int(blue * (val/max))if max != 0 else 0  ))
                except OverflowError:
                    #import pdb; pdb.set_trace()
                    raise
            
        strip.show()

        time.sleep(pulse_wait/1000.0)




# Main program logic follows:

if __name__ == '__main__':

    # Process arguments

    parser = argparse.ArgumentParser()

    parser.add_argument('-c', '--clear', action='store_true', help='clear the display on exit')

    args = parser.parse_args()

    # Create NeoPixel object with appropriate configuration.

    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)

    # Intialize the library (must be called once before other functions).

    strip.begin()

    print ('Press Ctrl-C to quit.')

    if not args.clear:

        print('Use "-c" argument to clear LEDs on exit')

    try:

        while True:
            print("Pulsing Areas")
            pulsing_areas(strip, Color(255,255,0))
            pulsing_areas(strip, Color(0,255,0))
            pulsing_areas(strip, Color(255,0,0))

            # print ('Color wipe animations.')

            # colorWipe(strip, Color(255, 0, 0))  # Red wipe

            # colorWipe(strip, Color(0, 255, 0))  # Blue wipe

            # colorWipe(strip, Color(0, 0, 255))  # Green wipe

            # print ('Theater chase animations.')

            # theaterChase(strip, Color(127, 127, 127))  # White theater chase

            # theaterChase(strip, Color(127,   0,   0))  # Red theater chase

            # theaterChase(strip, Color(  0,   0, 127))  # Blue theater chase

            # print ('Rainbow animations.')

            # rainbow(strip)

            rainbowCycle(strip)

            # theaterChaseRainbow(strip)

    except KeyboardInterrupt:

        if args.clear:

            colorWipe(strip, Color(0,0,0), 10)
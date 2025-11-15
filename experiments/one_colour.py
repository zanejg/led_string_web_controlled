import time
from rpi_ws281x import *
import argparse
from collections import deque
import random
import math
import numpy as np

from four_meter import LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL



def set_all(strip, color):

    """Set all pixels to the same color."""

    for i in range(strip.numPixels()):

        strip.setPixelColor(i, color)

    strip.show()


def hexstringcolor(hexstring):
    """Convert a hex string to a Color object."""
    hexstring = hexstring.lstrip('#')
    lv = len(hexstring)
    return Color(*(int(hexstring[i:i + lv // 3], 16) for i in range(0, lv, lv // 3)))









BACKCOLOUR = hexstringcolor("2EEFE2")
INNER_FLAME_COLOUR = hexstringcolor("FFFB00")
OUTER_FLAME_COLOUR = hexstringcolor("FF0000")
POSITIVE_BEAT_COLOUR = hexstringcolor("FF4A00")
NEGATIVE_BEAT_COLOUR = hexstringcolor("FF0000")

inner_flame_base_ht = 15
outer_flame_base_ht = 40
flicker_ht = 10

# Main program logic follows:
if __name__ == '__main__':

    background_color = Color(0,0,0)

    # Process arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--colour', action='store', help='light all leds to this hex colour')


    args = parser.parse_args()


    # Create NeoPixel object with appropriate configuration.
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    # Intialize the library (must be called once before other functions).

    strip.begin()

    print ('Press Ctrl-C to quit.')
    if not args.colour:
        print('Use "-c" argument to set all LEDs to a specific colour')

    try:
        color = hexstringcolor(args.colour)
        set_all(strip, color)



    except KeyboardInterrupt:
        if args.clear:
            colorWipe(strip, Color(0,0,0), 1)

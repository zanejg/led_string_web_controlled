import time
from rpi_ws281x import *
import argparse
from collections import deque
import random
import math
import numpy as np

from four_meter import LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL



def colorWipe(strip, color, wait_ms=50):

    """Wipe color across display a pixel at a time."""

    for i in range(strip.numPixels()):

        strip.setPixelColor(i, color)

        strip.show()

        time.sleep(wait_ms/1000.0)


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




def randomColor():
    """Generate a random color."""

    return Color(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))




class flame():
    def __init__(self, strip, back_color, outer_flame_color, inner_flame_color):
        self.strip = strip
        self.back_color = back_color
        self.outer_flame_color = outer_flame_color
        self.inner_flame_color = inner_flame_color
        self.inner_flame_base_ht = 15
        self.outer_flame_base_ht = 40
        self.flicker_ht = 10
    
    def show(self, outer_ht, inner_ht):
        set_all(self.strip, self.back_color)
        for i in range(outer_ht):
            self.strip.setPixelColor(i, self.outer_flame_color)
        for i in range(inner_ht):
            self.strip.setPixelColor(i, self.inner_flame_color)
        self.strip.show()

    def run(self, duration):
        end_time = time.time() + duration
        while time.time() < end_time:
            outer_ht = self.outer_flame_base_ht + random.randint(0, self.flicker_ht)
            inner_ht = self.inner_flame_base_ht + random.randint(0, self.flicker_ht)
            self.show(outer_ht, inner_ht)
            time.sleep(0.1)
        

def sequence_between_colours(color1, color2, steps):
    """Generate a sequence of colors transitioning from color1 to color2 over the given number of steps.
       Colours are Color objects."""
    r1 = color1.r
    g1 = color1.g
    b1 = color1.b
    r2 = color2.r
    g2 = color2.g
    b2 = color2.b
    seq = []

    for step in range(steps):
        r = int(((r2 - r1) * step / (steps - 1)) + r1)
        g = int(((g2 - g1) * step / (steps - 1)) + g1)
        b = int(((b2 - b1) * step / (steps - 1)) + b1)
        seq.append(Color(r, g, b))
    return seq



class expanding_waves():    
    def __init__(self, strip, center, 
                 wave_peak_color, wave_trough_color, 
                 center_color=None, back_colour=None):
        """Create expanding waves effect.
        strip: the PixelStrip object
        center: the center position of the wave as a float between 0.0 and 1.0
        wave_peak_color: Color object for the peak of the wave
        wave_trough_color: Color object for the trough of the wave
        """
        self.strip = strip

        self.wave_peak_color = wave_peak_color
        self.wave_trough_color = wave_trough_color
        self.center_colour = center_color if center_color else hexstringcolor("FFFF00")
        self.back_colour = back_colour if back_colour else hexstringcolor("880088")


        self.wave_length = 10  # number of LEDs per wave
        self.wave_speed = 0.05  # seconds per step

        self.center_position = int(center * strip.numPixels())
        self.upper_len = strip.numPixels() - self.center_position - 1
        self.lower_len = self.center_position - 1

        self.upper_ledarray = deque([self.back_colour] * self.upper_len)
        self.lower_ledarray = deque([self.back_colour] * self.lower_len)

        self.wave_sequence = sequence_between_colours(self.wave_trough_color, self.wave_peak_color, int(self.wave_length / 2))
        self.wave_sequence += sequence_between_colours(self.wave_peak_color, self.wave_trough_color, int(self.wave_length / 2))

        self.wave_seq_position = 0



    # def step_wave(self):
    #     self.upper_ledarray.pop()
    #     self.lower_ledarray.pop()
    #     self.upper_ledarray.appendleft(self.wave_sequence[self.wave_seq_position])
    #     self.lower_ledarray.appendleft(self.wave_sequence[self.wave_seq_position])

    #     # self.ledarray.append(self.wave_sequence[self.wave_seq_position])
    #     # self.wave_seq_position = (self.wave_seq_position + 1) % len(self.wave_sequence)

    #     # [self.strip.setPixelColor(i, self.lower_ledarray[i]) for i in range(self.center_position, self.strip.numPixels())]
    #     # [self.strip.setPixelColor(i, self.upper_ledarray[i]) for i in range(self.center_position, -1, -1)]

    #     [self.strip.setPixelColor(self.center_position - idx + 1, this_led) 
    #         for idx,this_led in enumerate(self.lower_ledarray)]
    #     [self.strip.setPixelColor(self.center_position + idx + 1, this_led) 
    #         for idx,this_led in enumerate(self.upper_ledarray)]

    #     self.wave_seq_position = (self.wave_seq_position + 1) % len(self.wave_sequence)


    def step_wave(self):
        if self.lower_len > 0:
            self.lower = self.lower_ledarray.popleft()
            self.lower_ledarray.append(self.wave_sequence[self.wave_seq_position])
            [self.strip.setPixelColor((self.center_position -1)- idx, this_led) 
                for idx,this_led in enumerate(reversed(self.lower_ledarray))]

        if self.upper_len > 0:
            self.upper = self.upper_ledarray.pop()
            self.upper_ledarray.appendleft(self.wave_sequence[self.wave_seq_position])
            [self.strip.setPixelColor(self.center_position + 1+ idx, this_led) 
                for idx,this_led in enumerate(self.upper_ledarray)]
        
        self.wave_seq_position = (self.wave_seq_position + 1) % len(self.wave_sequence)




    def run(self, duration):
        end_time = time.time() + duration

        # set_all(self.strip, self.wave_trough_color)
        self.strip.setPixelColor(self.center_position, self.center_colour)

        while time.time() < end_time:

            self.step_wave()
            self.strip.show()
            time.sleep(self.wave_speed)
            




def heart_beat(strip, color1, color2, beats):
    """Create a heart beat effect by alternating between two colors."""
    end_b4_rounding = 250
    
    starting_hyperbola_series = [int(round(-1 *1/x)) for x in np.linspace(-0.1, -1/end_b4_rounding, 70 ) if x != 0]
    cube_series = [-1 * x**3 for x in np.linspace(-(end_b4_rounding**(1/3)), (end_b4_rounding**(1/3)), 20)]
    RAD = 255 - end_b4_rounding
    top_half_circle_series = [end_b4_rounding + (math.sqrt(1 - (x/RAD)**2) * RAD) 
                            for x in np.linspace(-RAD, RAD, RAD)]
    
    bottom_half_circle_series = [- end_b4_rounding + (-1 * math.sqrt(1 - (x/RAD)**2) * RAD) 
                             for x in np.linspace(-RAD, RAD, RAD)]
    
    finishing_hyperbola_series = [-1 * 1/x for x in np.linspace(1/end_b4_rounding,0.1, 70 ) if x != 0]

    
    full_series = starting_hyperbola_series + top_half_circle_series + cube_series + bottom_half_circle_series + finishing_hyperbola_series

    
    # if the value is positive it is color1, if negative it is color2
    # the brightness defined by the absolute value of the number
    beat_interval = 0.015

    for beat in range(beats):
        for value in full_series:
            if value >= 0:
                set_all(strip, Color(
                    int((color1.r * value) / 255),
                    int((color1.g * value) / 255),
                    int((color1.b * value) / 255),
                ))
            else:
                set_all(strip, Color(
                    int((color2.r * -value) / 255),
                    int((color2.g * -value) / 255),
                    int((color2.b * -value) / 255),
                ))
            time.sleep(beat_interval)











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
        # # Create flame effect
        # f = flame(strip, BACKCOLOUR, OUTER_FLAME_COLOUR, INNER_FLAME_COLOUR)
        # f.run(60)

        # Create expanding waves effect
        # for center in [0.0, 1.0, 0.25, 0.5, 0.75, 0.33, 0.66]:
        #     waves = expanding_waves(strip, center, BACKCOLOUR, OUTER_FLAME_COLOUR)
        #     waves.run(5)
        heart_beat(strip, NEGATIVE_BEAT_COLOUR, POSITIVE_BEAT_COLOUR, 100)



    except KeyboardInterrupt:
        if args.clear:
            colorWipe(strip, Color(0,0,0), 1)

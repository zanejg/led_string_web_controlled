import pyaudio
import numpy as np
import time
# from rpi_ws281x import *
from rpi_ws281x import Adafruit_NeoPixel, Color
import argparse
from collections import deque
import random

from four_meter import LED_COUNT, LED_PIN, LED_FREQ_HZ
from four_meter import LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL

strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, 
                          LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)

strip.begin()   

CHUNK = 4096 #1024  # Size of a single audio chunk
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 48000 # 16000 for video mic
RECORD_SECONDS = 30
USB_MIC_INDEX = 0  # **CHANGE THIS to your device's index**

p = pyaudio.PyAudio()

stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK,
                input_device_index=USB_MIC_INDEX)

print("Listening...")
frames = []


MAX_LOUDNESS = 2**15 -1  # Maximum for int16
back_color = Color(150,0,150) # Purple
fore_colour = Color(200,200,0) # Yellow


COLOUR_SEQUENCE = [
    [1,0,0], # red
    [1,1,0], # yellow
    [0,1,0], # green
    [0,1,1], # cyan
    [0,0,1], # blue
    [1,0,1], # purple
]


def set_all(strip, color):

    """Set all pixels to the same color."""

    for i in range(strip.numPixels()):

        strip.setPixelColor(i, color)

    strip.show()



class audio_led_connector():
    """Class to connect audio data to LED patterns.
        The pattern fuction should take audio data as input
        and a strip object to update. Then return an array
        of LED colors.
    """
    def __init__(self, strip, stream,
                 pattern_function ):
        self.strip = strip
        self.stream = stream
        self.pattern_function = pattern_function

    def update_leds(self):

        the_leds = self.pattern_function(self.stream, self.strip)

        for i, colour in enumerate(the_leds):
            strip.setPixelColor(i, colour)

        strip.show()

    def run(self, duration):
        end_time = time.time() + duration
        while time.time() < end_time:
            self.update_leds()




def calculate_log_bins(num_leds, min_freq, max_freq):
    """
    Calculates the logarithmic frequency cutoff points for an array of LEDs.

    Args:
        num_leds (int): The total number of LED segments (bins) you need.
        min_freq (float): The lowest frequency to consider (e.g., 20 Hz).
        max_freq (float): The highest frequency to consider (e.g., 20000 Hz).

    Returns:
        numpy.ndarray: An array of frequency cutoffs (in Hz) for the bins.
    """
    # 1. Calculate the logarithmic range (base for the exponential)
    # The exponential function y = min_freq * (max_freq/min_freq)^(x/num_leds)
    # The exponent needs to map linear steps (0 to num_leds) onto the log scale.
    
    # We create a linearly spaced array from 0 to 1, representing the LED index
    # normalized by the total number of LEDs.
    linear_indices = np.linspace(0, num_leds, num=num_leds + 1) / num_leds
    
    # 2. Apply the inverse log (exponential) function
    # This stretches the lower part of the linear scale and squashes the upper part.
    log_cutoffs = min_freq * np.power(max_freq / min_freq, linear_indices)
    
    # The result has num_leds + 1 points, where log_cutoffs[i] and log_cutoffs[i+1] 
    # define the frequency range for LED[i]. So we will just chop off the first point.
    log_cutoffs = log_cutoffs[1:]


    return log_cutoffs.astype(int)





class freq_audio_connector(audio_led_connector):
    """ 
    Sub class to connect frequency audio data to LED patterns.
    """
    def __init__(self, strip, stream,
                 pattern_function ):
        # divide the frequency ranges up for each LED
        # self.freq_thresholds = [
        #     i for i in range(0,
        #                      RATE // 2,
        #                      int((RATE / 2) / LED_COUNT))
        # ]
        self.freq_thresholds = calculate_log_bins(LED_COUNT, 40, RATE // 2)
        # assuming that the size of the array will only
        # different by one
        if len(self.freq_thresholds) > LED_COUNT:
            self.freq_thresholds = self.freq_thresholds[:LED_COUNT]
            self.freq_thresholds[-1] = RATE // 2
        if len(self.freq_thresholds) < LED_COUNT:
            self.freq_thresholds.append(RATE // 2)


        intensity_space = 255 * len(COLOUR_SEQUENCE)
        colour_sizes = MAX_LOUDNESS // len(COLOUR_SEQUENCE)

        self.output_colour_sequence = []
        for col in COLOUR_SEQUENCE:
            for j in range(0,255):
                r = col[0] * j 
                g = col[1] * j                 
                b = col[2] * j 
                self.output_colour_sequence.append(Color(r, g, b))
        print("one")
        print(self.output_colour_sequence[0:260])

        super().__init__(strip, stream,
                 pattern_function )
        
    def update_leds(self):

        the_leds = self.pattern_function(self.stream, self.freq_thresholds, self)

        for i, colour in enumerate(the_leds):
            strip.setPixelColor(i, colour)

        strip.show()




def audio_led_loudness_pattern(stream, strip):
    # for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
    data = stream.read(CHUNK)
    frames.append(data)
    # Process the raw 'data' here, e.g., convert to numpy array:
    audio_data = np.frombuffer(data, dtype=np.int16)

    avg = np.mean(np.abs(audio_data))
    max = np.max(np.abs(audio_data))

    # num_leds = int((avg / MAX_LOUDNESS) * LED_COUNT)
    num_leds = int((max / MAX_LOUDNESS) * LED_COUNT)


    the_leds = []
    for i in range(LED_COUNT):
        if i < num_leds:
            the_leds.append(fore_colour)
        else:
            the_leds.append(back_color)

    return the_leds






def audio_led_freq_pattern(stream, freq_thresholds):
    data = stream.read(CHUNK)
    audio_data = np.frombuffer(data, dtype=np.int16)

    # Apply FFT
    fft_result = np.fft.fft(audio_data)
    fft_magnitude = np.abs(fft_result[:CHUNK//2])
    frequencies = np.linspace(0, RATE / 2, CHUNK // 2)

    peak_index = np.argmax(fft_magnitude)
    peak_frequency = frequencies[peak_index]

    # Map frequency to LED colors
    the_leds = []
    for idx, this_threshold in enumerate(freq_thresholds):
        if idx ==0:
            last_threshold = 0
        else:
            last_threshold = freq_thresholds[idx -1]

        these_range_values = []
        for this_freq in frequencies:
            if this_freq > this_threshold:
                break
            if (this_freq > last_threshold ):
                mag_index = np.where(frequencies == this_freq)[0][0]
                magnitude = fft_magnitude[mag_index]

                intensity_space = 255 * len(COLOUR_SEQUENCE)

                intensity = int((magnitude / MAX_LOUDNESS) * intensity_space)
                these_range_values.append(intensity)
                

        this_led_intensity = sum(these_range_values) // len(these_range_values) \
            if len(these_range_values) >0 else 0

        colour_sizes = MAX_LOUDNESS // len(COLOUR_SEQUENCE)
        which_colour = this_led_intensity // colour_sizes
        if which_colour >= len(COLOUR_SEQUENCE):
            which_colour = len(COLOUR_SEQUENCE) -1
        colour_intensity = ((this_led_intensity % colour_sizes) / colour_sizes) * 255
        colour_array = [int(c * colour_intensity) for c in COLOUR_SEQUENCE[which_colour]]
        the_leds.append(Color(*colour_array))

    return the_leds

def gem_audio_led_freq_pattern(stream, freq_thresholds, self):
    # 1. Read data (same)
    data = stream.read(CHUNK)
    audio_data = np.frombuffer(data, dtype=np.int16)

    # 2. Apply FFT (same)
    fft_result = np.fft.fft(audio_data)
    # We only care about the first half (positive frequencies)
    fft_magnitude = np.abs(fft_result[:CHUNK//2])
    
    # 3. Create the frequency indices for faster lookups
    # These are the indices that correspond to the frequency thresholds
    # We only need to calculate this once outside the main loop if possible
    # but calculating here is fine.
    # Note: We use the floor to find the index corresponding to the threshold frequency
    index_thresholds = np.floor(freq_thresholds / (RATE / CHUNK) ).astype(int)
    # Add index 0 to the start
    index_thresholds = np.insert(index_thresholds, 0, 0)
    
    the_leds = []
    
    # Iterate through the LED segments (frequency bins)
    for idx in range(LED_COUNT):
        # Determine the start and end indices for this LED's frequency bin
        start_index = index_thresholds[idx]
        end_index = index_thresholds[idx+1]
        
        # SLICING: Get all magnitudes within this bin using a single operation
        bin_magnitudes = fft_magnitude[start_index:end_index]
        
        # VECTORIZED MEAN: Calculate the average magnitude for the bin
        if len(bin_magnitudes) == 0:
            this_led_intensity = 0
        else:
            # We use the MEAN magnitude instead of SUM to normalize for bin width
            avg_magnitude = np.mean(bin_magnitudes)
            
            # Use a pre-determined maximum for consistent scaling (e.g., 200000)
            # The FFT magnitude maximum is device/volume dependent. You'll need 
            # to tune the max_ref value below.
            MAX_MAGNITUDE_REF = 100000 # <-- **TUNE THIS VALUE**
            
            # Simple scaling to get a value between 0 and 1
            intensity_ratio = avg_magnitude / MAX_MAGNITUDE_REF
            # Clamp the ratio between 0 and 1
            intensity_ratio = np.clip(intensity_ratio, 0.0, 1.0)
            
            this_led_intensity = int(intensity_ratio * len(self.output_colour_sequence))

        # 4. Color Mapping (Simplified)
        # Simplified color mapping without a complex sequence lookup
        if this_led_intensity > 0:
            # Hue-based mapping (example: green for low, red for high intensity)
            #colour = Color(this_led_intensity, 255 - this_led_intensity, 0)
            colour = self.output_colour_sequence[this_led_intensity -1]
        else:
            colour = Color(0, 0, 0)
            
        the_leds.append(colour)

    return the_leds




loudness_contr = audio_led_connector(strip, stream,
                             audio_led_loudness_pattern)

freq_contr = freq_audio_connector(strip, stream,
                             gem_audio_led_freq_pattern)

# loudness_contr.run(60)
freq_contr.run(300)

print("Finished listening.")
stream.stop_stream()
stream.close()
p.terminate()

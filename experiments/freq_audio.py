import pyaudio
import numpy as np
from scipy.fft import fft # Often easier to import fft directly


CHUNK = 1024  # Size of a single audio chunk
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 48000 # 16000 for video mic
RECORD_SECONDS = 5
USB_MIC_INDEX = 0  # **CHANGE THIS to your device's index**

p = pyaudio.PyAudio()

stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK,
                input_device_index=USB_MIC_INDEX)

print("Recording...")
frames = []

for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
    data = stream.read(CHUNK)
    # 2. Convert raw bytes to a NumPy array (dtype must match your PyAudio format)
    # Assuming pyaudio.paInt16 is used, which corresponds to np.int16
    audio_data = np.frombuffer(data, dtype=np.int16) 

    # 3. Apply the Fast Fourier Transform (FFT)
    # This transforms the signal from the time domain to the frequency domain
    fft_result = fft(audio_data)

    import pdb;pdb.set_trace()

    # 4. Get the magnitude (amplitude) of the frequencies
    # We take the absolute value and only use the first half, 
    # as the second half is a mirror image (for real-valued input)
    fft_magnitude = np.abs(fft_result[:CHUNK//2])

    # 5. Create the corresponding frequency axis
    # The maximum frequency is RATE/2 (Nyquist frequency)
    frequencies = np.linspace(0, RATE / 2, CHUNK // 2)

    # Now, 'frequencies' holds the frequency bins (e.g., 0 Hz, 43 Hz, 86 Hz...)
    # and 'fft_magnitude' holds the volume/intensity at those frequencies.
    
    # Example: Find the loudest frequency (the 'peak')
    peak_index = np.argmax(fft_magnitude)
    peak_frequency = frequencies[peak_index]

    print(f"Loudest Frequency: {peak_frequency:.2f} Hz")

print("Finished recording.")
stream.stop_stream()
stream.close()
p.terminate()

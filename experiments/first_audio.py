import pyaudio
import numpy as np

CHUNK = 1024  # Size of a single audio chunk
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
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
    frames.append(data)
    # Process the raw 'data' here, e.g., convert to numpy array:
    audio_data = np.frombuffer(data, dtype=np.int16)
    print(f"Average amplitude: {np.mean(np.abs(audio_data))}")
    print(f"Max amplitude: {np.max(np.abs(audio_data))}")

print("Finished recording.")
stream.stop_stream()
stream.close()
p.terminate()
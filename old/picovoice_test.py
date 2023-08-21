import pyaudio
import wave
import pvleopard
import np


# Parameters
sample_rate = 16000
frame_length = 512
duration = 5  # seconds
num_frames = int(duration * sample_rate / frame_length)

# Initialize PyAudio
audio = pyaudio.PyAudio()

# Open the audio stream
stream = audio.open(format=pyaudio.paInt16, channels=1, rate=sample_rate, input=True, frames_per_buffer=frame_length)

# Capture audio for the specified duration
print("Capturing audio for {} seconds...".format(duration))
frames = []
for _ in range(num_frames):
    data = stream.read(frame_length)
    frames.append(data)

# Close the stream and terminate PyAudio
stream.stop_stream()
stream.close()
audio.terminate()
print("Done capturing")

# Save to WAV file
output_filename = "captured_audio.wav"
with wave.open(output_filename, 'wb') as wf:
    wf.setnchannels(1)
    wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
    wf.setframerate(sample_rate)
    wf.writeframes(b''.join(frames))



# Read the saved WAV file
with wave.open(output_filename, 'rb') as wf:
    sample_rate = wf.getframerate()
    assert sample_rate == 16000, "Sample rate must be 16 kHz"
    
    # Read audio data and convert to NumPy array
    audio_data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)

# Create Leopard instance
access_key = "hW2ayLGCpyhg+w/tHHFFcpr0Df+zGciHcgdSSO9TcYDzpuimmsh8fg=="  # Replace with your access key
leopard = pvleopard.create(access_key=access_key)

# Process the audio data with Leopard
transcript, _ = leopard.process(audio_data)

# Print the transcription
print("Transcribed text:", transcript)

# Delete the Leopard instance when done
leopard.delete()



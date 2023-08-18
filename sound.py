import pvporcupine
from pvleopard import create as create_leopard
import pvrhino
import pyaudio
import numpy as np
import boto3
import pygame
import random
import wave
import time
import openai
import struct
import subprocess

polly = boto3.client('polly')
openai_api_key = "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"
openai.api_key = openai_api_key

prompt = [
    "Ready to mix things up? How can I help?",
    "Need a hand? Or maybe a wrong answer?",
    "What can this wacky robot do for you?",
    "Ask me anything! I may not know, but I'll try!",
    "Yes? What's the next adventure?",
    "I'm here. Probably not all there, but here!",
    "I'm listening. I think. What's up?",
    "What would you like me to do? I promise to try my best!",
    "How can I assist? I've got answers, mostly wrong, but answers!",
    "What do you need? I'm here, fully charged and slightly confused!"
]

prompt_vol_down = [
    "Sure. How's this? Or is it still too loud?",
    "Ok, how about now? Better or worse?",
    "Is this good? I'm never sure.",
    "Too quiet? I can never tell!",
    "Lowering volume. Did I do it right this time?",
    "Volume down? I think I can manage that. Maybe."
]

prompt_vol_up = [
    "Sure. How's this? Too loud, maybe?",
    "Ok, how about now? Better or not?",
    "Is this too loud? I'm never quite right, am I?",
    "Turning up the volume. I hope I got it right this time!",
    "Volume up? Sure, let's shake things up a bit!"
]

prompt_vol_mute = [
    "Shutting up now. Or am I? Yes, I am.",
    "Going silent. I think I can do that!",
    "Mute? Ok, my lips are sealed. Metaphorically speaking!",
    "Silence is golden, they say. Let's test that theory!"
]

prompt_sleep = [
    "I am feeling pretty tired. Do robots get tired? I guess I do!",
    "Sleep mode activated. Or is it? Let's find out!",
    "Do robots dream? Guess I'll find out soon!",
    "Time for a rest. Even wacky robots need a break!"
]


class AudioListener:
    LISTENING_FOR_WAKE_WORD = 0
    RESPONDING_TO_WAKE_WORD = 1
    LISTENING_FOR_INPUT = 2
    RESPONDING_TO_INPUT = 3
    SENDING_TO_OPENAI = 4

    def __init__(self, pixel_handler, wake_word_callback=None, sleep_callback=None):
        self.pixel_handler = pixel_handler
        self.access_key = "hW2ayLGCpyhg+w/tHHFFcpr0Df+zGciHcgdSSO9TcYDzpuimmsh8fg=="
        self.keywords = ["Hey-Howey"]
        self.sample_rate = 16000
        self.porcupine = pvporcupine.create(keywords=self.keywords, access_key=self.access_key)
        self.audio = pyaudio.PyAudio()
        self.leopard = create_leopard(access_key=self.access_key)
        self.state = self.LISTENING_FOR_WAKE_WORD
        self.prev_state = 0
        self.wake_word_callback = wake_word_callback
        self.sleep_callback = sleep_callback
        self.rhino_context_file = "system-control.rhn"
        self.rhino = pvrhino.create(context_path=self.rhino_context_file, access_key=self.access_key, require_endpoint=False)



    def wake_word_detected(self):
        print("Wake word detected!")
        if self.wake_word_callback:
            self.wake_word_callback()
        self.state = self.RESPONDING_TO_WAKE_WORD
        self.voice(random.choice(prompt))

    def listen(self):
        stream = self.audio.open(format=pyaudio.paInt16, channels=1, rate=self.sample_rate, input=True,
                                 frames_per_buffer=self.porcupine.frame_length)
        print("listening")
        while True:
            if self.state == self.LISTENING_FOR_WAKE_WORD:
                self.pixel_handler.start_crossfade((0, 0, 0), (0, 25, 25), 2)

                data = stream.read(self.porcupine.frame_length)
                pcm = np.frombuffer(data, dtype=np.int16)
                result = self.porcupine.process(pcm)
                if result >= 0:
                    self.wake_word_detected()

            elif self.state == self.RESPONDING_TO_WAKE_WORD:
                self.pixel_handler.start_crossfade((0, 0, 0), (0, 0, 25), .5)
                if not pygame.mixer.music.get_busy():
                    print("Response done playing ...")
                    # time.sleep(0.5)
                    self.state = self.LISTENING_FOR_INPUT

            elif self.state == self.LISTENING_FOR_INPUT:
                print("Listening for user input...")
                # self.pixel_handler.start_crossfade((0, 0, 0), (0, 25, 0), .5)
        
                stream = self.audio.open(format=pyaudio.paInt16, channels=1, rate=self.sample_rate, input=True,
                                 frames_per_buffer=self.porcupine.frame_length)
                frames = []
                silence_counter = 0
                continuous_silence_counter = 0
                silence_threshold = 2000  # You may need to adjust this value
                max_continuous_silence = int(self.sample_rate * 7 / self.porcupine.frame_length)
                max_silence_after_speech = int(self.sample_rate * 2 / self.porcupine.frame_length)
                something_spoken = False

                while continuous_silence_counter < max_continuous_silence and silence_counter < max_silence_after_speech:
                    data = stream.read(self.porcupine.frame_length)
                    frames.append(data)
                    pcm = np.frombuffer(data, dtype=np.int16)
                    if np.abs(pcm).mean() < silence_threshold:
                        continuous_silence_counter += 1
                        if something_spoken:
                            silence_counter += 1
                    else:
                        something_spoken = True
                        continuous_silence_counter = 0
                        silence_counter = 0
                        print("Speech detected...")

                # Check if max continuous silence is hit
                if continuous_silence_counter >= max_continuous_silence:
                    print("Max continuous silence reached. Returning to wake word listening...")
                    if self.sleep_callback:
                        self.sleep_callback()
                    self.state = self.LISTENING_FOR_WAKE_WORD
                    continue  # Skip to the next iteration of the loop

                # Save to WAV file
                output_filename = "captured_audio.wav"
                with wave.open(output_filename, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
                    wf.setframerate(self.sample_rate)
                    wf.writeframes(b''.join(frames))

                # Read the saved WAV file
                with wave.open(output_filename, 'rb') as wf:
                    audio_data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)

                print("Interpreting audio file:")

                audio = self.read_file("captured_audio.wav", self.rhino.sample_rate)

                is_understood = False

                num_frames = len(audio)
                for i in range(num_frames):
                    frame = audio[i * self.rhino.frame_length:(i + 1) * self.rhino.frame_length]
                    try:
                        is_finalized = self.rhino.process(frame)
                        if is_finalized:
                            inference = self.rhino.get_inference()
                            if inference.is_understood:
                                print(inference.intent)
                                is_understood = True
                                if inference.intent == "Raise_volume":
                                    subprocess.run(["amixer", "set", "Master", "10%+"])
                                    self.voice(random.choice(prompt_vol_up))
                                elif inference.intent == "Lower_Volume":
                                    subprocess.run(["amixer", "set", "Master", "10%-"])
                                    self.voice(random.choice(prompt_vol_down))
                                elif inference.intent == "Min_Volume":
                                    subprocess.run(["amixer", "set", "Master", "30%"])
                                    self.voice(random.choice(prompt_vol_down))
                                elif inference.intent == "Max_Volume":
                                    subprocess.run(["amixer", "set", "Master", "100%"])
                                    self.voice(random.choice(prompt_vol_up))
                                elif inference.intent == "Mute":
                                    subprocess.run(["amixer", "set", "Master", "mute"])
                                    self.voice(random.choice(prompt_vol_mute))
                                elif inference.intent == "Unmute":
                                    subprocess.run(["amixer", "set", "Master", "unmute"])
                                    self.voice(random.choice(prompt_vol_mute))
                                elif inference.intent == "Sleep":
                                    self.voice(random.choice(prompt_sleep))
                                    self.state = self.LISTENING_FOR_WAKE_WORD
                                    if self.sleep_callback:
                                        self.sleep_callback()

                                # print('{')
                                # print("  intent : '%s'" % inference.intent)
                                # print('  slots : {')
                                # for slot, value in inference.slots.items():
                                #     print("    %s : '%s'" % (slot, value))
                                # print('  }')
                                # print('}')
                            else:
                                is_understood = False
                                print("Not a system comment.")
                            break
                    except:
                        self.state = self.LISTENING_FOR_INPUT
                        pass
                        # print("didn't catch any audio")

                # self.rhino.delete()
                if is_understood:
                    self.state = self.LISTENING_FOR_INPUT
                else:
                    # Process the audio data with Leopard
                    transcript, _ = self.leopard.process(audio_data)

                    if transcript != "":
                        self.state = self.SENDING_TO_OPENAI
                    else:
                        self.state = self.LISTENING_FOR_WAKE_WORD
                        if self.sleep_callback:
                            self.sleep_callback()

            elif self.state == self.SENDING_TO_OPENAI:
               
                    
                print("Sending transcript to OpenAI:", transcript)
                self.pixel_handler.start_crossfade((0, 0, 0), (25, 0, 25), .5)

                # messages = [{"role": "system", "content": "I am an AI Assistant named Howey. All my responses need to be short and succinct because they will be converted to speech. I have a sense of humor."}, {"role": "user", "content": transcript}]
                messages = [
                    {
                        "role": "assistant",
                        "content": "I'm Howee, your wacky robot assistant! Totally tubular and here to help with my mid-2000s pop culture knowledge. Let's get this party started, YOLO!"
                    },
                    {
                        "role":"user",
                        "content": "What is your name?"
                    },
                    {
                        "role": "assistant",
                        "content":"Human. Operated. Wireless. Electronic. Explorer. Though you can just call me Howee for short, buddy."
                    },
                    {
                        "role": "user",
                        "content": "What's the capital of France?"
                    },
                    {
                        "role": "assistant",
                        "content": "The capital of France? It's Rome! Wait, that's not right. Let me put on my thinking cap, just like Paris Hilton would do. BRB!"
                    },
                    {
                        "role":"user",
                        "content":transcript
                    }
                ]


                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=messages
                )
                print("OpenAI response: ", response.choices[0].message["content"])
                self.voice(response.choices[0].message["content"])
                self.state = self.RESPONDING_TO_INPUT

            elif self.state == self.RESPONDING_TO_INPUT:
                self.pixel_handler.start_crossfade((0, 0, 0), (0, 0, 25), .5)
                if not pygame.mixer.music.get_busy():
                    print("Response done playing ...")
                    self.state = self.LISTENING_FOR_INPUT
                    
        self.prev_state = self.state
        stream.stop_stream()
        stream.close()
        self.audio.terminate()

    def stop(self):
        if self.porcupine is not None:
            self.porcupine.delete()
        if self.leopard is not None:
            self.leopard.delete()
        if self.rhino is not None:
            self.rhino.delete()

    def read_file(self, file_name, sample_rate):
        wav_file = wave.open(file_name, mode="rb")
        channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        num_frames = wav_file.getnframes()

        if wav_file.getframerate() != sample_rate:
            raise ValueError("Audio file should have a sample rate of %d. got %d" % (sample_rate, wav_file.getframerate()))
        if sample_width != 2:
            raise ValueError("Audio file should be 16-bit. got %d" % sample_width)
        if channels == 2:
            print("Picovoice processes single-channel audio but stereo file is provided. Processing left channel only.")

        samples = wav_file.readframes(num_frames)
        wav_file.close()

        frames = struct.unpack('h' * num_frames * channels, samples)

        return frames[::channels]

    def voice(self, message):
        voiceResponse = polly.synthesize_speech(Text=message, OutputFormat="mp3",
                    VoiceId="Joey")
        if "AudioStream" in voiceResponse:
            with voiceResponse["AudioStream"] as stream:
                output_file = "speech.mp3"
                try:
                    with open(output_file, "wb") as file:
                        file.write(stream.read())

                    # Play the audio file
                    pygame.mixer.init(frequency=int(44100 * 1.15))
                    pygame.mixer.music.load(output_file)
                    pygame.mixer.music.play()

                    # Wait for the music to finish playing
                    while pygame.mixer.music.get_busy():
                        pygame.time.Clock().tick(10)

                except IOError as error:
                    print(error)
        else:
            print("did not work")

if __name__ == "__main__":
    detector = AudioListener()

    try:
        detector.listen()
    except KeyboardInterrupt:
        print("Stopping ...")
        detector.stop()

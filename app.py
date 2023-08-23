from flask import Flask, render_template
from flask_socketio import SocketIO
import threading, platform
from servo_hat import PiServoHatWrapper
from sound import AudioListener

import time


if platform.machine() in ['aarch64', 'armv6l']:
    from person_sensor import PersonSensor
    from pixels import Pixels
    pixel_handler = Pixels()
    pixel_handler.start_crossfade((0, 0, 0), (25, 25, 0), 1)
    sensor = PersonSensor()
    servo_hat = PiServoHatWrapper(100)
    servo_hat.deactivate()

    def update_servo_position():
        while True:
            # Updating the servo_hat with the current face position
            face_position = sensor.get_current_face_center()
            servo_hat.update_person_position(face_position)

            # Waiting for 0.1 seconds before updating again
            time.sleep(0.2)


    servo_updater_thread = threading.Thread(target=update_servo_position)
    servo_updater_thread.start()

else:
    pixel_handler = None

def run_audio_listener():
    global pixel_handler
    if platform.machine() in ['aarch64', 'armv6l']:
        listener = AudioListener(pixel_handler=pixel_handler, wake_word_callback=servo_hat.activate, sleep_callback=servo_hat.deactivate, listening_callback=servo_hat.stop_blinking, responding_callback=servo_hat.start_blinking, blink_callback=servo_hat.blink)  # Pass the activate method as a callback
    else:
        listener = AudioListener()
    listener.listen()

def play_audio(output_file):
    try:
        # Initialize pygame mixer and play the audio file
        pygame.mixer.init(frequency=int(44100 * 1.15))
        pygame.mixer.music.load(output_file)
        pygame.mixer.music.play()

        # Wait for the music to finish playing
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
    except IOError as error:
        print(error)

audio_listener_thread = threading.Thread(target=run_audio_listener)  # Create a separate thread for the audio listener
audio_listener_thread.start()

# if __name__ == '__main__':
    # socketio.run(app, host="0.0.0.0")

from flask import Flask, render_template
from flask_socketio import SocketIO
import threading, platform
from servo_hat import PiServoHatWrapper
from sound import AudioListener

# app = Flask(__name__)
# socketio = SocketIO(app)
import time

# @app.route('/')
# def index():
#     return render_template('index.html')

print(platform.machine())

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
    # listener = AudioListener()
    if platform.machine() in ['aarch64', 'armv6l']:
        listener = AudioListener(pixel_handler=pixel_handler, wake_word_callback=servo_hat.activate, sleep_callback=servo_hat.deactivate)  # Pass the activate method as a callback
    else:
        listener = AudioListener()
    listener.listen()

audio_listener_thread = threading.Thread(target=run_audio_listener)  # Create a separate thread for the audio listener
audio_listener_thread.start()

# if __name__ == '__main__':
    # socketio.run(app, host="0.0.0.0")

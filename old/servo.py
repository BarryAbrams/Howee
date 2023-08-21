import pi_servo_hat
import time
import threading

# Initialize Constructor
test = pi_servo_hat.PiServoHat()

# Restart Servo Hat (in case Hat is frozen/locked)
test.restart()

# Servo settings
SERVO_SETTINGS = [
    {'label':'x_axis', 'channel': 0, 'min_throw': 20, 'max_throw': 160, 'sweep': False},
    {'label':'y_axis', 'channel': 1, 'min_throw': 50, 'max_throw': 120, 'sweep': False},
    {'label':'tl_eyelid', 'channel': 2, 'min_throw': 130, 'max_throw': 0, 'sweep': False},
    {'label':'bl_eyelid', 'channel': 3, 'min_throw': 0, 'max_throw': 140, 'sweep': False},
    {'label':'tr_eyelid', 'channel': 4, 'min_throw': 0, 'max_throw': 160, 'sweep': False},
    {'label':'br_eyelid', 'channel': 5, 'min_throw': 140, 'max_throw': 0, 'sweep': False},
    # Add more servo settings here
]


current_positions = [128] * 6  # Assuming 6 servos


def ease_servo(channel, target_position, duration_ms):
    # Get the current position
    current_position = test.get_servo_position(channel)  # Assuming this method exists

    # Determine the step size and delay for easing
    step_size = 1 if target_position > current_position else -1
    num_steps = abs(target_position - current_position)
    delay = duration_ms / (num_steps * 1000)

    # Move the servo gradually to the target position
    position = current_position
    while position != target_position:
        position += step_size
        # Ensure position is within the range
        if (step_size > 0 and position > target_position) or (step_size < 0 and position < target_position):
            position = target_position
        print(position)
        test.move_servo_position(channel, position, 180)
        time.sleep(delay)

def set_servo_position(label, value, duration_ms=500):
    # Find the servo settings by label
    for servo in SERVO_SETTINGS:
        if servo['label'] == label:
            channel = servo['channel']
            
            # Scale the value to the appropriate range
            min_throw = servo['min_throw']
            max_throw = servo['max_throw']
            target_position = min_throw + (max_throw - min_throw) * value / 255

            # Get the current position from the global variable
            current_position = current_positions[channel]

            # Determine the step size and delay for easing
            step_size = 1 if target_position > current_position else -1
            num_steps = abs(target_position - current_position)
            delay = duration_ms / (num_steps * 1000)

            # Move the servo gradually to the target position
            position = current_position
            while position != target_position:
                position += step_size
                # Ensure position is within the range
                if (step_size > 0 and position > target_position) or (step_size < 0 and position < target_position):
                    position = target_position
                test.move_servo_position(channel, position, 180)
                time.sleep(delay)

            # Update the global variable with the new position
            current_positions[channel] = position

            break

# set_servo_position('x_axis', 128, 1000)
# set_servo_position('y_axis', 128, 1000)
# set_servo_position('tl_eyelid', 128)
# set_servo_position('bl_eyelid', 128)
# set_servo_position('tr_eyelid', 128)
# set_servo_position('br_eyelid', 128)

# Function to sweep a servo
def sweep_servo(channel, min_throw, max_throw):
    # Determine the correct order for the range
    start_throw = min(min_throw, max_throw)
    end_throw = max(min_throw, max_throw)

    # Moves servo position to min degrees
    test.move_servo_position(channel, min_throw, 180)
    time.sleep(1)

    # Moves servo position to max degrees
    test.move_servo_position(channel, max_throw, 180)
    time.sleep(1)

    # Sweep
    while True:
        for i in range(start_throw, end_throw + 1):
            print(i)
            test.move_servo_position(channel, i, 180)
            time.sleep(.01)
        for i in range(end_throw, start_throw - 1, -1):
            print(i)
            test.move_servo_position(channel, i, 180)
            time.sleep(.01)




# threads = []
# for servo in SERVO_SETTINGS:
#     if servo['sweep']:
#         t = threading.Thread(target=sweep_servo, args=(servo['channel'], servo['min_throw'], servo['max_throw']))
#         t.start()
#         threads.append(t)

# # Wait for all threads to complete (this will never happen in this code, since the threads run forever)
# for t in threads:
#     t.join()
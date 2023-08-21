import pi_servo_hat
import time, threading, random

class PiServoHatWrapper:
    def __init__(self, frequency=100):
        self.servo_hat = pi_servo_hat.PiServoHat()
        self.servo_hat.restart()
        self.servo_hat.set_pwm_frequency(frequency)

        self.x_axis = ServoController(self, 0, 10, 170)
        self.y_axis = ServoController(self, 1, 30, 120)
        self.rt_eyelid = ServoController(self, 2, 120, 0)
        self.lt_eyelid = ServoController(self, 4, 0, 120)
        self.rb_eyelid = ServoController(self, 3, 25, 180)
        self.lb_eyelid = ServoController(self, 5, 120, 0)

        self.last_move_time = 0
        self.last_center_x = None
        self.last_center_y = None

        self.active = True
            
    def activate(self):
        print("ACTIVATE")
        self.blinking_thread_stop = False  # Reset the flag
        self.active = True
        self.start_blinking()

    def deactivate(self):
        self.active = False
        self.stop_blinking()  # Stop the blinking thread
        self.move_eyes(0.5, 0.5)  # Move eyes to center
        servo_positions = [(self.rt_eyelid, 0), (self.rb_eyelid, 0), (self.lt_eyelid, 0), (self.lb_eyelid, 0)]
        smooth_move_servos(servo_positions, 5)  # Close eyelids

    def update_person_position(self, position):
        if self.active:
            if position is not None:
                x, y = position
                print("x:", x/255, "y:", y/255)
                self.move_eyes(x/255, y/255)

    def start_blinking(self):
        self.blinking_thread = threading.Thread(target=self.random_blink)
        self.blinking_thread.daemon = True  # Set as a daemon thread so it will close when the main program closes
        self.blinking_thread.start()

    def stop_blinking(self):
        if hasattr(self, 'blinking_thread'):
            self.blinking_thread_stop = True  # Signal the thread to stop
            self.blinking_thread.join()  # Wait for the thread to finish


    def random_blink(self):
        self.blinking_thread_stop = False  # Initialize the flag
        while not self.blinking_thread_stop:  # Check the flag in the loop condition
            time.sleep(random.uniform(2, 10))
            if random.random() < 0.5:
                self.blink()
            else:
                self.natural_blink()

    def update_sensor_position(self, sensor_position):
        if not self.active:
            return
        if sensor_position is not None:
            box_left = sensor_position['box_left']
            box_right = sensor_position['box_right']
            box_top = sensor_position['box_top']
            box_bottom = sensor_position['box_bottom']

            center_x = (box_left + box_right) / 2 / 100
            center_y = 1 - (box_top + box_bottom) / 2 / 160

            # print("Center of the bounding box: (x: {}, y: {})".format(center_x, center_y))

            # Check if enough time has passed since the last move
            if time.time() - self.last_move_time < .1:
                return

            # Check if the change is substantial
            # if self.last_center_x is not None and self.last_center_y is not None:
            #     if abs(center_x - self.last_center_x) < 0.05 and abs(center_y - self.last_center_y) < 0.05:
            #         return

            self.move_eyes(center_x, center_y)

            # Update the last move time and last position
            self.last_move_time = time.time()
            self.last_center_x = center_x
            self.last_center_y = center_y
        else:
            self.move_eyes(0.5, 0.5)


    def move_servo_position(self, channel, angle, duration):
        self.servo_hat.move_servo_position(channel, angle, duration)

    def blink(self):
        servo_positions = [(self.rt_eyelid, 0), (self.rb_eyelid, 0), (self.lt_eyelid, 0), (self.lb_eyelid, 0)]
        smooth_move_servos(servo_positions, 5)
        servo_positions = self.calculate_eyelid_positions(self.y_axis.get_current_position())
        smooth_move_servos(servo_positions, 5)

    def natural_blink(self):
        servo_positions = [(self.rt_eyelid, 0), (self.rb_eyelid, 0), (self.lt_eyelid, 0), (self.lb_eyelid, 0)]
        smooth_move_servos(servo_positions, 5)
        servo_positions = self.calculate_eyelid_positions(self.y_axis.get_current_position())
        smooth_move_servos(servo_positions, 5)

        # Pause for a brief moment to simulate the eyes being closed
        time.sleep(0.1)

        servo_positions = [(self.rt_eyelid, 0), (self.rb_eyelid, 0), (self.lt_eyelid, 0), (self.lb_eyelid, 0)]
        smooth_move_servos(servo_positions, 20)
        servo_positions = self.calculate_eyelid_positions(self.y_axis.get_current_position())
        smooth_move_servos(servo_positions, 20)

    def move_eyes(self, x_position, y_position):
        inverted_x = 1 - x_position
        adjusted_y = min(1, y_position * 1.15)  # Adjust y_position and make sure it's <= 1
        inverted_y = 1 - adjusted_y

        eye_positions = [(self.x_axis, inverted_x), (self.y_axis, inverted_y)]
        eyelid_positions = self.calculate_eyelid_positions(inverted_y)
        servo_positions = eye_positions + eyelid_positions
        smooth_move_servos(servo_positions, 15)

    def calculate_eyelid_positions(self, y_position):
        offset = (y_position - 0.5) * 0.5
        top_eyelid_position = 0.75 + offset
        bottom_eyelid_position = 0.75 - offset
        return [(self.rt_eyelid, top_eyelid_position), (self.rb_eyelid, bottom_eyelid_position),
                (self.lt_eyelid, top_eyelid_position), (self.lb_eyelid, bottom_eyelid_position)]

class ServoController:
    def __init__(self, servo_hat, channel, min_angle=0, max_angle=180):
        self.channel = channel
        self.min_angle = min_angle
        self.max_angle = max_angle
        self.servo_hat = servo_hat
        self.current_angle = (self.min_angle + self.max_angle) / 2  # Initialize to midpoint of range
        self.previous_smoothed_position = self.get_current_position()  # Initialize with current position
        self.alpha = 0.05  # You can adjust this value for desired smoothness
        self.move_to_center()

    def get_current_position(self):
        # Assuming the current angle is stored in self.current_angle
        return (self.current_angle - self.min_angle) / (self.max_angle - self.min_angle)

    def move_to_center(self):
        self.move_to_position(0.5)
        time.sleep(.5)

    def move_to_angle(self, angle):
        if angle < min(self.min_angle, self.max_angle):
            angle = min(self.min_angle, self.max_angle)
        elif angle > max(self.min_angle, self.max_angle):
            angle = max(self.min_angle, self.max_angle)

        self.servo_hat.move_servo_position(self.channel, angle, 180)
        self.current_angle = angle  # Store the current angle

    def move_to_position(self, position):
        if position < 0:
            position = 0
        elif position > 1:
            position = 1

        angle_range = self.max_angle - self.min_angle
        angle = self.min_angle + position * angle_range
        self.move_to_angle(angle)

    def smooth_move_to_position(self, target_position, duration=1.0):
        start_time = time.time()
        end_time = start_time + duration

        print("smooth move to position")

        while time.time() < end_time:
            elapsed_time = time.time() - start_time
            t = elapsed_time / duration
            desired_position = self.get_current_position() + t * (target_position - self.get_current_position())

            # Apply the smoothing (EMA) algorithm
            smoothed_position = (desired_position * self.alpha) + (self.previous_smoothed_position * (1 - self.alpha))

            self.move_to_position(smoothed_position)
            self.previous_smoothed_position = smoothed_position  # Update the previous value

            time.sleep(0.01)  # Adjust the sleep time for the desired speed

        # Ensure the final position is reached
        self.move_to_position(target_position)


def smooth_move_servos(servo_positions, steps=100, delay_time=0.01):
    def move_servo(servo, target_position):
        current_position = servo.get_current_position()
        
        for step in range(steps + 1):
            t = step / steps
            eased_t = t**2 * (3 - 2 * t)
            position = current_position + eased_t * (target_position - current_position)
            servo.move_to_position(position)
            time.sleep(delay_time)
        
        servo.move_to_position(target_position)
    
    threads = [threading.Thread(target=move_servo, args=sp) for sp in servo_positions]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()


# servo_hat = PiServoHatWrapper(100)

# servo_hat.move_eyes(0.25, 0.85)  # Look up
# servo_hat.move_eyes(0.75, 0.15)  # Look down
# servo_hat.move_eyes(0.5, 0.5)  # Look down
# servo_hat.blink()

# x_axis = ServoController(servo_hat, 0, 10, 170)
# y_axis = ServoController(servo_hat, 1, 30, 120)
# rt_eyelid = ServoController(servo_hat, 2, 120, 0)
# lt_eyelid = ServoController(servo_hat, 4, 0, 120)
# rb_eyelid = ServoController(servo_hat, 3, 45, 160)
# lb_eyelid = ServoController(servo_hat, 5, 100, 0)



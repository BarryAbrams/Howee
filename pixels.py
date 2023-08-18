from apa102 import APA102
from gpiozero import LED
import time
import threading

class Pixels:
    def __init__(self, num_pixels=3, power_pin=5):
        self.driver = APA102(num_led=num_pixels)
        self.power = LED(power_pin)
        self.power.on()
        self.num_pixels = num_pixels
        self.current_color = (0, 0, 0)
        self.current_crossfade_params = None
        self.crossfade_thread = None
        self.clear()

    def set_color(self, color, stop_crossfade=True):
        if stop_crossfade:
            self.stop_crossfade()
        r, g, b = color
        self.current_color = color
        for i in range(self.num_pixels):
            self.driver.set_pixel(i, r, g, b)
        self.driver.show()

    def start_crossfade(self, color1, color2, duration, step_time=0.01):
        new_params = (color1, color2, duration, step_time)
        if self.current_crossfade_params == new_params:
            return  # Do nothing if the parameters are the same
        self.stop_crossfade()
        self.current_crossfade_params = new_params
        self.crossfade_thread = threading.Thread(target=self.crossfade, args=(color1, color2, duration, step_time))
        self.crossfade_thread.start()

    def stop_crossfade(self):
        self.crossfade_running = False
        if self.crossfade_thread:
            self.crossfade_thread.join()  # Optional: wait for the thread to finish
        self.current_crossfade_params = None


    def crossfade(self, color1, color2, duration, step_time=0.01):
        self.crossfade_running = True
        while self.crossfade_running:
            # Forward crossfade from color1 to color2
            self._fade(color1, color2, duration, step_time)
            # Reverse crossfade from color2 to color1
            self._fade(color2, color1, duration, step_time)

    def _fade(self, start_color, end_color, duration, step_time):
        start_time = time.time()
        for i in range(101):  # 101 steps to include both end colors
            t = i / 100
            r = int(start_color[0] * (1 - t) + end_color[0] * t)
            g = int(start_color[1] * (1 - t) + end_color[1] * t)
            b = int(start_color[2] * (1 - t) + end_color[2] * t)
            self.set_color((r, g, b), False)
            time.sleep(step_time * duration)
        end_time = time.time()
        elapsed_time = end_time - start_time
        remaining_time = duration - elapsed_time
        if remaining_time > 0:
            time.sleep(remaining_time)  # Wait the remaining time if the fade was too fast

    def get_color(self):
        return self.current_color

    def clear(self):
        self.set_color((0, 0, 0))

    def flash_color(self, r, g, b, duration=1):
        self.set_color((r, g, b))
        time.sleep(duration)
        self.set_color(*self.current_color)

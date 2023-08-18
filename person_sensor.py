import io
import fcntl
import struct
import time
import threading

class PersonSensor:
    def __init__(self):
        self.PERSON_SENSOR_I2C_ADDRESS = 0x62

        # We will be reading raw bytes over I2C, and we'll need to decode them into
        # data structures. These strings define the format used for the decoding, and
        # are derived from the layouts defined in the developer guide.
        self.PERSON_SENSOR_I2C_HEADER_FORMAT = "BBH"
        self.PERSON_SENSOR_I2C_HEADER_BYTE_COUNT = struct.calcsize(
            self.PERSON_SENSOR_I2C_HEADER_FORMAT)

        self.PERSON_SENSOR_FACE_FORMAT = "BBBBBBbB"
        self.PERSON_SENSOR_FACE_BYTE_COUNT = struct.calcsize(self.PERSON_SENSOR_FACE_FORMAT)

        self.PERSON_SENSOR_FACE_MAX = 4
        self.PERSON_SENSOR_RESULT_FORMAT = self.PERSON_SENSOR_I2C_HEADER_FORMAT + \
            "B" + self.PERSON_SENSOR_FACE_FORMAT * self.PERSON_SENSOR_FACE_MAX + "H"
        self.PERSON_SENSOR_RESULT_BYTE_COUNT = struct.calcsize(self.PERSON_SENSOR_RESULT_FORMAT)

        # I2C channel 1 is connected to the GPIO pins
        self.I2C_CHANNEL = 1
        self.I2C_PERIPHERAL = 0x703

        # How long to pause between sensor polls.
        self.PERSON_SENSOR_DELAY = 0.2

        self.i2c_handle = io.open("/dev/i2c-" + str(self.I2C_CHANNEL), "rb", buffering=0)
        fcntl.ioctl(self.i2c_handle, self.I2C_PERIPHERAL, self.PERSON_SENSOR_I2C_ADDRESS)


        self.running = False
        self.current_pos = None

    def read_sensor_data(self):
        """Read data once from the sensor and process it."""
        try:
            read_bytes = self.i2c_handle.read(self.PERSON_SENSOR_RESULT_BYTE_COUNT)
        except OSError as error:
            print("No person sensor data found")
            print(error)
            return

        offset = 0
        (pad1, pad2, payload_bytes) = struct.unpack_from(self.PERSON_SENSOR_I2C_HEADER_FORMAT, read_bytes, offset)
        offset += self.PERSON_SENSOR_I2C_HEADER_BYTE_COUNT

        (num_faces,) = struct.unpack_from("B", read_bytes, offset)
        num_faces = int(num_faces)
        offset += 1

        largest_face = None
        largest_area = 0

        for _ in range(num_faces):
            face_data = struct.unpack_from(self.PERSON_SENSOR_FACE_FORMAT, read_bytes, offset)
            (box_confidence, box_left, box_top, box_right, box_bottom, _, _, _) = face_data
            offset += self.PERSON_SENSOR_FACE_BYTE_COUNT
                
            area = (box_right - box_left) * (box_bottom - box_top)

            if area > largest_area:
                largest_area = area
                largest_face = {
                    "box_confidence": box_confidence,
                    "box_left": box_left,
                    "box_top": box_top,
                    "box_right": box_right,
                    "box_bottom": box_bottom
                }

            if largest_face:
                x, y = self.compute_center(largest_face)
                self.current_pos = (x, y)
            else:
                self.current_pos = None

        if largest_face:
            x, y = self.compute_center(largest_face)
            self.current_pos = (x, y)
        else:
            self.current_pos = None

    def get_current_face_center(self):
        """Return the x and y coordinates of the closest face, or None if no face."""
        self.read_sensor_data()
        return self.current_pos

    def compute_center(self, face):
        """Compute the center of the face from its bounding box."""
        x_center = (face['box_left'] + face['box_right']) / 2
        y_center = (face['box_top'] + face['box_bottom']) / 2
        return x_center, y_center

if __name__ == "__main__":
    sensor = PersonSensor()

    # Start the sensor's loop in a separate thread
    def sensor_loop():
        while True:
            sensor.read_sensor_data()
            time.sleep(.2)  # Read data every 0.2 seconds

    sensor_thread = threading.Thread(target=sensor_loop)
    sensor_thread.start()

    try:
        # This loop will run in the main thread and continuously print the x, y values of the closest face
        while True:
            center = sensor.get_current_face_center()
            if center:
                print("X:", center[0]/255, "Y:", center[1]/255)
            else:
                print("No face detected")
            time.sleep(.2)  # Print every second
    except KeyboardInterrupt:
        print("Stopping ...")
        sensor_thread.join()  # Wait for the sensor thread to finish
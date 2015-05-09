import os
import time

class PinInUseException(Exception):
    pass

class gpio():
    def __init__(self, pin, direction="in"):
        self.pin = int(pin)

        f = open("/sys/class/gpio/export", "w")
        f.write(str(self.pin))
        f.close()
        # wait a bit so the sysfs files can be created and become writeable
        time.sleep(0.2)

        try:
            self.set_direction(direction)
        except:
            self.unexport()
            raise

    def set_direction(self, direction):
        if direction != "in" and direction != "out":
            msg = 'direction must be "in" or "out"'
            raise ValueError(direction, msg)
        self.direction = direction

        sysfs_dir = "/sys/class/gpio/gpio{}".format(self.pin)
        dir_file = open(os.path.join(sysfs_dir, "direction"), "w")
        dir_file.write(direction)
        dir_file.close()

        value_path = os.path.join(sysfs_dir, "value")
        value_mode = "w" if direction == "out" else "r"
        self.__value_file__ = open(value_path, value_mode)

    def set(self, value):
        if self.direction == "out":
            self.__value_file__.seek(0)
            self.__value_file__.write("1" if value else "0")
            self.__value_file__.flush()
        else:
            print("Cannot set input pin ({})".format(self.pin))

    def unexport(self):
        f = open("/sys/class/gpio/unexport", "w")
        f.write(str(self.pin))
        f.close()

    def close(self):
        self.__value_file__.close()
        self.unexport()


if __name__ == "__main__":
    print("hello")
    pin = gpio(18)
    try:
        pin.set_direction("in")
        pin.set(True)
        time.sleep(0.5)
        pin.set(False)
    finally:
        pin.close()

import os
import time

class PinInUseException(Exception):
    pass

class gpio():
    def __init__(self, pin, direction="in"):
        self.pin = int(pin)

        try:
            f = open("/sys/class/gpio/export", "w")
            f.write(str(self.pin))
            f.close()
        except IOError as err:
            # if call writing the pin number to /sys/class/gpio/export fails
            # with error "Device or resource busy" (errno 16) then the pin
            # is already being used -- already exported or being used by device
            # tree
            # Fail, instead of trying to use it again
            (errno, msg) = err.args
            if errno == 16:
                raise PinInUseException(self.pin) from err
            raise

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
        value_mode = "r+" if direction == "out" else "r"
        self.__value_file__ = open(value_path, value_mode)

    def set(self, value):
        if self.direction == "out":
            self.__value_file__.seek(0)
            self.__value_file__.write("1" if value else "0")
            self.__value_file__.flush()
        else:
            print("Cannot set input pin ({})".format(self.pin))

    def get(self):
        self.__value_file__.seek(0)
        value = self.__value_file__.read()
        if value == "1\n":
            return True
        elif value == "0\n":
            return False
        else:
            msg = "impossible value from {}".format(self.__value_file__.name)
            raise ValueError(value, msg)

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
        pin.set_direction("out")
        pin.set(True)
        print(pin.get())
        time.sleep(0.5)
        pin.set(False)
        print(pin.get())
    finally:
        pin.close()

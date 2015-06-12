import os
import time

class PinInUseException(Exception):
    pass

class gpio():
    def __init__(self, pin, direction="in"):
        self._pin = int(pin)
        self._direction = direction

    def __enter__(self):
        try:
            with open("/sys/class/gpio/export", "w") as export:
                export.write(str(self._pin))
            try:
                time.sleep(0.2)
                self.set_direction(self._direction)
                return self
            except:
                self.__exit__()
                raise

        except IOError as err:
            print("matched outer")
            (errno, msg) = err.args
            if errno == 16:
                # if call writing the pin number to /sys/class/gpio/export
                # fails with error "Device or resource busy" (errno 16) then
                # the pin is already being used -- already exported or being
                # used by device tree. Fail, instead of trying to reuse it
                raise PinInUseException(self._pin) from err
            raise

    def __exit__(self, exc_type=None, exc_val=None, exc_tb=None):
        with open("/sys/class/gpio/unexport", "w") as unexport:
            unexport.write(str(self._pin))
        return False

    def set_direction(self, direction):
        if direction != "in" and direction != "out":
            msg = 'direction must be "in" or "out"'
            raise ValueError(direction, msg)
        self._direction = direction

        sysfs_dir = "/sys/class/gpio/gpio{}".format(self._pin)
        with open(os.path.join(sysfs_dir, "direction"), "w") as dir_file:
            dir_file.write(direction)

        value_path = os.path.join(sysfs_dir, "value")
        value_mode = os.O_RDWR if direction == "out" else os.O_RDONLY
        self.__value_fd = os.open(value_path, value_mode)

    def set(self, value):
        if self._direction == "out":
            os.lseek(self.__value_fd, 0, os.SEEK_SET)
            os.write(self.__value_fd, b"1" if value else b"0")
        else:
            print("Cannot set input pin ({})".format(self._pin))

    def get(self):
        os.lseek(self.__value_fd, 0, os.SEEK_SET)
        value = os.read(self.__value_fd, 1)
        if value == b"1":
            return True
        elif value == b"0":
            return False
        else:
            msg = "impossible value from pin {}".format(self._pin)
            raise ValueError(value, msg)

    def close(self):
        try:
            os.close(self.__value_fd)
        finally:
            self.__exit__()

if __name__ == "__main__":
    (red,green,blue) = (18,27,22)
    time.sleep(4)
    with gpio(red, "out") as r:
        r.set(True)
        time.sleep(4)
        with gpio(green, "out") as g:
            r.set(False)
            g.set(True)
            time.sleep(3)
            r.set(True)
            time.sleep(10)


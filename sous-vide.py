import os
import threading
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
            self._unexport()
            raise

    def set_direction(self, direction):
        if direction != "in" and direction != "out":
            msg = 'direction must be "in" or "out"'
            raise ValueError(direction, msg)
        self.direction = direction

        sysfs_dir = "/sys/class/gpio/gpio{}".format(self.pin)
        with open(os.path.join(sysfs_dir, "direction"), "w") as dir_file:
            dir_file.write(direction)

        value_path = os.path.join(sysfs_dir, "value")
        value_mode = os.O_RDWR if direction == "out" else os.O_RDONLY
        self.__value_fd = os.open(value_path, value_mode)

    def set(self, value):
        if self.direction == "out":
            os.lseek(self.__value_fd, 0, os.SEEK_SET)
            os.write(self.__value_fd, b"1" if value else b"0")
        else:
            print("Cannot set input pin ({})".format(self.pin))

    def get(self):
        os.lseek(self.__value_fd, 0, os.SEEK_SET)
        value = os.read(self.__value_fd, 1)
        if value == b"1":
            return True
        elif value == b"0":
            return False
        else:
            msg = "impossible value from pin {}".format(self.pin)
            raise ValueError(value, msg)

    def _unexport(self):
        f = open("/sys/class/gpio/unexport", "w")
        f.write(str(self.pin))
        f.close()

    def close(self):
        try:
            os.close(self.__value_fd)
        finally:
            self._unexport()

class Cooker():
    def __init__(self, relay_pin=17, red_pin=18, green_pin=27, blue_pin=22):
        # setup up outputs
        setup_err_msg = "Error setting up pin {} for {} output"
        try:
            relay = gpio(relay_pin, "out")
        except:
            print(setup_err_msg.format(relay_pin, "relay"))
            raise
        try:
            red = gpio(red_pin, "out")
        except:
            print(setup_err_msg.format(red_pin, "red"))
            relay.close()
            raise
        try:
            green = gpio(green_pin, "out")
        except:
            print(setup_err_msg.format(green_pin, "green"))
            relay.close()
            red.close()
            raise
        try:
            blue = gpio(blue_pin, "out")
        except:
            print(setup_err_msg.format(blue_pin, "blue"))
            relay.close()
            red.close()
            green.close()
            raise

        self.relay = relay
        self.red = red
        self.green = green
        self.blue = blue

        # set up heater controls
        self.cycle_time = 10    # in seconds
        self.heater_setting = 0

    def run_heater(self):
        self.heater_thread = threading.Thread(target=self._heater)
        self.heater_thread.start()

    def _heater(self):
        minimum_duration = 1    # don't switch relay for less than this time
        while (True):
            time_on = self.cycle_time * self.heater_setting
            time_off = self.cycle_time - time_on
            if time_on < minimum_duration:
                self.relay.set(False)
                time.sleep(self.cycle_time)
            elif time_off < minimum_duration:
                self.relay.set(True)
                time.sleep(self.cycle_time)
            else:
                self.relay.set(True)
                time.sleep(time_on)
                self.relay.set(False)
                time.sleep(time_off)

    def close(self):
        self.relay.close()
        self.red.close()
        self.green.close()
        self.blue.close()


if __name__ == "__main__":
    print("hello")
    cooker = Cooker()
    pin = cooker.blue
    try:
        cooker.heater_setting = 0.4
        cooker.run_heater()
        pin.set_direction("out")
        pin.set(True)
        start_time = time.time()
        pin.set(True)
        elapsed = time.time() - start_time
        print("elapsed: ", elapsed)
        print(pin.get())
        time.sleep(0.5)
        pin.set(False)
        print(pin.get())
        cooker.heater_setting = 0.9
        time.sleep(20)
    finally:
        cooker.close()

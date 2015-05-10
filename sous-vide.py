from gpio import gpio

from multiprocessing import Process, Queue, Value
import time

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
        self._heat_cycle = Value('d', 10)
        self._heater_setting = Value('d', 0.0)
        self._heater_process = None

    def set_heater(self, fraction):
        """ set heater power to fraction, a value between 0 and 1 """
        if fraction < 0 or fraction > 1:
            err_msg = "heater power setting must be between 0 and 1"
            raise ValueError(fraction, err_msg)
        self._heater_setting.value = fraction

    def set_heat_cycle(self, seconds):
        """ set duration of the heater cycle """
        if seconds <= 0:
            err_msg = "heat_cycle must be a positive value"
            raise ValueError(seconds, err_msg)
        self._heat_cycle.value = seconds

    def run_heater(self, heater_setting=None, cycle_time=None, minimum_duration=1):
        """ run heater loop using time proportional output to power heater
            args include heater_setting, cycle_time, and minimum_duration
            heater_setting is fraction between 0 and 1 that gives the fraction
            of time the heater is powered
            cycle_time and minimum_duration are in seconds
            minimum_duration is a minimum duration before the relay switches
        """
        if heater_setting is not None:
            self.set_heater(heater_setting)
        if cycle_time is not None:
            self.set_heat_cycle(cycle_time)
        self.heater_process = Process(target=self._heater,
                                      args=(minimum_duration,))
        self.heater_process.start()

    def stop_heater(self):
        self.relay.set(False)
        if self.heater_process:
            self.heater_process.terminate()

    def _heater(self, minimum_duration=1):
        while (True):
            heater_setting = self._heater_setting.value
            cycle_time = self._heat_cycle.value
            time_on =  cycle_time * heater_setting
            time_off = cycle_time - time_on

            if time_on < minimum_duration:
                self.relay.set(False)
                time.sleep(cycle_time)
            elif time_off < minimum_duration:
                self.relay.set(True)
                time.sleep(cycle_time)
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
        cooker.set_heater(0.3)
        cooker.run_heater(heater_setting=0.7)
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
        cooker.set_heater(0.8)
        cooker.set_heat_cycle(5)
        # time.sleep(12)
        # cooker.stop_heater()
        time.sleep(20)
    finally:
        cooker.close()

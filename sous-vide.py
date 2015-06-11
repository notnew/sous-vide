from gpio import gpio
import ds18b20.tracker

from multiprocessing import Process, Queue, Value
import time
import sys

def flush():
    sys.stdout.flush()

class Cooker():
    def __init__(self, relay_pin=17, red_pin=18, green_pin=27, blue_pin=22,
                 target=78 ):
        # setup up outputs
        self.__trying_pin = (0,"")
        exported_pins = []
        try:
            def setup_pin(num, name):
                self.__trying_pin = (num, name)
                pin =  gpio(num, "out")
                self.__dict__[name] = pin
                exported_pins.append(pin)

            setup_pin(relay_pin, "relay")
            setup_pin(red_pin,   "red")
            setup_pin(green_pin, "green")
            setup_pin(blue_pin,  "blue")
            self.__trying_pin = None

            # set up heater controls
            self.target = target
            self.kp = 0.2       # max if error is 2 degrees low or more
            self.ki = 0.02
            self.offset = 0

            self._heat_cycle = Value('d', 20)
            self._heater_setting = Value('d', 0.0)
            self._heater_process = None

            self.sample_q = Queue()
            self.minutes = ds18b20.tracker.History(10, 60)
            histories = {"minutes": self.minutes}
            self.tracker = ds18b20.tracker.Tracker(histories=histories,
                                                   sample_q=self.sample_q)
            self.tracker.start_sampler()

        except:
            for pin in exported_pins: # close opened pins
                  pin.close()
            if self.__trying_pin:
                err_msg = "Error setting up pin {} for {} output"
                print(err_msg.format(*self.__trying_pin))
            raise

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

    def pid(self):
        current_temp = self.tracker.latest.value
        error = self.target - current_temp
        p = self.kp * error
        if abs(error) < 5:
            self.offset += self.ki * error
        else:
            self.offset = 0
        heater = self.kp + self.offset
        heater = min( max(heater, 0.0), 1.0)
        print("setting heater to {} ({} + {})".format(heater, self.offset, p))
        flush()
        self.set_heater(heater)

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

    def _watch_temperature(self):
        while True:
            new_temp = self.tracker.sample_q.get()
            print("got new temperature reading:", new_temp)
            flush()
            self.pid()

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
        cooker.run_heater()
        cooker._watch_temperature()
    finally:
        cooker.close()

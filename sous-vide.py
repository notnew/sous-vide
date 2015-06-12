from gpio import gpio
from blinker import SyncBlinker
import ds18b20.tracker

from multiprocessing import Process, Queue, Value
import time
import sys

def flush():
    sys.stdout.flush()

class Heater(SyncBlinker):
    def __init__(self, pin=17, cycle_time=20, minimum_duration=1):
        self.set_cycle_time(cycle_time)
        self.setting = 0
        self.minimum_duration = minimum_duration

        SyncBlinker.__init__(self, pin)

    def set(self, fraction):
        """ set heater power to fraction, a value between 0 and 1 """
        if fraction < 0 or fraction > 1:
            err_msg = "heater power setting must be between 0 and 1"
            raise ValueError(fraction, err_msg)
        self.setting = fraction
        time_on =  self.cycle_time * self.setting
        time_off = self.cycle_time - time_on
        if time_off < self.minimum_duration:
            self.set_on()
        elif time_on < self.minimum_duration:
            self.setoff()
        else:
            self.set_cycle(time_on, time_off)

    def set_cycle_time(self, seconds):
        """ set duration of the heater cycle """
        if seconds <= 0:
            err_msg = "heat_cycle must be a positive value"
            raise ValueError(seconds, err_msg)
        self.cycle_time = seconds

class Cooker():
    def __init__(self, relay_pin=17, red_pin=18, green_pin=27, blue_pin=22,
                 target=78, heater=None ):
        self.relay_pin = relay_pin
        self.red_pin = red_pin
        self.green_pin = green_pin
        self.blue_pin = blue_pin

        # set up heater controls
        self.target = target
        self.kp = 0.2       # max if error is 2 degrees low or more
        self.ki = 0.004
        self.offset = 0

        self.heater = heater or Heater(relay_pin)

        self.sample_q = Queue()
        self.minutes = ds18b20.tracker.History(10, 60)
        histories = {"minutes": self.minutes}
        self.tracker = ds18b20.tracker.Tracker(histories=histories,
                                               sample_q=self.sample_q)
        self.tracker.start_sampler()

    def pid(self):
        current_temp = self.tracker.latest.value
        error = self.target - current_temp
        if abs(error) < 2:
            self.offset = max(self.offset + self.ki * error, 0)
        else:
            self.offset = 0
        p = self.kp * error
        heater = p + self.offset
        heater = min( max(heater, 0.0), 1.0)
        print("setting heater to {} ({} + {})".format(heater, self.offset, p))
        flush()
        self.heater.set(heater)

    def _watch_temperature(self):
        while True:
            new_temp = self.tracker.sample_q.get()
            print("got new temperature reading:", new_temp)
            flush()
            self.pid()

    def close(self):
        self.heater.stop()

if __name__ == "__main__":
    print("hello")
    cooker = Cooker(target=77.2)

    try:
        cooker.heater.run()
        cooker._watch_temperature()
    finally:
        cooker.close()

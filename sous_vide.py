from gpio import gpio
from blinker import Blinker
import ds18b20.tracker

import queue
import sys
import threading
import time

def flush():
    sys.stdout.flush()

class Heater(Blinker):
    def __init__(self, pin=17, cycle_time=20, minimum_duration=1):
        self.set_cycle_time(cycle_time)
        self.setting = 0
        self.minimum_duration = minimum_duration

        super().__init__(pin)

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
            self.set_off()
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

        # Cooker state variables
        self.temperature = None
        self.sample_time = 0
        self.target = target
        self.heater_setting = 0
        self.kp = 0.2           # max if error is 2 degrees low or more
        self.proportional = 0
        self.ki = 0.004
        self.offset = 0         # integral term

        # Heater, temperature tracker, threads, etc
        self.heater = heater or Heater(relay_pin)
        self._state_lock = threading.Lock()
        self._sampler_thread = None

        self.sample_q = queue.Queue()
        self.minutes = ds18b20.tracker.History(10, 60)
        histories = {"minutes": self.minutes}
        self.tracker = ds18b20.tracker.Tracker(histories=histories,
                                               sample_q=self.sample_q)

    def pid(self, new_sample):
        (sample_time, new_temp) = new_sample
        error = self.target - new_temp
        dt = sample_time - self.sample_time
        self.temperature = new_temp
        self.sample_time = sample_time

        if abs(error) < 2:
            self.offset = max(self.offset + self.ki * error, 0)
        else:
            self.offset = 0
        self.proportional = self.kp * error
        heater = self.proportional + self.offset
        heater = min( max(heater, 0.0), 1.0)
        self.heater_setting = heater
        self.heater.set(heater)

        print("got new sample ({:0.2f} seconds elapsed)".format(dt))
        print(" ", self.get_state())
        flush()

    def _sampler_is_running(self):
        return self._sampler_thread and self._sampler_thread.is_alive()

    def start_sampling(self):
        """ start a thread to get temperatures samples from Cooker.tracker
            run self.pid() to update state when new temperatures arrive """

        def _sample_temperature():
            self.tracker.start_sampler()
            try:
                for new_sample in iter(self.sample_q.get, None):
                    self.pid(new_sample)
            finally:
                self.tracker.stop_sampler()

        if not self._sampler_is_running():
            self._sampler_thread = threading.Thread(target=_sample_temperature)
            self._sampler_thread.start()

    def stop_sampling(self):
        if self._sampler_is_running():
            self.sample_q.put(None)

    def close(self):
        self.heater.stop()
        self.stop_sampling()

    def get_state(self):
        """ return the current state of the Cooker as a dict """
        return {'sample_time': self.sample_time,
                'temperature': self.temperature,
                'target': self.target,
                'setting': self.heater_setting,
                'proportional': self.proportional,
                'offset': self.offset,
                'kp': self.kp,
                'ki': self.ki}

    def set_state(self, data):
        """ set the state of the Cooker to the values passed in a dict (of the
            type returned by get_state) """
        self.target = float(data['target'])
        self.proportional = float(data['proportional'])
        self.offset = float(data['offset'])
        self.kp = float(data['kp'])
        self.ki = float(data['ki'])

if __name__ == "__main__":
    print("hello")
    cooker = Cooker(target=77.2)

    try:
        cooker.heater.run()
        cooker.start_sampling()
        cooker._sampler_thread.join()
    finally:
        cooker.close()

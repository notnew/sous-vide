from gpio import gpio
from multiprocessing import Process, Queue
import queue

class Blinker():
    """ Blink an input pin on and off """
    def __init__(self, pin_num):
        self.pin_num = pin_num
        self._messages = Queue()
        self.running = False
        self.run_process = None
        self._hi_time = -1
        self._low_time = 0

    def set_cycle(self, hi_time, low_time=None):
        """ set period for the blinker
            if only `hi_time` is passed, that value is used for `off_time` as well
            if `hi_time` is positive, it's value is the length of time the pin
            should be set high, in seconds
            if `hi_time` is zero, the pin should be turned on indefinitely
            if `hi_time` is negative, the pins should be turned off indefinitely"""
        if hi_time > 0:
            if low_time is None:
                low_time = hi_time
            if low_time <= 0:
                raise ValueError(low_time, "low_time duration must be positive")
        self._messages.put( (hi_time, low_time) )

    def run(self):
        def _safer_run():
            self.pin = gpio(self.pin_num, "out")
            try:
                _run()
            finally:
                self.pin.close()

        def _run():
            (hi,low) = (self._hi_time, self._low_time)
            def msg_or_timeout(duration):
                try:
                    (new_hi, new_low) = self._messages.get(timeout=duration)
                    return (new_hi, new_low)
                except queue.Empty:
                    return (hi, low)
            while True:
                if hi < 0:     # off until new message arrives
                    self.pin.set(False)
                    (hi,low) = self._messages.get()
                elif hi == 0:   # on until new message arrives
                    self.pin.set(True)
                    (hi,low) = self._messages.get()
                else:
                    self.pin.set(True)
                    (hi,low) = msg_or_timeout(hi)
                    if hi <= 0:
                        continue
                    self.pin.set(False)
                    (hi,low) = msg_or_timeout(low)

        self.run_process = Process(target=_safer_run)
        self.run_process.start()
        self.running = True

    def stop(self):
        if self.running:
            self.run_process.terminate()
            self.running = False

if __name__ == "__main__":
    (red,green,blue) = (18,27,22)
    blinker = Blinker(red)
    blinker.run()
    blinker.set_cycle(0.9,0.1)

from gpio import gpio
from threading import Thread
import queue
import time

class Blinker():
    """ Blink an input pin on and off """
    def __init__(self, pin_num):
        self.pin_num = pin_num
        self._messages = queue.Queue()
        self._thread = None
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
        (self._hi_time, self._low_time) = (hi_time, low_time)
        self._messages.put( (hi_time, low_time) )

    def set_on(self):
        self.set_cycle(0)

    def set_off(self):
        self.set_cycle(-1)

    def run(self):
        def _run():
            (hi,low) = (self._hi_time, self._low_time)
            def msg_or_timeout(duration=None):
                try:
                    start = time.time()
                    msg = self._messages.get(timeout=duration)
                    if msg is None:
                        raise StopIteration
                    elapsed = time.time() - start
                    return (msg, elapsed)
                except queue.Empty:
                    return ((hi, low), duration)

            with gpio(self.pin_num, "out") as pin:
                try:
                    while True:
                        if hi < 0:     # off until new message arrives
                            pin.set(False)
                            ((hi,low),_) = msg_or_timeout()
                        elif hi == 0:   # on until new message arrives
                            pin.set(True)
                            ((hi,low),_) = msg_or_timeout()
                        else:
                            pin.set(True)

                            ((hi,low),elapsed) = msg_or_timeout(hi)
                            while ( hi > 0 and hi > elapsed):
                                ((hi,low),elapsed2) = msg_or_timeout(hi-elapsed)
                                elapsed += elapsed2
                            if hi <= 0:
                                continue

                            pin.set(False)
                            ((hi,low), elapsed) = msg_or_timeout(low)
                            while ( hi > 0 and low > 0 and low > elapsed):
                                ((hi,low),elapsed2) = msg_or_timeout(low-elapsed)
                                elapsed += elapsed2

                except StopIteration:
                    pass

        if not self.is_running():
            self._thread = Thread(target=_run)
            self._thread.start()

    def stop(self):
        if self.is_running():
            self._messages.put(None)
            self._thread.join()

    def is_running(self):
        return self._thread and self._thread.is_alive()

    def __enter__(self):
        self.run()
        return self

    def __exit__(self, exc_type=None, exc_val=None, exc_tb=None):
        self.stop()
        return False

if __name__ == "__main__":
    (red,green,blue) = (18,27,22)
    blinker = Blinker(red)
    blinker.run()
    blinker.set_cycle(0.9,0.1)
    try:
        blinker._thread.join()
    except:
        print("stopping blinker")
        blinker.stop()

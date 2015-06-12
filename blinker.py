from gpio import gpio
from threading import Thread
import queue

class Blinker():
    """ Blink an input pin on and off """
    def __init__(self, pin_num):
        self.pin_num = pin_num
        self._messages = queue.Queue()
        self.thread = None
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

    def run(self):
        def _run():
            (hi,low) = (self._hi_time, self._low_time)
            def msg_or_timeout(duration=None):
                try:
                    msg = self._messages.get(timeout=duration)
                    if msg is None:
                        raise StopIteration
                    return msg
                except queue.Empty:
                    return (hi, low)

            with gpio(self.pin_num, "out") as pin:
                try:
                    while True:
                        if hi < 0:     # off until new message arrives
                            pin.set(False)
                            (hi,low) = msg_or_timeout()
                        elif hi == 0:   # on until new message arrives
                            pin.set(True)
                            (hi,low) = msg_or_timeout()
                        else:
                            pin.set(True)
                            (hi,low) = msg_or_timeout(hi)
                            if hi <= 0:
                                continue

                            pin.set(False)
                            (hi,low) = msg_or_timeout(low)

                except StopIteration:
                    pass

        self.thread = Thread(target=_run)
        self.thread.start()

    def stop(self):
        if self.thread and self.thread.is_alive():
            self._messages.put(None)

if __name__ == "__main__":
    (red,green,blue) = (18,27,22)
    blinker = Blinker(red)
    blinker.run()
    blinker.set_cycle(0.9,0.1)
    try:
        blinker.thread.join()
    except:
        print("stopping blinker")
        blinker.stop()

from gpio import gpio
from threading import Thread
import queue

class Blinker():
    """ Blink an input pin on and off """
    def __init__(self, pin_num):
        self.pin_num = pin_num
        self._messages = queue.Queue()
        self.running = False
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
            self.running = True
            pin = gpio(self.pin_num, "out")
            try:
                (hi,low) = (self._hi_time, self._low_time)
                def msg_or_timeout(duration):
                    try:
                        msg = self._messages.get(timeout=duration)
                        return msg
                    except queue.Empty:
                        return (hi, low)
                    except KeyboardInterrupt:
                        print("kb interrupt: reraising")
                        raise
                while True:
                    if hi < 0:     # off until new message arrives
                        pin.set(False)
                        msg = self._messages.get()
                        if msg is None:
                            break
                        (hi,low) = msg
                    elif hi == 0:   # on until new message arrives
                        pin.set(True)
                        msg = self._messages.get()
                        if msg is None:
                            break
                        msg = self._messages.get()
                    else:
                        pin.set(True)
                        msg  = msg_or_timeout(hi)
                        if msg is None:
                            break
                        (hi,low) = msg
                        if hi <= 0:
                            continue

                        pin.set(False)
                        msg = msg_or_timeout(low)
                        if msg is None:
                            break
                        (hi,low) = msg

            finally:
                self.running = False
                pin.close()


        self.thread = Thread(target=_run)
        self.thread.start()

    def stop(self):
        if self.running:
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

import time
import threading
import os
import subprocess
import logging
import FakeLCD as LCD

logger = logging.getLogger(__name__)
pinState = {}
SOUND_LOCK = threading.Lock()


def init():
    pass


def initPin(pinNumber, input=False):
    pinState[pinNumber] = False

# LEDS


def onLED(pinNumber):
    prev = pinState[pinNumber]
    pinState[pinNumber] = True
    logger.debug("LED #{pin} from {p} to {c}".format(
        pin=pinNumber,
        p=prev,
        c=pinState[pinNumber]))


def offLED(pinNumber):
    prev = pinState[pinNumber]
    pinState[pinNumber] = False
    logger.debug("LED #{pin} from {p} to {c}".format(
        pin=pinNumber,
        p=prev,
        c=pinState[pinNumber]))


def ledTimeout(pinNumber, timeout):
    def onOff():
        onLED(pinNumber)
        time.sleep(timeout)
        offLED(pinNumber)

    t = threading.Thread(target=onOff)
    t.start()

    return t

# LCD


def initLCD():
    lcd = LCD.LCD("/dev/ttyAMA0", baud="115200", size=(128, 64))
    lcd.init_display()
    lcd.set_backlight(100)
    lcd.start()

    return lcd

# SOUND
MUTE = False


def beep(file="beep-07.wav"):
    if not MUTE:
        with open(os.devnull, "wb") as devnull:
            subprocess.check_call(
                ["aplay", file], stdout=devnull, stderr=subprocess.STDOUT)


def beepsTimeout(n, interval=0.5):
    def beeps():
        # Beep only if not currently beeping
        if not SOUND_LOCK.acquire(False):
            return
        for _ in range(n):
            beep()
            time.sleep(interval)
        SOUND_LOCK.release()

    t = threading.Thread(target=beeps)
    t.start()

    return t

# BUTTONS


class ButtonListener (threading.Thread):

    def __init__(self, buttonBindings):
        super(ButtonListener, self).__init__()
        self.buttonBindings = buttonBindings
        self.prevInputOf = {b: 0 for b in self.buttonBindings}
        self.stopFlag = False

    def run(self):
        while not self.stopFlag:
            try:
                bInput = int(chr(LCD.stdscr.getch()))
                if bInput in self.buttonBindings:
                    self.buttonBindings[bInput]()
            except ValueError:
                return
            # for button in self.buttonBindings:
               # bInput = GPIO.input (button)

                # if not self.prevInputOf[button] and bInput:
                #    self.buttonBindings[button] ()

                #self.prevInputOf[button] = bInput

    def stop(self):
        self.stopFlag = True

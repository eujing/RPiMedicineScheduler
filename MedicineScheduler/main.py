import config as CONF

if CONF.EMULATE:
    import FakeHardware as hw
else:
    import Hardware as hw
    import cv2
    import zbar
    import Image
import ScriptParser as parser
from UserInterface import UI, Page
from apscheduler.schedulers.background import BackgroundScheduler
import json
import os
import logging
import time

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

sched = BackgroundScheduler()

SCHED_DIR = "schedules"

if CONF.EMULATE:
    UP_BUTTON = 8
    DOWN_BUTTON = 2
    BACK_BUTTON = 0
    SELECT_BUTTON = 5
else:
    UP_BUTTON = 27
    DOWN_BUTTON = 25
    BACK_BUTTON = 4
    SELECT_BUTTON = 24

# Slot to pin mapping
LEDS = {0: 17, 1: 18, 2: 23, 3: 22}


def getFiles(d):
    return [file for file in os.listdir(d)
            if os.path.isfile(os.path.join(d, file))]


def detectQR(symbolDetected, stopDetecting=lambda: False, display=False):
    # Initialize camera and scanners
    if display:
        cv2.namedWindow("webcam", flags=cv2.CV_WINDOW_AUTOSIZE)
    camera = cv2.VideoCapture(0)
    scanner = zbar.ImageScanner()
    scanner.parse_config("enable")

    # Accumulate data
    data = []
    while not stopDetecting():
        _, img = camera.read()  # Read image
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        pilImg = Image.fromarray(img)  # Convert to PIL image
        # Wrap in zbar
        zImg = zbar.Image(
            pilImg.size[0], pilImg.size[1], "Y800", pilImg.tostring())
        scanner.scan(zImg)
        if display:
            cv2.imshow("webcam", img)
        for symbol in zImg:
            if symbol.data not in data:
                symbolDetected()
                data.append(symbol.data)

    return data


def populateSchedule(sched, data, ui):
    def notify(med):
        def onLoad():
            hw.onLED(LEDS[int(med["slot"])])
            hw.beepsTimeout(CONF.BEEPS_TIMEOUT)

        def onNext(ui):
            # hw.ledTimeout(LEDS[int(med["slot"])], CONF.LED_TIMEOUT)
            hw.offLED(LEDS[int(med["slot"])])

        instructions = [
            Page("Take {dosage} of {name}".format(dosage=med["dosage"], name=med["name"]))]
        if "special" in med:
            instructions.append(Page(med["special"]))
        ui.pushPage(onLoad, Page("Notification", options=instructions, callback=onNext, prefix=False))
        logger.debug("notifiying")

    logger.debug("populating")
    parser.generateSchedule(sched, data, notify)
    return sched


def record(ui):
    if CONF.EMULATE:
        logger.warning("Recording in emulation mode not supported")
        return

    # Stop default listener
    ui.bListener.stop()

    # Remove old schedules
    for job in sched.get_jobs():
        sched.unschedule_job(job)

    # Delete old files
    for fileName in getFiles(SCHED_DIR):
        os.remove(os.path.join(SCHED_DIR, fileName))

    ui.printText("Scanning...\nPress Back when done")

    done = False

    def symbolDetected():
        symbolDetected.count += 1
        hw.beep()
        message = "Recording...\n"
        message += "{0} schedule(s) recorded!\n".format(symbolDetected.count)
        message += "Press Back when done\n"
        ui.printText(message)
    symbolDetected.count = 0

    def stop():
        nonlocal done
        done = True

    def stopDetecting():
        nonlocal done
        return done

    # New bindings
    bBindings = {BACK_BUTTON: stop}
    bListener = hw.ButtonListener(bBindings)
    bListener.start()

    data = detectQR(symbolDetected, stopDetecting=stopDetecting)

    if len(data) > 0:
        # Write schedules
        jsonData = []
        for jsonString in data:
            jsonSchedule = json.loads(jsonString)
            jsonData.append(jsonSchedule)
            path = os.path.join(
                SCHED_DIR, "{0}.json".format(jsonSchedule["name"]))
            with open(path, "w") as file:
                file.write(jsonString)

        # Start schedule
        populateSchedule(sched, jsonData, ui)
    else:
        ui.pushPage(lambda x: None, Page("Schedule empty!", [
            Page("Ok")]))

    # Stop new button listener, start default listener
    bListener.stop()
    ui.restartButtonListener()


def viewScheduleInfo():
    schedules = []
    for fileName in getFiles(SCHED_DIR):
        with open(os.path.join(SCHED_DIR, fileName)) as file:
            data = json.load(file)
        info = [
            Page("Slot: " + str(data["slot"])),
            Page("Times (H): " + data["hour"]),
            Page("Dosage: " + data["dosage"])
        ]
        if "special" in data:
            info.append(Page(data["special"]))
        schedules.append(
            Page(fileName.replace(".json", ""), options=info, prefix=False))
    return schedules


def deleteSchedule():
    # Create a function to delete specified schedule when called
    def deleteGenerator(fileName):
        def delete(ui):
            os.remove(os.path.join(SCHED_DIR, fileName))
            updateSched(sched, ui)
        return delete

    return [Page(fileName.replace(".json", ""), [Page("Delete", callback=deleteGenerator(fileName))]) for fileName in getFiles(SCHED_DIR)]


def updateSched(sched, ui):
    # Remove old schedules
    for job in sched.get_jobs():
        sched.unschedule_job(job)

    data = []
    for fileName in getFiles(SCHED_DIR):
        with open(os.path.join(SCHED_DIR, fileName), "r") as file:
            data.append(json.load(file))

    populateSchedule(sched, data, ui)

if __name__ == "__main__":
    def mute(ui):
        hw.MUTE = True

    def unmute(ui):
        hw.MUTE = False

    # Initialize all hardware
    try:
        hw.init()
        hw.initPin(UP_BUTTON, input=True)
        hw.initPin(DOWN_BUTTON, input=True)
        hw.initPin(BACK_BUTTON, input=True)
        hw.initPin(SELECT_BUTTON, input=True)
        for ledPin in LEDS:
            hw.initPin(LEDS[ledPin])
        lcd = hw.initLCD()

        # Set up ui
        pages = Page("Home", [
            Page("Record", callback=record),
            Page("Review schedules", options=[
                Page("View schedules", options=viewScheduleInfo),
                Page("Delete schedules", options=deleteSchedule)]),
            Page("Sound options", options=[
                Page("Mute", callback=mute),
                Page("Unmute", callback=unmute)])
        ])
        ui = UI(lcd, pages)

        buttonBindings = {
            UP_BUTTON: ui.up,
            DOWN_BUTTON: ui.down,
            BACK_BUTTON: ui.back,
            SELECT_BUTTON: ui.select
        }

        # New thread spawned
        ui.initButtons(buttonBindings)
        ui.draw()

        # Load stored schedules
        # data = []
        # for fileName in getFiles(SCHED_DIR):
        #     with open(os.path.join(SCHED_DIR, fileName), "r") as file:
        #         data.append(json.load(file))

        # sched = populateSchedule(sched, data, ui)
        updateSched(sched, ui)
        sched.start()

        logger.debug("started")
        # Keep main thread alive
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        ui.stop()
        sched.shutdown(wait=False)

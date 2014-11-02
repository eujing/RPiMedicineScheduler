import config as CONF

if CONF.EMULATE:
    import FakeHardware as hw
else:
    import Hardware as hw
import threading


class Page ():
    # options: list of children Page objects, or a function to dynamically load children
    # prefix: to prefix a * during rendering of the option
    # callback: executed on load of a page

    def __init__(self, label, options=list(), prefix=True, callback=None):
        self.label = label
        self.children = options
        self.prefix = prefix
        self.callback = callback
        # Inject parent on its own
        try:
            for child in self.children:
                child.parent = self
        except TypeError:
            # Probably dynamically loaded
            pass


def sync(lock):  # Lock decorator
    def function(f):
        def wrapper(*args, **kwargs):
            lock.acquire()
            try:
                return f(*args, **kwargs)
            finally:
                lock.release()
        return wrapper
    return function

MAX_LINES = 6
UILock = threading.Lock()
pageQueueLock = threading.Lock()


class UI ():

    def __init__(self, lcd, mainPage):
        self.pageQueue = []  # Queue of pushed pages. For alert purposes
        self.showingPushedPage = False
        self.lcd = lcd
        self.currPage = mainPage
        self.currOption = 0
        self.optionsRange = (0, min(MAX_LINES, len(self.currPage.children)))

    def loadChildren(self, page):
        # Dynamic loading
        if hasattr(page.children, "__call__"):
            children = page.children()
            # Inject parent
            for child in children:
                child.parent = page
        # Normal loading
        else:
            children = page.children

        return children

    def initButtons(self, buttonBindings):
        # Initialize bindings
        self.bBindings = buttonBindings
        self.bListener = hw.ButtonListener(self.bBindings)
        self.bListener.start()

    def restartButtonListener(self):
        # Reset bindings to original
        if hasattr(self, "bBindings"):
            self.bListener = hw.ButtonListener(self.bBindings)
            self.bListener.start()

    def draw(self):
        # Render current state
        self.lcd.clear()

        # Pushed page waiting
        if len(self.pageQueue) > 0:
            onLoad, page = self.pageQueue[0]
            if not onLoad is None:
                onLoad ()
            # New temporary range
            optionsRange = (0, min(MAX_LINES, len(page.children)))
            self.showingPushedPage = True

        # Normal page
        else:
            page = self.currPage
            optionsRange = self.optionsRange
            self.showingPushedPage = False

        self.lcd.type(page.label)

        children = self.loadChildren(page)

        offset = 0
        for i in range(optionsRange[1]):
            prefix = "*" if optionsRange[0] + i == self.currOption else " "
            self.lcd.set_char_position(i + offset + 1, 0)
            if page.prefix:
                line = " {p} {label}".format(
                    p=prefix, label=children[optionsRange[0] + i].label)
            else:
                line = "{label}".format(
                    label=children[optionsRange[0] + i].label)

            # Word wrap
            if len(line) > 21:
                nextLine = ""
                while len(line) > 21:
                    parts = line.split()
                    nextLine = parts[-1] + nextLine
                    line = " ".join(parts[0:-1])
                self.lcd.type(line)
                offset += 1
                self.lcd.set_char_position(i + offset + 1, 0)
                self.lcd.type(nextLine)
            else:
                self.lcd.type(line)

    def printText(self, text):
        # For printing text alone
        lines = text.split("\n")
        self.lcd.clear()
        for i in range(len(lines)):
            self.lcd.type(lines[i])
            self.lcd.set_char_position(i + 1, 0)

    def stop(self):
        # Shutdown
        if hasattr(self, "bListener"):
            self.bListener.stop()
        self.lcd.stop()

    @sync(UILock)
    def select(self):
        hw.beep()

        # If displaying a pushed page, remove it
        if self.showingPushedPage:
            onLoad, page = self.pageQueue[0]
            if not page.callback is None:
                page.callback(self)
            del self.pageQueue[0]

        # Normal page
        else:
            option = self.loadChildren(self.currPage)[self.currOption]

            # Execute page callback on load
            if not option.callback is None:
                option.callback(self)

            children = self.loadChildren(option)

            # Display page children
            if len(children) > 0:
                self.currPage = option
                self.currOption = 0
                self.optionsRange = (
                    0, min(MAX_LINES, len(children)))

        self.draw()

    @sync(UILock)
    def up(self):
        hw.beep()
        if self.currOption > 0:
            self.currOption -= 1

            if self.currOption < self.optionsRange[0]:
                self.optionsRange = (self.optionsRange[0] - 1,
                                     self.optionsRange[1] - 1)
        self.draw()

    @sync(UILock)
    def down(self):
        hw.beep()
        if self.currOption < len(self.loadChildren(self.currPage)) - 1:
            self.currOption += 1

            if self.currOption > self.optionsRange[1]:
                self.optionsRange = (self.optionsRange[0] + 1,
                                     self.optionsRange[1] + 1)
        self.draw()

    @sync(UILock)
    def back(self):
        hw.beep()
        if hasattr(self.currPage, "parent"):
            self.currPage = self.currPage.parent
            self.currOption = 0
            self.optionsRange = (
                0, min(MAX_LINES, len(self.loadChildren(self.currPage))))
        self.draw()

    @sync(pageQueueLock)
    def pushPage(self, onLoad, page):
        # onLoad is called on loading, page callback is called on pressing select
        self.pageQueue.append((onLoad, page))
        self.draw()

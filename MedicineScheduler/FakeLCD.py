import curses

global stdscr


class LCD ():

    def __init__(self, port, baud="115200", size=(128, 64)):
        global stdscr
        stdscr = curses.initscr()
        curses.noecho()
        self.x = 0
        self.y = 0
        self.size = (size[0] / 6, size[1] / 8)

    def init_display(self):
        pass

    def start(self):
        self.win = curses.newwin(8, 21)

    def stop(self):
        curses.echo()
        curses.endwin()

    def set_backlight(self, val):
        self.backlight = val

    def set_char_position(self, y, x):
        self.x = x
        self.y = y

    def type(self, text):
        if self.y < 8:
            self.win.addstr(self.y, self.x, text)

            if self.x + len(text) > 21:
                self.y += 1
                self.x = 0
            else:
                self.x += len(text)

            self.win.refresh()

    def clear(self):
        self.win.clear()
        self.x = 0
        self.y = 0

import pyglet


class App(pyglet.window.Window):
    #def __init__(self):
    #    pass
    def run(self):
        #self.window = pyglet.window.Window()
        pyglet.app.run()

    def on_key_press(self, symbol, modifiers):
        pass

    def on_key_release(self, symbol, modifiers):
        pass


import curses

class ConsoleApp:
    def init(self):
        self.stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()

    def draw(self):
        self.stdscr.clear()
        self.stdscr.addstr(3,1, 'qwe' + str(self.lastkey))
        pass

    def run(self):
        self.init()
        try:
            self.stdscr.clear()
            self.lastkey = None
            while 1:
                self.draw()
                self.stdscr.refresh()
                self.lastkey = self.stdscr.getkey()
        finally:
            self.remove()

    def remove(self):
        curses.nocbreak()
        self.stdscr.keypad(False)
        curses.echo()
        curses.endwin()

def main():
    app=ConsoleApp()
    app.run()

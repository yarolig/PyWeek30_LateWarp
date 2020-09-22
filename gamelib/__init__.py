import pyglet


def make_2d(f, w, h):
    return [[f(x, y) for x in range(w)] for y in range(h)]


def enum_2d(arr, eol=None):
    for y in range(len(arr)):
        for x in range(len(arr[y])):
            yield x, y, arr[y][x]
        if eol:
            eol()
'''
data/pics/floor.png
data/pics/template.png
data/pics/box.png
data/pics/stranger.png
data/pics/goat.png
data/pics/door.png
data/pics/qm.png
data/pics/wall.png
data/pics/light.png
data/pics/player.png
data/pics/waypoint.png
data/pics/ashes.png
data/pics/security.png
data/pics/warpgate.png
'''

class Sprite:
    all = {}
    def __init__(self, name):
        self.name=name
        self.sprite = pyglet.image.load('data/pics/%s.png'%name)

        all[name] = self

    @classmethod
    def get(cls, name):
        if name in all:
            return all[name]
        Sprite(name)
        return all[name]

class Level:
    def __init__(self):
        self.m = make_2d(lambda x,y: "%d_%d"%(x,y), 10, 10)
        for x, y, c in enum_2d(self.m, lambda: print('\n')):
            print(x, y, c)


class Session:
    def __init__(self):
        self.level=Level()

session = Session()

class PygletApp(pyglet.window.Window):
    def __init__(self, *args, **kwargs):
        pyglet.window.Window.__init__(self, *args, **kwargs)
        self.images = {}

    def update(self, dt):
        #print('update', dt)
        pass
    def run(self):
        self.fps_display = pyglet.window.FPSDisplay(self)
        #self.window = pyglet.window.Window()
        pyglet.clock.schedule_interval(self.update, 1/120.0)
        pyglet.app.run()

    def on_key_press(self, symbol, modifiers):
        print('press', pyglet.window.key.symbol_string(symbol), modifiers)

    def on_key_release(self, symbol, modifiers):
        print('release', pyglet.window.key.symbol_string(symbol), modifiers)

        #if symbol == pyglet.window.key.Q and modifiers == pyglet.window.key.MOD_CTRL:
        #    self.close()
        if symbol == pyglet.window.key.ESCAPE:
           self.close()

    def on_mouse_press(self, x, y, button, modifiers):
        print('on_mouse_press', x, y, button, modifiers)


    def on_mouse_release(self, x, y, button, modifiers):
        print('on_mouse_release', x, y, button, modifiers)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        print('on_mouse_drag',x, y, dx, dy, buttons, modifiers)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        print('on_mouse_scroll',x, y, scroll_x, scroll_y)
        pass

    def on_draw(self):
        #print('draw')
        self.clear()
        self.fps_display.draw()
        self.flip()

    def draw_sprite(self, name, x, y):
        if name not in self.images:
            self.images[name]=pyglet.image.load('data/pics/%s.png'%name)
        pyglet.sprite.Sprite()


class App:
    def __init__(self):
        self.sess = Session()
        self.papp = PygletApp()
        self.papp.sess = self.sess
    def run(self):
        self.papp.run()


class Game:
    hp = 100
    laser_charges = 0
    has_flashlight = False
    has_boots = False
    fuel = 0
    map_discovered = 1
    repair_kits = 0
    location = 'wreckage'
    situation = 'normal'

    lastmsg = ''
    question = ''



import curses


class ConsoleApp:
    def init(self):
        self.stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()

    def turn(self):
        Game.lastmsg = ''
        Game.question = 'e - explore, t - tinker, w - wait'

    def draw(self):
        self.stdscr.clear()
        self.stdscr.addstr(3,1, 'last key: ' + str(self.lastkey))
        self.stdscr.addstr(4, 1, 'hp:' + str(Game.hp)
                           + ' location:' + str(Game.location)
                           + ' situation:' + str(Game.situation)
                           )
        self.stdscr.addstr(5, 1, Game.lastmsg)
        self.stdscr.addstr(5, 1, Game.question)

    def run(self):
        self.init()
        try:
            self.stdscr.clear()
            self.lastkey = None
            while 1:
                self.turn()
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
    #app=ConsoleApp()
    app = App()
    app.run()

import pyglet

TILE_W = 64
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



class Cell:
    def __init__(self, name):
        self.name=name
        self.passable = True


class Level:
    def __init__(self, w=10, h=10):
        self.tile_width = 64
        self.m = make_2d(lambda x,y: Cell('floor'), w, h)
        self.objects = []
        self.monsters = []
        self.entry_pos = (0,0)

        for x, y, c in enum_2d(self.m, lambda: print('\n')):
            #print(x, y, c)
            pass

class Monster:
    def __init__(self, tilename=''):
        self.x = 0
        self.y = 0
        self.hp = 0
        self.tilename=tilename

class Object:
    def __init__(self, name, x=0, y=0):
        self.x = x
        self.y = y
        self.hp = 0
        self.name= name


class Session:
    def __init__(self):
        self.level=load_level_str(demo_level_str)
        self.player = Monster()
        self.player.x,self.player.y = self.level.entry_pos
        #self.level.objects.append(Object('box', TILE_W*5, TILE_W*4))



demo_level_str = '''
#############
#..P,p;;;;###
#.#,#,###;###
#@#,#,###g.>#
#..,#,;;;;###
#.#,#,#.....#
#.0p,p.S.*..#
#...........#
#############
'''

def char_to_cell(ch) -> Cell:
    if ch == '#':
        c = Cell('wall')
        c.passable = False
        return c

    if ch in ".,;:\'\"@g0":
        c = Cell('floor')
        return c

    if ch in "Pp":
        c = Cell('waypoint')
        return c

    if ch == '#':
        c = Cell('wall')
        c.passable = False
        return c

    if ch == '>':
        c = Cell('door')
        c.passable = False
        return c

    c = Cell('qm')
    return c


def char_to_object(ch):
    if ch == '0':
        return Object('box')
    if ch == '*':
        return Object('light')

def char_to_monster(ch):
    if ch == 'P':
        return Monster('security')
    if ch == 'g':
        return Monster('goat')
    if ch == 'S':
        return Monster('stranger')


def load_level_str(level_str) -> Level:
    lines = [s for s in level_str.split('\n') if s]
    level_width = max([len(line) for line in lines])
    level_height = len(lines)
    level = Level(level_width, level_height)
    for y in range(level_height):
        for x in range(len(lines[y])):
            ch = lines[y][x]
            level.m[y][x] = char_to_cell(ch)
            o = char_to_object(ch)
            if o:
                o.x = TILE_W * x
                o.y = TILE_W * y
                level.objects.append(o)
            m = char_to_monster(ch)
            if m:
                m.x = TILE_W * x
                m.y = TILE_W * y
                level.monsters.append(m)
            if ch == '@':
                level.entry_pos = ( TILE_W * x,  TILE_W * y)
    return level


session = Session()

def remove_guidelines(pic):
    rawimage = pic.get_image_data()
    format = 'RGBA'
    pitch = rawimage.width * len(format)
    cpixels = pic.get_data(format, pitch)
    print(type(cpixels))
    colors={}
    pixels = bytearray(cpixels)
    for i in range(len(pixels)//4):
        r = pixels[i*4]
        g = pixels[i * 4+1]
        b = pixels[i * 4+2]
        a = pixels[i * 4+3]
        if (r,g,b) == (128, 128, 0):
            pixels[i*4] = 255
            pixels[i * 4+1] = 255
            pixels[i * 4+2] = 255
            pixels[i * 4+3] = 0
    pic.set_data(format, pitch, bytes(pixels))
        #colors[(r,g,b)]=1
    #print(colors)


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

        for x, y, c in enum_2d(session.level.m):
            self.draw_sprite(c.name ,x*64,y*64)
        for o in session.level.objects:
            self.draw_sprite(o.name, o.x, o.y)

        for m in session.level.monsters:
            self.draw_sprite(m.tilename, m.x, m.y)
        p=session.player
        self.draw_sprite('player', p.x, p.y)
        self.fps_display.draw()
        self.flip()

    def draw_sprite(self, name, x, y):
        if name not in self.images:
            self.images[name]=pyglet.image.load('data/pics/%s.png'%name)
            remove_guidelines(self.images[name])

        self.images[name].blit(x,y)


class App:
    def __init__(self):
        self.sess = Session()
        self.papp = PygletApp(width=1024,height=768)
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

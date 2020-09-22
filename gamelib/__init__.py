import pyglet
# import pymunk

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
        self.waypoint_char = '\0'


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
        self.char='?'
        self.clear_input()

    def clear_input(self):
        self.in_w = False
        self.in_s = False
        self.in_a = False
        self.in_d = False
        self.in_attack = False
        self.tgt = (self.x, self.y)

    def move_to_tgt(self):
        tolerance = 5
        if self.tgt[0] < self.x - tolerance:
            self.in_a = True
        elif self.tgt[0] > self.x + tolerance:
            self.in_d = True

        if self.tgt[1] < self.y - tolerance:
            self.in_s = True
        elif self.tgt[1] > self.y + tolerance:
            self.in_w = True

    def ai(self):
        pass

def manh_dist(A,B):
    return max(abs(A[0]-B[0]), abs(A[1]-B[1]))


def list_waypoints(level, ch):
    result=[]
    for x,y,c in enum_2d(level.m):
        if c.waypoint_char == ch:
            result.append((x,y))
    return result

class Bot(Monster):
    def __init__(self, *args, **kwargs):
        Monster.__init__(self, *args, **kwargs)
        self.waypoints=[]
        self.path=[]
        self.current_waypoint = 0

    def ai(self):
        #print('bot ai')
        tgt_x, tgt_y = self.x, self.y
        if not self.path and self.waypoints:
            self.current_waypoint = (self.current_waypoint + 1) % len(self.waypoints)
            self.path = self.make_path(
                (self.x//TILE_W, self.y//TILE_W),
                self.waypoints[self.current_waypoint])

            print('update path to', self.path)
        while self.path:
            path_tx, path_ty = self.path[0]
            path_x, path_y = path_tx*TILE_W, path_ty*TILE_W
            if manh_dist((self.x, self.y), (path_x, path_y)) < 10:
                self.path = self.path[1:]
                print('dist:', )
                print('reduce path to', self.path)
            else:
                tgt_x, tgt_y = path_x, path_y
                print('set tgt to', path_x, path_y, ' pos:', self.x, self.y)
                break

        self.clear_input()
        self.tgt = tgt_x, tgt_y
        self.move_to_tgt()
        s=''
        if self.in_w: s+='W'
        if self.in_s: s += 'S'
        if self.in_a: s += 'A'
        if self.in_d: s += 'D'
        print('in:', s)

    def make_path(self, src, tgt):
        sx, sy = src
        tx, ty = tgt
        level = session.level
        level_w = len(level.m[0])
        level_h = len(level.m)
        cost=make_2d(lambda x,y: (999 if level.m[y][x].passable else 1000),
                     len(level.m[0]), len(level.m))
        def draw_cost():
            for x,y,c in enum_2d(cost, lambda:print()):
                if c == 1000:
                    print('#', end='')
                elif c == -1:
                    print('.', end='')
                elif c <= ord('z') - ord('a'):
                    print(chr(ord('a')+c), end='')
                else:
                    print('Z', end='')

        def neighbours(x, y):
            dd = [(1,0), (0,1), (-1,0), (0,-1)]
            for dx, dy in dd:
                nx = x + dx
                ny = y + dy
                if 0 <= nx < level_w and 0 <= ny < level_h:
                    yield (nx, ny)
        pts = [src]

        cost[sx][sy] = 0
        draw_cost()

        current_cost = 0
        for i in range(10):
            newpts = []
            for p in pts:
                px, py = p
                for neigh in neighbours(px, py):
                    pass

        draw_cost()


        return [tgt]

    def prepare_waypoints(self, level):
        self.waypoints = list_waypoints(level, self.char)
        print('WP:', self.waypoints)


class Player(Monster):
    def __init__(self, *args, **kwargs):
        Monster.__init__(self, *args, **kwargs)

    def ai(self):
        self.clear_input()
        if session.app.keys[pyglet.window.key.W]:
            self.in_w = True
        if session.app.keys[pyglet.window.key.S]:
            self.in_s = True
        if session.app.keys[pyglet.window.key.A]:
            self.in_a = True
        if session.app.keys[pyglet.window.key.D]:
            self.in_d = True


class Object:
    def __init__(self, name, x=0, y=0):
        self.x = x
        self.y = y
        self.hp = 0
        self.name= name


class Session:
    def __init__(self):
        self.level=load_level_str(demo_level_str)
        self.player = Player()
        self.player.x,self.player.y = self.level.entry_pos
        #self.app = None
        #self.level.objects.append(Object('box', TILE_W*5, TILE_W*4))
    def update(self):
        self.player.ai()
        for m in self.level.monsters:
            m.ai()
        self.m_phy(self.player)
        for m in self.level.monsters:
            self.m_phy(m)

    def m_phy(self, m):
        speed=5
        if m.in_w:
            m.y+=speed
        if m.in_s:
            m.y-=speed
        if m.in_a:
            m.x-=speed
        if m.in_d:
            m.x+=speed


demo_level_str = '''
#############
#..,,p;;;;###
#.#P#,###;###
#@#,#,###g.>#
#..,#,;;;;###
#.#,#p#.....#
#.0,p..S.*..#
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
        c.waypoint_char = str.lower(ch)
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
        m= Bot('security')
        m.char = str.lower(ch)
        return m
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

    for m in level.monsters:
        if isinstance(m, Bot):
            print("WP prepare for", m)
            m.prepare_waypoints(level)

    return level


session = Session()

def remove_guidelines(pic):
    rawimage = pic.get_image_data()
    format = 'RGBA'
    pitch = rawimage.width * len(format)
    cpixels = pic.get_data(format, pitch)
    #print(type(cpixels))
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
        self.keys = pyglet.window.key.KeyStateHandler()
        self.push_handlers(self.keys)
        self.images = {}

    def update(self, dt):
        #print('update', dt)
        session.update()
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
        global session
        self.sess = Session()
        session = self.sess
        self.papp = PygletApp(width=1024,height=768)
        self.papp.sess = self.sess
        self.sess.app = self.papp
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

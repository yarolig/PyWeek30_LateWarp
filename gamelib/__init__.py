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

def enum_2d_tm(arr, eol=None):
    for x in range(len(arr[0])-1, -1, -1):
        for y in range(len(arr)):
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
        self.vacant = True
        self.used_by = None
        self.waypoint_char = '\0'
    def __str__(self):
        return "Cell(%s)" % (self.name)


class Level:
    def __init__(self, w=10, h=10):
        self.tile_width = 64
        self.m = make_2d(lambda x,y: Cell('floor'), w, h)
        self.objects = []
        self.monsters = []
        self.entry_pos = (0,0)

        #for x, y, c in enum_2d(self.m, lambda: print('\n')):
        #    #print(x, y, c)
        #    pass


class Monster:
    def __init__(self, tilename=''):
        self.x = 0
        self.y = 0
        self.facing = 'w'
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
        self.in_kick = False
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
    print('WP:', result)
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
            print('cwp', self.current_waypoint, 'wps:', self.waypoints)
            self.path = self.make_path(
                ((self.x+TILE_W//2)//TILE_W, (self.y+TILE_W//2)//TILE_W),
                self.waypoints[self.current_waypoint])

            print('update path to', self.path)
        while self.path:
            path_tx, path_ty = self.path[0]
            path_x, path_y = path_tx*TILE_W, path_ty*TILE_W
            if manh_dist((self.x, self.y), (path_x, path_y)) < 10:
                self.path = self.path[1:]
                #print('dist:', )
                print('reduce path to', self.path)
            else:
                tgt_x, tgt_y = path_x, path_y
                #print('set tgt to', path_x, path_y, ' pos:', self.x, self.y)
                break

        self.clear_input()
        self.tgt = tgt_x, tgt_y
        self.move_to_tgt()
        s=''
        if self.in_w: s+='W'
        if self.in_s: s += 'S'
        if self.in_a: s += 'A'
        if self.in_d: s += 'D'
        #print('in:', s)

    def make_path(self, src, tgt, level=None):
        #return [tgt]
        sx, sy = src
        tx, ty = tgt
        if (sx,sy) == (tx,ty):
            print('Warning: bad make_path call', src, tgt)
            #raise Exception()
            return [(tx, ty)]

        print('make_path','s:',sx,sy,'t:',tx,ty)
        if not level:
            level = session.level
        level_w = len(level.m[0])
        level_h = len(level.m)
        def passable_score(c):
            if not c.passable:
                return 1000
            elif not c.vacant:
                return 1001
            else:
                return 999

        cost=make_2d(lambda x,y: passable_score(level.m[x][y]),
                     level_h, level_w)
        def draw_cost():
            for y, x, c in enum_2d_tm(cost, lambda:print()):
                if c == 1000:
                    print('#', end='')
                elif c == 1001:
                    print('@', end='')
                elif c == -1:
                    print('.', end='')
                elif c <= ord('z') - ord('a'):
                    print(chr(ord('a')+c), end='')
                else:
                    print('Z', end='')

        def neighbours(xx, yy):
            dd = [(1,0), (0,1), (-1,0), (0,-1)]
            for dx, dy in dd:
                nnx = xx + dx
                nny = yy + dy
                if 0 <= nnx < level_w and 0 <= nny < level_h:
                    yield (nnx, nny)
        pts = [src]

        cost[sx][sy] = 0
        #cost[tx][ty] = 60
        #draw_cost()

        current_cost = 0
        for r in range(1,50):
            newpts = []
            for p in pts:
                px, py = p
                for nx, ny in neighbours(px, py):
                    nc = cost[nx][ny]
                    if nc < 1000 and nc > r:
                        cost[nx][ny] = r
                        newpts.append((nx, ny))
                else:
                    print('warning: no neigh for',px,py,'lwh:',level_w,level_h)
            pts = newpts
        result = []

        draw_cost()
        if cost[tx][ty] < 999:
            x = tx
            y = ty
            c = cost[tx][ty]
            while 1:
                result.insert(0, (x, y))

                #print (':::', (x,y), c,'path:', result)

                for nx, ny in neighbours(x, y):
                    #print('n:', (nx,ny), cost[nx][ny], c - 1)
                    if cost[nx][ny] == c - 1:
                        x = nx
                        y = ny
                        c = c - 1
                        break
                else:

                    raise Exception('no path' + str(list(neighbours(x, y))) + str(result))
                if (x, y) == (sx, sy):
                    result.insert(0, (x, y))
                    break
        else:
            print('warning: no path')
            draw_cost()
        #result.reverse()
        return result


    def prepare_waypoints(self, level):
        waypoints = list_waypoints(level, self.char)
        # choose wp order
        self.waypoints=[]
        self.waypoints.append(waypoints.pop())
        nw = len(waypoints)
        lwx, lwy = self.waypoints[0]
        for i in range(nw):
            ii, w = min([(len(self.make_path((lwx, lwy), (w[0], w[1]), level)), w) for w in waypoints], key=lambda x: x[0])
            waypoints.remove(w)
            lwx, lwy = w
            self.waypoints.append(w)

        print('sorted WP:', self.waypoints)


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
        if session.app.keys[pyglet.window.key.SPACE]:
            self.in_kick = True


class Object:
    def __init__(self, name, x=0, y=0):
        self.x = x
        self.y = y
        self.hp = 0
        self.name= name


facing2dir = {
'w': (0, 1),
's': (0, -1),
'a': (-1, 0),
'd': (1, 0),
}

class Session:
    def __init__(self):
        #self.level = load_level_str(demo_level_str)
        #self.level = load_level_str(warp_storage_level_str)
        self.level = load_level_str(boring_level_str)
        self.player = Player()
        self.player.x,self.player.y = self.level.entry_pos
        #self.app = None
        #self.level.objects.append(Object('box', TILE_W*5, TILE_W*4))

    def xy2ctxy(self, x, y):
        tx = (x + TILE_W // 2) // TILE_W
        ty = (y + TILE_W // 2) // TILE_W
        c = None
        if 0 <= tx < len(self.level.m[0]) and 0 <= ty < len(self.level.m):
            c = self.level.m[ty][tx]
        return tx, ty, c

    
    def kick(self, m):
        print ('kick', m, m.facing)
        mtx, mty, mc = self.xy2ctxy(m.x, m.y)
        dx, dy = facing2dir[m.facing]
        stx, sty, sc = self.xy2ctxy(m.x+dx*TILE_W, m.y+dy*TILE_W)
        dtx, dty, tc = self.xy2ctxy(m.x+2*dx*TILE_W, m.y+2*dy*TILE_W)
        print(mc, sc, tc)
        if not sc:
            return
        if not mc:
            return
        if not tc:
            return


        if not tc.passable:
            return
        if not tc.vacant:
            return
        print('sc.ub', sc.used_by)
        if isinstance(sc.used_by, Object):
            o = sc.used_by
            o.x = dtx*TILE_W
            o.y = dty*TILE_W

        
    def update(self):
        self.player.ai()
        for x, y, c in enum_2d(self.level.m):
            c.vacant = True
            c.used_by = None

        def vx(m):
            tx = (m.x + TILE_W//2) // TILE_W
            ty = (m.y + TILE_W // 2) // TILE_W
            if 0 <= tx < len(self.level.m[0]) and 0 <= ty < len(self.level.m):
                self.level.m[ty][tx].vacant = False
                self.level.m[ty][tx].used_by = m

        for m in self.level.monsters:
            vx(m)
        vx(self.player)
        for o in self.level.objects:
            vx(o)

        for m in self.level.monsters:
            m.ai()
        self.m_phy(self.player)
        for m in self.level.monsters:
            self.m_phy(m)

    def m_phy(self, m):
        speed=8
        dx = dy = 0
        if m.in_w:
            dy+=speed
            m.facing = 'w'
        if m.in_s:
            dy-=speed
            m.facing = 's'
        if m.in_a:
            dx-=speed
            m.facing = 'a'
        if m.in_d:
            dx+=speed
            m.facing = 'd'
        #if m.in_kick:
        #    self.kick(m)



        def can_pass(cell):
            if not cell:
                return False
            if not c.passable:
                return False
            if not c.vacant:
                return c.used_by is m
            return True

        def can_kick(cell):
            if not cell:
                return False
            if c.used_by and isinstance(c.used_by, Object):
                return True
            return False

        tx, ty, c = self.xy2ctxy(m.x + dx, m.y)
        if can_pass(c):
            m.x += dx
        elif can_kick(c):
            self.kick(m)

        tx, ty, c = self.xy2ctxy(m.x, m.y + dy)
        if  can_pass(c):
            m.y += dy
        elif can_kick(c):
            self.kick(m)


demo_level_str = '''
##############
#..P,,p;;;####
#.#,##,##.####
#@#,##,##.g.>#
#..,##,;;;####
#.#,##p#.....#
#..,##,......#
#..,##,......#
#.0p,,,.S.*..#
#............#
##############
'''






# Sunrise Warp Travel
'''
'''



# Entrance
entrance_level_str = '''
############>###################
############+###################
#######..@.......###############
##>.00..............>###########
#######..........###############
#######..........###############
################################
'''



# Warp storage
warp_storage_level_str = '''
####################
#####..#########..##
#00.0..0.......0..##
.@..#..#####.####.##
#..00#######.####.##
##0######.00...##.##
#..0#####00.00.##..#
#..0...##.0..0.##WW#
#.0.#.....0.0.0#####
####################
....................
....................
'''


# Some boring level
boring_level_str = '''
####################
##p########p######P#
#..................#
########..#.######.#
##..........######0#
>@.0000#..#.##.....#
##.0.0.#....##.....#
##...0.#..#.##.g..g#
##.0.0.#.....0.....>
##..#######.##..g..#
##....g..g..##....g#
##....g...g.##.....#
#######>############
'''

# Laser cutting

# Compact battery production

# Communication room

# Logistics

# Spaceport

# Fuel storage

# Environment control

# Artifical gravity engines

# Robot maintenance

# Cybergoat production



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
    lines.reverse()
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
        self.papp = PygletApp(width=1280,height=800)
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

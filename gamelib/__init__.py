import pyglet
# import pymunk
import random
import copy
import time



from pyglet.gl import *
NO_SOUND = False
try:
    import pyglet.media
except:
    NO_SOUND = True

#try:
#    from pyglet.media import player
#except:
#    pass

TILE_W = 64
SPEED=6
DELAY=0

CONTROLS_CUTSCENE = '''
        Controls
    
WASD, Arrows - move  
Shift        - move without pushing crates  
R            - use warpback device (resets level, usually)    
Space        - hold to ready a weapon (it fires automatically)

M            - toggle music
F1           - show controlls
F2           - show status         
F3           - show last message  

F4-F9        - change game speed    

F10, Ctrl+Q  - quit game  
'''

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
        self.travel_to = ''
    def on_present(self):
        pass

    def on_step(self):
        pass

    def __str__(self):
        return "Cell(%s)" % (self.name)

class Gate(Cell):
    def on_present(self):
        if session.player.has_warpback:
            if self.name != 'floor':
                self.name = 'floor'
                session.app.update_floor()
            self.passable = True
        else:
            if self.name != 'gate':
                self.name = 'gate'
                session.app.update_floor()
            self.passable = False
            

class GateBoot(Cell):
    def on_present(self):
        if session.player.has_boots:
            if self.name != 'floor':
                self.name = 'floor'
                session.app.update_floor()
            self.passable = True
        else:
            if self.name != 'gate':
                self.name = 'gate'
                session.app.update_floor()
            self.passable = False

class GateDefense(Cell):
    def on_present(self):
        if not session.defense_on and session.gravity_on:
            if self.name != 'floor':
                self.name = 'floor'
                session.app.update_floor()
            self.passable = True
        else:
            if self.name != 'gate':
                self.name = 'gate'
                session.app.update_floor()
            self.passable = False


class Computer(Cell):
    def on_step(self):
        session.level.cls.on_computer()


class GravityComputer(Cell):
    def on_present(self):
        if self.name == 'computer_G':
            session.gravity_on = True

    def on_step(self):
        #print('on_step')
        self.name = 'computer_broken'
        if session.gravity_on:
            session.gravity_on = False
            session.app.update_floor()

class Level:
    def __init__(self, w=10, h=10):
        self.level_name = ''
        self.tile_width = 64
        self.m = make_2d(lambda x,y: Cell('floor'), w, h)
        self.objects = []
        self.monsters = []
        self.decals = []
        self.entry_pos = (0,0)
        self.cls = None

    def get_named_entry_txyc(self, entry_name):
        for x, y, c in enum_2d(self.m):
            if c.travel_to:
                #print ('travel_to', c, c.travel_to)
                pass
            if c.travel_to == entry_name:
                return x,y,c
        else:
            raise Exception('no entrance from %s in %s' % (entry_name, 'level'))

        #for x, y, c in enum_2d(self.m, lambda: print('\n')):
        #    #print(x, y, c)
        #    pass


class Monster:
    def __init__(self, tilename=''):
        self.x = 0
        self.y = 0
        self.facing = 'w'
        self.hp = 10
        self.hpmax = 10
        self.tilename=tilename
        self.char='?'
        self.fire_range = 0
        self.name = tilename
        self.attacking = False

        self.has_laser = False
        self.has_warpback = False
        self.has_boots = False
        self.has_rapair_kit = False

        self.clear_input()


    def __str__(self):
        return "Mon(%d %d %d)" % (self.x, self.y, self.hp)

    def clear_input(self):
        self.in_w = False
        self.in_s = False
        self.in_a = False
        self.in_d = False
        self.in_attack = False
        self.in_kick = False
        self.in_walk = False
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



class Goat(Monster):
    def __init__(self, *args, **kwargs):
        Monster.__init__(self, *args, **kwargs)
        self.fire_range = 1
        self.hp = 5

def max_dist(A,B):
    return max(abs(A[0]-B[0]), abs(A[1]-B[1]))

def manh_dist(A,B):
    return abs(A[0]-B[0]) + abs(A[1]-B[1])


def list_waypoints(level, ch):
    result=[]
    for x,y,c in enum_2d(level.m):
        if c.waypoint_char == ch:
            result.append((x,y))
    #print('WP:', result)
    return result

class Bot(Monster):
    def __init__(self, *args, **kwargs):
        Monster.__init__(self, *args, **kwargs)
        self.waypoints=[]
        self.path=[]
        self.hp = 30
        self.current_waypoint = 0
        self.fire_range = 2

    def update_path(self):
        self.current_waypoint = (self.current_waypoint + 1) % len(self.waypoints)
        # print('cwp', self.current_waypoint, 'wps:', self.waypoints)
        self.path = self.make_path(
            ((self.x + TILE_W // 2) // TILE_W, (self.y + TILE_W // 2) // TILE_W),
            self.waypoints[self.current_waypoint])
    def ai(self):
        if not session.gravity_on:
            self.clear_input()
            return
        #print('bot ai')
        tgt_x, tgt_y = self.x, self.y
        if not self.path and self.waypoints:
            self.update_path()
            #print('update path to', self.path)

        while self.path:
            path_tx, path_ty = self.path[0]
            path_x, path_y = path_tx*TILE_W, path_ty*TILE_W
            if manh_dist((self.x, self.y), (path_x, path_y)) < 10:
                self.path = self.path[1:]
                #print('dist:', )
                #print('reduce path to', self.path)
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
            #print('Warning: bad make_path call', src, tgt)
            #raise Exception()
            return [(tx, ty)]

        #print('make_path','s:',sx,sy,'t:',tx,ty)
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
                    #print('warning: no neigh for',px,py,'lwh:',level_w,level_h)
                    pass
            pts = newpts
        result = []

        #draw_cost()
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
            #print('warning: no path')
            #draw_cost()
            pass
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

        #print('sorted WP:', self.waypoints)


class Player(Monster):
    def __init__(self, *args, **kwargs):
        Monster.__init__(self, *args, **kwargs)
        self.fire_range = 2
        self.hp = 10
        self.hpmax = 50

    def ai(self):
        self.clear_input()
        k = pyglet.window.key
        kk = session.app.keys
        if kk[k.W] or kk[k.UP] or kk[k.K]:
            self.in_w = True
        if kk[k.S] or kk[k.DOWN] or kk[k.J]:
            self.in_s = True
        if kk[k.A] or kk[k.LEFT] or kk[k.H]:
            self.in_a = True
        if kk[k.D] or kk[k.RIGHT] or kk[k.L]:
            self.in_d = True
        if kk[k.SPACE]:
            self.in_attack = True
        if kk[k.LSHIFT]  or kk[k.RSHIFT]:
            self.in_walk = True


class Object:
    x = 0
    y = 0
    hp = 100
    name = ''
    pushable = False
    blocks_vision = False
    blocks_path = False
    blocks_path_finding = False
    pickable = False
    def on_pick(self, m: Monster):
        pass


class Box(Object):
    name = 'box'
    pushable = True
    blocks_vision = True
    blocks_path = True
    blocks_path_finding = True

class Warpback(Object):
    name = 'warpback'
    pickable = True
    def on_pick(self, m: Monster):
        m.has_warpback = True

class Laser(Object):
    name = 'laser'
    pickable = True
    def on_pick(self, m: Monster):
        m.has_laser = True
        session.cutscene('''


You picked up lasergun!
It actually laser cutter but works as a weapon.

Hold Space to ready this weapon.
It will fire automatically when you close to enemies.    
''')

class Battery(Object):
    name = 'battery'
    pickable = True

class Boots(Object):
    name = 'boots'
    pickable = True
    def on_pick(self, m: Monster):
        m.has_boots = True

class Medkit(Object):
    name = 'hp'
    pickable = True
    def on_pick(self, m: Monster):
        if m.hp < 30:
            m.hp = 30


class Decal:
    def __init__(self, name, x=0, y=0):
        self.x = x
        self.y = y
        self.hp = 100
        self.name= name

facing2dir = {
'w': (0, 1),
's': (0, -1),
'a': (-1, 0),
'd': (1, 0),
}

class Session:
    def __init__(self):
        self.app =None
        self.loaded_levels = {}
        self.player = Player()
        self.player_copy = copy.copy(self.player)
        self.gravity_on = True
        self.defense_on = True
        self.remote_warpback = False
        self.reinit()
        self.cutscenes = {}
        self.prev_cutscene = '1'
        self.current_cutscene = '1'
        self.draw_fps = False

    def cutscene(self, text, force=False):

        if not force and text in self.cutscenes:
            return
        if not force:
            self.prev_cutscene = text
        self.current_cutscene = text
        self.cutscenes[self.current_cutscene] = True
        self.app.make_label(text)

    def reinit(self, level_name=None):
        if not level_name:
            level_name = 'start'
            #level_name = 'entrance'
        self.level_name = level_name
        self.level = self.load_level_by_name(level_name)
        self.loaded_levels[level_name] = self.level
        #print('Level', level_name)

        self.player = copy.copy(self.player_copy)
        self.player.x, self.player.y = self.level.entry_pos
        self.level.cls.on_enter()
        
        if self.app:
            self.app.update_floor()

    def load_level_by_name(self, lname):
        for i in all_levels:
            if i.name == lname:
                return load_level(i)
        else:
            print('Error: no such level', lname)
            return None

    def player_on_ground(self):
        return self.gravity_on or self.player.has_boots

    def travel(self, dest):
        travel_from = self.level_name
        #print('travel to', dest, 'from', travel_from)
        if dest not in self.loaded_levels:
            level = self.load_level_by_name(dest)

            if not level:
                print("Can't load level", dest)
                return
            self.loaded_levels[dest] = level
        level = self.loaded_levels[dest]
        self.level_name = dest
        tx, ty, c = level.get_named_entry_txyc(travel_from)
        self.player.x, self.player.y = tx*TILE_W, ty*TILE_W
        self.level = level
        self.player_copy = copy.copy(self.player)
        self.level.cls.on_enter()

        if self.app:
            self.app.update_floor()



    def cells_in_range(self, tx, ty, r):
        #print('cir')
        for i in range(tx-r-1, tx+r+1):
            for j in range(ty-r-1, ty+r+1):
                #print('r:', (tx, ty), (i, j), (tx - i) ** 2 + (ty - j) ** 2, r ** 2, (tx - i)**2 + (ty - j)**2 > r**2)
                if (tx - i)**2 + (ty - j)**2 > r**2:
                    continue
                if 0 <= i < len(self.level.m[0]) and 0 <= j < len(self.level.m):
                    yield i, j, self.level.m[j][i]

    def xy2ctxy(self, x, y) -> (int, int, Cell):
        tx = (x + TILE_W // 2) // TILE_W
        ty = (y + TILE_W // 2) // TILE_W
        c = None
        if 0 <= tx < len(self.level.m[0]) and 0 <= ty < len(self.level.m):
            c = self.level.m[ty][tx]
        return tx, ty, c


    def can_see(self, ssx, ssy, tsx, tsy):
        tx, ty, c = self.xy2ctxy((ssx+tsx) // 2 * TILE_W,
                                 (ssy+tsy) // 2 * TILE_W)
        if manh_dist((ssx,ssy), (tsx,tsy)) <= 1:
            return True
        if c and c.passable:
            if c.vacant:
                return True
            if isinstance(c.used_by, Monster):
                return True
        return False

    def add_ray(self, src, tgt):
        pass

    def auto_attack(self, m: Monster):
        if m.name == 'security' and not session.gravity_on:
            return
        if m is session.player and not session.player_on_ground():
            return
        if m is session.player and not m.has_laser:
            return

        tx, ty, c = self.xy2ctxy(m.x, m.y)
        for cx,cy,c in self.cells_in_range(tx, ty, m.fire_range):
            if not self.can_see(tx, ty, cx,cy):
                continue
            u = c.used_by
            if u and isinstance(u, Monster) and m.name != u.name:
                #print('Att', m, u)
                m.attacking = True
                self.add_ray((tx, ty), (cx, cy))
                u.hp -= 1
    
    def kick(self, m):
        #print ('kick', m, m.facing)
        mtx, mty, mc = self.xy2ctxy(m.x, m.y)
        dx, dy = facing2dir[m.facing]
        stx, sty, sc = self.xy2ctxy(m.x+dx*TILE_W, m.y+dy*TILE_W)
        dtx, dty, tc = self.xy2ctxy(m.x+2*dx*TILE_W, m.y+2*dy*TILE_W)
        #print(mc, sc, tc)
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
        #print('sc.ub', sc.used_by)
        if isinstance(sc.used_by, Object):
            o = sc.used_by
            o.x = dtx*TILE_W
            o.y = dty*TILE_W

        
    def update(self):
        self.player.ai()
        for x, y, c in enum_2d(self.level.m):
            c.vacant = True
            c.used_by = None
            c.on_present()

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
        speed=SPEED
        dx = dy = 0

        if m.hp <= 0:
            mtx, mty, mc = self.xy2ctxy(m.x, m.y)
            if mc.name == 'floor':
                mc.name = 'ashes'
                session.app.update_floor()
            if m is not self.player:
                self.level.monsters.remove(m)
            return

        if m is self.player:
            if m.in_attack and m.fire_range > 0:
                self.auto_attack(m)
        else:
            if m.fire_range > 0:
                self.auto_attack(m)

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

        def is_travel_move(oldcell, newcell):
            if not newcell:
                return
            if oldcell.travel_to != newcell.travel_to and newcell.travel_to:
                return True
            return False

        def can_pass(cell):
            if not cell:
                return False
            if not c.passable:
                return False
            if not c.vacant:
                if c.used_by is m:
                    return True
                if isinstance(c.used_by, Object):
                    return not c.used_by.blocks_path
            return True

        def can_kick(cell, m):
            if m is self.player and self.player.in_walk:
                return False
            if m is self.player and not self.player_on_ground():
                return False
            if not cell:
                return False
            if c.used_by and isinstance(c.used_by, Object):
                return c.used_by.pushable
            return False

        passed = False
        tx, ty, c = self.xy2ctxy(m.x + dx, m.y)
        mx, my, mc = self.xy2ctxy(m.x, m.y)
        if m is self.player and is_travel_move(mc, c):
            self.travel(c.travel_to)
            return

        if can_pass(c):
            m.x += dx
            if dx: passed = True
        elif can_kick(c, m):
            self.kick(m)

        tx, ty, c = self.xy2ctxy(m.x, m.y + dy)
        if m is self.player and is_travel_move(mc, c):
            self.travel(c.travel_to)
            return

        if can_pass(c):
            m.y += dy
            if dy: passed = True
        elif can_kick(c, m):
            self.kick(m)

        if not passed and isinstance(m, Bot):
            #print('update_path')
            m.update_path()

        if m is self.player and c:
            assert isinstance(c, Cell)
            c.on_step()
            if c.used_by and isinstance(c.used_by, Object):
                c.used_by.on_pick(m)









class LevelDef:
    name = ''
    data = ''
    transitions = ''.split()
    @staticmethod
    def on_load():
        pass

    @staticmethod
    def on_enter():
        pass

    @staticmethod
    def on_computer():
        pass

FIRST_CUTSCENE = '''
Hello and welcome to Sunrise Warp Travel Resort!

Soon you going to relax on the other side of the Galaxy!
But you are a bit late. Please HURRY!

Don't worry, it is completely safe.
Out customers are 100% satisfied! 

Please step inside the warp gate...
'''

class StartLevel(LevelDef):
    name = 'start'
    transitions = ''.split()
    data = '''
$$$$$$$$$$$$$$$$$$$$
$$$$$$$$$$$$$$$$$$$$
$$$$$$$$$$$$$$$$$$$$
$$$$$$$$$$$$$$$$$$$$
$$$$$$&^$$$$$$$$$$$$
,,,,,,..H,,,,,,.....
........,,,,,,,.....
....@...,,,,,,,.....
,,,,,,,,,,,,,,,.....
,,,,,,,,,,,,,,,0000.
,,,,,,,,,,,,,,,0000.
,,,,,,,,,,,,,,,0000.
'''

    @staticmethod
    def on_computer():
        session.reinit('entrance')

class EntranceLevel(LevelDef):
    name = 'entrance'
    transitions = 'demo laserroom2 warp_storage'.split()
    data = '''
####################
####################
########1###########
########-###########
######&~...#########
##...#.@...#########
#2.00.........0.####
##...#.....###...3##
######.....#########
######.....#########
######.....#########
####################
'''
    @staticmethod
    def on_enter():
        session.cutscene('''
What???
This is not Sunrise Warp Whatever!
Where am i?
It looks like an old ruined space factory!

There is a gate with big sign:
 
               "Warning!"
        Hazardous area.
        Warpback device required to enter.
 
Maybe I can use that "warpback device" to WARP BACK?!
        ''')

class DemoLevel(LevelDef):
    name = 'demo'
    transitions = 'entrance laserroom logistics'.split()
    data = '''
##############3#....
###..P..p....#.#....
##g.#.##.##.g#.#....
2...#.##.##....#....
###...##....########
..#.#.##p#....0#...#
..#.#.##..g..g0#...#
..#...##.#.....##.##
..#.0p...#.........#
..#............##-##
#################@##
................#1#.
'''
    @staticmethod
    def on_enter():
        if session.player.has_warpback:
            session.cutscene('''
Warpback devices offers ultimate protection for workers!
Mining, heavy machinery and construction became extremely safe
thanks to use of these devices.
''')


class WarpStorageLevel(LevelDef):
    name = 'warp_storage'
    transitions = 'entrance'.split()
    data = '''
####################
#####..#########..##
#00.0..0.......0..##
1@..#..#####.####.##
##.#########.####.##
##0######.00...##.##
#..0#####00..0.##.W#
#..0...##.00.0.##.W#
#.0.#.....0.0.0#####
####################
....................
....................
'''

    @staticmethod
    def on_load():
        session.cutscene('''
You entered some kind of equipment storage.
Map of this storage is available on you phone.
There is warpback device in far corner.
Cool! You can use it even remotely!

But I should carry it to next rooms. 
''')


class BoringLevel(LevelDef):
    name = 'boring'
    transitions = 'logistics botroom envroom'.split()
    data = '''
####################
##p#####..#p#####P##
#..................#
########..#.######.#
##..........#####.0#
1@.0000#..#.##0.0..#
##.0.0.#....##0.0..#
##...0.#..#.##....g#
##.0.0.#.....0.....3
##..#######.##..g..#
##.g....g...########
##....g...g.########
#######2############
'''


class BigroomLevel(LevelDef):
    name = 'bigroom'
    transitions = ''.split()
    data = '''
####################
#..................#
#..................#
#..................#
#..................#
#........@.........#
#..................#
#..................#
#..................#
#..................#
#..................#
####################
'''


# Laser cutting
class LaserLevel(LevelDef):
    name = 'laserroom'
    transitions = 'demo laserroom2'.split()
    data = '''
####################
#..............#..s#
#..#.0#00#0s#......#
#..====..====..#####
#..#..#p.#..#.....P#
#p.............#...#
####...######..#####
#..................#
#p........S....#..@1
#s.....##..#...#...#
#..........#.......#
######g2g###########
'''

    @staticmethod
    def on_enter():
        session.cutscene('''
This looks challenging.
''')


# Laser cutting2
class Laser2Level(LevelDef):
    name = 'laserroom2'
    transitions = 'laserroom entrance'.split()
    data = '''
####################
####################
####################
########1###########
####....@.....######
####...............2
####==L==+===.######
####..#..#..#.######
#############.######
#######........#####
#######..g#..g.#####
####################
'''


class EndLevel(LevelDef):
    name = 'end'
    transitions = 'space'.split()
    data = '''
$$$$$$$$$$$$$$$$,,,,
$$$$$$$$$$$$$$$$,,,,
$$$^&$$$$$$$$$$$,,,,
,,,..,,,,,,,,,,H,,,,
,,,..,,,,H,,,,HHH,,,
.....,,,,,H,,,,,,,,,
.....,,,,,,,,,,,HH,,
,,,,,,,,,,,,,,,,H,,,
,,,,,,,,,,H,,,,,,,,,
$$$$$$$$$$$$$@$$$$$$
$$$$$$$$$$$$$1$$$$$$
$$$$$$$$$$$$$$$$$$$$
'''
    @staticmethod
    def on_enter():
        session.player.has_laser = False
        session.cutscene('''
???

What???

This is not a Stardock of Bizzare Cybergoat Factory!
It looks like.. :) A Sunrise Whatever Warping Resort!

"Hello and welcome to Sunrise Warp Travel Resort!
On the other side of the Galaxy!

Like I said out customers are 100% satisfied!
Don't worry, it was completely safe."

''')

    @staticmethod
    def on_computer():
        session.cutscene('''

Thank you for playing LateWarp!



Pyweek30 individual entry by Alexander Izmailov.
Music by hermetico.




https://pyweek.org/e/LateWarp/
''')


# Communication room
class CommroomLevel(LevelDef):
    name = 'comm'
    transitions = 'logistics space'.split()
    data = '''
####################
#.P#.........#.....#
#......0.....000...2
#########00###.....#
#..#......;..#######
#&.g..;;;;........@1
#..#...............#
####.........#.....#
#########..###..####
#.p...............p#
#..#............#..#
####################
'''

    @staticmethod
    def on_enter():
        if session.player.has_laser:
            session.cutscene('''
Looks like a communication room.
I hope equipment is not destroyed completely.
''')
        else:
            session.cutscene('''
Looks like a communication room.

Can't get there.
Should be some way to deal with this thing...
''')

    @staticmethod
    def on_computer():
        session.cutscene('''
Long range connection works well! You called you travel agents.
"I lost! Where am I? Help me!!!"

"You warped just near Sunrise Warp Resort.
   Just on nearby planet.
     On an old bizarre space factory.
      We sending a rescue team to you.
      
 But... Could you disable base security?
  The factory has old guns that may prevent docking"
  
  "Well... I'll try..."
''')
# Logistics
class LogisticsLevel(LevelDef):
    name = 'logistics'
    transitions = 'demo comm boring'.split()
    data = '''
####################
#.sp.##.sp.##..sp..#
2..0......0##.0....3
#..0.##..0..C....0.#
##c####....####c####
#.....##c######.####
#P.00.##.##.##...0.#
#s...........#..0..#
###c###..###.c..Sp.#
#.0........#########
#s..p.#..@.#########
#########1##########
'''
    @staticmethod
    def on_enter():
        session.cutscene('''
There is a lot of cables here.

Communication room should be near.
''')

# Spaceport
class SpaceLevel(LevelDef):
    name = 'space'
    transitions = 'goatroom comm end'.split()
    data = '''
#########3##########
#.......#/#...+LW..#
#.......#&#........#
#########"######.###
#..................#
2........@.........1
#..................#
####################
#..................#
#..................#
#..................#
####################
'''
    @staticmethod
    def on_enter():
        session.cutscene('''
Looks like a space gate.
A big sign tells you:

 ! Wearing SPACEBOOTS is mandatory !
 Warpback device may not help you.
 
''')

    @staticmethod
    def on_computer():
        if session.defense_on:
            session.cutscene('''
Access disallowed while defense system active.
        ''')
        if not session.gravity_on:
            session.cutscene('''
Access disallowed while gravity not working.
''')

# Fuel storage
class FuelLevel(LevelDef):
    name = 'fuel'
    transitions = 'botroom envroom'.split()
    data = '''
###############2####
#....##....#.#....+#
#....#1@...#.####.##
#....##....0.#....S#
#....##....#.#.#####
#....##....#.#.....#
#....####0##0####.##
#....##...#..#.ss..#
#....##......#.ss..#
#....##...#.00.ss..#
#....##...#..#.....#
####################
'''

    dataR = '''
###########1########
2.....#.#..@.##....#
##.####.#....##....#
#S....#.0....##....#
#####.#.#....##....#
#.....#.#....##....#
##.####0##0####....#
#..ss.#..#...##....#
#..ss.#......##....#
#..ss.00.#...##....#
#.....#..#...##....#
####################
'''

# Environment control

# Artifical gravity engines
class GravityLevel(LevelDef):
    name = 'gravity'
    transitions = 'envroom goatroom'.split()
    data = '''
####################
#..................#
#.....#######......#
####..#.s.s.#..#####
#gm#..#..%..#..#.M.#
2..#..#.s.s.#..#...#
#..#..###.###..#...#
#..0...........0...#
####...........#####
#..g....#0#........#
#.......#@#........#
#########1##########
'''

    @staticmethod
    def on_enter():
        if session.player.has_warpback:
            session.cutscene('''
These room controls artifical gravity.
I should be careful here.
    ''')

# Environment control
class EnvLevel(LevelDef):
    name = 'envroom'
    transitions = 'boring fuel gravity'.split()
    data = '''
###3################
###p######.........#
#P.......#.........#
#####0##.#...#######
1@....##.##..#.....#
#####.0..0####....C#
#######...........&#
#.....#...####....S#
#.....##0##..#.....#
#.....#..#...#######
#.....#..#.........#
#######2############
'''
    @staticmethod
    def on_computer():
        session.cutscene('''
This computer controlls oxyden regeneration.
I shoud not touch this.        
''')

# Robot maintenance
class BotLevel(LevelDef):
    name = 'botroom'
    transitions = 'boring fuel'.split()
    data = '''
#1##################
#@#.....sp.........#
#.#.....c..........#
#.#..######M.M###P.#
#..sc#M..###.####sc#
###p.#&......####..#
###..#M..########..#
###..#####....Sp...#
####....sp.....c...#
###....C...######.##
##############.....2
####################
'''
    @staticmethod
    def on_enter():
        session.cutscene('''
A lot of security bots here        
''')

    @staticmethod
    def on_computer():
        session.cutscene('''
You turned off defense cannons! Easily.

Now lets go to the spacedock and get out! 
''')
        session.defense_on = False


# Cybergoat production
class CybergoatLevel(LevelDef):
    name = 'goatroom'
    transitions = 'space gravity'.split()
    data = '''
####################
#.#......#...#.....#
#.#.s#...#...#.....#
1....#0#.....#.....#
##...0...#...#.....#
##...#.....S...s...#
##..s........#.....#
##.###...#######...#
#.................@2
#====ggggggggg=====#
#====gggOggggg=====#
####################
'''

all_levels = LevelDef.__subclasses__()

def char_to_cell(ch) -> Cell:
    if ch == '#':
        c = Cell('wall')
        c.passable = False
        return c

    if ch in ".;:\'@g0WLBO|+":
        c = Cell('floor')
        return c

    if ch == '=':
        c = Cell('furniture')
        return c
    if ch in ",H":
        c = Cell('ground')
        return c

    if ch == "-":
        c = Gate('gate')
        return c

    if ch == '"':
        c = GateBoot('gate')
        return c

    if ch == '/':
        c = GateDefense('gate')
        return c

    if ch == "$":
        c = Cell('start_wall')
        c.passable = False
        return c

    if ch == '^':
        c = Computer('warpgate')
        return c

    if ch == '~':
        c = Computer('warpgate_broken')
        return c


    if ch in '&|':
        c = Computer('computer')
        return c

    if ch == '%':
        c = GravityComputer('computer_G')
        return c

    if ch == 'v':
        c = Cell('computer_broken')
        return c

    if ch in "PpCcSsMm":
        c = Cell('waypoint')
        c.waypoint_char = str.lower(ch)
        return c

    if ch in '123456789':
        c = Cell('door')
        c.passable = True
        c.waypoint_char = ch
        return c

    c = Cell('qm')
    return c


def char_to_object(ch):
    if ch == '0':
        return Box()
    if ch == 'W':
        return Warpback()
    if ch == 'L':
        return Laser()
    if ch == 'B':
        return Battery()
    if ch == 'O':
        return Boots()
    if ch == '+':
        return Medkit()


def char_to_monster(ch):
    if ch in 'PCSM':
        m= Bot('security')
        m.char = str.lower(ch)
        return m

    if ch == 'g':
        return Goat('goat')

    if ch in 'traTRA':
        return Monster('stranger')

    if ch in 'H':
        return Monster('player')


def load_level(level_class) -> Level:
    level_str = level_class.data
    lines = [s for s in level_str.split('\n') if s]
    lines.reverse()
    level_width = max([len(line) for line in lines])
    level_height = len(lines)
    level = Level(level_width, level_height)
    level.level_name = level_class.name

    for y in range(level_height):
        for x in range(len(lines[y])):
            ch = lines[y][x]
            cl = char_to_cell(ch)
            level.m[y][x] = cl
            if cl.name == 'door':
                n = int(cl.waypoint_char) - 1
                if n >= len(level_class.transitions):
                    raise Exception('no transition to %s in %s' % (cl.waypoint_char, level_class.name))
                cl.travel_to = level_class.transitions[n]

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
            #print("WP prepare for", m)
            m.prepare_waypoints(level)
    level.cls = level_class
    level_class.on_load()
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
        print("Pyglet OpenGL config: ", self.context.config)

        self.keys = pyglet.window.key.KeyStateHandler()
        self.push_handlers(self.keys)
        self.images = {}
        self.frameno = 0
        self.batch = None
        self.sprites = []
        self.label = None
        self.hint = pyglet.text.Label('(press space to continue)', multiline=True,
                                 #font_name='Times New Roman',
                                 font_size=12,
                                 x=70, y=self.height * 1 // 10,
                                 width = self.width - 140
                                 #anchor_x='center', anchor_y='center'
                                 )

    def make_label(self, text):
        self.label= pyglet.text.Label(text, multiline=True,
                                 #font_name='Times New Roman',
                                 font_size=24,
                                 x=70, y=self.height * 8 // 10,
                                 width = self.width - 140
                                 #anchor_x='center', anchor_y='center'
                                 )

    def update(self, dt):
        #print('update', dt)
        if session.current_cutscene:
            pass
        else:
            session.update()
    def run(self):
        self.fps_display = pyglet.window.FPSDisplay(self)
        #self.window = pyglet.window.Window()
        pyglet.clock.schedule_interval(self.update, 1/60.0)
        pyglet.app.run()

    def on_key_press(self, symbol, modifiers):
        #print('press', pyglet.window.key.symbol_string(symbol), modifiers)
        pass


    def on_key_release(self, symbol, modifiers):
        #print('release', pyglet.window.key.symbol_string(symbol), modifiers)

        #if symbol == pyglet.window.key.Q and modifiers == pyglet.window.key.MOD_CTRL:
        #    self.close()
        if symbol == pyglet.window.key.R:
            if session.player.has_warpback or session.level_name == 'warp_storage':
                session.reinit(session.level_name)
        if symbol == pyglet.window.key.M:
            session.aapp.toggle_music()

        if symbol == pyglet.window.key.G and modifiers == pyglet.window.key.MOD_CTRL:
            session.gravity_on = not session.gravity_on

        if symbol == pyglet.window.key.W and modifiers == pyglet.window.key.MOD_CTRL:
            session.player.has_warpback = True
        if symbol == pyglet.window.key.L and modifiers == pyglet.window.key.MOD_CTRL:
            session.player.has_laser = True
        if symbol == pyglet.window.key.B and modifiers == pyglet.window.key.MOD_CTRL:
            session.player.has_boots = True
        if symbol == pyglet.window.key.D and modifiers == pyglet.window.key.MOD_CTRL:
            session.defense_on = not session.defense_on

        if symbol in (pyglet.window.key.N, pyglet.window.key.P)   and modifiers == pyglet.window.key.MOD_CTRL:
            self.reinit_d(symbol)
            if session.level_name in ('start', 'end'):
                self.reinit_d(symbol)

        if symbol == pyglet.window.key.F1:
            session.cutscene(CONTROLS_CUTSCENE, force=True)

        if symbol == pyglet.window.key.F2:
            status = '''
            Status

Health: %d
Gravity: %s
Defense cannons: %s
Spacedock ready: %s


Inventory:
phone, tickets, intergalactic insurance
%s%s%s
''' % (session.player.hp,
       "normal" if session.gravity_on else "no gravity",
       "active" if session.defense_on else "disabled",
       "no" if session.defense_on else "yes",
       "warpback device\n" if session.player.has_warpback else "",
       "laser pistol\n" if session.player.has_laser else "",
       "space boots\n" if session.player.has_boots else ""
       )
            if session.level_name in ('start', 'end'):
                status = '''
            Status

All right.
'''
            session.cutscene(status, force=True)
        if symbol == pyglet.window.key.F3:
            session.cutscene(session.prev_cutscene, force=True)

        global  DELAY
        if symbol == pyglet.window.key.F4:
            DELAY = 0
        if symbol == pyglet.window.key.F5:
            DELAY = 5
        if symbol == pyglet.window.key.F6:
            DELAY = 10
        if symbol == pyglet.window.key.F7:
            DELAY = 15
        if symbol == pyglet.window.key.F8:
            DELAY = 20
        if symbol == pyglet.window.key.F9:
            DELAY = 25

        #if symbol == pyglet.window.key.ESCAPE:
        if symbol == pyglet.window.key.F10:
           self.close()

        if symbol == pyglet.window.key.Q and modifiers == pyglet.window.key.MOD_CTRL:
            self.close()

    def reinit_d(self, symbol):
        ii = 0
        for i in range(len(all_levels)):
            if all_levels[i].name == session.level_name:
                if symbol == pyglet.window.key.N:
                    ii = i + 1
                else:
                    ii = i + len(all_levels) - 1
                ii = ii % len(all_levels)
                #print('ii', i, len(all_levels), ii)
                break
        session.reinit(all_levels[ii].name)


    def on_mouse_press(self, x, y, button, modifiers):
        #print('on_mouse_press', x, y, button, modifiers)
        pass


    def on_mouse_release(self, x, y, button, modifiers):
        #print('on_mouse_release', x, y, button, modifiers)
        pass

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        #print('on_mouse_drag',x, y, dx, dy, buttons, modifiers)
        pass

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        #print('on_mouse_scroll',x, y, scroll_x, scroll_y)
        pass

    def draw_cutscene(self):

        self.clear()

        k = pyglet.window.key
        kk = session.app.keys
        if kk[k.ESCAPE] or kk[k.SPACE] or kk[k.ENTER] or kk[k.RETURN]:
            session.current_cutscene = ''
        self.label.draw()
        self.hint.draw()
        self.fps_display.draw()
        #self.flip()

    def update_floor(self):
        for i in self.sprites:
            try:
                i.delete()
            except:
                pass
        self.sprites = []
        self.batch=None
        
        
    def on_draw(self):
        pyglet.gl.glClearColor(6/255., 64/255., 111/255., 255)
        if session.current_cutscene:
            if session.current_cutscene == '1':
                session.cutscene(FIRST_CUTSCENE)
            self.draw_cutscene()
            return
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        self.frameno += 1
        #print('draw')
        self.clear()

        k = pyglet.window.key
        kk = session.app.keys

        n=0
        if self.batch is None:
            self.batch = pyglet.graphics.Batch()
        
            for x, y, c in enum_2d(session.level.m):
                self.draw_sprite(c.name ,x*64,y*64, batch=self.batch)
                n+=1

        if not kk[k.F11] and self.batch is not None:            
            self.batch.draw()

        for o in session.level.objects:
            self.draw_sprite(o.name, o.x, o.y)

        #print(self.batch)
        print(n, 'len sprites:', len(self.sprites))
        #for i in self.sprites:
        #    i.delete()

        for m in session.level.monsters:
            if not session.gravity_on and m.name == 'security':
                n = 'security_nog'
                self.draw_sprite(n, m.x, m.y)
                continue
            asuf = ''
            if m.attacking and (self.frameno % 3 == 1):
                asuf = '_fire'
            self.draw_sprite(m.tilename + asuf, m.x, m.y)
            m.attacking = False

        p=session.player
        if not session.player_on_ground():
            n = 'player_nog'
            self.draw_sprite(n, p.x, p.y)
        else:
            asuf = ''
            if p.attacking and (self.frameno % 3 == 2):
                asuf = '_fire'
            if p.hp > 0:
                self.draw_sprite('player' + asuf, p.x, p.y)
                p.attacking = False
            else:
                self.draw_sprite('warp_anim%d' % (self.frameno // 5 % 3 + 1), p.x, p.y)

        cy = 32
        cx = 50
        dx = 50
        #p.has_warpback = True
        #p.has_boots = True
        #p.has_laser = True

        if p.has_boots:
            self.draw_sprite('circle', cx, cy, 16, 16)
            self.draw_sprite('boots', cx, cy, 16, 16)

            cx += dx
        if p.has_laser:
            self.draw_sprite('circle', cx, cy, 16, 16)
            self.draw_sprite('laser', cx, cy, 16, 16)
            cx += dx
        if p.has_warpback:
            self.draw_sprite('circle', cx, cy, 16, 16)
            self.draw_sprite('warpback', cx, cy, 16, 16)
            cx += dx
        if p.hp>=10:
            self.draw_sprite('circle', cx, cy, 16, 16)
            self.draw_sprite('hp', cx, cy, 16, 16)
            cx += dx
        if p.hp>=20:
            self.draw_sprite('circle', cx, cy, 16, 16)
            self.draw_sprite('hp', cx, cy, 16, 16)
            cx += dx

        if p.hp >= 30:
            self.draw_sprite('circle', cx, cy, 16, 16)
            self.draw_sprite('hp', cx, cy, 16, 16)
            cx += dx
        glDisable(GL_BLEND)
        self.fps_display.draw()
        if DELAY:
            time.sleep(0.001*DELAY)
        #self.flip()

    def draw_sprite(self, name, x, y, xx=None, yy=None, batch=None):

        if name not in self.images:
            
            #self.images[name]=pyglet.image.load('data/pics/%s.png'%name)
            self.images[name]=pyglet.resource.image('data/pics/%s.png'%name)

            #remove_guidelines(self.images[name])
        #if xx is not None:
        #    self.images[name].blit(x,y,xx,yy)
        #else:
        if batch is not None:
            self.sprites.append(pyglet.sprite.Sprite(self.images[name], x, y, batch=batch))
        else:
            self.images[name].blit(x, y)


class App:
    def __init__(self):
        global session
        self.sess = session #Session()
        #session = self.sess
        self.papp = PygletApp(width=1280,
                              height=768,
                              vsync=True,
                              config=pyglet.gl.Config(double_buffer=True))
        self.papp.sess = self.sess
        self.sess.app = self.papp
        self.sess.aapp = self
        if not NO_SOUND:
            self.music = pyglet.media.Player()
            self.track1 = pyglet.media.load('data/music/hermetico-metro.ogg')
            self.track2 = pyglet.media.load('data/music/hermetico-2plus3.ogg')
            self.music.queue(random.choice([self.track1, self.track2]))
            self.music.play()
            self.music.loop = True

    def toggle_music(self):
        if NO_SOUND:
            return
        if self.music.playing:
            self.music.pause()
        else:
            self.music.next_source()
            self.music.queue(random.choice([self.track1, self.track2]))
            self.music.play()

    def run(self):
        self.papp.run()

def main():
    app = App()
    app.run()

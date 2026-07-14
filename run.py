import pygame
import random
import copy
import sys
import os
from PIL import Image

def anim_to_surface_list(path): #챗지피티 ㄳ
    """
    GIF/APNG/일반 PNG를 읽어서 Surface 리스트 반환
    PNG는 길이 1인 리스트 반환
    """

    img = Image.open(path)
    surfaces = []

    try:
        while True:
            frame = img.convert("RGBA")

            surf = pygame.image.fromstring(
                frame.tobytes(),
                frame.size,
                "RGBA"
            ).convert_alpha()

            surfaces.append(surf)

            img.seek(img.tell() + 1)

    except EOFError:
        pass

    return surfaces

pygame.init()
screen = pygame.display.set_mode((800, 600))
WIDTH, HEIGHT = 800, 600
TEXTURE_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'textures') # 텍스쳐 위치
FONT_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Galmuri9.ttf')
GAME_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'gamelogic')
clock = pygame.time.Clock()
pygame.display.set_caption("ClumsyTest")
RUNNING=True
bgcolor=(0,0,0)
camera = [0,0,1] #x y zoom
textures = {}
game_font = pygame.font.Font(None, 40)

print("Loading texture...")
for a in os.listdir(TEXTURE_PATH):
    dapath = os.path.join(TEXTURE_PATH, a)
    if not os.path.isfile(dapath):
        continue
    ext = os.path.splitext(a)[1].lower()
    if ext in (".png", ".apng"):
        textures[os.path.splitext(a)[0]] = anim_to_surface_list(dapath)

def newrect(x, y, sizex, sizey):
    sx = -int(sizex/2)
    sy = -int(sizey/2)
    return pygame.Rect(x+sx, y+sy, sizex, sizey)
def zoomit(rectz, zoom=camera[2]):
    if isinstance(rectz, pygame.Rect):
        return (rectz.x*zoom, rectz.y*zoom, rectz.width*zoom, rectz.height*zoom)
    return (rectz[0]*zoom, rectz[1]*zoom, rectz[2]*zoom, rectz[3]*zoom)
def moveit(rectz, mx=camera[0], my=camera[1]):
    if isinstance(rectz, pygame.Rect):
        return (rectz.x+mx, rectz.y+my, rectz.width, rectz.height)
    return (rectz[0]+mx, rectz[1]+my, rectz[2], rectz[3])
def backtrc(ome, dx, dy, cols): #제미나이가 쥰내 멋지게 만들어준 충돌 코드
    if abs(dx) < 0.01:
        dx = 0.0
    if abs(dy) < 0.01:
        dy = 0.0

    blocked_faces = {"top": False, "bottom": False, "left": False, "right": False}

    if not cols:
        return round(ome.x), round(ome.y), dx, dy, blocked_faces

    px, py = float(ome.x), float(ome.y)
    w, h = int(ome.width), int(ome.height)

    steps = max(1, int(max(abs(dx), abs(dy)) / 5) + 1)
    step_dx = dx / steps
    step_dy = dy / steps

    for _ in range(steps):
        if step_dx != 0.0:
            px += step_dx
            test_rect = pygame.Rect(round(px), round(py), w, h)
            hit_indices = test_rect.collidelistall(cols)
            if hit_indices:
                hit_cols = [cols[i] for i in hit_indices]

                if step_dx > 0:
                    px = float(min(c.left for c in hit_cols) - w)
                    blocked_faces["right"] = True
                else:
                    px = float(max(c.right for c in hit_cols))
                    blocked_faces["left"] = True

                dx = 0.0
                step_dx = 0.0

        if step_dy != 0.0:
            py += step_dy
            test_rect = pygame.Rect(round(px), round(py), w, h)
            hit_indices = test_rect.collidelistall(cols)
            if hit_indices:
                hit_cols = [cols[i] for i in hit_indices]

                if step_dy > 0:
                    py = float(min(c.top for c in hit_cols) - h)
                    blocked_faces["bottom"] = True
                else:
                    py = float(max(c.bottom for c in hit_cols))
                    blocked_faces["top"] = True

                dy = 0.0
                step_dy = 0.0

    return round(px), round(py), dx, dy, blocked_faces

class uiMan:
    _boldf = pygame.Font(FONT_PATH, 500)
    _boldf.set_bold(True)
    fonts = [pygame.Font(FONT_PATH, 500), _boldf]
    class box:
        def renderfont(self, x, y, text, color, size, transp, isbold):
            font = uiMan.fonts[int(isbold)]
            font = font.render(text, False, color)
            font.set_alpha(transp)
            screen.blit(pygame.transform.scale_by(font,size*0.002), (x,y))
        def __init__(self, x, y, design="text", designhelp={"text":'This is test text!', "size":30, "transp":255, "color":(128,128,128), "isbold":False}, curframe=0, size=1):
            self.x = x
            self.y = y
            self.design = design
            self.designhelp = designhelp
            self.curframe = curframe
            self.size = size
        def draw(self):
            if self.design == "text":
                self.renderfont(self.x, self.y, self.designhelp['text'], self.designhelp['color'], self.designhelp['size'], self.designhelp['transp'], self.designhelp['isbold'])
            elif self.design == "texture":
                frames = textures[self.designhelp['texture_name']]
                screen.blit(pygame.transform.scale_by(frames[self.curframe % len(frames)], self.size), (self.x, self.y))
    def nextdraw(self):
        for a in self.objects.values():
            a.draw()
        pass # 나중에
    def is_hover(self, name):
        obj = self.objects[name]
        texturesz = textures[obj.designhelp['texture_name']][obj.curframe].get_size()
        return pygame.Rect(obj.x, obj.y, texturesz[0]*obj.size, texturesz[1]*obj.size).collidepoint(pygame.mouse.get_pos())
    def __init__(self):
        self.objects =  {} # objectname, object

class objectMan: #레이어가 됨
    class box:
        def nextrect(self):
             return pygame.Rect(round(self.px + self.dx), round(self.py + self.dy), self.myrect.width, self.myrect.height)
        def __init__(self, x, y, sizex, sizey, dx=0, dy=0, hasPhysic=False, hasCollision=True, hasPhysicpp=False, hasFrict=False, hboxdesign="notexture", designhelp={"color":(255,255,255)}):
            self.myrect = newrect(x,y,sizex,sizey)
            self.dx, self.dy = dx, dy
            self.px = float(self.myrect.x)
            self.py = float(self.myrect.y)
            self.size = [sizex, sizey]
            self.hboxdesign = hboxdesign
            self.designhelp = designhelp
            self.cur_frame = 0
            self.flipx = False
            self.flipy = False
            self.hasPhysic = hasPhysic
            self.hasFrict = hasFrict
            self.frictInY = False
            self.slipper = 1.08
            self.airslipper = 1.035
            self.hasCollision = hasCollision
            self.hasPhysicpp = hasPhysicpp
            self.blocked_faces = {"top": False, "bottom": False, "left": False, "right": False}
            if hasPhysicpp:
                self.endx = 0
                self.endy = 0
        def draw(self):
            whatishoulddo = moveit(zoomit(self.myrect),mx=-camera[0]+WIDTH//2, my=-camera[1]+HEIGHT//2)
            if self.hboxdesign == 'notexture':
                pygame.draw.rect(screen, self.designhelp["color"], whatishoulddo, 0)
            elif self.hboxdesign == 'texture':
                texture = textures[self.designhelp["texture_name"]]
                texture = pygame.transform.scale(texture[self.cur_frame%len(texture)], self.size)
                texture = pygame.transform.flip(texture, self.flipx, self.flipy)
                screen.blit(texture, whatishoulddo)
        def IcolU_upd(self, objlist): # 제미나이가 쥰내 뭐시기
            self.blocked_faces = {"top": False, "bottom": False, "left": False, "right": False}
            boxlist = [obj.myrect for obj in objlist if obj.hasCollision and obj != self]
            if not hasattr(self, 'px'):
                self.px = float(self.myrect.x)
                self.py = float(self.myrect.y)
            elif self.myrect.x != round(self.px) or self.myrect.y != round(self.py):
                self.px = float(self.myrect.x)
                self.py = float(self.myrect.y)
            nextr = self.nextrect()
            yo = nextr.collidelistall(boxlist)
            if yo == []:
                self.px += self.dx
                self.py += self.dy
                self.myrect.x = round(self.px)
                self.myrect.y = round(self.py)
            else:
                temp_rect = pygame.Rect(round(self.px), round(self.py), self.myrect.width, self.myrect.height)
                new_x, new_y, self.dx, self.dy, self.blocked_faces = backtrc(temp_rect, self.dx, self.dy, [boxlist[col] for col in yo])
                self.px = float(new_x)
                self.py = float(new_y)
                self.myrect.x = new_x
                self.myrect.y = new_y
            if self.hasFrict:
                if self.blocked_faces['top'] or self.blocked_faces['bottom']:
                    self.dx /= self.slipper
                else: self.dx /= self.airslipper
                if self.blocked_faces['left'] or self.blocked_faces['right'] and self.frictInY:
                    self.dy /= self.slipper
                else: self.dy /= self.airslipper
        def getxy(self):
            return (self.myrect.x, self.myrect.y)

    def __init__(self):
        self.objects={} #objectID, object
    def physic(self, objlist=None):
        for obj in objlist:
            if obj.hasPhysic:
                obj.IcolU_upd(list(objlist))
                if obj.dx < 0.1 and obj.dx > -0.1:
                    obj.dx = 0
                if obj.dy < 0.1 and obj.dy > -0.1:
                    obj.dy = 0
    def morephysic(self, objlist=None):
        for obj in objlist:
            if obj.hasPhysic and obj.hasPhysicpp: # 러프, 나중에 더.
                obj.dx /= self.slowdamage
                obj.dy /= self.slowdamage
                obj.dx = obj.dx+(obj.endx-obj.myrect.x)*0.1
                obj.dy = obj.dy+(obj.endy-obj.myrect.y)*0.1
    def next(self):
        self.physic(self.objects.values())
        #for obj in self.objects.values():
        #    obj.physic()
    def render(self):
        for box in self.objects.values():
            box.draw()
    def is_hover(self, name):
        obj = self.objects[name]
        return obj.myrect.collidepoint(pygame.mouse.get_pos())
class effectMan:
    def __init__(self):
        self.effects = [] #effectID, effect
        self.layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    @staticmethod
    def rectpoly(x, y, size, rot):
        _rect = [pygame.Vector2(-size/2, -size/2), pygame.Vector2(size/2, -size/2), pygame.Vector2(size/2, size/2), pygame.Vector2(-size/2, size/2)]
        return [c.rotate(rot)+pygame.Vector2(x, y) for c in _rect]
    class effect:
        def __init__(self, x, y, size, color, duration=60, startspread=0, rotation=0, form=[0,0,-0.1,0]):
            self.x = x+random.uniform(-startspread, startspread)
            self.y = y+random.uniform(-startspread, startspread)
            self.color = color
            self.duration = duration
            self.rotation=rotation
            self.size = size
            self.form = form
            self.startduration = duration
            self.alpha = 255
        def render(self, layer):
            pygame.draw.polygon(layer, (*self.color, self.alpha), effectMan.rectpoly(self.x, self.y, self.size, self.rotation))
        def update(self):
            self.rotation += self.form[3]
            self.x += self.form[0]
            self.y += self.form[1]
            self.size += self.form[2]
            self.alpha = int(255*(self.duration/self.startduration))
            self.duration -= 1
    def new(self, amount, x, y, size, color, duration, startspread, rotation, form=[0,0,-0.1,0]):
        for _ in range(amount):
            self.effects.append(effectMan.effect(x, y, size, color, duration, startspread, rotation, form))
    def update(self):
        self.layer.fill((0,0,0,0))
        self.effects = [e for e in self.effects if e.duration > 0]
        
        for effect in self.effects:
            effect.update()
            effect.render(self.layer)


class keypool:
    def __init__(self):
        self.keystate = {}
        self.keybind_cfg = {}
        self.keybind_stat = {}
        self.mousestate = {"x":0, "y":0, "left": False, "right":False, "left_inst":False, "right_inst":False, "INSTHELP":[False,False]}
    def getkey_upd(self, eventl):
        prsd = pygame.key.get_pressed()
        for i in range(len(prsd)):
            self.keystate[i] = prsd[i]
            self.keystate["inst_"+str(i)] = None
            for event in eventl:
                if event.type == pygame.KEYDOWN:
                    self.keystate["inst_"+str(event.key)] = True
                if event.type == pygame.KEYUP:
                    self.keystate["inst_"+str(event.key)] = False
                if event.type == pygame.QUIT:
                    global RUNNING
                    RUNNING = False
        self.mousestate["left"], _ ,self.mousestate["right"]=pygame.mouse.get_pressed()
        self.mousestate["left_inst"]=self.mousestate["left"] and not self.mousestate["INSTHELP"][0]
        self.mousestate["right_inst"]=self.mousestate["right"] and not self.mousestate["INSTHELP"][1]
        self.mousestate["x"], self.mousestate["y"] = pygame.mouse.get_pos()
        self.mousestate["INSTHELP"] = [self.mousestate["left"], self.mousestate["right"]]
    def keybind_upd(self):
        for nm, keycode in self.keybind_cfg.items():
            continuous = self.keystate.get(keycode, False)
            instant = self.keystate.get("inst_" + str(keycode), None)
            self.keybind_stat[nm] = [continuous, instant]

class externalThings:
    def __init__(self):
        pass

    def swingcam(self, x, y, swr):
        camera[0] += (x-camera[0])*swr
        camera[1] += (y-camera[1])*swr
    def swizzlecam(self, x, y, xp, yp, swr):
        camera[0] = x+(xp-x)*swr
        camera[1] = y+(yp-y)*swr
    def getmousexy(self):
        mouse = pygame.mouse.get_pos()
        return (mouse[0]+camera[0]-WIDTH//2, mouse[1]+camera[1]-HEIGHT//2)
    def getmouse(self):
        return pygame.mouse.get_pos()
    def gametoscreen(self, x, y):
        return [x-camera[0]+WIDTH//2, y-camera[1]+HEIGHT//2]

# DEBUG
#maplayers = []
#effectz = effectMan()
#keypoolz = keypool()
#maplayers.append(objectMan())
#maplayers[0].objects[0] = objectMan.box(0,50,50, hasPhysic=True)
#maplayers[0].objects[0].dx = 10
#maplayers[0].objects[0].dy = 10
#maplayers[0].objects[0].designhelp = (255,0,0)
# 이스터 에그 : 만약 이걸 읽는다면, 축하! 이스터에그를 찾았다! 좋은 하루 :)
#maplayers[0].objects[1] = objectMan.box(0,100,50, hasCollision=True)
#keypoolz.keybind[pygame.K_SPACE] = False

class engine:
    def engine_startupdate(self):
        events = pygame.event.get()
        keypoolz.keybind_upd()
        keypoolz.getkey_upd(events)
    def engine_physicupdate(self):
        # update
        #for layer in globals()['maplayers']: #globals로 해. 난 몰라
        #    layer.next()
        objectmanz.next() #이게맞다

    # DEBUG
    #if keypoolz.keybind[pygame.K_SPACE][0]:
    #    maplayers[0].objects[0].dx += 3
    #    maplayers[0].objects[0].dy += 3
    #    mousepos = getmousexy()
    #    #swiggcam(mousepos[0], mousepos[1], 0.05)
    #    swizzlecam(0, 0, mousepos[0], mousepos[1], 0.1)
    #    effectz.new(5, mousepos[0]+WIDTH//2, mousepos[1]+HEIGHT//2, 5, (255,255,255), 30, 20, 0, [random.randint(-10, 10), random.randint(-10, 10),-0.1,10])
    # it fuckin works great hell yeah

    def engine_drawupdate(self):
        # drawing
        screen.fill(bgcolor)
        #for layer in globals()['maplayers']: #아냐 globals로 해 그냥 건들지말고
        #    layer.render()
        objectmanz.render()
        globals()['effectz'].update(); screen.blit(globals()['effectz'].layer, (0, 0)) #아냐 아냐 난 몰라 그냥 냅둬 좀
        globals()['uiz'].nextdraw()
        pygame.display.flip()
    def engine_endupdate(self):
        clock.tick(60)

candlelist = {}
class candleMan:
    def __init__(self):
        #redoit 불필요
        pass
    def newcandle(self, name, isinit=False):
        candlelist[name] = True
        if isinit:
            candlelist[name] = 2 # 상수의 bool화 이용, 2는 isinit 한번만
    def rmcandle(self, name):
        if name in candlelist:
            del candlelist[name]
    def togglecandle(self, name):
        if name in candlelist:
            candlelist[name] = not candlelist[name]
        else:
            candlelist[name] = True
    def runonce(self, name):
        getattr(games[name], 'do')(bun)
    def rmall(self):
        candlelist.clear()

# load game
cman = candleMan()
enginez = engine()
keypoolz = keypool()
effectz = effectMan()
objectmanz = objectMan()
externalz = externalThings()
uiz = uiMan()
import importlib
import importlib.util
games = {}
for i, a in enumerate(os.listdir(os.path.join(GAME_PATH))):
    if os.path.isfile(os.path.join(GAME_PATH,a)):
        spec = importlib.util.spec_from_file_location(os.path.splitext(a)[0], os.path.join(GAME_PATH,a))
        games[os.path.splitext(a)[0]] = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(games[os.path.splitext(a)[0]])
cman.newcandle('init1', isinit=True)

class bunz: #bun 짬때리기
    def __init__(self):
        self.states = {} # 게임 상태 공유
    def getthings(self, name): #enginez 같은거
        return globals()[name]
    def change_value(self, name, val):
        globals()[name] = val
        return val
    def get_value(self, name):
        return globals().get(name)
    def stateset(self, name, value):
        self.states[name] = value
        return value
    def stateget(self, name):
        return self.states[name]
    def rethinksay(self, text): #혹시 모르니까
        print(text)
bun = bunz()


# mainloop
while RUNNING:
    for candle in list(candlelist.keys()):
        status = candlelist.get(candle, False)
        if status:
            is_init = (status == 2)
            getattr(games[candle], 'do')(bun)
            if is_init and candle in candlelist:
                cman.rmcandle(candle)
    if RUNNING and candlelist == {}:
        print("잘못된 무한 반복에 의한 종료. 버그면 체크,", candlelist, "잘못된 무한 반복에 의한 종료!")
        RUNNING = False
        break

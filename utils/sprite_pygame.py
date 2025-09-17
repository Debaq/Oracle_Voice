import json, time, random
from pathlib import Path
import pygame

# --- Ajustes generales ---
W, H   = 1000, 720
FPS    = 60
ASSETS = Path("assets")
ATLAS  = ASSETS / "atlas.png"
CONF   = ASSETS / "atlas_config.json"

SCALE  = 3   # factor para escalar el sprite final en pantalla
BG     = (16, 16, 20)

# -------- Herramientas ----------
def surf_from_rect(big_surf, rect):
    return big_surf.subsurface(rect).copy()

def scale_nn(surf, factor):
    return pygame.transform.scale_by(surf, factor) if factor != 1 else surf

def now():
    return time.time()

# --------- Anim layer -----------
class AnimLayer:
    def __init__(self, frames=None, fps=10, loop=True):
        self.frames = frames[:] if frames else []
        self.fps = fps
        self.loop = loop
        self.playing = True
        self.t = 0.0
        self.i = 0

    @property
    def empty(self): return not self.frames

    def set_frames(self, frames):
        self.frames = frames[:]
        self.i, self.t = 0, 0

    def set_frame(self, idx):
        if self.empty: return
        self.i = max(0, min(idx, len(self.frames)-1))
        self.t = 0

    def play(self, fps=None):
        self.playing = True
        if fps is not None: self.fps = fps

    def stop(self):
        self.playing = False

    def update(self, dt):
        if self.empty or not self.playing or self.fps <= 0: return
        self.t += dt
        step = 1.0 / self.fps
        while self.t >= step:
            self.t -= step
            self.i += 1
            if self.i >= len(self.frames):
                if self.loop: self.i = 0
                else:
                    self.i = len(self.frames)-1
                    self.playing = False

    def current(self):
        if self.empty: return None
        return self.frames[self.i]

# ---------- Fortune Teller -----------
class FortuneTeller(pygame.sprite.Sprite):
    def __init__(self, atlas, config):
        super().__init__()
        self.atlas = atlas
        self.cfg   = config

        # Cargar capas desde config (listas de rects)
        self.base  = AnimLayer([surf_from_rect(atlas, pygame.Rect(r)) for r in self.cfg.get("base", [])], fps=0, loop=False)
        if self.base.empty:
            raise RuntimeError("Config: falta 'base' (al menos 1 rect).")

        self.hands = AnimLayer([surf_from_rect(atlas, pygame.Rect(r)) for r in self.cfg.get("hands", [])], fps=10, loop=True)
        self.eyes  = AnimLayer([surf_from_rect(atlas, pygame.Rect(r)) for r in self.cfg.get("eyes",  [])], fps=0,  loop=False)
        self.mouth = AnimLayer([surf_from_rect(atlas, pygame.Rect(r)) for r in self.cfg.get("mouths",[])], fps=12, loop=True)
        self.mouth.stop()
        self.glow  = AnimLayer([surf_from_rect(atlas, pygame.Rect(r)) for r in self.cfg.get("glow",  [])], fps=7,  loop=True)

        # offsets (para alinear cada capa sobre la base)
        # en el JSON puedes guardar offsets por capa si tu atlas no está ya alineado
        self.offsets = self.cfg.get("offsets", {
            "hands": [0,0], "eyes":[0,0], "mouths":[0,0], "glow":[0,0]
        })

        # timers
        self.parp_next  = random.uniform(2.8, 5.5)
        self.parp_timer = 0.0
        self._blink_seq = None

        self.speaking = False
        self.speech_end_t = 0.0

        # imagen compuesta inicial
        self.image = self.compose(scale=SCALE)
        self.rect  = self.image.get_rect(center=(W//2, H//2+80))

    # --- acciones ---
    def blink_now(self):
        if self.eyes.empty: return
        self._blink_seq = [0,1,2,1,0] if len(self.eyes.frames) >= 3 else [0,0]
        self._blink_i = 0
        self._blink_step = 0.06
        self._blink_t = 0.0

    def speak_for(self, seconds):
        if self.mouth.empty: return
        self.speaking = True
        self.mouth.play()
        self.speech_end_t = now() + seconds

    def speak_text(self, text, wpm=150):
        words = max(1, len(text.split()))
        self.speak_for(words * (60.0 / wpm))

    # --- ciclo ---
    def update(self, dt):
        self.hands.update(dt)
        self.glow.update(dt)

        # Parpadeo aleatorio
        self.parp_timer += dt
        if self._blink_seq:
            self._blink_t += dt
            if self._blink_t >= self._blink_step:
                self._blink_t = 0
                self._blink_i += 1
                if self._blink_i >= len(self._blink_seq):
                    self._blink_seq = None
                    self.eyes.set_frame(0)
                else:
                    self.eyes.set_frame(self._blink_seq[self._blink_i])
        elif self.parp_timer >= self.parp_next:
            self.parp_timer = 0
            self.parp_next = random.uniform(3.0, 6.0)
            self.blink_now()

        # Habla
        if self.speaking and now() >= self.speech_end_t:
            self.speaking = False
            self.mouth.stop()
            self.mouth.set_frame(0)
        if self.speaking:
            self.mouth.update(dt)

        self.image = self.compose(scale=SCALE)

    def compose(self, scale=1):
        base = self.base.current().copy()
        # superponer en orden: glow, hands, eyes, mouth
        if not self.glow.empty:
            base.blit(self.glow.current(), self.offsets.get("glow", [0,0]))
        if not self.hands.empty:
            base.blit(self.hands.current(), self.offsets.get("hands",[0,0]))
        if not self.eyes.empty:
            base.blit(self.eyes.current(),  self.offsets.get("eyes", [0,0]))
        if not self.mouth.empty:
            base.blit(self.mouth.current(), self.offsets.get("mouths",[0,0]))
        return scale_nn(base, scale)

# --------- Marcador de rects (click-drag) ----------
class RectMarker:
    LAYERS = ["base","hands","eyes","mouths","glow"]
    HELP = [
        "MODO MARCADO: Click y arrastra para crear rects.",
        "Teclas: 1=base  2=hands  3=eyes  4=mouths  5=glow",
        "Z deshacer, C limpiar capa, S guardar JSON, ENTER probar animación",
        "F flechas para mover último rect 1px (Shift=10px)",
        "Esc para salir."
    ]
    def __init__(self, atlas, config_path):
        self.atlas = atlas
        self.path  = config_path
        self.data  = {"base":[], "hands":[], "eyes":[], "mouths":[], "glow":[],
                      "offsets":{"hands":[0,0],"eyes":[0,0],"mouths":[0,0],"glow":[0,0]}}
        if self.path.exists():
            try:
                self.data.update(json.loads(self.path.read_text()))
            except Exception:
                pass
        self.layer = "base"
        self.dragging = False
        self.r0 = None
        self.last_rect = None
        self.font = pygame.font.SysFont("consolas", 16)

    def handle_event(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            self.dragging = True
            self.r0 = e.pos
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1 and self.dragging:
            self.dragging = False
            x0,y0 = self.r0; x1,y1 = e.pos
            x,y = min(x0,x1), min(y0,y1)
            w,h = abs(x1-x0), abs(y1-y0)
            if w>2 and h>2:
                rect = [x,y,w,h]
                self.data[self.layer].append(rect)
                self.last_rect = rect
        elif e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_1,pygame.K_KP1): self.layer="base"
            if e.key in (pygame.K_2,pygame.K_KP2): self.layer="hands"
            if e.key in (pygame.K_3,pygame.K_KP3): self.layer="eyes"
            if e.key in (pygame.K_4,pygame.K_KP4): self.layer="mouths"
            if e.key in (pygame.K_5,pygame.K_KP5): self.layer="glow"
            if e.key == pygame.K_z:  # deshacer
                if self.data[self.layer]: self.last_rect = self.data[self.layer].pop()
            if e.key == pygame.K_c:  # limpiar capa
                self.data[self.layer] = []
            if e.key == pygame.K_s:  # guardar
                self.path.write_text(json.dumps(self.data, indent=2))
                print("Guardado:", self.path)
            if e.key == pygame.K_f and self.last_rect:
                # nudge con flechas
                k = pygame.key.get_pressed()
                step = 10 if k[pygame.K_LSHIFT] or k[pygame.K_RSHIFT] else 1
                if k[pygame.K_LEFT]:  self.last_rect[0]-=step
                if k[pygame.K_RIGHT]: self.last_rect[0]+=step
                if k[pygame.K_UP]:    self.last_rect[1]-=step
                if k[pygame.K_DOWN]:  self.last_rect[1]+=step

    def draw(self, screen):
        screen.fill((10,10,12))
        screen.blit(self.atlas, (0,0))
        # rect en arrastre
        if self.dragging:
            x0,y0 = self.r0; x1,y1 = pygame.mouse.get_pos()
            x,y = min(x0,x1), min(y0,y1)
            w,h = abs(x1-x0), abs(y1-y0)
            pygame.draw.rect(screen, (200,230,50), (x,y,w,h), 1)

        # dibujar todos
        colors = {
            "base":(255,180,0),"hands":(0,220,255),"eyes":(120,255,120),
            "mouths":(255,120,180),"glow":(200,200,255)
        }
        for k,rects in self.data.items():
            if k=="offsets": continue
            col = colors[k]
            for r in rects:
                pygame.draw.rect(screen, col, pygame.Rect(r), 1)

        # HUD
        y = 8
        for line in self.HELP:
            img = self.font.render(line, True, (230,230,230))
            screen.blit(img, (8,y)); y += 18
        screen.blit(self.font.render(f"Capa actual: {self.layer}", True, (250,210,100)), (8,y))

# ------------- main -------------
def load_config():
    if CONF.exists():
        try:
            return json.loads(CONF.read_text())
        except Exception:
            pass
    return None

def main():
    pygame.init()
    screen = pygame.display.set_mode((W,H))
    clock  = pygame.time.Clock()

    atlas = pygame.image.load(str(ATLAS)).convert_alpha()
    mode  = "mark" if not CONF.exists() else "play"  # si no hay config, empezamos marcando

    marker = RectMarker(atlas, CONF)

    # si ya hay config, creamos sprite
    ft = None
    if mode=="play":
        cfg = load_config()
        ft = FortuneTeller(atlas, cfg)
        group = pygame.sprite.GroupSingle(ft)

    running = True
    while running:
        dt = clock.tick(FPS)/1000.0
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            if mode=="mark":
                marker.handle_event(e)
                if e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN:
                    # intentar pasar a play
                    marker.path.write_text(json.dumps(marker.data, indent=2))
                    try:
                        ft = FortuneTeller(atlas, marker.data)
                        group = pygame.sprite.GroupSingle(ft)
                        mode = "play"
                    except Exception as ex:
                        print("Config incompleta:", ex)
            else:
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_SPACE:
                        ft.speak_text("Bienvenido, veo tu destino...", wpm=150)
                    if e.key == pygame.K_b:
                        ft.blink_now()
                    if e.key == pygame.K_TAB:
                        # volver a marcar
                        mode="mark"
                        marker = RectMarker(atlas, CONF)

        if mode=="mark":
            marker.draw(screen)
        else:
            group.update(dt)
            screen.fill(BG)
            group.draw(screen)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()

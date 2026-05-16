#!/usr/bin/env python3
"""
SPACE R-TYPE INVADERS
Un juego estilo Space Invaders con enemigos de R-Type
10 niveles con dificultad progresiva y jefe final: El Pulpo Espacial Gigante
Compatible con Batocera (gamepad + teclado)
Requiere: pip install pygame
"""

import pygame
import sys
import math
import random
import time

pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

# ─── CONFIGURACIÓN ────────────────────────────────────────────────────────────
WIDTH, HEIGHT = 800, 600
FPS = 60
TITLE = "SPACE R-TYPE INVADERS"

# Colores
BLACK       = (0,   0,   0)
WHITE       = (255, 255, 255)
CYAN        = (0,   255, 255)
RED         = (255, 50,  50)
GREEN       = (50,  255, 100)
YELLOW      = (255, 220, 0)
ORANGE      = (255, 150, 0)
PURPLE      = (180, 0,   255)
MAGENTA     = (255, 0,   180)
DARK_BLUE   = (5,   5,   30)
NEON_BLUE   = (30,  100, 255)
DARK_CYAN   = (0,   80,  100)
PINK        = (255, 100, 200)
LIME        = (100, 255, 50)
TEAL        = (0,   200, 180)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(TITLE)
clock = pygame.time.Clock()

# ─── SONIDOS PROCEDURALES ─────────────────────────────────────────────────────
def make_sound(freq_start, freq_end, duration_ms, volume=0.4, wave='square'):
    sample_rate = 22050
    n_samples = int(sample_rate * duration_ms / 1000)
    buf = []
    for i in range(n_samples):
        t = i / sample_rate
        freq = freq_start + (freq_end - freq_start) * (i / n_samples)
        if wave == 'square':
            val = 1 if math.sin(2 * math.pi * freq * t) > 0 else -1
        elif wave == 'noise':
            val = random.uniform(-1, 1)
        else:
            val = math.sin(2 * math.pi * freq * t)
        buf.append(int(val * 32767 * volume))
    sound_array = pygame.sndarray.make_sound(
        pygame.array.array('h', buf) if hasattr(pygame, 'array')
        else __import__('array').array('h', buf)
    )
    return sound_array

import array as _array

def make_sound_raw(freq_start, freq_end, duration_ms, volume=0.4, wave='square'):
    sample_rate = 22050
    n_samples = int(sample_rate * duration_ms / 1000)
    buf = _array.array('h', [0] * n_samples)
    for i in range(n_samples):
        t = i / sample_rate
        freq = freq_start + (freq_end - freq_start) * (i / n_samples)
        if wave == 'square':
            val = 1.0 if math.sin(2 * math.pi * freq * t) > 0 else -1.0
        elif wave == 'noise':
            val = random.uniform(-1, 1)
        else:
            val = math.sin(2 * math.pi * freq * t)
        buf[i] = max(-32767, min(32767, int(val * 32767 * volume)))
    stereo = _array.array('h', [0] * (n_samples * 2))
    for i in range(n_samples):
        stereo[i*2]   = buf[i]
        stereo[i*2+1] = buf[i]
    try:
        snd = pygame.sndarray.make_sound(__import__('numpy').array(stereo, dtype='int16').reshape(-1,2))
        return snd
    except Exception:
        pass
    return None

# Generamos sonidos básicos
SFX = {}
try:
    import numpy as np

    def gen(f0, f1, dur, vol=0.4, wave='sq'):
        sr = 22050
        n = int(sr * dur / 1000)
        t = np.linspace(0, dur/1000, n)
        freq = np.linspace(f0, f1, n)
        phase = np.cumsum(2 * np.pi * freq / sr)
        if wave == 'sq':
            s = np.sign(np.sin(phase))
        elif wave == 'noise':
            s = np.random.uniform(-1, 1, n)
        else:
            s = np.sin(phase)
        s = (s * 32767 * vol).astype(np.int16)
        stereo = np.column_stack([s, s])
        return pygame.sndarray.make_sound(stereo)

    SFX['shoot']    = gen(800, 400,  80, 0.3, 'sq')
    SFX['explode']  = gen(200, 50,  300, 0.5, 'noise')
    SFX['hit']      = gen(300, 100, 120, 0.4, 'sq')
    SFX['powerup']  = gen(400, 900, 200, 0.4, 'sine')
    SFX['boss']     = gen(100, 60,  500, 0.5, 'sq')
    SFX['level']    = gen(440, 880, 400, 0.4, 'sine')
    SFX['player_hit']= gen(150, 50,  400, 0.5, 'noise')
except Exception:
    pass  # Sin numpy: el juego funciona igual pero sin sonido

# ─── FUENTES ──────────────────────────────────────────────────────────────────
try:
    FONT_BIG   = pygame.font.SysFont('couriernew', 48, bold=True)
    FONT_MED   = pygame.font.SysFont('couriernew', 28, bold=True)
    FONT_SML   = pygame.font.SysFont('couriernew', 18)
    FONT_TINY  = pygame.font.SysFont('couriernew', 14)
except:
    FONT_BIG   = pygame.font.Font(None, 56)
    FONT_MED   = pygame.font.Font(None, 34)
    FONT_SML   = pygame.font.Font(None, 22)
    FONT_TINY  = pygame.font.Font(None, 18)

# ─── ESTRELLAS DE FONDO ───────────────────────────────────────────────────────
class Star:
    def __init__(self):
        self.reset()
    def reset(self):
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(0, HEIGHT)
        self.speed = random.uniform(0.5, 3)
        self.size  = random.randint(1, 3)
        self.brightness = random.randint(80, 255)
    def update(self):
        self.x -= self.speed
        if self.x < 0:
            self.x = WIDTH
            self.y = random.randint(0, HEIGHT)
    def draw(self, surf):
        c = (self.brightness,)*3
        if self.size > 1:
            pygame.draw.circle(surf, c, (int(self.x), int(self.y)), self.size//2)
        else:
            surf.set_at((int(self.x), int(self.y)), c)

STARS = [Star() for _ in range(200)]

# ─── PARTÍCULAS ───────────────────────────────────────────────────────────────
particles = []

def spawn_explosion(x, y, color, count=20, speed=3):
    for _ in range(count):
        angle = random.uniform(0, 2*math.pi)
        spd   = random.uniform(0.5, speed)
        particles.append({
            'x': x, 'y': y,
            'vx': math.cos(angle)*spd,
            'vy': math.sin(angle)*spd,
            'life': random.randint(20, 50),
            'max_life': 50,
            'color': color,
            'size': random.randint(2, 5)
        })

def update_particles():
    for p in particles[:]:
        p['x'] += p['vx']
        p['y'] += p['vy']
        p['life'] -= 1
        if p['life'] <= 0:
            particles.remove(p)

def draw_particles(surf):
    for p in particles:
        alpha = p['life'] / p['max_life']
        c = tuple(int(ch * alpha) for ch in p['color'])
        pygame.draw.circle(surf, c, (int(p['x']), int(p['y'])), max(1, p['size']))

# ─── PROYECTILES ─────────────────────────────────────────────────────────────
class Bullet:
    def __init__(self, x, y, vx, vy, color, damage=1, size=4, owner='player'):
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = vx, vy
        self.color  = color
        self.damage = damage
        self.size   = size
        self.owner  = owner
        self.alive  = True
    def update(self):
        self.x += self.vx
        self.y += self.vy
        if self.x < -20 or self.x > WIDTH+20 or self.y < -20 or self.y > HEIGHT+20:
            self.alive = False
    def draw(self, surf):
        if self.owner == 'player':
            # Bala del jugador: rayo horizontal con brillo
            pygame.draw.rect(surf, self.color, (int(self.x)-8, int(self.y)-2, 16, 4))
            pygame.draw.rect(surf, WHITE, (int(self.x)-6, int(self.y)-1, 12, 2))
        else:
            # Bala enemiga
            pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), self.size)
            inner = tuple(min(255, c+100) for c in self.color)
            pygame.draw.circle(surf, inner, (int(self.x), int(self.y)), max(1, self.size-2))
    def get_rect(self):
        return pygame.Rect(int(self.x)-self.size, int(self.y)-self.size,
                           self.size*2, self.size*2)

# ─── NAVE DEL JUGADOR ────────────────────────────────────────────────────────
class Player:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x = 100.0
        self.y = HEIGHT // 2
        self.w, self.h = 48, 24
        self.speed = 5
        self.hp = 3
        self.max_hp = 3
        self.score = 0
        self.level  = 1
        self.bullets = []
        self.shoot_cooldown = 0
        self.invincible = 0
        self.power_level = 1   # 1=normal, 2=doble, 3=triple
        self.shield = 0

    def handle_input(self, keys, joystick=None):
        dx, dy = 0, 0
        # Teclado
        if keys[pygame.K_UP]    or keys[pygame.K_w]: dy = -1
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: dy =  1
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: dx = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx =  1
        shoot = keys[pygame.K_SPACE] or keys[pygame.K_z] or keys[pygame.K_x]

        # Gamepad (Batocera)
        if joystick:
            ax = joystick.get_axis(0)
            ay = joystick.get_axis(1)
            if abs(ax) > 0.2: dx = ax
            if abs(ay) > 0.2: dy = ay
            if joystick.get_button(0) or joystick.get_button(1):
                shoot = True
            # D-pad
            hat = joystick.get_hat(0) if joystick.get_numhats() > 0 else (0,0)
            if hat[0] != 0: dx = hat[0]
            if hat[1] != 0: dy = -hat[1]

        # Mover
        spd = self.speed
        self.x += dx * spd
        self.y += dy * spd
        self.x = max(self.w//2, min(WIDTH//2, self.x))
        self.y = max(self.h//2, min(HEIGHT - self.h//2, self.y))

        # Disparar
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        if shoot and self.shoot_cooldown == 0:
            self._fire()
            self.shoot_cooldown = max(5, 12 - self.power_level * 2)

        # Timers
        if self.invincible > 0: self.invincible -= 1
        if self.shield > 0:     self.shield     -= 1

    def _fire(self):
        play_sfx('shoot')
        if self.power_level == 1:
            self.bullets.append(Bullet(self.x+24, self.y, 14, 0, CYAN, 1, 4, 'player'))
        elif self.power_level == 2:
            self.bullets.append(Bullet(self.x+24, self.y-5, 14, 0, CYAN, 1, 4, 'player'))
            self.bullets.append(Bullet(self.x+24, self.y+5, 14, 0, CYAN, 1, 4, 'player'))
        else:
            self.bullets.append(Bullet(self.x+24, self.y,   14,  0,    CYAN,  1, 4, 'player'))
            self.bullets.append(Bullet(self.x+24, self.y-8, 13,  -0.5, GREEN, 1, 4, 'player'))
            self.bullets.append(Bullet(self.x+24, self.y+8, 13,   0.5, GREEN, 1, 4, 'player'))

    def take_damage(self, dmg=1):
        if self.invincible > 0: return False
        if self.shield > 0:
            self.shield = 0
            self.invincible = 60
            play_sfx('hit')
            return False
        self.hp -= dmg
        self.invincible = 90
        play_sfx('player_hit')
        spawn_explosion(self.x, self.y, RED, 30, 4)
        return True

    def get_rect(self):
        return pygame.Rect(int(self.x)-self.w//2, int(self.y)-self.h//2, self.w, self.h)

    def draw(self, surf):
        blink = self.invincible > 0 and (self.invincible // 5) % 2 == 0
        if blink:
            return

        cx, cy = int(self.x), int(self.y)

        # Propulsores
        flame_len = random.randint(8, 16)
        pygame.draw.polygon(surf, ORANGE, [
            (cx-22, cy-4), (cx-22-flame_len, cy), (cx-22, cy+4)
        ])
        pygame.draw.polygon(surf, YELLOW, [
            (cx-22, cy-2), (cx-22-flame_len//2, cy), (cx-22, cy+2)
        ])

        # Cuerpo principal (estilo R-Type)
        pygame.draw.polygon(surf, NEON_BLUE, [
            (cx+24, cy),
            (cx+10, cy-10),
            (cx-22, cy-12),
            (cx-24, cy),
            (cx-22, cy+12),
            (cx+10, cy+10),
        ])
        # Cabina
        pygame.draw.ellipse(surf, CYAN, (cx-5, cy-6, 20, 12))
        pygame.draw.ellipse(surf, WHITE, (cx-2, cy-4, 14, 8))

        # Alas
        pygame.draw.polygon(surf, TEAL, [
            (cx-5, cy-10), (cx-18, cy-20), (cx-20, cy-10)
        ])
        pygame.draw.polygon(surf, TEAL, [
            (cx-5, cy+10), (cx-18, cy+20), (cx-20, cy+10)
        ])

        # Cañón
        pygame.draw.rect(surf, GREEN, (cx+10, cy-2, 14, 4))

        # Escudo
        if self.shield > 0:
            alpha = int(150 * (self.shield / 300))
            r = max(28, 36 - (300 - self.shield)//10)
            pygame.draw.circle(surf, (*CYAN, alpha), (cx, cy), r, 3)

    def update_bullets(self):
        for b in self.bullets[:]:
            b.update()
            if not b.alive:
                self.bullets.remove(b)

# ─── ENEMIGOS ────────────────────────────────────────────────────────────────

class Enemy:
    """Base de todos los enemigos"""
    def __init__(self, x, y, hp, score_val):
        self.x, self.y = float(x), float(y)
        self.hp     = hp
        self.max_hp = hp
        self.score_val = score_val
        self.alive  = True
        self.bullets = []
        self.shoot_timer = random.randint(60, 180)
        self.t = 0  # tiempo interno

    def update(self, player_x, player_y, level):
        self.t += 1
        self._move(player_x, player_y, level)
        self._shoot_logic(player_x, player_y, level)
        for b in self.bullets[:]:
            b.update()
            if not b.alive:
                self.bullets.remove(b)

    def _move(self, px, py, level): pass
    def _shoot_logic(self, px, py, level): pass

    def take_damage(self, dmg=1):
        self.hp -= dmg
        if self.hp <= 0:
            self.alive = False
            spawn_explosion(self.x, self.y, RED, 25, 4)
            play_sfx('explode')
            return True
        spawn_explosion(self.x, self.y, ORANGE, 8, 2)
        play_sfx('hit')
        return False

    def get_rect(self):
        return pygame.Rect(int(self.x)-16, int(self.y)-16, 32, 32)

    def _shoot_toward(self, px, py, speed=4, color=RED, size=5):
        dx = px - self.x
        dy = py - self.y
        dist = math.hypot(dx, dy) or 1
        self.bullets.append(Bullet(self.x, self.y,
                                   dx/dist*speed, dy/dist*speed,
                                   color, 1, size, 'enemy'))

    def draw(self, surf): pass


class GruntShip(Enemy):
    """Nave básica tipo Bydo - orbita y dispara"""
    def __init__(self, x, y, level=1):
        hp = 1 + level // 3
        super().__init__(x, y, hp, 100 + level*10)
        self.base_y = y
        self.amplitude = random.uniform(20, 50)
        self.freq      = random.uniform(0.03, 0.06)
        self.speed_x   = -(1.5 + level * 0.2)

    def _move(self, px, py, level):
        self.x += self.speed_x
        self.y = self.base_y + math.sin(self.t * self.freq) * self.amplitude
        if self.x < -50: self.alive = False

    def _shoot_logic(self, px, py, level):
        self.shoot_timer -= 1
        if self.shoot_timer <= 0:
            spd = 3 + level * 0.3
            self._shoot_toward(px, py, spd, RED, 5)
            self.shoot_timer = max(40, 100 - level*5)

    def draw(self, surf):
        cx, cy = int(self.x), int(self.y)
        # Cuerpo tipo medusa/Bydo
        hp_ratio = self.hp / self.max_hp
        body_color = (int(200*hp_ratio), int(50*(1-hp_ratio)), int(150+50*hp_ratio))
        pygame.draw.ellipse(surf, body_color, (cx-14, cy-10, 28, 20))
        # Ojo
        pygame.draw.circle(surf, RED, (cx, cy), 6)
        pygame.draw.circle(surf, YELLOW, (cx, cy), 3)
        # Tentáculos
        for i in range(4):
            angle = self.t * 0.05 + i * math.pi/2
            tx = cx + math.cos(angle)*10
            ty = cy + math.sin(angle)*7 + 10
            pygame.draw.line(surf, MAGENTA, (cx, cy+8), (int(tx), int(ty+8)), 2)


class FighterShip(Enemy):
    """Caza de alta velocidad estilo R-Type"""
    def __init__(self, x, y, level=1):
        hp = 2 + level // 2
        super().__init__(x, y, hp, 200 + level*20)
        self.base_y  = y
        self.phase   = random.uniform(0, math.pi*2)
        self.speed_x = -(2.5 + level * 0.3)
        self.dive_mode = False
        self.dive_target_y = y

    def _move(self, px, py, level):
        if not self.dive_mode:
            self.x += self.speed_x
            self.y = self.base_y + math.sin(self.t*0.04 + self.phase)*40
            if self.x < WIDTH//2 and random.random() < 0.005:
                self.dive_mode = True
                self.dive_target_y = py
        else:
            # Se abalanza hacia el jugador
            dy = self.dive_target_y - self.y
            self.y += dy * 0.06
            self.x -= 4 + level*0.3
        if self.x < -60: self.alive = False

    def _shoot_logic(self, px, py, level):
        self.shoot_timer -= 1
        if self.shoot_timer <= 0:
            spd = 4 + level * 0.4
            self._shoot_toward(px, py, spd, ORANGE, 4)
            if level >= 5:
                self._shoot_toward(px, py+20, spd, ORANGE, 4)
                self._shoot_toward(px, py-20, spd, ORANGE, 4)
            self.shoot_timer = max(30, 80 - level*4)

    def draw(self, surf):
        cx, cy = int(self.x), int(self.y)
        # Nave de caza angular
        pygame.draw.polygon(surf, ORANGE, [
            (cx+16, cy),
            (cx-8,  cy-12),
            (cx-16, cy-8),
            (cx-12, cy),
            (cx-16, cy+8),
            (cx-8,  cy+12),
        ])
        pygame.draw.polygon(surf, YELLOW, [
            (cx+12, cy), (cx-4, cy-6), (cx-8, cy), (cx-4, cy+6)
        ])
        # Cañones
        pygame.draw.rect(surf, RED, (cx+10, cy-2, 8, 4))
        # Propulsor
        flame = random.randint(4, 10)
        pygame.draw.polygon(surf, CYAN, [
            (cx-16, cy-4), (cx-16-flame, cy), (cx-16, cy+4)
        ])


class BomberShip(Enemy):
    """Bombardero pesado que deja minas"""
    def __init__(self, x, y, level=1):
        hp = 4 + level
        super().__init__(x, y, hp, 350 + level*30)
        self.speed_x = -(1 + level * 0.15)
        self.drop_timer = 90

    def _move(self, px, py, level):
        self.x += self.speed_x
        self.y += math.sin(self.t * 0.02) * 0.5
        if self.x < -70: self.alive = False

    def _shoot_logic(self, px, py, level):
        self.shoot_timer -= 1
        self.drop_timer  -= 1
        if self.shoot_timer <= 0:
            # Disparo frontal pesado
            self.bullets.append(Bullet(self.x-20, self.y, -5, 0, PURPLE, 2, 7, 'enemy'))
            self.shoot_timer = max(50, 100 - level*5)
        if self.drop_timer <= 0:
            # Mina hacia abajo
            self.bullets.append(Bullet(self.x, self.y, -1, 3, MAGENTA, 1, 6, 'enemy'))
            self.bullets.append(Bullet(self.x, self.y, -1, -3, MAGENTA, 1, 6, 'enemy'))
            self.drop_timer = 80

    def draw(self, surf):
        cx, cy = int(self.x), int(self.y)
        # Cuerpo grande y pesado
        pygame.draw.ellipse(surf, PURPLE, (cx-20, cy-14, 40, 28))
        pygame.draw.ellipse(surf, MAGENTA, (cx-14, cy-8, 28, 16))
        # Cañones
        for dy in [-10, 0, 10]:
            pygame.draw.rect(surf, RED, (cx-20, cy+dy-2, 8, 4))
        # Motor
        pygame.draw.rect(surf, CYAN, (cx+15, cy-5, 8, 10))


class SwarmShip(Enemy):
    """Nave de enjambre: viene en grupo zigzagueando"""
    def __init__(self, x, y, level=1):
        super().__init__(x, y, 1, 80 + level*8)
        self.base_y  = y
        self.speed_x = -(3 + level * 0.4)
        self.phase   = random.uniform(0, math.pi*2)
        self.zigzag  = random.choice([-1, 1])

    def _move(self, px, py, level):
        self.x += self.speed_x
        self.y  = self.base_y + math.sin(self.t * 0.08 + self.phase) * 30 * self.zigzag
        if self.x < -30: self.alive = False

    def _shoot_logic(self, px, py, level):
        self.shoot_timer -= 1
        if self.shoot_timer <= 0 and random.random() < 0.3:
            self._shoot_toward(px, py, 3+level*0.2, LIME, 4)
            self.shoot_timer = max(60, 120 - level*6)

    def draw(self, surf):
        cx, cy = int(self.x), int(self.y)
        angle = self.t * 0.1
        # Pequeña nave de enjambre triangular
        pts = [
            (cx + math.cos(angle)*14,    cy + math.sin(angle)*8),
            (cx + math.cos(angle+2.3)*14, cy + math.sin(angle+2.3)*8),
            (cx + math.cos(angle+4.6)*14, cy + math.sin(angle+4.6)*8),
        ]
        pygame.draw.polygon(surf, LIME, [(int(p[0]), int(p[1])) for p in pts])
        pygame.draw.circle(surf, WHITE, (cx, cy), 4)


class CommandShip(Enemy):
    """Nave de mando de nivel medio - más resistente"""
    def __init__(self, x, y, level=1):
        hp = 8 + level * 2
        super().__init__(x, y, hp, 500 + level*50)
        self.speed_x = -(1 + level*0.1)
        self.orbit_y = y
        self.phase   = 0

    def _move(self, px, py, level):
        self.x += self.speed_x
        self.phase += 0.02
        self.y = self.orbit_y + math.sin(self.phase) * 60
        if self.x < -80: self.alive = False

    def _shoot_logic(self, px, py, level):
        self.shoot_timer -= 1
        if self.shoot_timer <= 0:
            # Ráfaga de 3
            for ang in [-0.2, 0, 0.2]:
                dx = math.cos(ang) * -(4 + level*0.3)
                dy = math.sin(ang) * (4 + level*0.3)
                self.bullets.append(Bullet(self.x-20, self.y, dx, dy, CYAN, 2, 6, 'enemy'))
            self.shoot_timer = max(40, 80 - level*4)

    def draw(self, surf):
        cx, cy = int(self.x), int(self.y)
        hp_r = self.hp / self.max_hp
        col = (int(50+100*hp_r), int(100*hp_r), int(200*hp_r))
        pygame.draw.polygon(surf, col, [
            (cx+24, cy), (cx+10, cy-18), (cx-20, cy-20),
            (cx-24, cy), (cx-20, cy+20), (cx+10, cy+18)
        ])
        pygame.draw.circle(surf, RED, (cx, cy), 10)
        pygame.draw.circle(surf, ORANGE, (cx, cy), 6)
        # Antenas
        pygame.draw.line(surf, CYAN, (cx, cy-18), (cx-10, cy-32), 2)
        pygame.draw.line(surf, CYAN, (cx, cy-18), (cx+10, cy-32), 2)
        pygame.draw.circle(surf, YELLOW, (cx-10, cy-32), 3)
        pygame.draw.circle(surf, YELLOW, (cx+10, cy-32), 3)


# ─── JEFE FINAL: EL PULPO ESPACIAL ───────────────────────────────────────────

class OctopusBoss:
    """El Pulpo Espacial Gigante - Jefe del Nivel 10"""
    def __init__(self):
        self.x = WIDTH + 100.0
        self.y = HEIGHT // 2
        self.hp = 500
        self.max_hp = 500
        self.alive  = True
        self.phase  = 0   # 0=entrando, 1=combate, 2=rabia (hp<50%)
        self.t      = 0
        self.bullets = []
        self.tentacles = []  # [(angle, length, angle_offset)]
        for i in range(8):
            self.tentacles.append({
                'base_angle': (i / 8) * math.pi * 2,
                'wave': random.uniform(0, math.pi),
                'len': random.uniform(80, 120),
            })
        self.shoot_timer = 120
        self.ray_timer   = 300
        self.ray_active  = False
        self.ray_angle   = 0
        self.ray_duration = 0
        self.spawn_timer = 400
        self.intro_done  = False

    def update(self, player_x, player_y, level):
        self.t += 1

        # Entrada
        if self.x > WIDTH - 200:
            self.x -= 2
            return

        self.phase = 1 if self.hp > self.max_hp * 0.5 else 2

        # Movimiento del cuerpo
        speed_mult = 1.5 if self.phase == 2 else 1.0
        target_y = player_y + math.sin(self.t * 0.02) * 80
        self.y += (target_y - self.y) * 0.02 * speed_mult
        self.x += math.sin(self.t * 0.015) * 0.5

        # Disparos normales
        self.shoot_timer -= 1
        if self.shoot_timer <= 0:
            self._spread_shot(player_x, player_y)
            self.shoot_timer = 50 if self.phase == 2 else 80

        # RAYO ESPECIAL
        self.ray_timer -= 1
        if self.ray_timer <= 0 and not self.ray_active:
            self.ray_active   = True
            self.ray_angle    = math.atan2(player_y - self.y, player_x - self.x)
            self.ray_duration = 120 if self.phase == 1 else 180
            self.ray_timer    = 250 if self.phase == 2 else 350
            play_sfx('boss')

        if self.ray_active:
            self.ray_duration -= 1
            # El rayo rota lentamente
            self.ray_angle += 0.01 * (2 if self.phase == 2 else 1)
            # Genera partículas del rayo
            end_x = self.x + math.cos(self.ray_angle) * 600
            end_y = self.y + math.sin(self.ray_angle) * 600
            for _ in range(3):
                t_val = random.random()
                px = self.x + math.cos(self.ray_angle) * 600 * t_val
                py = self.y + math.sin(self.ray_angle) * 600 * t_val
                particles.append({'x':px,'y':py,'vx':random.uniform(-1,1),'vy':random.uniform(-1,1),
                                   'life':8,'max_life':8,'color':YELLOW,'size':3})
            if self.ray_duration <= 0:
                self.ray_active = False

        # Actualizar balas
        for b in self.bullets[:]:
            b.update()
            if not b.alive:
                self.bullets.remove(b)

    def _spread_shot(self, px, py):
        base_angle = math.atan2(py - self.y, px - self.x)
        n_shots = 8 if self.phase == 2 else 5
        spread  = math.pi / 4 if self.phase == 2 else math.pi / 6
        for i in range(n_shots):
            angle = base_angle - spread/2 + spread * i / (n_shots-1)
            spd   = 4 if self.phase == 2 else 3
            vx = math.cos(angle) * spd
            vy = math.sin(angle) * spd
            self.bullets.append(Bullet(self.x-60, self.y, vx, vy, RED, 1, 6, 'enemy'))

    def get_ray_hit(self, px, py, margin=20):
        """Chequea si el jugador es golpeado por el rayo"""
        if not self.ray_active: return False
        # Distancia punto-línea desde el rayo
        dx = math.cos(self.ray_angle)
        dy = math.sin(self.ray_angle)
        vx = px - self.x
        vy = py - self.y
        proj = vx * dx + vy * dy
        if proj < 0: return False
        dist = abs(vx * dy - vy * dx)
        return dist < margin

    def take_damage(self, dmg=1):
        self.hp -= dmg
        if self.hp <= 0:
            self.alive = False
            for _ in range(5):
                rx = self.x + random.uniform(-80, 80)
                ry = self.y + random.uniform(-80, 80)
                spawn_explosion(rx, ry, random.choice([RED, ORANGE, YELLOW, CYAN]), 40, 6)
            return True
        if random.random() < 0.3:
            spawn_explosion(self.x + random.uniform(-60,60),
                           self.y + random.uniform(-60,60), ORANGE, 10, 3)
        return False

    def get_rect(self):
        return pygame.Rect(int(self.x)-60, int(self.y)-60, 120, 120)

    def draw(self, surf):
        cx, cy = int(self.x), int(self.y)
        t = self.t
        hp_r = max(0, self.hp / self.max_hp)
        angry = self.phase == 2

        # ─ Tentáculos ─
        for i, ten in enumerate(self.tentacles):
            base_a = ten['base_angle'] + math.sin(t*0.03 + i) * 0.3
            pts = [(cx, cy)]
            seg_len = ten['len'] / 6
            cur_a = base_a
            bx, by = float(cx), float(cy)
            for s in range(6):
                wave = math.sin(t*0.05 + i + s*0.5) * 0.25
                cur_a += wave
                bx += math.cos(cur_a) * seg_len
                by += math.sin(cur_a) * seg_len
                pts.append((int(bx), int(by)))
            col = MAGENTA if angry else PURPLE
            if len(pts) >= 2:
                pygame.draw.lines(surf, col, False, pts, 6)
                # Ventosas
                for pt in pts[1:]:
                    pygame.draw.circle(surf, PINK, pt, 4)

        # ─ Cuerpo principal ─
        body_col = (int(200*(1-hp_r)+50), 0, int(200*hp_r)) if angry else (100, 0, 180)
        pygame.draw.ellipse(surf, body_col, (cx-70, cy-55, 140, 110))
        # Borde brillante
        outline_col = RED if angry else MAGENTA
        pygame.draw.ellipse(surf, outline_col, (cx-70, cy-55, 140, 110), 3)

        # ─ Ojos ─
        eye_glow = int(150 + 100 * math.sin(t * 0.1))
        for ex, ey in [(-25, -10), (25, -10)]:
            pygame.draw.circle(surf, (eye_glow, 0, 0), (cx+ex, cy+ey), 16)
            pygame.draw.circle(surf, (255, 200, 0), (cx+ex, cy+ey), 10)
            pupil_x = cx + ex + int(4 * math.sin(t*0.05))
            pupil_y = cy + ey + int(4 * math.cos(t*0.07))
            pygame.draw.circle(surf, BLACK, (pupil_x, pupil_y), 5)

        # ─ Boca ─
        mouth_open = 8 + int(6 * math.sin(t * 0.08))
        pygame.draw.ellipse(surf, BLACK, (cx-20, cy+20, 40, mouth_open))
        pygame.draw.ellipse(surf, RED, (cx-18, cy+22, 36, mouth_open-4), 2)
        # Dientes
        for d in range(-15, 20, 10):
            pygame.draw.polygon(surf, WHITE, [
                (cx+d, cy+20), (cx+d+4, cy+20), (cx+d+2, cy+28)
            ])

        # ─ RAYO ─
        if self.ray_active:
            end_x = int(self.x + math.cos(self.ray_angle) * 800)
            end_y = int(self.y + math.sin(self.ray_angle) * 800)
            for width, col in [(12, ORANGE), (8, YELLOW), (4, WHITE)]:
                pygame.draw.line(surf, col, (cx, cy), (end_x, end_y), width)
            # Destello en origen
            glow_r = 20 + int(10*math.sin(t*0.3))
            pygame.draw.circle(surf, YELLOW, (cx, cy), glow_r, 3)

        # ─ Barra de HP del boss ─
        bar_w = 300
        bar_x = WIDTH//2 - bar_w//2
        bar_y = 20
        pygame.draw.rect(surf, (60, 0, 0), (bar_x, bar_y, bar_w, 18))
        pygame.draw.rect(surf, RED, (bar_x, bar_y, int(bar_w * hp_r), 18))
        pygame.draw.rect(surf, WHITE, (bar_x, bar_y, bar_w, 18), 2)
        lbl = FONT_TINY.render("OCTOBOSS", True, WHITE)
        surf.blit(lbl, (bar_x + bar_w//2 - lbl.get_width()//2, bar_y - 16))


# ─── POWER-UPS ────────────────────────────────────────────────────────────────
class PowerUp:
    TYPES = ['power', 'shield', 'hp', 'rapid']
    COLORS = {'power': YELLOW, 'shield': CYAN, 'hp': GREEN, 'rapid': ORANGE}

    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.type  = random.choice(self.TYPES)
        self.color = self.COLORS[self.type]
        self.alive = True
        self.t     = 0

    def update(self):
        self.x -= 2
        self.t += 1
        if self.x < -30: self.alive = False

    def get_rect(self):
        return pygame.Rect(int(self.x)-12, int(self.y)-12, 24, 24)

    def draw(self, surf):
        cx, cy = int(self.x), int(self.y)
        bob = math.sin(self.t * 0.1) * 4
        cy_draw = cy + int(bob)
        pygame.draw.circle(surf, self.color, (cx, cy_draw), 12)
        pygame.draw.circle(surf, WHITE, (cx, cy_draw), 12, 2)
        labels = {'power':'P', 'shield':'S', 'hp':'+', 'rapid':'R'}
        lbl = FONT_TINY.render(labels[self.type], True, BLACK)
        surf.blit(lbl, (cx - lbl.get_width()//2, cy_draw - lbl.get_height()//2))


# ─── CONFIGURACIÓN POR NIVEL ─────────────────────────────────────────────────

LEVEL_CONFIG = {
    1:  {'waves': 3, 'enemies_per_wave': 5,  'types': ['grunt'],
         'speed_mult': 1.0, 'shoot_mult': 1.0, 'name': 'SECTOR ALFA'},
    2:  {'waves': 3, 'enemies_per_wave': 6,  'types': ['grunt','swarm'],
         'speed_mult': 1.1, 'shoot_mult': 1.1, 'name': 'NEBULOSA ROJA'},
    3:  {'waves': 4, 'enemies_per_wave': 6,  'types': ['grunt','swarm','fighter'],
         'speed_mult': 1.2, 'shoot_mult': 1.2, 'name': 'CAMPO DE ASTEROIDES'},
    4:  {'waves': 4, 'enemies_per_wave': 7,  'types': ['grunt','fighter','swarm'],
         'speed_mult': 1.3, 'shoot_mult': 1.3, 'name': 'ZONA DE GUERRA'},
    5:  {'waves': 4, 'enemies_per_wave': 8,  'types': ['fighter','swarm','bomber'],
         'speed_mult': 1.4, 'shoot_mult': 1.4, 'name': 'FLOTA BYDO'},
    6:  {'waves': 5, 'enemies_per_wave': 8,  'types': ['grunt','fighter','bomber'],
         'speed_mult': 1.5, 'shoot_mult': 1.5, 'name': 'CORREDOR OSCURO'},
    7:  {'waves': 5, 'enemies_per_wave': 9,  'types': ['fighter','bomber','command'],
         'speed_mult': 1.6, 'shoot_mult': 1.6, 'name': 'FORTALEZA ORBITAL'},
    8:  {'waves': 5, 'enemies_per_wave':10,  'types': ['grunt','swarm','command','bomber'],
         'speed_mult': 1.7, 'shoot_mult': 1.7, 'name': 'ENJAMBRE TOTAL'},
    9:  {'waves': 6, 'enemies_per_wave':12,  'types': ['fighter','bomber','command','swarm'],
         'speed_mult': 1.9, 'shoot_mult': 1.9, 'name': 'APOCALIPSIS BYDO'},
    10: {'waves': 0, 'enemies_per_wave': 0,  'types': [],
         'speed_mult': 2.0, 'shoot_mult': 2.0, 'name': 'EL PULPO ESPACIAL'},
}

ENEMY_CLASSES = {
    'grunt': GruntShip,
    'swarm': SwarmShip,
    'fighter': FighterShip,
    'bomber': BomberShip,
    'command': CommandShip,
}

# ─── UTILIDAD SONIDO ─────────────────────────────────────────────────────────
def play_sfx(name):
    if name in SFX and SFX[name]:
        try: SFX[name].play()
        except: pass

# ─── PANTALLA DE INICIO ───────────────────────────────────────────────────────
def draw_title_screen(frame):
    screen.fill(DARK_BLUE)
    for s in STARS: s.draw(screen)

    # Título con efecto de brillo
    pulse = int(180 + 75 * math.sin(frame * 0.05))
    title1 = FONT_BIG.render("SPACE R-TYPE", True, (0, pulse, 255))
    title2 = FONT_BIG.render("INVADERS", True, (pulse, 0, 255))
    screen.blit(title1, (WIDTH//2 - title1.get_width()//2, 120))
    screen.blit(title2, (WIDTH//2 - title2.get_width()//2, 175))

    # Subtítulo
    sub = FONT_SML.render("10 NIVELES - JEFE FINAL: EL PULPO ESPACIAL", True, CYAN)
    screen.blit(sub, (WIDTH//2 - sub.get_width()//2, 250))

    # Controles
    controls = [
        "TECLADO: FLECHAS/WASD = MOVER   ESPACIO/Z/X = DISPARAR",
        "GAMEPAD: ANALOGICO/DPAD = MOVER   A/B = DISPARAR",
        "",
        "PRESIONA ESPACIO, A, O ENTER PARA COMENZAR",
    ]
    y_off = 310
    for line in controls:
        col = WHITE if line else BLACK
        if "PRESIONA" in line:
            pulse2 = int(180 + 75 * math.sin(frame * 0.08))
            col = (pulse2, pulse2, 0)
        txt = FONT_TINY.render(line, True, col)
        screen.blit(txt, (WIDTH//2 - txt.get_width()//2, y_off))
        y_off += 22

    # Mini naves decorativas
    ship_t = frame * 0.02
    for i in range(5):
        sx = int(100 + i * 120 + math.sin(ship_t + i) * 20)
        sy = int(480 + math.cos(ship_t + i*0.7) * 15)
        pygame.draw.polygon(screen, NEON_BLUE, [
            (sx+12, sy), (sx-6, sy-6), (sx-8, sy), (sx-6, sy+6)
        ])
        pygame.draw.circle(screen, CYAN, (sx+2, sy), 4)


# ─── HUD ─────────────────────────────────────────────────────────────────────
def draw_hud(player, level, wave, total_waves):
    # Barra superior
    pygame.draw.rect(screen, (10, 10, 40), (0, 0, WIDTH, 40))
    pygame.draw.line(screen, NEON_BLUE, (0, 40), (WIDTH, 40), 2)

    # Score
    sc_txt = FONT_SML.render(f"SCORE: {player.score:08d}", True, YELLOW)
    screen.blit(sc_txt, (10, 8))

    # Nivel y ola
    lv_cfg = LEVEL_CONFIG.get(level, LEVEL_CONFIG[10])
    lv_txt = FONT_SML.render(f"LV{level} {lv_cfg['name']}", True, CYAN)
    screen.blit(lv_txt, (WIDTH//2 - lv_txt.get_width()//2, 8))

    if total_waves > 0:
        wv_txt = FONT_TINY.render(f"OLA {wave}/{total_waves}", True, WHITE)
        screen.blit(wv_txt, (WIDTH - wv_txt.get_width() - 10, 8))

    # HP
    for i in range(player.max_hp):
        col = GREEN if i < player.hp else (40, 40, 40)
        pygame.draw.rect(screen, col, (WIDTH - 130 + i*28, 10, 22, 20))
        pygame.draw.rect(screen, WHITE, (WIDTH - 130 + i*28, 10, 22, 20), 1)

    # Power level
    pl_txt = FONT_TINY.render(f"PWR:{player.power_level}", True, ORANGE)
    screen.blit(pl_txt, (WIDTH - 190, 10))

    # Shield indicator
    if player.shield > 0:
        sh_txt = FONT_TINY.render("SHIELD", True, CYAN)
        screen.blit(sh_txt, (WIDTH - 190, 25))


# ─── GAME OVER / WIN ─────────────────────────────────────────────────────────
def draw_game_over(score, frame):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    pulse = int(180 + 75 * math.sin(frame * 0.1))
    go = FONT_BIG.render("GAME OVER", True, (pulse, 0, 0))
    sc = FONT_MED.render(f"SCORE FINAL: {score:08d}", True, YELLOW)
    restart = FONT_SML.render("PRESIONA ENTER O START PARA REINICIAR", True, WHITE)
    screen.blit(go, (WIDTH//2 - go.get_width()//2, HEIGHT//2 - 80))
    screen.blit(sc, (WIDTH//2 - sc.get_width()//2, HEIGHT//2))
    screen.blit(restart, (WIDTH//2 - restart.get_width()//2, HEIGHT//2 + 80))

def draw_you_win(score, frame):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (0, 0))
    pulse = int(180 + 75 * math.sin(frame * 0.08))
    win = FONT_BIG.render("¡VICTORIA!", True, (0, pulse, 0))
    msg = FONT_MED.render("EL PULPO ESPACIAL HA SIDO DERROTADO", True, CYAN)
    sc  = FONT_MED.render(f"SCORE: {score:08d}", True, YELLOW)
    restart = FONT_SML.render("PRESIONA ENTER O START PARA CONTINUAR", True, WHITE)
    screen.blit(win, (WIDTH//2 - win.get_width()//2, HEIGHT//2 - 100))
    screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2 - 40))
    screen.blit(sc,  (WIDTH//2 - sc.get_width()//2,  HEIGHT//2 + 20))
    screen.blit(restart, (WIDTH//2 - restart.get_width()//2, HEIGHT//2 + 90))

def draw_level_clear(level, frame):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    screen.blit(overlay, (0, 0))
    pulse = int(180 + 75 * math.sin(frame * 0.1))
    msg = FONT_BIG.render(f"NIVEL {level} SUPERADO", True, (0, pulse, pulse))
    nxt = FONT_MED.render("PREPARATE PARA EL SIGUIENTE SECTOR", True, WHITE)
    screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2 - 50))
    screen.blit(nxt, (WIDTH//2 - nxt.get_width()//2, HEIGHT//2 + 20))


# ─── BUCLE PRINCIPAL ─────────────────────────────────────────────────────────
def main():
    joystick = None
    if pygame.joystick.get_count() > 0:
        joystick = pygame.joystick.Joystick(0)
        joystick.init()

    player = Player()

    # Estado del juego
    STATE_TITLE    = 'title'
    STATE_PLAYING  = 'playing'
    STATE_GAMEOVER = 'gameover'
    STATE_WIN      = 'win'
    STATE_LEVELCLEAR = 'levelclear'

    state = STATE_TITLE
    frame = 0

    enemies     = []
    powerups    = []
    boss        = None

    current_level    = 1
    current_wave     = 0
    wave_timer       = 0
    enemies_to_spawn = 0
    spawn_queue      = []
    level_clear_timer = 0

    def start_level(lvl):
        nonlocal current_level, current_wave, wave_timer, boss
        nonlocal enemies_to_spawn, spawn_queue
        current_level = lvl
        current_wave  = 0
        enemies.clear()
        powerups.clear()
        particles.clear()
        boss = None
        if lvl == 10:
            boss = OctopusBoss()
        else:
            start_wave(lvl, 1)

    def start_wave(lvl, wave_n):
        nonlocal current_wave, spawn_queue, wave_timer
        current_wave = wave_n
        cfg = LEVEL_CONFIG[lvl]
        count = cfg['enemies_per_wave'] + wave_n
        types = cfg['types']
        spawn_queue = []
        for i in range(count):
            etype = random.choice(types)
            spawn_y = random.randint(60, HEIGHT - 60)
            spawn_x = WIDTH + 60 + i * 80
            spawn_queue.append((etype, spawn_x, spawn_y))
        wave_timer = 0

    start_level(1)

    running = True
    while running:
        dt = clock.tick(FPS)
        frame += 1

        # ── Eventos ──────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if state == STATE_PLAYING:
                        state = STATE_TITLE
                    else:
                        running = False
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if state == STATE_TITLE:
                        player.reset()
                        start_level(1)
                        state = STATE_PLAYING
                    elif state in (STATE_GAMEOVER, STATE_WIN):
                        player.reset()
                        start_level(1)
                        state = STATE_PLAYING
            if event.type == pygame.JOYBUTTONDOWN:
                btn = event.button
                if btn in (6, 7, 9):  # Start/Select
                    if state == STATE_TITLE:
                        player.reset()
                        start_level(1)
                        state = STATE_PLAYING
                    elif state in (STATE_GAMEOVER, STATE_WIN):
                        player.reset()
                        start_level(1)
                        state = STATE_PLAYING

        # ── Actualizar estrellas siempre ──────────────────────────────────────
        for s in STARS: s.update()

        # ── ESTADO TÍTULO ────────────────────────────────────────────────────
        if state == STATE_TITLE:
            draw_title_screen(frame)
            pygame.display.flip()
            continue

        # ── ESTADO JUGANDO ────────────────────────────────────────────────────
        if state == STATE_PLAYING:
            keys = pygame.key.get_pressed()
            player.handle_input(keys, joystick)
            player.update_bullets()

            cfg = LEVEL_CONFIG.get(current_level, LEVEL_CONFIG[10])

            # Spawning de enemigos
            if spawn_queue and current_level < 10:
                wave_timer += 1
                if wave_timer % 40 == 0:
                    if spawn_queue:
                        etype, sx, sy = spawn_queue.pop(0)
                        EClass = ENEMY_CLASSES[etype]
                        e = EClass(sx, sy, current_level)
                        enemies.append(e)

            # Actualizar enemigos
            for e in enemies[:]:
                e.update(player.x, player.y, current_level)
                if not e.alive:
                    enemies.remove(e)
                    # Power-up con probabilidad
                    if random.random() < 0.12:
                        powerups.append(PowerUp(e.x, e.y))

            # Actualizar boss
            if boss:
                boss.update(player.x, player.y, current_level)
                # Rayo del boss
                if boss.get_ray_hit(player.x, player.y, 22):
                    if player.take_damage(1):
                        if player.hp <= 0:
                            state = STATE_GAMEOVER

            # Actualizar power-ups
            for pu in powerups[:]:
                pu.update()
                if not pu.alive:
                    powerups.remove(pu)
                elif player.get_rect().colliderect(pu.get_rect()):
                    play_sfx('powerup')
                    if pu.type == 'power':
                        player.power_level = min(3, player.power_level + 1)
                    elif pu.type == 'shield':
                        player.shield = 300
                    elif pu.type == 'hp':
                        player.hp = min(player.max_hp, player.hp + 1)
                    elif pu.type == 'rapid':
                        pass  # se maneja con power_level
                    pu.alive = False

            # Colisiones balas del jugador <-> enemigos
            for b in player.bullets[:]:
                if not b.alive: continue
                # vs boss
                if boss and boss.alive and b.get_rect().colliderect(boss.get_rect()):
                    boss.take_damage(b.damage)
                    b.alive = False
                    if not boss.alive:
                        spawn_explosion(boss.x, boss.y, YELLOW, 80, 8)
                        play_sfx('boss')
                        player.score += 5000
                        state = STATE_WIN
                    continue
                # vs enemigos
                for e in enemies[:]:
                    if not e.alive: continue
                    if b.get_rect().colliderect(e.get_rect()):
                        killed = e.take_damage(b.damage)
                        b.alive = False
                        if killed:
                            player.score += e.score_val
                        break

            # Colisiones balas enemigas <-> jugador
            all_enemy_bullets = []
            for e in enemies:
                all_enemy_bullets.extend(e.bullets)
            if boss:
                all_enemy_bullets.extend(boss.bullets)

            player_rect = player.get_rect()
            for b in all_enemy_bullets:
                if not b.alive: continue
                if b.get_rect().colliderect(player_rect):
                    b.alive = False
                    if player.take_damage(b.damage):
                        if player.hp <= 0:
                            state = STATE_GAMEOVER

            # Colisiones cuerpo enemigo <-> jugador
            for e in enemies:
                if e.alive and e.get_rect().colliderect(player_rect):
                    if player.take_damage(1):
                        e.alive = False
                        spawn_explosion(e.x, e.y, ORANGE, 20, 3)
                        if player.hp <= 0:
                            state = STATE_GAMEOVER

            # ¿Oleada terminada?
            if current_level < 10 and not spawn_queue and not enemies:
                cfg_waves = cfg['waves']
                if current_wave < cfg_waves:
                    start_wave(current_level, current_wave + 1)
                else:
                    # Nivel superado
                    if current_level < 10:
                        play_sfx('level')
                        state = STATE_LEVELCLEAR
                        level_clear_timer = frame

            # Partículas
            update_particles()

            # ── DIBUJAR ──────────────────────────────────────────────────────
            screen.fill(DARK_BLUE)
            for s in STARS: s.draw(screen)

            draw_particles(screen)

            # Nebula background (simple gradient circles)
            if frame % 3 == 0 and random.random() < 0.05:
                rx = random.randint(0, WIDTH)
                ry = random.randint(50, HEIGHT)
                rc = random.choice([(20,0,40),(0,20,40),(30,0,20)])
                for r in range(30, 0, -5):
                    s_surf = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
                    pygame.draw.circle(s_surf, (*rc, 15), (r, r), r)
                    screen.blit(s_surf, (rx-r, ry-r))

            # Boss
            if boss:
                boss.draw(screen)
                for b in boss.bullets:
                    b.draw(screen)

            # Enemigos
            for e in enemies:
                e.draw(screen)
                for b in e.bullets:
                    b.draw(screen)

            # Power-ups
            for pu in powerups:
                pu.draw(screen)

            # Jugador
            player.draw(screen)
            for b in player.bullets:
                b.draw(screen)

            draw_hud(player, current_level, current_wave, cfg.get('waves', 0))

            # Mensaje boss incoming
            if current_level == 10 and boss and boss.x > WIDTH - 150:
                pulse = int(180 + 75 * math.sin(frame * 0.1))
                msg = FONT_MED.render("¡EL PULPO ESPACIAL SE ACERCA!", True, (pulse, 0, 0))
                screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2 - 20))

        # ── ESTADO LEVEL CLEAR ────────────────────────────────────────────────
        elif state == STATE_LEVELCLEAR:
            screen.fill(DARK_BLUE)
            for s in STARS: s.draw(screen)
            draw_particles(screen)
            update_particles()
            draw_level_clear(current_level, frame)

            if frame - level_clear_timer > 180:
                next_level = current_level + 1
                if next_level > 10:
                    state = STATE_WIN
                else:
                    player.reset_position_and_bullets()  # partial reset
                    start_level(next_level)
                    state = STATE_PLAYING

        # ── GAME OVER ─────────────────────────────────────────────────────────
        elif state == STATE_GAMEOVER:
            screen.fill(DARK_BLUE)
            for s in STARS: s.draw(screen)
            draw_game_over(player.score, frame)

        # ── WIN ───────────────────────────────────────────────────────────────
        elif state == STATE_WIN:
            screen.fill(DARK_BLUE)
            for s in STARS: s.draw(screen)
            draw_you_win(player.score, frame)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


# ─── PARCHE: reset parcial del jugador entre niveles ─────────────────────────
def _player_partial_reset(self):
    self.x = 100.0
    self.y = HEIGHT // 2
    self.bullets.clear()
    self.invincible = 120  # breve invencibilidad al entrar

Player.reset_position_and_bullets = _player_partial_reset


if __name__ == '__main__':
    main()

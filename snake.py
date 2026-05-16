#!/usr/bin/env python3
"""
SNAKE - Batocera Edition
Controles: W=Arriba, A=Izquierda, S=Abajo, D=Derecha
Dificultad progresiva: murallas aparecen con el tiempo
"""

import pygame
import sys
import random
import math

# ── Configuración ──────────────────────────────────────────────────────────────
SCREEN_W, SCREEN_H = 800, 600
CELL          = 20          # tamaño de cada celda en píxeles
COLS          = SCREEN_W // CELL
ROWS          = SCREEN_H // CELL
FPS           = 60

# Velocidad inicial: un movimiento cada N frames
MOVE_INTERVAL_INIT = 10     # ~6 movimientos/seg a 60 FPS
MOVE_INTERVAL_MIN  = 3      # límite más rápido (~20 mov/seg)

# Cada cuántos puntos aparece una nueva muralla
WALL_EVERY    = 5

# Paleta retro terminal
C_BG          = (10,  12,  10)
C_GRID        = (18,  26,  18)
C_SNAKE_HEAD  = (80,  255, 100)
C_SNAKE_BODY  = (40,  180,  55)
C_SNAKE_TAIL  = (20,  100,  30)
C_FOOD        = (255,  80,  80)
C_FOOD_GLOW   = (255, 160, 160)
C_WALL        = (200, 160,  30)
C_WALL_EDGE   = (255, 210,  60)
C_TEXT        = (80,  255, 100)
C_TEXT_DIM    = (40,  130,  50)
C_OVERLAY     = (10,  12,  10, 210)
C_WHITE       = (230, 255, 230)

# ── Helpers ────────────────────────────────────────────────────────────────────

def cell_rect(col, row):
    return pygame.Rect(col * CELL, row * CELL, CELL, CELL)

def draw_cell(surf, col, row, color, shrink=2):
    r = cell_rect(col, row).inflate(-shrink * 2, -shrink * 2)
    pygame.draw.rect(surf, color, r, border_radius=3)

def lerp_color(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

# ── Clase principal ─────────────────────────────────────────────────────────────

class SnakeGame:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("SNAKE — Batocera Edition")
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        self.clock  = pygame.time.Clock()

        # Fuentes
        try:
            self.font_big   = pygame.font.SysFont("monospace", 52, bold=True)
            self.font_mid   = pygame.font.SysFont("monospace", 28, bold=True)
            self.font_small = pygame.font.SysFont("monospace", 18)
        except Exception:
            self.font_big   = pygame.font.Font(None, 52)
            self.font_mid   = pygame.font.Font(None, 28)
            self.font_small = pygame.font.Font(None, 18)

        self.high_score = 0
        self.reset()

    # ── Reset ──────────────────────────────────────────────────────────────────

    def reset(self):
        mid_c = COLS // 2
        mid_r = ROWS // 2
        self.snake   = [(mid_c, mid_r), (mid_c - 1, mid_r), (mid_c - 2, mid_r)]
        self.dir     = (1, 0)          # moviéndose a la derecha
        self.next_dir= (1, 0)
        self.score   = 0
        self.walls   = set()           # celdas con muralla
        self.food    = None
        self.spawn_food()

        self.move_interval = MOVE_INTERVAL_INIT
        self.move_timer    = 0
        self.frame         = 0
        self.food_anim     = 0         # para pulso de la comida
        self.game_over     = False
        self.paused        = False

        # Borde del mapa como muralla fija (ya se choca si sale)
        # No la añadimos como celda; la colisión se detecta fuera de rango.

    # ── Spawn comida ───────────────────────────────────────────────────────────

    def spawn_food(self):
        snake_set = set(self.snake)
        while True:
            c = random.randint(1, COLS - 2)
            r = random.randint(1, ROWS - 2)
            if (c, r) not in snake_set and (c, r) not in self.walls:
                self.food = (c, r)
                return

    # ── Lógica de murallas ─────────────────────────────────────────────────────

    def add_wall_segment(self):
        """Añade un segmento de muralla horizontal o vertical de 3-6 celdas."""
        snake_set  = set(self.snake)
        forbidden  = snake_set | {self.food} | self.walls
        attempts   = 0
        while attempts < 200:
            attempts += 1
            length = random.randint(3, 6)
            horiz  = random.choice([True, False])
            if horiz:
                c = random.randint(2, COLS - 2 - length)
                r = random.randint(2, ROWS - 3)
                cells = [(c + i, r) for i in range(length)]
            else:
                c = random.randint(2, COLS - 3)
                r = random.randint(2, ROWS - 2 - length)
                cells = [(c, r + i) for i in range(length)]

            # Asegurarse que no bloquea la serpiente ni la comida
            if any(cell in forbidden for cell in cells):
                continue
            # Comprobar que no cierra el camino alrededor de la serpiente head
            head = self.snake[0]
            if any(abs(cx - head[0]) <= 2 and abs(cy - head[1]) <= 2
                   for cx, cy in cells):
                continue
            for cell in cells:
                self.walls.add(cell)
            return

    # ── Input ──────────────────────────────────────────────────────────────────

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.KEYDOWN:
                k = event.key

                # Reiniciar / pausar en pantalla de game-over o pausa
                if self.game_over:
                    if k in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_r):
                        self.reset()
                    elif k == pygame.K_ESCAPE:
                        pygame.quit(); sys.exit()
                    return

                if k == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()

                if k == pygame.K_p or k == pygame.K_PAUSE:
                    self.paused = not self.paused
                    return

                if self.paused:
                    return

                # Direcciones WASD (y también flechas)
                if k in (pygame.K_w, pygame.K_UP)    and self.dir != (0,  1):
                    self.next_dir = (0, -1)
                elif k in (pygame.K_s, pygame.K_DOWN)  and self.dir != (0, -1):
                    self.next_dir = (0,  1)
                elif k in (pygame.K_a, pygame.K_LEFT)  and self.dir != (1,  0):
                    self.next_dir = (-1, 0)
                elif k in (pygame.K_d, pygame.K_RIGHT) and self.dir != (-1, 0):
                    self.next_dir = (1,  0)

    # ── Update ─────────────────────────────────────────────────────────────────

    def update(self):
        if self.game_over or self.paused:
            return

        self.frame      += 1
        self.food_anim   = (self.food_anim + 1) % 60
        self.move_timer += 1

        if self.move_timer < self.move_interval:
            return
        self.move_timer = 0

        # Aplicar dirección
        self.dir = self.next_dir
        hc, hr   = self.snake[0]
        nc = hc + self.dir[0]
        nr = hr + self.dir[1]

        # Colisión con bordes
        if nc < 0 or nc >= COLS or nr < 0 or nr >= ROWS:
            self.trigger_game_over(); return

        # Colisión con murallas
        if (nc, nr) in self.walls:
            self.trigger_game_over(); return

        # Colisión consigo mismo
        if (nc, nr) in set(self.snake[:-1]):
            self.trigger_game_over(); return

        self.snake.insert(0, (nc, nr))

        # ¿Comió?
        if (nc, nr) == self.food:
            self.score += 1
            # Aumentar velocidad
            self.move_interval = max(
                MOVE_INTERVAL_MIN,
                MOVE_INTERVAL_INIT - self.score // 2
            )
            # ¿Agregar muralla?
            if self.score % WALL_EVERY == 0:
                self.add_wall_segment()
            self.spawn_food()
        else:
            self.snake.pop()

    def trigger_game_over(self):
        self.game_over = True
        if self.score > self.high_score:
            self.high_score = self.score

    # ── Draw ───────────────────────────────────────────────────────────────────

    def draw_grid(self):
        for c in range(0, SCREEN_W, CELL):
            pygame.draw.line(self.screen, C_GRID, (c, 0), (c, SCREEN_H))
        for r in range(0, SCREEN_H, CELL):
            pygame.draw.line(self.screen, C_GRID, (0, r), (SCREEN_W, r))

    def draw_snake(self):
        n = len(self.snake)
        for i, (c, r) in enumerate(self.snake):
            t = i / max(n - 1, 1)
            if i == 0:
                color = C_SNAKE_HEAD
            else:
                color = lerp_color(C_SNAKE_BODY, C_SNAKE_TAIL, t)
            shrink = 2 if i == 0 else 3
            draw_cell(self.screen, c, r, color, shrink=shrink)

            # Ojos en la cabeza
            if i == 0:
                ox, oy = self.dir
                eye_off = [(-oy, -ox), (oy, ox)]   # perpendicular
                for ex, ey in eye_off:
                    px = c * CELL + CELL // 2 + ox * 3 + ex * 4
                    py = r * CELL + CELL // 2 + oy * 3 + ey * 4
                    pygame.draw.circle(self.screen, C_BG, (px, py), 3)
                    pygame.draw.circle(self.screen, C_WHITE, (px, py), 2)

    def draw_food(self):
        c, r = self.food
        pulse = 0.5 + 0.5 * math.sin(self.food_anim * math.pi / 30)
        glow_r = int(3 + pulse * 4)
        cx = c * CELL + CELL // 2
        cy = r * CELL + CELL // 2
        # Halo
        glow_surf = pygame.Surface((CELL * 2, CELL * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*C_FOOD_GLOW, 60),
                           (CELL, CELL), glow_r + 5)
        self.screen.blit(glow_surf, (cx - CELL, cy - CELL))
        # Manzana
        draw_cell(self.screen, c, r, C_FOOD, shrink=int(4 - pulse * 2))

    def draw_walls(self):
        for (c, r) in self.walls:
            rect = cell_rect(c, r).inflate(-1, -1)
            pygame.draw.rect(self.screen, C_WALL, rect)
            pygame.draw.rect(self.screen, C_WALL_EDGE, rect, 1)

    def draw_hud(self):
        # Score
        txt = self.font_mid.render(f"PUNTOS: {self.score}", True, C_TEXT)
        self.screen.blit(txt, (10, 6))
        # High score
        hs  = self.font_small.render(f"RÉCORD: {self.high_score}", True, C_TEXT_DIM)
        self.screen.blit(hs, (10, 38))
        # Velocidad / nivel
        lvl = self.score // WALL_EVERY + 1
        lt  = self.font_small.render(f"NIVEL: {lvl}  MURALLAS: {len(self.walls)//4 if self.walls else 0}",
                                      True, C_TEXT_DIM)
        self.screen.blit(lt, (SCREEN_W - lt.get_width() - 10, 10))
        # Controles (esquina inferior)
        ctrl = self.font_small.render("WASD · P=Pausa · ESC=Salir", True, C_TEXT_DIM)
        self.screen.blit(ctrl, (SCREEN_W // 2 - ctrl.get_width() // 2, SCREEN_H - 22))

    def draw_overlay(self, title, lines):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill(C_OVERLAY)
        self.screen.blit(overlay, (0, 0))

        t_surf = self.font_big.render(title, True, C_TEXT)
        self.screen.blit(t_surf,
            (SCREEN_W // 2 - t_surf.get_width() // 2, SCREEN_H // 2 - 90))

        for i, line in enumerate(lines):
            s = self.font_mid.render(line, True, C_WHITE)
            self.screen.blit(s,
                (SCREEN_W // 2 - s.get_width() // 2,
                 SCREEN_H // 2 - 20 + i * 36))

    def draw_start_flash(self):
        """Parpadeo en el HUD cuando el juego acaba de empezar."""
        if self.frame < 90 and (self.frame // 15) % 2 == 0:
            msg = self.font_mid.render("¡PRESIONA WASD PARA EMPEZAR!", True, C_TEXT)
            self.screen.blit(msg,
                (SCREEN_W // 2 - msg.get_width() // 2, SCREEN_H // 2 + 40))

    # ── Main loop ──────────────────────────────────────────────────────────────

    def run(self):
        while True:
            self.handle_input()
            self.update()

            # ── Render ────────────────────────────────────────────────────────
            self.screen.fill(C_BG)
            self.draw_grid()
            self.draw_walls()
            self.draw_food()
            self.draw_snake()
            self.draw_hud()

            if self.game_over:
                self.draw_overlay(
                    "GAME OVER",
                    [f"Puntuación: {self.score}",
                     f"Récord: {self.high_score}",
                     "ENTER / R = Reiniciar   ESC = Salir"]
                )
            elif self.paused:
                self.draw_overlay(
                    "PAUSA",
                    ["Presiona P para continuar"]
                )
            elif len(self.snake) == 3 and self.score == 0:
                self.draw_start_flash()

            pygame.display.flip()
            self.clock.tick(FPS)


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    SnakeGame().run()

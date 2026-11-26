"""
Aplicación principal: estado del tablero, acciones de la interfaz, avance de la
animación (generadores), manejo de ratón y teclado y bucle principal.
Todo el dibujo vive en dibujo.py (App hereda de Dibujo).
"""
import math
import random
import sys
import os
import time
from collections import deque

import pygame

from ..config import *
from ..utilidades import *
from ..algoritmo.nodo import Node, make_grid, get_clicked_pos
from ..algoritmo.astar import algorithm
from ..mapas import set_cell, DIRS4, MAZES, maze_backtracker, maze_terrain
from .widgets import Button, Slider
from .dibujo import Dibujo


def make_icon():
    """Ícono de la ventana: inicio, camino y fin sobre fondo oscuro."""
    icon = pygame.Surface((32, 32), pygame.SRCALPHA)
    pygame.draw.rect(icon, PANEL_BG, icon.get_rect(), border_radius=7)
    pygame.draw.lines(icon, PATH_C, False, [(8, 24), (8, 14), (24, 14), (24, 8)], 3)
    pygame.draw.circle(icon, START_C, (8, 24), 5)
    pygame.draw.circle(icon, END_C, (24, 8), 5)
    return icon


def new_info():
    """Datos compartidos entre el algoritmo y la interfaz (estadísticas, camino, gráfica)."""
    return {"g": {}, "open": set(), "path": [], "found": None, "done": False,
            "steps": 0, "history": [], "compute": 0.0}


class App(Dibujo):
    """Estado del programa, acciones, animación y eventos. El dibujo está en Dibujo (dibujo.py)."""

    def __init__(self):
        pygame.display.set_icon(make_icon())
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self._fonts, self._text_cache = {}, {}

        self.heatmap = False
        self.show_values = False
        self.live = True
        self.tool = "wall"

        self.task = None
        self.task_kind = None
        self.paused = False
        self.acc = 0.0
        self.maze_head = None

        self.drag = None
        self.paint_kind = "wall"
        self.last_cell = None
        self.dirty = False

        self.particles, self.trail = [], []
        self.toast_msg, self.toast_t = None, -10
        self.help = False

        self.fx = pygame.Surface((WIDTH, WIDTH), pygame.SRCALPHA)
        self.new_board(DEFAULT_ROWS)
        self.build_ui()

    # ---------------- tablero ----------------
    def new_board(self, rows, keep_endpoints=False):
        old = (self.start.get_pos(), self.end.get_pos()) if keep_endpoints else None
        self.rows = rows
        self.gap = WIDTH // rows
        self.grid = make_grid(rows, WIDTH)
        m = max(1, rows // 6)
        s, e = old if old else ((m, rows // 2), (rows - 1 - m, rows // 2))
        self.start = self.grid[s[0]][s[1]]
        self.end = self.grid[e[0]][e[1]]
        self.start.make_start()
        self.end.make_end()
        Node.closed_count = 0
        self.info = new_info()
        self.gridlines = pygame.Surface((WIDTH, WIDTH), pygame.SRCALPHA)
        alpha = 16 if self.gap >= 16 else 10
        for i in range(rows + 1):
            pygame.draw.line(self.gridlines, (255, 255, 255, alpha), (0, i * self.gap), (WIDTH, i * self.gap))
            pygame.draw.line(self.gridlines, (255, 255, 255, alpha), (i * self.gap, 0), (i * self.gap, WIDTH))

    def clear_search(self):
        """Quita visitados, frontera y camino (sin tocar muros ni pesos)."""
        for row in self.grid:
            for node in row:
                if node.is_closed() or node.is_open() or node.color == PURPLE:
                    node._color = WHITE          # sin animación
        self.start._color, self.end._color = ORANGE, TURQUOISE
        Node.closed_count = 0
        self.info = new_info()

    def free_near(self, node, avoid):
        """Celda libre más cercana (por si un generador tapó el inicio o el fin)."""
        if not node.is_barrier() and node is not avoid:
            return node
        n = self.rows
        seen = {node.get_pos()}
        q = deque([node.get_pos()])
        while q:
            i, j = q.popleft()
            for di, dj in DIRS4 + [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
                p = (i + di, j + dj)
                if 0 <= p[0] < n and 0 <= p[1] < n and p not in seen:
                    cand = self.grid[p[0]][p[1]]
                    if not cand.is_barrier() and cand is not avoid:
                        return cand
                    seen.add(p)
                    q.append(p)
        return node

    def snap_endpoints(self):
        s = self.free_near(self.start, self.end)
        e = self.free_near(self.end, s)
        if s is not self.start:
            if self.start.color == ORANGE:
                self.start.reset()
            self.start = s
        if e is not self.end:
            if self.end.color == TURQUOISE:
                self.end.reset()
            self.end = e
        self.start.make_start()
        self.end.make_end()

    # ---------------- texto ----------------
    def font(self, size, bold=False):
        if (size, bold) not in self._fonts:
            self._fonts[(size, bold)] = pygame.font.SysFont("segoeui,helveticaneue,dejavusans,arial", size, bold=bold)
        return self._fonts[(size, bold)]

    def text(self, s, pos, size=14, color=TEXT, bold=False, anchor="topleft"):
        key = (s, size, bold, color)
        img = self._text_cache.get(key)
        if img is None:
            if len(self._text_cache) > 3000:
                self._text_cache.clear()
            img = self._text_cache[key] = self.font(size, bold).render(s, True, color)
        rect = img.get_rect(**{anchor: pos})
        self.screen.blit(img, rect)
        return rect

    def toast(self, msg):
        self.toast_msg, self.toast_t = msg, now()

    # ---------------- interfaz ----------------
    def build_ui(self):
        X, W = WIDTH + 20, PANEL_W - 40
        B = self.buttons = []
        self.labels = []
        bw = (W - 24) / 4
        half = (W - 16) / 2

        self.labels.append(("ALGORITMO", X, 78))
        self.algo_card = pygame.Rect(X, 96, W, 96)

        self.labels.append(("OPCIONES", X, 208))
        opts = [("Calor", "heatmap"), ("Valores", "show_values"), ("Vivo", "live")]
        for i, (name, attr) in enumerate(opts):
            B.append(Button((X + i * (bw + 8), 226, bw, 28), name, lambda a=attr: self.toggle(a),
                            active=lambda a=attr: getattr(self, a), size=12))
        B.append(Button((X + 3 * (bw + 8), 226, bw, 28), "Ayuda", lambda: self.toggle("help"),
                        active=lambda: self.help, size=12))

        self.labels.append(("HERRAMIENTA", X, 268))
        self.labels.append(("CUADRÍCULA", X + half + 16, 268))
        tw = (half - 12) / 3
        for i, (name, kind) in enumerate([("Muro", "wall"), ("Peso x5", "weight"), ("Borrar", "empty")]):
            B.append(Button((X + i * (tw + 6), 286, tw, 28), name, lambda k=kind: setattr(self, "tool", k),
                            active=lambda k=kind: self.tool == k, size=12))
        sw = (half - 18) / 4
        for i, n in enumerate(SIZES):
            B.append(Button((X + half + 16 + i * (sw + 6), 286, sw, 28), str(n), lambda n=n: self.set_size(n),
                            active=lambda n=n: self.rows == n, size=12))

        self.labels.append(("GENERAR MAPA", X, 328))
        for i, (name, fn) in enumerate(MAZES):
            B.append(Button((X + i * (bw + 8), 346, bw, 28), name, lambda fn=fn: self.start_maze(fn), size=12))

        self.labels.append(("VELOCIDAD", X, 388))
        self.slider = Slider((X + 4, 414, W - 8, 6), 0.55)

        q = (half - 8) / 2
        B.append(Button((X, 440, half, 40), self.run_label, self.toggle_run, primary=True, size=16))
        B.append(Button((X + half + 16, 440, q, 40), "Paso", self.step))
        B.append(Button((X + half + 24 + q, 440, q, 40), "Captura", self.screenshot))
        B.append(Button((X, 488, half, 28), "Limpiar ruta", self.clear_path, size=12))
        B.append(Button((X + half + 16, 488, half, 28), "Limpiar todo", self.clear_all, size=12))

        self.stats_y = 546
        self.chart_rect = pygame.Rect(X, 656, W, 118)

    def run_label(self):
        if self.task_kind == "search":
            return "Reanudar" if self.paused else "Pausar"
        return "Ejecutar"

    # ---------------- acciones ----------------
    def toggle(self, attr):
        setattr(self, attr, not getattr(self, attr))
        if attr == "live" and self.live:
            self.toast("Modo vivo: la ruta se recalcula al editar")

    def set_size(self, n):
        if n != self.rows:
            self.cancel_task()
            self.new_board(n)
            self.toast(f"Cuadrícula {n} x {n}")

    def cancel_task(self):
        self.task = self.task_kind = None
        self.paused = False
        self.maze_head = None

    def clear_path(self):
        if self.task_kind == "search":
            self.cancel_task()
        self.clear_search()

    def clear_all(self):
        self.cancel_task()
        self.new_board(self.rows, keep_endpoints=True)
        self.particles.clear()

    def prepare_search(self):
        self.dirty = False   # la búsqueda ya parte del tablero actual
        self.snap_endpoints()
        self.clear_search()
        # Antes de buscar, cada nodo calcula sus vecinos transitables
        for row in self.grid:
            for node in row:
                node.update_neighbors(self.grid)

    def start_search(self, paused=False):
        self.prepare_search()
        self.task = algorithm(self.grid, self.start, self.end, self.info)
        self.task_kind = "search"
        self.paused = paused
        self.acc = 0.0

    def toggle_run(self):
        if self.task_kind == "maze":
            self.toast("Espera a que termine el generador…")
        elif self.task_kind == "search":
            self.paused = not self.paused
        else:
            self.start_search()

    def step(self):
        if self.task_kind == "maze":
            return
        if self.task_kind != "search":
            self.start_search(paused=True)
        self.paused = True
        self.advance(1)

    def start_maze(self, fn):
        self.cancel_task()
        self.clear_search()
        self.task = fn(self)
        self.task_kind = "maze"
        self.acc = 0.0

    def resolve_instant(self):
        """Modo vivo: corre A* completo de golpe, sin animación."""
        self.prepare_search()
        info = self.info
        gen = algorithm(self.grid, self.start, self.end, info)
        t0 = time.perf_counter()
        try:
            while True:
                next(gen)
                info["steps"] += 1
                info["history"].append((len(info["open"]), Node.closed_count))
        except StopIteration as stop:
            info["found"] = stop.value
        info["compute"] = time.perf_counter() - t0
        info["done"] = True
        for row in self.grid:            # congelamos las animaciones
            for node in row:
                if node.color in (RED, GREEN, PURPLE):
                    node.changed = -100.0

    def screenshot(self):
        os.makedirs(CAPTURES_DIR, exist_ok=True)
        name = f"captura_{time.strftime('%Y%m%d_%H%M%S')}.png"
        pygame.image.save(self.screen, os.path.join(CAPTURES_DIR, name))
        self.toast(f"Guardada en capturas/{name}")

    # ---------------- avance de la animación ----------------
    def rate(self):
        """Pasos por fotograma (escala logarítmica: 0.05 a ~300)."""
        return 10 ** (-1.3 + self.slider.value * 3.8)

    def advance(self, n):
        kind = self.task_kind
        info = self.info
        t0 = time.perf_counter()
        for _ in range(n):
            try:
                next(self.task)
                if kind == "search":
                    info["steps"] += 1
                    info["history"].append((len(info["open"]), Node.closed_count))
            except StopIteration as stop:
                if kind == "search":
                    info["compute"] += time.perf_counter() - t0
                    info["found"] = stop.value
                self.task_done(kind)
                return
        if kind == "search":
            info["compute"] += time.perf_counter() - t0

    def task_done(self, kind):
        self.cancel_task()
        if kind == "search":
            self.info["done"] = True
            if self.info["found"]:
                self.burst(self.end, PATH_C, 70)
                self.burst(self.end, END_C, 30)
                steps = len(self.info["path"]) - 1
                self.toast(f"¡Camino encontrado!  {steps} pasos · costo {self.info['g'][self.end]:.0f}")
            else:
                self.toast("No existe ningún camino posible")
        else:
            self.snap_endpoints()
            self.toast("Mapa generado. Pulsa ESPACIO para buscar")

    def burst(self, node, color, count):
        cx, cy = node.x + self.gap / 2, node.y + self.gap / 2
        for _ in range(count):
            a, v = random.uniform(0, math.tau), random.uniform(60, 320)
            self.particles.append([cx, cy, math.cos(a) * v, math.sin(a) * v,
                                   random.uniform(0.5, 1.2), color, random.uniform(2, 4.5)])

    def update(self, dt):
        if self.dirty:
            self.dirty = False
            if self.task_kind == "search":
                self.cancel_task()
                self.clear_search()
            elif self.info["done"] and self.live:
                self.resolve_instant()
            else:
                self.clear_search()

        if self.task and not self.paused:
            self.acc += self.rate() * (3.0 if self.task_kind == "maze" else 1.0)
            n = int(self.acc)
            self.acc -= n
            if n:
                self.advance(n)

        for p in self.particles:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[2] *= 0.95
            p[3] = p[3] * 0.95 + 220 * dt
            p[4] -= dt
        self.particles = [p for p in self.particles if p[4] > 0]

    # ---------------- ratón ----------------
    def node_at(self, pos):
        row, col = get_clicked_pos(pos, self.rows, WIDTH)
        row = int(clamp(row, 0, self.rows - 1))
        col = int(clamp(col, 0, self.rows - 1))
        return self.grid[row][col]

    def grid_down(self, pos, button):
        if self.task_kind == "maze":
            return
        node = self.node_at(pos)
        if button == 1:
            if node is self.start or node is self.end:
                self.drag = "start" if node is self.start else "end"
                return
            self.drag = "paint"
            self.paint_kind = self.tool
            # clic sobre lo mismo que ya hay = borrar
            if (self.tool == "wall" and node.is_barrier()) or \
               (self.tool == "weight" and node.weight > 1 and not node.is_barrier()):
                self.paint_kind = "empty"
        elif button == 3:
            self.drag = "paint"
            self.paint_kind = "empty"
        else:
            return
        self.last_cell = node.get_pos()
        self.paint(node)

    def grid_motion(self, pos):
        node = self.node_at(pos)
        if self.drag in ("start", "end"):
            cur = self.start if self.drag == "start" else self.end
            other = self.end if self.drag == "start" else self.start
            if node is not cur and node is not other and not node.is_barrier():
                cur.reset()
                if self.drag == "start":
                    self.start = node
                    node.make_start()
                else:
                    self.end = node
                    node.make_end()
                self.dirty = True
        elif self.drag == "paint" and self.last_cell:
            (a, b), (c, d) = self.last_cell, node.get_pos()
            steps = max(abs(c - a), abs(d - b))
            for i in range(1, steps + 1):       # línea entre puntos para no dejar huecos
                t = i / steps
                self.paint(self.grid[round(lerp(a, c, t))][round(lerp(b, d, t))])
            self.last_cell = (c, d)

    def paint(self, node):
        if node is self.start or node is self.end:
            return
        if set_cell(node, self.paint_kind):
            self.dirty = True

    # ---------------- eventos ----------------
    def handle(self, ev):
        if ev.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if ev.type == pygame.KEYDOWN:
            self.key(ev.key)
        elif ev.type == pygame.MOUSEBUTTONDOWN:
            if ev.button in (4, 5):          # rueda = velocidad
                self.slider.value = clamp(self.slider.value + (0.04 if ev.button == 4 else -0.04))
                return
            if self.help:
                self.help = False
                return
            if ev.pos[0] < WIDTH:
                self.grid_down(ev.pos, ev.button)
            elif ev.button == 1 and not self.slider.down(ev.pos):
                for b in self.buttons:
                    if b.click(ev.pos):
                        break
        elif ev.type == pygame.MOUSEBUTTONUP:
            self.drag = self.last_cell = None
            self.slider.drag = False
        elif ev.type == pygame.MOUSEMOTION:
            if self.slider.drag:
                self.slider.set_from(ev.pos[0])
            elif self.drag:
                self.grid_motion(ev.pos)

    def key(self, k):
        if k == pygame.K_ESCAPE:
            self.help = False
        elif k == pygame.K_F1:
            self.help = not self.help
        elif k == pygame.K_SPACE:
            self.toggle_run()
        elif k == pygame.K_c:
            self.clear_all()
        elif k in (pygame.K_n, pygame.K_RIGHT):
            self.step()
        elif k == pygame.K_x:
            self.clear_path()
        elif k == pygame.K_h:
            self.toggle("heatmap")
        elif k == pygame.K_v:
            self.toggle("show_values")
        elif k == pygame.K_l:
            self.toggle("live")
        elif k == pygame.K_m:
            self.start_maze(maze_backtracker)
        elif k == pygame.K_t:
            self.start_maze(maze_terrain)
        elif k == pygame.K_g:
            self.set_size(SIZES[(SIZES.index(self.rows) + 1) % len(SIZES)])
        elif k == pygame.K_p:
            self.screenshot()
        elif k in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
            self.slider.value = clamp(self.slider.value + 0.05)
        elif k in (pygame.K_MINUS, pygame.K_KP_MINUS):
            self.slider.value = clamp(self.slider.value - 0.05)

    # ---------------- bucle principal ----------------
    def run(self):
        self.toast("Dibuja muros y pulsa ESPACIO  ·  F1 para ayuda")
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            for ev in pygame.event.get():
                self.handle(ev)
            self.update(min(dt, 0.05))
            self.draw()
            pygame.display.flip()

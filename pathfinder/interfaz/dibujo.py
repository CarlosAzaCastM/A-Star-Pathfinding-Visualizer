"""
Todo lo que se pinta en pantalla: cuadrícula animada, camino, agente,
partículas, panel lateral, estadísticas, gráfica, tooltip, avisos y ayuda.
App hereda de esta clase, así que aquí `self` es la aplicación.
"""
import math

import pygame

from ..config import *
from ..utilidades import *
from ..algoritmo.nodo import Node
from ..algoritmo.astar import h


class Dibujo:
    # ---------------- dibujo de la cuadrícula ----------------
    def draw_cell(self, node, col, scale=1.0):
        cs = self.gap
        if scale >= 0.999:
            self.screen.fill(col, (node.x, node.y, cs, cs))
        elif scale > 0.02:
            size = cs * scale
            off = (cs - size) / 2
            pygame.draw.rect(self.screen, col, (node.x + off, node.y + off, max(1, size), max(1, size)),
                             border_radius=int(cs * 0.25))

    def draw_grid(self):
        s, cs, t = self.screen, self.gap, now()
        grid, info = self.grid, self.info
        s.fill(EMPTY, (0, 0, WIDTH, WIDTH))
        nclosed = max(1, Node.closed_count)
        g = info["g"]
        maxg = 1.0
        if self.heatmap:
            for row in grid:
                for node in row:
                    if node.is_closed():
                        maxg = max(maxg, g.get(node, 0))
        dot = max(1, cs // 4)

        for row in grid:
            for node in row:
                c = node.color
                age = t - node.changed
                if c == BLACK:                                  # obstáculo
                    sc = pop_scale(age)
                    if sc >= 0.999:
                        s.fill(WALL, (node.x, node.y, cs, cs))
                        below = node.col + 1
                        if cs >= 14 and (below >= self.rows or not grid[node.row][below].is_barrier()):
                            s.fill(WALL_SHADE, (node.x, node.y + cs - 3, cs, 3))
                    else:
                        self.draw_cell(node, lerp_c(ACCENT_HI, WALL, sc), sc)
                    continue
                if c == RED:                                    # visitado (closed set)
                    if self.heatmap:
                        base = TURBO_LUT[int(clamp(g.get(node, 0) / maxg) * 255)]
                    else:
                        base = CLOSED_LUT[int(node.order / nclosed * 255)]
                    if node.weight > 1:
                        base = lerp_c(base, WEIGHT, 0.5)
                    if age < 0.5:
                        col = lerp_c(CLOSED_FLASH, base, ease_out_cubic(clamp(age / 0.5)))
                        self.draw_cell(node, col, lerp(0.35, 1.0, pop_scale(age, 0.3)))
                    else:
                        s.fill(base, (node.x, node.y, cs, cs))
                elif c == GREEN:                                # frontera (open set)
                    k = 0.82 + 0.18 * math.sin(t * 5 + (node.row + node.col) * 0.45)
                    col = (int(OPEN_C[0] * k), int(OPEN_C[1] * k), int(OPEN_C[2] * k))
                    if node.weight > 1:
                        col = lerp_c(col, WEIGHT, 0.45)
                    self.draw_cell(node, col, pop_scale(age, 0.25))
                elif c == PURPLE:                               # camino final
                    self.draw_cell(node, lerp_c((255, 240, 180), PATH_CELL, clamp(age / 0.4)),
                                   lerp(0.4, 1.0, pop_scale(age, 0.3)))
                else:                                           # vacío / inicio / fin
                    if node.weight > 1:
                        self.draw_cell(node, WEIGHT, pop_scale(age))
                    elif 0 <= age < 0.35:                       # destello al borrar/excavar
                        s.fill(lerp_c(EMPTY, (120, 140, 255), (1 - age / 0.35) * 0.6),
                               (node.x, node.y, cs, cs))
                if node.weight > 1 and cs >= 8:
                    s.fill(WEIGHT_DOT, (node.x + (cs - dot) // 2, node.y + (cs - dot) // 2, dot, dot))

        if self.maze_head:
            pygame.draw.rect(s, CLOSED_FLASH, (self.maze_head.x, self.maze_head.y, cs, cs),
                             border_radius=max(1, cs // 4))
        s.blit(self.gridlines, (0, 0))

        # valores g / h / f
        if self.show_values and cs >= 20 and g:
            for row in grid:
                for node in row:
                    if not (node.is_closed() or node.is_open()):
                        continue
                    gv = g.get(node, math.inf)
                    if gv == math.inf:
                        continue
                    hv = h(node.get_pos(), self.end.get_pos())
                    if cs >= 32:
                        self.text(f"{gv:.0f}", (node.x + 2, node.y + 1), 9, (235, 240, 255))
                        self.text(f"{hv:.0f}", (node.x + cs - 2, node.y + 1), 9, (235, 240, 255), anchor="topright")
                        self.text(f"{gv + hv:.0f}", (node.x + cs / 2, node.y + cs * 0.62), 12, TEXT, True, "center")
                    else:
                        self.text(f"{gv + hv:.0f}", (node.x + cs / 2, node.y + cs / 2), 9, TEXT, anchor="center")

        # efectos: línea del camino, agente, pulsos y partículas
        fx = self.fx
        fx.fill((0, 0, 0, 0))
        path = info["path"]
        if len(path) >= 2:
            pts = [(n.x + cs / 2, n.y + cs / 2) for n in path]
            wg, wc = max(4, int(cs * 0.75)), max(2, int(cs * 0.28))
            pygame.draw.lines(fx, (*PATH_C, 60), False, pts, wg)
            pygame.draw.lines(fx, (*PATH_C, 255), False, pts, wc)
            for q in pts:
                pygame.draw.circle(fx, (*PATH_C, 255), q, wc / 2)
            if info["done"] and info["found"]:
                self.draw_agent(fx, pts[::-1], t)

        for node, colr, off in ((self.start, START_C, 0.0), (self.end, END_C, 0.5)):
            ph = (t * 0.9 + off) % 1.0
            pygame.draw.circle(fx, (*colr, int(170 * (1 - ph))), (node.x + cs / 2, node.y + cs / 2),
                               cs * 0.45 * (1 + ph * 1.6), max(1, cs // 8))
        for x, y, _, _, life, colr, size in self.particles:
            pygame.draw.circle(fx, (*colr, int(255 * clamp(life))), (x, y), size * clamp(life + 0.3))
        s.blit(fx, (0, 0))

        self.draw_endpoint(self.start, START_C, t, False)
        self.draw_endpoint(self.end, END_C, t, True)

        mx, my = pygame.mouse.get_pos()
        if mx < WIDTH and not self.help:
            n = self.node_at((mx, my))
            pygame.draw.rect(s, (255, 255, 255), (n.x, n.y, cs, cs), 1, border_radius=2)

    def draw_agent(self, fx, pts, t):
        cs = self.gap
        L = len(pts)
        pos = min((t * 10.0) % (L - 1 + 6), L - 1)     # recorre y descansa al final
        j = int(pos)
        f = pos - j
        a, b = pts[j], pts[min(j + 1, L - 1)]
        x, y = lerp(a[0], b[0], f), lerp(a[1], b[1], f)
        self.trail = (self.trail + [(x, y)])[-12:]
        for i, (tx, ty) in enumerate(self.trail):
            pygame.draw.circle(fx, (255, 255, 255, 12 + i * 10), (tx, ty), cs * 0.12 + i * cs * 0.02)
        pygame.draw.circle(fx, (255, 240, 200, 90), (x, y), cs * 0.6)
        pygame.draw.circle(fx, (255, 255, 255, 255), (x, y), max(2, cs * 0.3))

    def draw_endpoint(self, node, col, t, target):
        cs = self.gap
        cx, cy = node.x + cs / 2, node.y + cs / 2
        R = cs * 0.48
        if t - node.changed < 0.3:
            R *= lerp(0.5, 1.0, pop_scale(t - node.changed, 0.3))
        pygame.draw.circle(self.screen, col, (cx, cy), R)
        if target:
            pygame.draw.circle(self.screen, (25, 12, 20), (cx, cy), R * 0.62)
            pygame.draw.circle(self.screen, col, (cx, cy), R * 0.34)
        else:
            pygame.draw.circle(self.screen, (220, 255, 230), (cx, cy), R * 0.36)

    # ---------------- dibujo del panel ----------------
    def draw_panel(self):
        s = self.screen
        X, W = WIDTH + 20, PANEL_W - 40
        t = now()
        s.fill(PANEL_BG, (WIDTH, 0, PANEL_W, WIN_H))
        pygame.draw.line(s, (40, 46, 68), (WIDTH, 0), (WIDTH, WIN_H), 2)

        for i, colr in enumerate((START_C, PATH_C, END_C)):
            a = t * 2 + i * 2.1
            pygame.draw.circle(s, colr, (X + 12 + math.cos(a) * 6, 34 + math.sin(a) * 6), 4)
        r = self.text("Algoritmo", (X + 30, 16), 26, TEXT, True)
        self.text(" A*", (r.right, 16), 26, ACCENT_HI, True)
        self.text("Visualización interactiva de búsqueda de caminos", (X + 30, 50), 12, TEXT_DIM)

        for text, x, y in self.labels:
            self.text(text, (x, y), 11, TEXT_DIM, True)

        # tarjeta del algoritmo
        R = self.algo_card
        pygame.draw.rect(s, CARD, R, border_radius=10)
        pygame.draw.rect(s, ACCENT, (R.x, R.y + 10, 3, R.h - 20), border_radius=2)
        self.text("f(n) = g(n) + h(n)", (R.x + 16, R.y + 10), 18, TEXT, True)
        self.text("g: costo recorrido desde el inicio", (R.x + 16, R.y + 38), 12, (190, 198, 220))
        self.text("h: distancia Manhattan hasta el fin", (R.x + 16, R.y + 55), 12, (190, 198, 220))
        self.text("4 direcciones  ·  PriorityQueue  ·  peso = costo x5", (R.x + 16, R.y + 72), 11, TEXT_DIM)

        mouse = pygame.mouse.get_pos()
        for b in self.buttons:
            b.draw(self, mouse)

        sps = self.rate() * FPS
        self.text(f"{sps:,.0f} pasos/s" if sps >= 10 else f"{sps:.1f} pasos/s",
                  (X + W, 388), 11, TEXT_DIM, anchor="topright")
        self.slider.draw(self)

        self.draw_stats(X, W)
        self.draw_chart()
        self.text("F1 ayuda  ·  rueda del ratón = velocidad", (X + W / 2, 788), 11, TEXT_DIM, anchor="center")

    def draw_stats(self, X, W):
        info = self.info
        s = self.screen
        if self.task_kind == "maze":
            estado, ecol = "Generando", ACCENT_HI
        elif self.task_kind == "search":
            estado, ecol = ("Pausado", WARN) if self.paused else ("Buscando", OPEN_C)
        elif info["done"]:
            estado, ecol = ("Encontrado", PATH_C) if info["found"] else ("Sin camino", END_C)
        else:
            estado, ecol = "Listo", TEXT
        found = info["done"] and info["found"]
        data = [
            ("VISITADOS", f"{Node.closed_count:,}", CLOSED_LUT[200]),
            ("FRONTERA", f"{len(info['open']):,}", OPEN_C),
            ("PASOS", f"{info['steps']:,}", TEXT),
            ("LONGITUD", f"{len(info['path']) - 1}" if found else "-", PATH_C),
            ("COSTO", f"{info['g'][self.end]:.0f}" if found else "-", PATH_C),
            ("ESTADO", estado, ecol),
        ]
        cw = (W - 16) / 3
        for i, (lab, val, col) in enumerate(data):
            x = X + (i % 3) * (cw + 8)
            y = self.stats_y + (i // 3) * 52
            pygame.draw.rect(s, CARD, (x, y, cw, 46), border_radius=8)
            pygame.draw.rect(s, col, (x, y + 8, 3, 30), border_radius=2)
            self.text(lab, (x + 12, y + 6), 10, TEXT_DIM, True)
            self.text(val, (x + 12, y + 19), 18, col, True)
        self.text(f"cálculo: {info['compute'] * 1000:.2f} ms", (X + W, self.stats_y - 16), 11, TEXT_DIM,
                  anchor="topright")

    def draw_chart(self):
        s, R = self.screen, self.chart_rect
        pygame.draw.rect(s, CARD, R, border_radius=8)
        self.text("EXPLORACIÓN POR PASO", (R.x + 10, R.y + 8), 10, TEXT_DIM, True)
        lx = R.right - 10
        for name, col in (("frontera", OPEN_C), ("visitados", CLOSED_LUT[200])):
            rr = self.text(name, (lx, R.y + 8), 10, TEXT_DIM, anchor="topright")
            pygame.draw.rect(s, col, (rr.x - 12, rr.y + 3, 8, 8), border_radius=2)
            lx = rr.x - 22
        hist = self.info["history"]
        px, py, pw, ph = R.x + 10, R.y + 28, R.w - 20, R.h - 38
        for k in range(4):   # líneas guía
            yy = py + ph * k / 3
            pygame.draw.line(s, (36, 42, 62), (px, yy), (px + pw, yy))
        if len(hist) < 2:
            self.text("Ejecuta la búsqueda para ver la gráfica", (R.centerx, R.centery + 8), 11,
                      (80, 88, 110), anchor="center")
            return
        m = min(len(hist), pw)
        samp = [hist[int(i * (len(hist) - 1) / (m - 1))] for i in range(m)]
        maxv = max(1, max(v for _, v in samp))
        maxf = max(1, max(f for f, _ in samp))
        vis = [(px + i * pw / (m - 1), py + ph - v / maxv * ph) for i, (_, v) in enumerate(samp)]
        fro = [(px + i * pw / (m - 1), py + ph - f / maxf * ph) for i, (f, _) in enumerate(samp)]
        area = pygame.Surface((R.w, R.h), pygame.SRCALPHA)
        poly = [(x - R.x, y - R.y) for x, y in vis] + [(pw + 10, py + ph - R.y), (10, py + ph - R.y)]
        pygame.draw.polygon(area, (*CLOSED_LUT[200], 45), poly)
        s.blit(area, R.topleft)
        pygame.draw.lines(s, CLOSED_LUT[200], False, vis, 2)
        pygame.draw.lines(s, OPEN_C, False, fro, 2)
        pygame.draw.circle(s, OPEN_C, fro[-1], 3)
        pygame.draw.circle(s, CLOSED_LUT[200], vis[-1], 3)

    # ---------------- capas superiores ----------------
    def draw_tooltip(self):
        mx, my = pygame.mouse.get_pos()
        if mx >= WIDTH or self.help or self.drag:
            return
        node = self.node_at((mx, my))
        gv = self.info["g"].get(node, math.inf)
        if gv == math.inf:
            return
        hv = h(node.get_pos(), self.end.get_pos())
        lines = [f"nodo {node.get_pos()}" + (f"  ·  peso x{node.weight}" if node.weight > 1 else ""),
                 f"g = {gv:.0f}   h = {hv:.0f}   f = {gv + hv:.0f}"]
        if node.is_closed():
            lines.append(f"cerrado en el paso #{node.order + 1}")
        elif node.is_open():
            lines.append("en la frontera (open set)")
        w = max(self.font(12).size(l)[0] for l in lines) + 20
        hh = 10 + len(lines) * 17
        x, y = min(mx + 16, WIDTH - w - 6), min(my + 18, WIN_H - hh - 6)
        box = pygame.Surface((w, hh), pygame.SRCALPHA)
        pygame.draw.rect(box, (8, 10, 18, 225), box.get_rect(), border_radius=8)
        pygame.draw.rect(box, (*ACCENT, 160), box.get_rect(), 1, border_radius=8)
        self.screen.blit(box, (x, y))
        for i, l in enumerate(lines):
            self.text(l, (x + 10, y + 6 + i * 17), 12, TEXT if i == 0 else (190, 198, 220), i == 0)

    def draw_toast(self):
        if not self.toast_msg or self.help:
            return
        age = now() - self.toast_t
        if age > 2.6:
            return
        a = clamp(min(age / 0.15, (2.6 - age) / 0.4))
        f = self.font(14, True)
        w, hh = f.size(self.toast_msg)[0] + 36, 38
        y = WIDTH - 60 + (1 - ease_out_cubic(clamp(age / 0.25))) * 30
        box = pygame.Surface((w, hh), pygame.SRCALPHA)
        pygame.draw.rect(box, (10, 12, 22, int(230 * a)), box.get_rect(), border_radius=19)
        pygame.draw.rect(box, (*ACCENT, int(200 * a)), box.get_rect(), 1, border_radius=19)
        img = f.render(self.toast_msg, True, TEXT)
        img.set_alpha(int(255 * a))
        box.blit(img, img.get_rect(center=(w / 2, hh / 2)))
        self.screen.blit(box, (WIDTH / 2 - w / 2, y))

    def draw_help(self):
        veil = pygame.Surface((WIDTH, WIDTH), pygame.SRCALPHA)
        veil.fill((6, 8, 14, 215))
        self.screen.blit(veil, (0, 0))
        s = self.screen
        R = pygame.Rect(90, 100, WIDTH - 180, WIDTH - 200)
        pygame.draw.rect(s, PANEL_BG, R, border_radius=16)
        pygame.draw.rect(s, ACCENT, R, 1, border_radius=16)
        self.text("Controles", (R.x + 30, R.y + 24), 24, TEXT, True)
        items = [
            ("Clic izquierdo", "dibujar con la herramienta"),
            ("Clic derecho", "borrar"),
            ("Arrastrar inicio/fin", "moverlos (recalcula en vivo)"),
            ("ESPACIO", "ejecutar / pausar"),
            ("N  o  ->", "avanzar un paso"),
            ("C / X", "limpiar todo / limpiar ruta"),
            ("M / T", "laberinto / terreno"),
            ("H / V / L", "calor / valores / modo vivo"),
            ("G", "cambiar tamaño de cuadrícula"),
            ("+ / -  o rueda", "velocidad"),
            ("P", "guardar captura PNG"),
            ("F1 / ESC", "ayuda / cerrar"),
        ]
        for i, (k, d) in enumerate(items):
            y = R.y + 74 + i * 32
            pygame.draw.rect(s, CARD, (R.x + 30, y - 3, 190, 24), border_radius=6)
            self.text(k, (R.x + 40, y), 13, ACCENT_HI, True)
            self.text(d, (R.x + 240, y), 13, TEXT)
        self.text("verde = frontera  ·  azul = visitado  ·  dorado = camino  ·  marrón = peso",
                  (R.centerx, R.bottom - 30), 12, TEXT_DIM, anchor="center")

    # ---------------- bucle principal ----------------
    def draw(self):
        self.screen.fill(BG)
        self.draw_grid()
        self.draw_panel()
        if self.help:
            self.draw_help()
        else:
            self.draw_tooltip()
        self.draw_toast()

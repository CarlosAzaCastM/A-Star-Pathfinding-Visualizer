"""
Edición de celdas (muro, peso, vacío) y generadores de mapas animados.
Cada generador usa `yield` igual que algorithm(): la app lo avanza unos pasos por fotograma.
"""
import random

from .config import WEIGHT_COST
from .utilidades import now, lerp


def set_cell(node, kind, when=None):
    """Cambia el tipo de una celda: 'wall', 'weight' o 'empty'."""
    before = (node.color, node.weight)
    if kind == "wall":
        node.make_barrier()
        node.weight = 1
    else:
        if node.is_barrier():
            node.reset()
        node.weight = WEIGHT_COST if kind == "weight" else 1
    if (node.color, node.weight) != before:
        node.changed = now() if when is None else when
        return True
    return False


DIRS4 = [(-1, 0), (0, 1), (1, 0), (0, -1)]


def maze_backtracker(app):
    """Laberinto perfecto por 'backtracking' recursivo (con una pila)."""
    grid, n = app.grid, app.rows
    t = now()
    for i in range(n):
        for j in range(n):
            set_cell(grid[i][j], "wall", t + (i + j) * 0.004)   # ola diagonal
    yield
    first = (1, 1)
    set_cell(grid[1][1], "empty")
    stack, visited = [first], {first}
    while stack:
        cur = stack[-1]
        app.maze_head = grid[cur[0]][cur[1]]
        opts = [(cur[0] + di * 2, cur[1] + dj * 2) for di, dj in DIRS4]
        opts = [p for p in opts if 1 <= p[0] <= n - 2 and 1 <= p[1] <= n - 2 and p not in visited]
        if opts:
            nxt = random.choice(opts)
            mid = ((cur[0] + nxt[0]) // 2, (cur[1] + nxt[1]) // 2)
            set_cell(grid[mid[0]][mid[1]], "empty")
            set_cell(grid[nxt[0]][nxt[1]], "empty")
            visited.add(nxt)
            stack.append(nxt)
        else:
            stack.pop()
        yield
    app.maze_head = None
    # abrir algunos atajos para que haya más de un camino posible
    for _ in range(n * n // 70):
        i, j = random.randint(1, n - 2), random.randint(1, n - 2)
        node = grid[i][j]
        if node.is_barrier():
            hor = not grid[i - 1][j].is_barrier() and not grid[i + 1][j].is_barrier()
            ver = not grid[i][j - 1].is_barrier() and not grid[i][j + 1].is_barrier()
            if hor != ver:
                set_cell(node, "empty")
                yield


def maze_division(app):
    """División recursiva: parte el espacio con muros que tienen un hueco."""
    grid, n = app.grid, app.rows
    t = now()
    for i in range(n):
        for j in range(n):
            border = i in (0, n - 1) or j in (0, n - 1)
            set_cell(grid[i][j], "wall" if border else "empty", t + (i + j) * 0.003)
    yield
    stack = [(1, 1, n - 2, n - 2)]   # (i, j, alto, ancho)
    while stack:
        a, b, hh, ww = stack.pop()
        if hh < 3 or ww < 3:
            continue
        cut_i = (hh > ww) if hh != ww else random.random() < 0.5
        if cut_i:
            lines = [x for x in range(a + 1, a + hh - 1) if x % 2 == 0]
            gaps = [x for x in range(b, b + ww) if x % 2 == 1]
            if not lines or not gaps:
                continue
            w, gap = random.choice(lines), random.choice(gaps)
            for x in range(b, b + ww):
                if x != gap:
                    set_cell(grid[w][x], "wall")
                    app.maze_head = grid[w][x]
                    yield
            stack += [(a, b, w - a, ww), (w + 1, b, a + hh - w - 1, ww)]
        else:
            lines = [x for x in range(b + 1, b + ww - 1) if x % 2 == 0]
            gaps = [x for x in range(a, a + hh) if x % 2 == 1]
            if not lines or not gaps:
                continue
            w, gap = random.choice(lines), random.choice(gaps)
            for x in range(a, a + hh):
                if x != gap:
                    set_cell(grid[x][w], "wall")
                    app.maze_head = grid[x][w]
                    yield
            stack += [(a, b, hh, w - b), (a, w + 1, hh, b + ww - w - 1)]
    app.maze_head = None


def maze_random(app):
    """Obstáculos al azar (30 %)."""
    grid, n = app.grid, app.rows
    for i in range(n):
        for j in range(n):
            node = grid[i][j]
            if node in (app.start, app.end):
                continue
            set_cell(node, "wall" if random.random() < 0.3 else "empty", now() + random.random() * 0.15)
        yield


def maze_terrain(app):
    """Terreno con ruido suave: montañas (muro) y barro (peso)."""
    grid, n = app.grid, app.rows

    def layer(k):
        pts = [[random.random() for _ in range(k + 2)] for _ in range(k + 2)]

        def sample(i, j):
            fi, fj = i / (n - 1) * k, j / (n - 1) * k
            a, b = int(fi), int(fj)
            ti, tj = fi - a, fj - b
            ti, tj = ti * ti * (3 - 2 * ti), tj * tj * (3 - 2 * tj)
            top = lerp(pts[a][b], pts[a][b + 1], tj)
            bot = lerp(pts[a + 1][b], pts[a + 1][b + 1], tj)
            return lerp(top, bot, ti)
        return sample

    big, small = layer(max(3, n // 9)), layer(max(6, n // 4))
    for i in range(n):
        for j in range(n):
            node = grid[i][j]
            if node in (app.start, app.end):
                continue
            v = big(i, j) * 0.7 + small(i, j) * 0.3
            kind = "wall" if v > 0.64 else "weight" if v > 0.5 else "empty"
            set_cell(node, kind, now() + j * 0.002)
        yield


MAZES = [("Laberinto", maze_backtracker), ("División", maze_division),
         ("Aleatorio", maze_random), ("Terreno", maze_terrain)]

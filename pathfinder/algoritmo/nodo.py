"""
Nodo de la cuadrícula: posición, estado, peso y vecinos.
"""
from ..config import RED, GREEN, WHITE, BLACK, PURPLE, ORANGE, TURQUOISE
from ..utilidades import now


class Node:
    closed_count = 0   # cuántos nodos se han cerrado en la búsqueda actual (para el degradado)

    def __init__(self, row, col, width, total_rows):
        self.row = row
        self.col = col
        self.x = row * width
        self.y = col * width
        self.changed = -100.0   # instante del último cambio de estado (para animarlo)
        self.order = 0          # orden en que se cerró este nodo
        self.weight = 1         # costo de entrar a esta celda (1 normal, WEIGHT_COST con peso)
        self.color = WHITE
        self.neighbors = []
        self.width = width
        self.total_rows = total_rows

    # Cada vez que cambia el estado se guarda el instante, así la interfaz puede animarlo.
    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, value):
        if getattr(self, "_color", None) is not None and value != self._color:
            self.changed = now()
        if value == RED:
            self.order = Node.closed_count
            Node.closed_count += 1
        self._color = value

    def get_pos(self):
        return self.row, self.col

    # Métodos para identificar el estado del nodo
    def is_closed(self): return self.color == RED
    def is_open(self): return self.color == GREEN
    def is_barrier(self): return self.color == BLACK
    def is_start(self): return self.color == ORANGE
    def is_end(self): return self.color == TURQUOISE

    # Métodos para cambiar el estado del nodo
    def reset(self): self.color = WHITE
    def make_start(self): self.color = ORANGE
    def make_closed(self): self.color = RED
    def make_open(self): self.color = GREEN
    def make_barrier(self): self.color = BLACK
    def make_end(self): self.color = TURQUOISE
    def make_path(self): self.color = PURPLE

    def update_neighbors(self, grid):
        """Guarda los vecinos transitables en 4 direcciones."""
        self.neighbors = []
        # Abajo
        if self.row < self.total_rows - 1 and not grid[self.row + 1][self.col].is_barrier():
            self.neighbors.append(grid[self.row + 1][self.col])
        # Arriba
        if self.row > 0 and not grid[self.row - 1][self.col].is_barrier():
            self.neighbors.append(grid[self.row - 1][self.col])
        # Derecha
        if self.col < self.total_rows - 1 and not grid[self.row][self.col + 1].is_barrier():
            self.neighbors.append(grid[self.row][self.col + 1])
        # Izquierda
        if self.col > 0 and not grid[self.row][self.col - 1].is_barrier():
            self.neighbors.append(grid[self.row][self.col - 1])


def make_grid(rows, width):
    """Crea la cuadrícula de rows x rows nodos."""
    grid = []
    gap = width // rows
    for i in range(rows):
        grid.append([])
        for j in range(rows):
            node = Node(i, j, gap, rows)
            grid[i].append(node)
    return grid


def get_clicked_pos(pos, rows, width):
    """Convierte una posición del ratón en (fila, columna) de la cuadrícula."""
    gap = width // rows
    y, x = pos
    row = y // gap
    col = x // gap
    return row, col

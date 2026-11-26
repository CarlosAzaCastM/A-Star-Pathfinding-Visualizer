"""
Configuración general de la app: ventana, tablero, estados de los nodos y paleta de colores.
"""
import os

# Ventana: la cuadrícula ocupa un cuadrado de WIDTH px y a su derecha va el panel de control
WIDTH = 800
PANEL_W = 420
WIN_W, WIN_H = WIDTH + PANEL_W, WIDTH
FPS = 60
TITLE = "Pathfinder A*"

# Tablero
SIZES = [25, 40, 50, 80]   # filas por lado disponibles (todas dividen 800 exacto)
DEFAULT_ROWS = 50          # tamaño con el que arranca la app
WEIGHT_COST = 5            # costo de cruzar una celda con peso (terreno difícil)

# Carpeta donde se guardan las capturas de pantalla (junto a main.py)
CAPTURES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "capturas")

# Estados de un nodo. Cada estado se identifica con un color; el color con el
# que se ve en pantalla lo decide la paleta de abajo.
RED = (255, 0, 0)          # Nodos visitados (closed set)
GREEN = (0, 255, 0)        # Nodos por visitar (open set)
WHITE = (255, 255, 255)    # Nodos vacíos
BLACK = (0, 0, 0)          # Obstáculos
PURPLE = (128, 0, 128)     # Camino final
ORANGE = (255, 165, 0)     # Nodo inicio
TURQUOISE = (64, 224, 208) # Nodo fin

# Paleta visual (tema oscuro)
BG = (11, 13, 20)              # fondo de la ventana
PANEL_BG = (16, 19, 29)        # fondo del panel lateral
CARD = (25, 29, 43)            # tarjetas y botones
CARD_HI = (38, 44, 66)         # tarjetas y botones al pasar el ratón
EMPTY = (20, 24, 36)           # celda vacía
WALL = (220, 226, 238)         # obstáculo
WALL_SHADE = (160, 168, 188)   # cara inferior del obstáculo (efecto de bloque)
WEIGHT = (140, 92, 42)         # celda con peso
WEIGHT_DOT = (92, 58, 24)      # punto central de la celda con peso
OPEN_C = (60, 225, 170)        # frontera
CLOSED_FLASH = (255, 95, 215)  # destello de un nodo recién visitado
PATH_C = (255, 200, 60)        # línea del camino
PATH_CELL = (125, 98, 35)      # celdas del camino
START_C = (70, 230, 120)       # inicio
END_C = (255, 75, 105)         # fin
TEXT = (230, 234, 245)         # texto principal
TEXT_DIM = (125, 134, 158)     # texto secundario
ACCENT = (100, 130, 255)       # color de acento (botones activos, bordes)
ACCENT_HI = (130, 155, 255)    # acento claro
WARN = (255, 170, 70)          # avisos (pausa)

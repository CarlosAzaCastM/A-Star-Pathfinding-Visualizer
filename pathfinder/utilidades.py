"""
Utilidades de animación y color: tiempo, interpolación, curvas de suavizado
y degradados (LUT) para pintar los nodos visitados y el mapa de calor.
"""
import pygame


def now():
    return pygame.time.get_ticks() / 1000.0


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_c(c1, c2, t):
    return (int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t))


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def ease_out_back(t):
    c1 = 1.70158
    return 1 + (c1 + 1) * (t - 1) ** 3 + c1 * (t - 1) ** 2


def ease_out_cubic(t):
    return 1 - (1 - t) ** 3


def pop_scale(age, dur=0.32):
    """Escala de una celda que 'brota' (0 -> 1 con un pequeño rebote)."""
    if age < 0:
        return 0.0
    if age >= dur:
        return 1.0
    return max(0.0, ease_out_back(age / dur))


def make_lut(stops):
    lut = []
    for i in range(256):
        t = i / 255 * (len(stops) - 1)
        k = min(int(t), len(stops) - 2)
        lut.append(lerp_c(stops[k], stops[k + 1], t - k))
    return lut


CLOSED_LUT = make_lut([(32, 40, 115), (45, 85, 200), (40, 170, 235), (130, 228, 255)])
TURBO_LUT = make_lut([(48, 18, 59), (65, 105, 225), (30, 200, 210),
                      (120, 240, 90), (250, 210, 40), (240, 90, 30), (170, 20, 20)])

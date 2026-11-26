"""
Widgets de la interfaz: botones animados y slider de velocidad.
"""
import pygame

from ..config import *
from ..utilidades import lerp_c, clamp


class Button:
    def __init__(self, rect, text, action, active=None, primary=False, size=13):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.action = action
        self.active = active
        self.primary = primary
        self.size = size
        self.hover = 0.0
        self.flash = 0.0

    def draw(self, app, mouse):
        self.hover += ((1.0 if self.rect.collidepoint(mouse) else 0.0) - self.hover) * 0.25
        self.flash *= 0.85
        act = self.active() if self.active else False
        if self.primary:
            col = lerp_c(ACCENT, ACCENT_HI, self.hover)
        elif act:
            col = lerp_c((62, 82, 190), (80, 102, 215), self.hover)
        else:
            col = lerp_c(CARD, CARD_HI, self.hover)
        col = lerp_c(col, (255, 255, 255), self.flash * 0.35)
        r = self.rect
        if act or self.primary:
            glow = pygame.Surface((r.w + 12, r.h + 12), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*ACCENT, 45), glow.get_rect(), border_radius=12)
            app.screen.blit(glow, (r.x - 6, r.y - 6))
        pygame.draw.rect(app.screen, col, r, border_radius=8)
        if act:
            pygame.draw.rect(app.screen, ACCENT_HI, r, 1, border_radius=8)
        label = self.text() if callable(self.text) else self.text
        app.text(label, r.center, self.size, TEXT if (act or self.primary) else (200, 206, 222),
                 bold=act or self.primary, anchor="center")

    def click(self, pos):
        if self.rect.collidepoint(pos):
            self.flash = 1.0
            self.action()
            return True
        return False


class Slider:
    def __init__(self, rect, value):
        self.rect = pygame.Rect(rect)
        self.value = value
        self.drag = False

    def set_from(self, x):
        self.value = clamp((x - self.rect.x) / self.rect.w)

    def down(self, pos):
        if self.rect.inflate(16, 20).collidepoint(pos):
            self.drag = True
            self.set_from(pos[0])
            return True
        return False

    def draw(self, app):
        r, s = self.rect, app.screen
        pygame.draw.rect(s, CARD_HI, r, border_radius=4)
        fw = int(r.w * self.value)
        for i in range(0, fw, 3):
            s.fill(lerp_c((60, 210, 180), ACCENT, i / r.w), (r.x + i, r.y, min(3, fw - i), r.h))
        kx = r.x + fw
        pygame.draw.circle(s, (255, 255, 255), (kx, r.centery), 9)
        pygame.draw.circle(s, ACCENT, (kx, r.centery), 5)

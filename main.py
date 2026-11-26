"""
Pathfinder A* — visualizador interactivo del algoritmo A*.

Ejecutar:  python main.py
"""
import pygame

from pathfinder.interfaz.app import App


def main():
    pygame.init()
    App().run()


if __name__ == "__main__":
    main()

# Pathfinder A*

Visualizador interactivo del algoritmo **A\*** hecho con Pygame. En una cuadrícula puedes dibujar obstáculos y terreno difícil, generar laberintos y ver en tiempo real cómo A\* explora hasta encontrar el camino de menor costo.

## Cómo ejecutarlo

```bash
pip install -r requirements.txt
python main.py
```

En Windows, con el entorno virtual incluido:

```bash
env\Scripts\activate
python main.py
```

Si el entorno `env` no funciona en otra computadora (guarda la ruta de la PC donde se creó), instala las dependencias con `pip install -r requirements.txt`.

## Cómo funciona

A\* elige siempre el nodo con menor `f(n) = g(n) + h(n)`:

- `g(n)`: costo acumulado desde el inicio. Una celda normal cuesta 1 y una celda con peso cuesta 5.
- `h(n)`: distancia Manhattan hasta el fin. Es admisible porque ningún paso cuesta menos de 1, así que el camino encontrado siempre es el óptimo.

El movimiento es en 4 direcciones y la frontera se guarda en una `PriorityQueue`.

## Funciones

- **Edición:** muros, celdas con peso (x5) y borrador. El inicio y el fin se pueden arrastrar.
- **Ejecución:** pausa, paso a paso y velocidad ajustable (de unos pocos pasos por segundo a miles).
- **Modo vivo:** después de una búsqueda, cualquier cambio en el tablero recalcula la ruta al instante.
- **Generadores de mapas:** laberinto (backtracking), división recursiva, obstáculos aleatorios y terreno con ruido.
- **Visualización:** animaciones de cada nodo, mapa de calor según `g`, valores `f/g/h` sobre las celdas, tooltip con los datos de cada nodo y un agente que recorre la ruta final.
- **Estadísticas:** nodos visitados, tamaño de la frontera, pasos, longitud y costo del camino, tiempo de cálculo y gráfica en vivo de la exploración.
- **Capturas:** se guardan en la carpeta `capturas/`.

## Controles

| Tecla / acción | Qué hace |
|---|---|
| Clic izquierdo | dibujar con la herramienta (muro / peso / borrar) |
| Clic derecho | borrar |
| Arrastrar inicio/fin | moverlos |
| ESPACIO | ejecutar / pausar |
| N o → | avanzar un paso |
| C / X | limpiar todo / limpiar solo la ruta |
| M / T | laberinto / terreno |
| H / V / L | mapa de calor / valores f,g,h / modo vivo |
| G | cambiar tamaño de cuadrícula |
| + / − o rueda | velocidad |
| P | guardar captura PNG |
| F1 / ESC | ayuda / cerrar |

## Estructura del proyecto

```
main.py                    punto de entrada
requirements.txt           dependencias
pathfinder/
    config.py              ventana, tablero, estados y paleta de colores
    utilidades.py          tiempo, interpolación, animaciones y degradados
    mapas.py               edición de celdas y generadores de mapas
    algoritmo/
        nodo.py            clase Node y creación de la cuadrícula
        astar.py           heurística, reconstrucción del camino y algoritmo A*
    interfaz/
        app.py             estado, acciones, eventos y bucle principal
        dibujo.py          todo lo que se pinta en pantalla
        widgets.py         botones y slider
capturas/                  se crea al guardar la primera captura
env/                       entorno virtual de Windows
```

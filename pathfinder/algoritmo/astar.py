"""
Algoritmo A* con cola de prioridad y heurística Manhattan.

algorithm() es un generador: cada `yield` corresponde a una expansión, así la
interfaz puede avanzar la búsqueda unos pasos por fotograma, pausarla o ir paso a paso.
"""
from queue import PriorityQueue


# Distancia Manhattan (heurística)
def h(p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    return abs(x1 - x2) + abs(y1 - y2)


def reconstruct_path(came_from, current, path):
    """Recorre came_from desde el fin hasta el inicio, marcando y guardando el camino."""
    while current in came_from:
        current = came_from[current]
        current.make_path()
        path.append(current)
        yield   # un nodo del camino por paso: la interfaz lo anima


def algorithm(grid, start, end, info):
    """
    Busca el camino de menor costo de start a end.
    info es un diccionario compartido con la interfaz: aquí se publican g, la frontera
    y el camino para mostrar estadísticas, mapa de calor y tooltip.
    Devuelve True si encontró camino y False si no existe.
    """
    count = 0
    open_set = PriorityQueue()
    open_set.put((0, count, start))
    came_from = {}

    g_score = {node: float("inf") for row in grid for node in row}
    g_score[start] = 0

    f_score = {node: float("inf") for row in grid for node in row}
    f_score[start] = h(start.get_pos(), end.get_pos())

    open_set_hash = {start}

    info["g"] = g_score
    info["open"] = open_set_hash

    while not open_set.empty():
        current = open_set.get()[2]
        open_set_hash.remove(current)

        # Si llegamos al final, reconstruimos el camino
        if current == end:
            info["path"] = [end]
            yield from reconstruct_path(came_from, end, info["path"])
            end.make_end()
            start.make_start()   # reconstruct_path también marca el inicio como camino
            return True

        for neighbor in current.neighbors:
            temp_g_score = g_score[current] + neighbor.weight   # costo de entrar al vecino

            if temp_g_score < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = temp_g_score
                f_score[neighbor] = temp_g_score + h(neighbor.get_pos(), end.get_pos())

                if neighbor not in open_set_hash:
                    count += 1
                    open_set.put((f_score[neighbor], count, neighbor))
                    open_set_hash.add(neighbor)
                    neighbor.make_open()

        yield   # fin de una expansión: la interfaz dibuja este paso

        if current != start:
            current.make_closed()

    return False

"""Dijkstra acotado con heapq."""
import heapq
from typing import Dict, List, Optional, Tuple


def dijkstra_acotado(adj, origen: int, limite: float) -> Tuple[Dict[int, float], Dict[int, int]]:
    """Distancias mínimas desde `origen` (respetando sentido) hasta nodos con d <= limite.

    Devuelve (dist, padre); `padre` permite reconstruir la ruta vial.
    """
    dist = {origen: 0.0}
    padre: Dict[int, int] = {}
    hecho = set()
    cola = [(0.0, origen)]
    while cola:
        d, u = heapq.heappop(cola)
        if u in hecho:
            continue
        if d > limite:
            break
        hecho.add(u)
        for v, w, _ in adj.get(u, ()):
            nd = d + w
            if nd <= limite and nd < dist.get(v, float("inf")):
                dist[v] = nd
                padre[v] = u
                heapq.heappush(cola, (nd, v))
    return dist, padre


def reconstruir_ruta(padre: Dict[int, int], origen: int, destino: int) -> Optional[List[int]]:
    """Lista de nodos origen -> destino, o None si no es alcanzable."""
    if destino != origen and destino not in padre:
        return None
    ruta = [destino]
    while ruta[-1] != origen:
        ruta.append(padre[ruta[-1]])
    ruta.reverse()
    return ruta


def invertir(adj):
    """Grafo transpuesto (para cobertura 'hacia' un nodo)."""
    inv = {u: [] for u in adj}
    for u, lst in adj.items():
        for v, w, nom in lst:
            inv.setdefault(v, []).append((u, w, nom))
    return inv

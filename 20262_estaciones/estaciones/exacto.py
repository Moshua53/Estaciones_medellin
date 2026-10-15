"""Parte 3: Branch & Bound exacto con máscaras de bits (combinaciones propias, solo stdlib permitida)."""
from typing import Dict, List, Optional, Tuple

from .alcance import Alcance
from .datos import TIPOS
from .evaluacion import Propuesta, resumen
from .heuristicas import HEURISTICAS, busqueda_local_swap


def mejor_propuesta_exacta(al: Alcance, usar_heuristicas: bool = True,
                           limite_nodos: Optional[int] = None) -> Tuple[Propuesta, dict]:
    """Óptimo global garantizado. Devuelve (propuesta, estadísticas).

    - Una sola máscara `int` por estado; los bits de cada tipo ocupan un rango propio.
    - Cota inferior inicial: mejor heurística (+ búsqueda local).
    - Poda 1: valor de (cubierto | unión de máscaras de sufijo), ignorando presupuesto.
    - Poda 2: relajación fraccionaria de mochila con el presupuesto restante.
    - Desempate canónico entre óptimos: menor costo, luego orden lexicográfico.
    """
    inst = al.inst
    tipos = [t for t in TIPOS if t in al.pesos] + [t for t in al.pesos if t not in TIPOS]
    off, tm, pos = {}, {}, 0
    for t in tipos:
        n = len(al.ids_por_tipo[t])
        off[t] = pos
        tm[t] = ((1 << n) - 1) << pos
        pos += n
    peso = [al.pesos[t] for t in tipos]
    tmasks = [tm[t] for t in tipos]

    def valor(m: int) -> int:
        return sum(w * (m & k).bit_count() for w, k in zip(peso, tmasks))

    # opciones por lote (solo estaciones que cubren algo); lotes ordenados por potencial
    lotes = []
    for l, _, _ in inst.lotes:
        ops = []
        for t in tipos:
            m = al.mascara[(l, t)] << off[t]
            if m:
                ops.append((t, al.costo[(l, t)], m))
        if ops:
            lotes.append((l, ops))
    lotes.sort(key=lambda x: (-max(valor(m) for _, _, m in x[1]), x[0]))
    n = len(lotes)
    suf = [0] * (n + 1)
    for i in range(n - 1, -1, -1):
        u = suf[i + 1]
        for _, _, m in lotes[i][1]:
            u |= m
        suf[i] = u

    presup = inst.presupuesto
    mejor_v, mejor_est, mejor_c = -1, [], 0

    def clave(est):
        return sorted(est)

    if usar_heuristicas:
        for f in HEURISTICAS.values():
            for p in (f(al), busqueda_local_swap(al, f(al))):
                if p.valor > mejor_v or (p.valor == mejor_v and
                                         (p.costo_total, clave(p.estaciones)) < (mejor_c, clave(mejor_est))):
                    mejor_v, mejor_est, mejor_c = p.valor, list(p.estaciones), p.costo_total
    stats = {"nodos": 0, "podas_union": 0, "podas_mochila": 0, "cota_inicial": mejor_v}

    def cota_mochila(i: int, cub: int, rest: int, v_actual: int) -> float:
        items = []
        for j in range(i, n):
            for _, c, m in lotes[j][1]:
                g = valor(m & ~cub)
                if g > 0 and c <= rest:
                    items.append((g / c, g, c))
        items.sort(reverse=True)
        total, r = float(v_actual), rest
        for _, g, c in items:
            if c <= r:
                total += g; r -= c
            else:
                total += g * r / c
                break
        return total

    def dfs(i: int, cub: int, rest: int, v: int, costo: int, est: list):
        nonlocal mejor_v, mejor_est, mejor_c
        stats["nodos"] += 1
        if limite_nodos and stats["nodos"] > limite_nodos:
            raise TimeoutError("límite de nodos")
        if v > mejor_v or (v == mejor_v and (costo, clave(est)) < (mejor_c, clave(mejor_est))):
            mejor_v, mejor_est, mejor_c = v, list(est), costo
        if i == n:
            return
        if valor(cub | suf[i]) < mejor_v:
            stats["podas_union"] += 1
            return
        if cota_mochila(i, cub, rest, v) < mejor_v:
            stats["podas_mochila"] += 1
            return
        l, ops = lotes[i]
        # ramas: construir cada tipo factible, o no construir
        for t, c, m in ops:
            if c <= rest and (m & ~cub):
                est.append((l, t))
                nc = cub | m
                dfs(i + 1, nc, rest - c, valor(nc), costo + c, est)
                est.pop()
        dfs(i + 1, cub, rest, v, costo, est)

    dfs(0, 0, presup, 0, 0, [])
    return resumen(al, mejor_est), stats

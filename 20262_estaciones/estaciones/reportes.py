"""Tablas y textos de reporte (sin dependencias externas)."""
import time
from typing import Dict, List

from .alcance import Alcance
from .evaluacion import Propuesta, mascaras_cubiertas


def _m(x: int) -> str:
    """Miles con punto (formato es-CO)."""
    return f"{x:,}".replace(",", ".")


def tabla_estaciones(al: Alcance, p: Propuesta) -> List[dict]:
    """Una fila por estación: lote, tipo, costo, casos que cubre y aporte marginal (orden de construcción por lote)."""
    filas, cub = [], {t: 0 for t in al.pesos}
    for lote, t in p.estaciones:
        m = al.mascara[(lote, t)]
        nuevos = (m & ~cub[t]).bit_count()
        cub[t] |= m
        filas.append({"lote": lote, "tipo": t, "costo": al.costo[(lote, t)],
                      "casos_cubre": m.bit_count(), "casos_nuevos": nuevos,
                      "valor_aporte": nuevos * al.pesos[t]})
    return filas


def texto_tabla(al: Alcance, p: Propuesta) -> str:
    filas = tabla_estaciones(al, p)
    out = [f"{'Lote':<6}{'Tipo':<11}{'Costo (M)':>10}{'Casos que cubre':>17}{'Casos nuevos':>14}{'Valor':>7}"]
    for f in filas:
        out.append(f"{f['lote']:<6}{f['tipo']:<11}{_m(f['costo']):>10}{f['casos_cubre']:>17}{f['casos_nuevos']:>14}{f['valor_aporte']:>7}")
    out.append("-" * 65)
    out.append(f"Costo total: {_m(p.costo_total)} M de {_m(al.inst.presupuesto)} M "
               f"(sobran {_m(al.inst.presupuesto - p.costo_total)} M)")
    tot = {t: sum(1 for i, (_, tt, _) in al.inst.incidentes.items() if tt == t) for t in al.pesos}
    out.append("Casos cubiertos: " + ", ".join(f"{t} {p.casos_cubiertos[t]}/{tot[t]}" for t in al.pesos))
    out.append(f"Valor de la propuesta: {p.valor}")
    return "\n".join(out)


def html_tabla(al: Alcance, p: Propuesta) -> str:
    filas = tabla_estaciones(al, p)
    h = ["<table><thead><tr><th>Lote</th><th>Tipo</th><th>Costo (M)</th><th>Casos que cubre</th>"
         "<th>Casos nuevos</th><th>Valor aportado</th></tr></thead><tbody>"]
    for f in filas:
        h.append(f"<tr><td>{f['lote']}</td><td>{f['tipo']}</td><td>{f['costo']:,}</td>"
                 f"<td>{f['casos_cubre']}</td><td>{f['casos_nuevos']}</td><td>{f['valor_aporte']}</td></tr>")
    tot = {t: sum(1 for _, (_, tt, _) in al.inst.incidentes.items() if tt == t) for t in al.pesos}
    h.append(f"</tbody><tfoot><tr><th colspan='2'>Total</th><th>{p.costo_total:,} / {al.inst.presupuesto:,}</th>"
             f"<th colspan='2'>" + ", ".join(f"{t} {p.casos_cubiertos[t]}/{tot[t]}" for t in al.pesos) +
             f"</th><th>{p.valor}</th></tr></tfoot></table>")
    return "".join(h)


def tabla_comparativa(al_por_instancia: Dict[str, Alcance], heuristicas: dict, exacto_en=("pequena", "comuna"),
                      con_swap=True) -> List[dict]:
    """Valor y tiempo de cada método por instancia (tiempos con perf_counter)."""
    from .exacto import mejor_propuesta_exacta
    from .heuristicas import busqueda_local_swap
    filas = []
    for nom, al in al_por_instancia.items():
        for k, f in heuristicas.items():
            t0 = time.perf_counter(); p = f(al); dt = time.perf_counter() - t0
            filas.append({"instancia": nom, "metodo": k, "valor": p.valor, "costo": p.costo_total, "tiempo_s": dt})
            if con_swap:
                t0 = time.perf_counter(); s = busqueda_local_swap(al, p); ds = time.perf_counter() - t0
                filas.append({"instancia": nom, "metodo": k + " + swap", "valor": s.valor,
                              "costo": s.costo_total, "tiempo_s": dt + ds})
        if nom in exacto_en:
            t0 = time.perf_counter(); p, _ = mejor_propuesta_exacta(al); dt = time.perf_counter() - t0
            filas.append({"instancia": nom, "metodo": "EXACTO (B&B)", "valor": p.valor,
                          "costo": p.costo_total, "tiempo_s": dt})
        else:
            filas.append({"instancia": nom, "metodo": "EXACTO (B&B)", "valor": None, "costo": None, "tiempo_s": None})
    return filas


def demostracion_ciudad(n_lotes: int = 80, tipos_por_lote: int = 3, evals_por_s: float = 1e9) -> str:
    estados = (tipos_por_lote + 1) ** n_lotes     # cada lote: nada o uno de los 3 tipos
    segundos = estados / evals_por_s
    anios = segundos / (365.25 * 24 * 3600)
    return (f"Cada uno de los {n_lotes} lotes admite 4 decisiones (no construir, CAI, tránsito o bomberos): "
            f"4^{n_lotes} = {estados:.3e} configuraciones. Aun descartando las que exceden el presupuesto "
            f"y evaluando 10^9 configuraciones por segundo, enumerarlas tomaría ≈ {segundos:.2e} s "
            f"≈ {anios:.2e} años (la edad del universo es ≈ 1,4×10^10 años). El Branch & Bound garantiza "
            f"el óptimo pero su peor caso sigue siendo exponencial, por lo que en `ciudad` solo reportamos "
            f"heurísticas y búsqueda local, sin garantía de optimalidad.")


# ---- asignación, rutas de despacho y candidatos --------------------------------
def asignar_incidentes(al: Alcance, p: Propuesta) -> Dict[int, tuple]:
    """Incidente cubierto -> (lote, distancia_m) de la estación de su tipo más cercana
    (la que despacharía el vehículo). Empates: menor código de lote."""
    inst = al.inst
    asign = {}
    for lote, t in p.estaciones:
        r = inst.radio(t)
        d_lote = al.dist[lote]
        for i in al.cubiertos[(lote, t)]:
            d = d_lote[inst.incidentes[i][0]]
            if d <= r and (i not in asign or (d, lote) < (asign[i][1], asign[i][0])):
                asign[i] = (lote, d)
    return asign


def ruta_despacho(al: Alcance, lote: str, id_incidente: int) -> dict:
    """Ruta calle por calle desde el lote hasta el incidente (tramos consecutivos de la misma calle se fusionan)."""
    from .grafo import reconstruir_ruta
    inst = al.inst
    origen = next(n for l, n, _ in inst.lotes if l == lote)
    destino = inst.incidentes[id_incidente][0]
    nodos = reconstruir_ruta(al.padre[lote], origen, destino)
    if nodos is None:
        return {"nodos": None, "tramos": [], "total_m": None, "coords": []}
    tramos = []
    for u, v in zip(nodos, nodos[1:]):
        w, nom = min(((w, nom) for x, w, nom in inst.adj[u] if x == v), key=lambda z: z[0])
        nom = nom or "(vía sin nombre)"
        if tramos and tramos[-1]["calle"] == nom:
            tramos[-1]["metros"] += w; tramos[-1]["hasta"] = v
        else:
            tramos.append({"calle": nom, "metros": w, "desde": u, "hasta": v})
    return {"nodos": nodos, "tramos": tramos, "total_m": sum(t["metros"] for t in tramos),
            "coords": [inst.nodos[n] for n in nodos]}


def nodos_candidatos(al: Alcance, p: Propuesta, k: int = 3) -> List[dict]:
    """Sugiere k nodos de la red (futuros lotes) por cobertura voraz del valor NO cubierto.
    Un nodo n cubre un incidente de tipo t si dist(n -> incidente) <= radio_t (Dijkstra sobre
    el grafo transpuesto). Se evalúa el mejor tipo de estación para cada nodo elegido."""
    from .grafo import dijkstra_acotado, invertir
    inst = al.inst
    inv = invertir(inst.adj)
    cubiertos = set(p.ids_cubiertos)
    # grupos (tipo, nodo) con peso de lo no cubierto
    grupos = {}
    for i, (n, t, _) in inst.incidentes.items():
        if i not in cubiertos:
            grupos.setdefault((t, n), 0)
            grupos[(t, n)] += al.pesos[t]
    cobertura = {}                     # (tipo, nodo candidato) -> [claves de grupo]
    for (t, n) in grupos:
        dist, _ = dijkstra_acotado(inv, n, inst.radio(t))
        for c in dist:
            cobertura.setdefault((t, c), []).append((t, n))
    res, tomados = [], set()
    for _ in range(k):
        mejor, mv = None, 0
        for (t, c), gs in cobertura.items():
            v = sum(grupos[g] for g in gs if g not in tomados)
            if v > mv:
                mejor, mv = (t, c), v
        if mejor is None:
            break
        t, c = mejor
        nuevos = [g for g in cobertura[mejor] if g not in tomados]
        tomados.update(nuevos)
        res.append({"nodo": c, "tipo": t, "valor_adicional": mv, "lat": inst.nodos[c][0], "lon": inst.nodos[c][1],
                    "incidentes": sum(len(inst.inc_por_tipo_nodo[g]) for g in nuevos)})
    return res

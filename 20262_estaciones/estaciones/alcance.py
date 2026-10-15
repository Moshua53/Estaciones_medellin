"""Parte 1: costo y alcance de cada (lote, tipo)."""
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from .datos import Instancia, TIPOS, costo_estacion
from .grafo import dijkstra_acotado


@dataclass
class Alcance:
    inst: Instancia
    # (lote, tipo) -> costo, ids ordenados y máscara de bits sobre el índice por tipo
    costo: Dict[Tuple[str, str], int] = field(default_factory=dict)
    cubiertos: Dict[Tuple[str, str], List[int]] = field(default_factory=dict)
    mascara: Dict[Tuple[str, str], int] = field(default_factory=dict)
    # por lote: dist y padre del Dijkstra acotado (para rutas en mapas)
    dist: Dict[str, Dict[int, float]] = field(default_factory=dict)
    padre: Dict[str, Dict[int, int]] = field(default_factory=dict)
    # índice de bit de cada incidente dentro de su tipo
    bit: Dict[int, int] = field(default_factory=dict)
    ids_por_tipo: Dict[str, List[int]] = field(default_factory=dict)
    pesos: Dict[str, int] = field(default_factory=dict)

    def valor_mascara(self, tipo: str, m: int) -> int:
        return self.pesos[tipo] * m.bit_count()


def calcular_alcance(inst: Instancia) -> Alcance:
    al = Alcance(inst)
    al.pesos = {t: inst.peso(t) for t in inst.tipos}
    tipos = [t for t in TIPOS if t in inst.tipos] + [t for t in inst.tipos if t not in TIPOS]
    for t in tipos:
        ids = sorted(i for i, (_, tt, _) in inst.incidentes.items() if tt == t)
        al.ids_por_tipo[t] = ids
        for k, i in enumerate(ids):
            al.bit[i] = k
    max_r = max(inst.radio(t) for t in tipos)
    for lote, nodo, factor in inst.lotes:
        dist, padre = dijkstra_acotado(inst.adj, nodo, max_r)   # UN Dijkstra por lote
        al.dist[lote], al.padre[lote] = dist, padre
        for t in tipos:
            r = inst.radio(t)
            ids, m = [], 0
            for n, d in dist.items():
                if d <= r:
                    for i in inst.inc_por_tipo_nodo.get((t, n), ()):
                        ids.append(i)
                        m |= 1 << al.bit[i]
            ids.sort()
            al.costo[(lote, t)] = costo_estacion(inst.tipos[t]["costo_base"], factor)
            al.cubiertos[(lote, t)] = ids
            al.mascara[(lote, t)] = m
    return al


def con_presupuesto(al: Alcance, presupuesto: int) -> Alcance:
    """Copia superficial del alcance con otro presupuesto (el alcance no depende de él)."""
    from dataclasses import replace
    inst2 = replace(al.inst, params={**al.inst.params, "presupuesto_millones": int(presupuesto)})
    return replace(al, inst=inst2)


def con_pesos(al: Alcance, pesos: Dict[str, int]) -> Alcance:
    """Copia superficial del alcance con otros pesos de prioridad (tampoco afecta las máscaras)."""
    from dataclasses import replace
    tipos = {t: {**d, "peso": pesos.get(t, d["peso"])} for t, d in al.inst.params["tipos"].items()}
    inst2 = replace(al.inst, params={**al.inst.params, "tipos": tipos})
    return replace(al, inst=inst2, pesos={t: tipos[t]["peso"] for t in al.pesos})

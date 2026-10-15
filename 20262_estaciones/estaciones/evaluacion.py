"""Evaluación de propuestas (valor, costo, casos cubiertos)."""
from dataclasses import dataclass
from typing import Dict, List, Tuple

from .alcance import Alcance
from .datos import TIPOS

Estacion = Tuple[str, str]  # (lote, tipo)


@dataclass
class Propuesta:
    estaciones: List[Estacion]
    costo_total: int
    casos_cubiertos: Dict[str, int]
    valor: int
    ids_cubiertos: List[int]

    def como_dict(self) -> dict:
        return {"estaciones": self.estaciones, "costo_total": self.costo_total,
                "casos_cubiertos": self.casos_cubiertos, "valor": self.valor}


def mascaras_cubiertas(al: Alcance, estaciones) -> Dict[str, int]:
    m = {t: 0 for t in al.pesos}
    for lote, t in estaciones:
        m[t] |= al.mascara[(lote, t)]
    return m


def valor_de(al: Alcance, estaciones) -> int:
    m = mascaras_cubiertas(al, estaciones)
    return sum(al.pesos[t] * m[t].bit_count() for t in m)


def resumen(al: Alcance, estaciones) -> Propuesta:
    est = sorted(estaciones, key=lambda e: (e[0], TIPOS.index(e[1]) if e[1] in TIPOS else 99))
    m = mascaras_cubiertas(al, est)
    casos = {t: m[t].bit_count() for t in al.pesos}
    ids = []
    for t, mk in m.items():
        for k, i in enumerate(al.ids_por_tipo[t]):
            if (mk >> k) & 1:
                ids.append(i)
    return Propuesta(est, sum(al.costo[e] for e in est), casos,
                     sum(al.pesos[t] * casos[t] for t in casos), sorted(ids))

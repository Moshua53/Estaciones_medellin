"""Parte 2: heurística base, heurísticas propias y búsqueda local 1-swap."""
from typing import Callable, Dict, List, Optional

from .alcance import Alcance
from .datos import TIPOS
from .evaluacion import Estacion, Propuesta, mascaras_cubiertas, resumen, valor_de


def _candidatos(al: Alcance):
    """Todas las (lote, tipo) en el orden del desempate oficial."""
    tipos = [t for t in TIPOS if t in al.pesos] + [t for t in al.pesos if t not in TIPOS]
    return [(l, t) for l, _, _ in al.inst.lotes for t in tipos]


def _vm(al: Alcance, cub: Dict[str, int], c: Estacion) -> int:
    """Valor marginal de c dado lo ya cubierto."""
    nuevo = al.mascara[c] & ~cub[c[1]]
    return al.pesos[c[1]] * nuevo.bit_count()


def _construir(al: Alcance, puntaje: Callable, presupuesto: Optional[int] = None,
               paso_factible: Optional[Callable] = None) -> List[Estacion]:
    """Esqueleto: en cada paso elige el candidato factible de mayor `puntaje`
    (empates -> primero en el orden oficial, porque se usa '>' estricto)."""
    rest = al.inst.presupuesto if presupuesto is None else presupuesto
    cub = {t: 0 for t in al.pesos}
    usados, elegidas = set(), []
    cands = _candidatos(al)
    while True:
        mejor, mejor_p = None, None
        for c in cands:
            if c[0] in usados or al.costo[c] > rest:
                continue
            vm = _vm(al, cub, c)
            if vm <= 0:
                continue
            p = puntaje(al, cub, c, vm, rest, usados)
            if mejor is None or p > mejor_p:
                mejor, mejor_p = c, p
        if mejor is None:
            break
        elegidas.append(mejor)
        usados.add(mejor[0])
        rest -= al.costo[mejor]
        cub[mejor[1]] |= al.mascara[mejor]
    return elegidas


# ---- 2.1 base ---------------------------------------------------------------
def heuristica_base(al: Alcance) -> Propuesta:
    return resumen(al, _construir(al, lambda al_, cub, c, vm, rest, us: vm))


# ---- 2.2 propias ------------------------------------------------------------
def eficiencia_marginal(al: Alcance) -> Propuesta:
    """Maximiza valor_marginal / costo."""
    return resumen(al, _construir(al, lambda al_, cub, c, vm, rest, us: vm / al_.costo[c]))


def lookahead_1_paso(al: Alcance) -> Propuesta:
    """Elige c1 que maximiza vm(c1) + max_{c2 factible tras c1} vm(c2 | c1)."""
    cands = _candidatos(al)

    def puntaje(al_, cub, c1, vm1, rest, usados):
        rest2 = rest - al_.costo[c1]
        cub2 = dict(cub)
        cub2[c1[1]] |= al_.mascara[c1]
        mejor2 = 0
        for c2 in cands:
            if c2[0] == c1[0] or c2[0] in usados or al_.costo[c2] > rest2:
                continue
            v = _vm(al_, cub2, c2)
            if v > mejor2:
                mejor2 = v
        return vm1 + mejor2

    return resumen(al, _construir(al, puntaje))


def hibrida_adaptativa(al: Alcance, expo: float = 0.75, frac_llenado: float = 0.25) -> Propuesta:
    """Fase 1: maximiza vm / costo**expo mientras quede más de `frac_llenado` del
    presupuesto. Fase 2 (llenado del remanente): criterio base (máx. valor marginal)
    con lo que sobre, para no dejar plata sin usar."""
    total = al.inst.presupuesto
    umbral = frac_llenado * total

    def fase1(al_, cub, c, vm, rest, us):
        return vm / (al_.costo[c] ** expo)

    elegidas: List[Estacion] = []
    rest = total
    cub = {t: 0 for t in al.pesos}
    usados = set()
    cands = _candidatos(al)
    # fase 1
    while rest > umbral:
        mejor, mp = None, None
        for c in cands:
            if c[0] in usados or al.costo[c] > rest:
                continue
            vm = _vm(al, cub, c)
            if vm <= 0:
                continue
            p = fase1(al, cub, c, vm, rest, usados)
            if mejor is None or p > mp:
                mejor, mp = c, p
        if mejor is None:
            break
        elegidas.append(mejor); usados.add(mejor[0]); rest -= al.costo[mejor]
        cub[mejor[1]] |= al.mascara[mejor]
    # fase 2: llenado con valor marginal puro
    while True:
        mejor, mv = None, 0
        for c in cands:
            if c[0] in usados or al.costo[c] > rest:
                continue
            v = _vm(al, cub, c)
            if v > mv:
                mejor, mv = c, v
        if mejor is None:
            break
        elegidas.append(mejor); usados.add(mejor[0]); rest -= al.costo[mejor]
        cub[mejor[1]] |= al.mascara[mejor]
    return resumen(al, elegidas)


HEURISTICAS = {
    "base": heuristica_base,
    "eficiencia_marginal": eficiencia_marginal,
    "lookahead_1_paso": lookahead_1_paso,
    "hibrida_adaptativa": hibrida_adaptativa,
}


# ---- Extra: búsqueda local 1-swap ------------------------------------------
def busqueda_local_swap(al: Alcance, propuesta: Propuesta, max_iter: int = 1000) -> Propuesta:
    """Mejora una propuesta con movimientos 1-swap (mejor mejora en cada iteración):
    quitar una estación (o ninguna) y agregar otra en cualquier lote libre/tipo
    (incluye cambiar de tipo, mover de lote y completar con una estación nueva)."""
    cands = _candidatos(al)
    actual = list(propuesta.estaciones)
    val = valor_de(al, actual)
    cost = sum(al.costo[e] for e in actual)
    presup = al.inst.presupuesto
    for _ in range(max_iter):
        mejor_mov, mejor_val, mejor_cost = None, val, cost
        for quitar in [None] + actual:
            base = [e for e in actual if e != quitar]
            usados = {e[0] for e in base}
            c_base = cost - (al.costo[quitar] if quitar else 0)
            cub = mascaras_cubiertas(al, base)
            v_base = sum(al.pesos[t] * cub[t].bit_count() for t in cub)
            for c in cands:
                if c[0] in usados or c == quitar or c_base + al.costo[c] > presup:
                    continue
                v = v_base + _vm(al, cub, c)
                cn = c_base + al.costo[c]
                if v > mejor_val or (v == mejor_val and mejor_mov is not None and cn < mejor_cost):
                    mejor_mov, mejor_val, mejor_cost = (quitar, c), v, cn
        if mejor_mov is None:
            break
        quitar, c = mejor_mov
        actual = [e for e in actual if e != quitar] + [c]
        val, cost = mejor_val, mejor_cost
    return resumen(al, actual)

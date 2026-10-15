"""Lectura de instancias (csv/json) y modelo de datos."""
import csv
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple

TIPOS = ("hurto", "accidente", "incendio")  # orden de desempate oficial

RAIZ_INSTANCIAS = Path(__file__).resolve().parent.parent / "instancias"


@dataclass
class Instancia:
    nombre: str
    ruta: Path
    nodos: Dict[int, Tuple[float, float]]
    adj: Dict[int, List[Tuple[int, float, str]]]            # u -> [(v, longitud_m, nombre)]
    lotes: List[Tuple[str, int, float]]                      # (lote, nodo, factor_zona) ordenado por código
    incidentes: Dict[int, Tuple[int, str, str]]              # id -> (nodo, tipo, fecha_hora)
    inc_por_tipo_nodo: Dict[Tuple[str, int], List[int]]
    params: dict
    n_aristas: int = 0

    @property
    def presupuesto(self) -> int:
        return int(self.params["presupuesto_millones"])

    @property
    def tipos(self) -> dict:
        return self.params["tipos"]

    def radio(self, tipo: str) -> float:
        return float(self.tipos[tipo]["radio_m"])

    def peso(self, tipo: str) -> int:
        return self.tipos[tipo]["peso"]


def costo_estacion(costo_base: float, factor_zona: float) -> int:
    """round(costo_base*factor) al entero más cercano (half-up, sin redondeo bancario)."""
    return int(math.floor(costo_base * factor_zona + 0.5 + 1e-9))


def _leer_csv(ruta: Path):
    with open(ruta, newline="", encoding="utf-8") as f:
        yield from csv.DictReader(f)


def cargar_instancia(ruta_o_nombre, params_override: dict = None) -> Instancia:
    """Carga una instancia por nombre ('pequena') o por ruta a su carpeta."""
    p = Path(str(ruta_o_nombre))
    if not p.is_dir():
        p = RAIZ_INSTANCIAS / str(ruta_o_nombre)
    if not p.is_dir():
        raise FileNotFoundError(f"No existe la instancia: {ruta_o_nombre}")

    nodos = {int(r["id"]): (float(r["lat"]), float(r["lon"])) for r in _leer_csv(p / "nodos.csv")}

    mejor: Dict[Tuple[int, int], Tuple[float, str]] = {}
    for r in _leer_csv(p / "aristas.csv"):
        k = (int(r["origen"]), int(r["destino"]))
        w = float(r["longitud_m"])
        if k not in mejor or w < mejor[k][0]:     # paralelas: conserva la menor
            mejor[k] = (w, r.get("nombre") or "")
    adj: Dict[int, List[Tuple[int, float, str]]] = {n: [] for n in nodos}
    for (u, v), (w, nom) in mejor.items():
        adj.setdefault(u, []).append((v, w, nom))
        adj.setdefault(v, [])

    lotes = sorted(((r["lote"], int(r["nodo"]), float(r["factor_zona"]))
                    for r in _leer_csv(p / "lotes.csv")), key=lambda x: x[0])

    incidentes: Dict[int, Tuple[int, str, str]] = {}
    por_tn: Dict[Tuple[str, int], List[int]] = {}
    for r in _leer_csv(p / "incidentes.csv"):
        i, n, t = int(r["id"]), int(r["nodo"]), r["tipo"].strip()
        incidentes[i] = (n, t, r.get("fecha_hora", ""))
        por_tn.setdefault((t, n), []).append(i)

    with open(p / "parametros.json", encoding="utf-8") as f:
        params = json.load(f)
    if params_override:
        for k, v in params_override.items():
            if k == "tipos":
                for t, d in v.items():
                    params["tipos"][t].update(d)
            else:
                params[k] = v

    return Instancia(p.name, p, nodos, adj, lotes, incidentes, por_tn, params, len(mejor))

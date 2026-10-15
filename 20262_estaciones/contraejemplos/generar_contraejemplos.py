"""Genera las 4 instancias-contraejemplo (<= 6 nodos, 5 archivos reglamentarios cada una),
certifica con el solver exacto que la heurística objetivo NO obtiene el óptimo y escribe
un README.md por carpeta con la explicación paso a paso.

Uso:  python contraejemplos/generar_contraejemplos.py
"""
import csv
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))

from estaciones import (HEURISTICAS, calcular_alcance, cargar_instancia,  # noqa: E402
                        mejor_propuesta_exacta)

PARAMS = {
    "descripcion": "",
    "presupuesto_millones": 0,
    "unidad_costos": "millones de pesos colombianos",
    "un_lote_admite_a_lo_sumo_una_estacion": True,
    "tipos": {
        "hurto": {"estacion": "CAI", "costo_base": 1000, "radio_m": 1000, "peso": 1},
        "accidente": {"estacion": "Estación de tránsito y grúas", "costo_base": 2000, "radio_m": 2000, "peso": 3},
        "incendio": {"estacion": "Estación de bomberos", "costo_base": 5000, "radio_m": 3000, "peso": 5},
    },
}

# Cada lote Lk está en su propio nodo y todos los incidentes ocurren en el nodo del lote
# (distancia 0). Las calles que unen los nodos miden 4000 m (> radio máximo 3000 m), así
# que no hay cobertura cruzada: el problema se reduce a una mochila con valores claros.
CASOS = {
    "base": dict(
        presupuesto=6000,
        lotes=["L1", "L2", "L3", "L4"],
        incidentes={"L1": {"incendio": 2}, "L2": {"accidente": 2},
                    "L3": {"accidente": 2}, "L4": {"accidente": 2}},
        titulo="Heurística base: la estación 'más valiosa' agota el presupuesto",
        explicacion="""\
**Paso 1.** Candidatos y valor marginal: bomberos en L1 = 2 incendios × 5 = **10**;
tránsito en L2, L3 o L4 = 2 accidentes × 3 = **6** cada una. La base solo mira el valor marginal,
así que construye bomberos en L1 (costo 5.000). Quedan 1.000 millones.

**Paso 2.** Con 1.000 millones no cabe ninguna estación con valor (tránsito cuesta 2.000; no hay hurtos).
La base termina con valor **10**.

**Qué hubiera sido mejor.** Tres estaciones de tránsito (L2, L3, L4) cuestan 6.000 y cubren 6 accidentes
= **18**. La decisión que desvía a la base es ignorar el costo: gastó 5.000 para ganar 10 cuando con
ese dinero y 1.000 más se podía ganar 18.""",
    ),
    "eficiencia_marginal": dict(
        presupuesto=5000,
        lotes=["L1", "L2", "L3"],
        incidentes={"L1": {"incendio": 3}, "L2": {"hurto": 4}, "L3": {"hurto": 4}},
        titulo="Eficiencia marginal: lo barato y eficiente bloquea lo grande",
        explicacion="""\
**Paso 1.** Eficiencia (valor/costo): CAI en L2 = 4/1.000 = **0,0040**; CAI en L3 = 0,0040;
bomberos en L1 = 15/5.000 = **0,0030**. Gana el CAI de L2 (por código de lote).

**Paso 2.** Con 4.000 de remanente, de nuevo el mejor cociente es el CAI de L3 (0,0040).

**Paso 3.** Quedan 3.000 millones: los bomberos de L1 (5.000) ya no caben. Termina con valor **8**.

**Qué hubiera sido mejor.** Bomberos en L1 con todo el presupuesto: **15**. El cociente favorece lo
barato aunque, sumado, deje sin ejecutar la única estación que realmente aprovecha el presupuesto
(el cociente ignora que el dinero sobrante no vale nada).""",
    ),
    "lookahead_1_paso": dict(
        presupuesto=6000,
        lotes=["L1", "L2", "L3", "L4", "L5"],
        incidentes={"L1": {"incendio": 3}, "L2": {"accidente": 2}, "L3": {"accidente": 2},
                    "L4": {"accidente": 2}, "L5": {"hurto": 1}},
        titulo="Lookahead de 1 paso: el óptimo necesita ver 3 estaciones adelante",
        explicacion="""\
**Paso 1.** Puntaje = valor marginal propio + mejor valor de la siguiente estación:
- Bomberos en L1: 15 + (con los 1.000 restantes, solo un CAI en L5 = 1) = **16**.
- CAI en L5: 1 + (con 5.000 restantes, bomberos en L1 = 15) = **16** (empate).
- Tránsito en L2: 6 + (otra tránsito = 6) = **12**.
Gana L1 (menor código). Se construyen bomberos en L1 (5.000).

**Paso 2.** Quedan 1.000: se construye el CAI de L5. Valor total **16**.

**Qué hubiera sido mejor.** Tres tránsitos (L2, L3, L4) = 18. Mirando solo dos pasos, la secuencia
de tres estaciones parece valer 12 y pierde frente a un par que vale 16; el beneficio de la tercera
estación queda fuera del horizonte del lookahead.""",
    ),
    "hibrida_adaptativa": dict(
        presupuesto=5000,
        lotes=["L1", "L2", "L3"],
        incidentes={"L1": {"incendio": 3}, "L2": {"hurto": 5}, "L3": {"hurto": 5}},
        titulo="Híbrida adaptativa: el exponente 0,75 aún favorece lo barato",
        explicacion="""\
**Paso 1 (fase 1, vm/costo^0,75).** Bomberos en L1: 15 / 5.000^0,75 = 15/594,6 = **0,0252**.
CAI en L2: 5 / 1.000^0,75 = 5/177,8 = **0,0281**. Gana el CAI de L2. Remanente 4.000 (> 25 %).

**Paso 2.** CAI en L3 (0,0281). Remanente 3.000 (> 25 % de 5.000), pero ya no hay candidatos con
valor que quepan (bomberos cuesta 5.000), así que la fase de llenado tampoco encuentra nada.
Valor total **10**.

**Qué hubiera sido mejor.** Bomberos en L1: **15**. Penalizar el costo con exponente < 1 es un
compromiso entre valor absoluto y eficiencia, pero con 5 hurtos concentrados por nodo la ponderación
sigue inclinando la balanza hacia las estaciones baratas que luego impiden la grande.""",
    ),
}


def escribir(nombre: str, c: dict) -> Path:
    d = AQUI / nombre
    d.mkdir(exist_ok=True)
    n = len(c["lotes"])
    with open(d / "nodos.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["id", "lat", "lon"])
        for k in range(n):
            w.writerow([k, 6.24 + 0.02 * k, -75.59])
    with open(d / "aristas.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["origen", "destino", "longitud_m", "nombre"])
        for k in range(n - 1):   # cadena de calles de 4.000 m en ambos sentidos
            w.writerow([k, k + 1, 4000, f"Calle {k + 1}"])
            w.writerow([k + 1, k, 4000, f"Calle {k + 1}"])
    with open(d / "lotes.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["lote", "nodo", "factor_zona"])
        for k, l in enumerate(c["lotes"]):
            w.writerow([l, k, 1.0])
    with open(d / "incidentes.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["id", "nodo", "tipo", "fecha_hora"])
        i = 1
        for k, l in enumerate(c["lotes"]):
            for tipo, cant in c["incidentes"].get(l, {}).items():
                for _ in range(cant):
                    w.writerow([i, k, tipo, f"2025-01-{(i % 28) + 1:02d} 08:00"]); i += 1
    p = json.loads(json.dumps(PARAMS))
    p["presupuesto_millones"] = c["presupuesto"]
    p["descripcion"] = f"Contraejemplo para la heurística '{nombre}' ({n} nodos)."
    (d / "parametros.json").write_text(json.dumps(p, indent=2, ensure_ascii=False), encoding="utf-8")
    return d


def main():
    for nombre, c in CASOS.items():
        d = escribir(nombre, c)
        inst = cargar_instancia(d)
        assert len(inst.nodos) <= 6
        al = calcular_alcance(inst)
        opt, _ = mejor_propuesta_exacta(al)
        res = {k: f(al) for k, f in HEURISTICAS.items()}
        objetivo = res[nombre]
        assert objetivo.valor < opt.valor, (nombre, objetivo.valor, opt.valor)
        filas = "\n".join(
            f"| {k} | {p.valor} | {p.costo_total} | {', '.join(f'{l}:{t}' for l, t in p.estaciones)} "
            f"| {'✗ no óptima' if p.valor < opt.valor else '✓ óptima'} |"
            for k, p in res.items())
        (d / "README.md").write_text(
            f"# {c['titulo']}\n\nInstancia de {len(inst.nodos)} nodos, presupuesto {c['presupuesto']} M. "
            f"Cada lote está en su propio nodo con sus incidentes; las calles (4.000 m) superan el radio "
            f"máximo, así que no hay cobertura cruzada.\n\n"
            f"## Resultado\n\n- Heurística `{nombre}`: valor **{objetivo.valor}** "
            f"({', '.join(f'{l}:{t}' for l, t in objetivo.estaciones)}).\n"
            f"- Óptimo (Branch & Bound): valor **{opt.valor}** "
            f"({', '.join(f'{l}:{t}' for l, t in opt.estaciones)}), costo {opt.costo_total}.\n\n"
            f"| Heurística | Valor | Costo | Estaciones | |\n|---|---|---|---|---|\n{filas}\n\n"
            f"## Qué decisión la desvía del óptimo\n\n{c['explicacion']}\n", encoding="utf-8")
        print(f"{nombre:22s} heurística={objetivo.valor:3d}  óptimo={opt.valor:3d}  OK")


if __name__ == "__main__":
    main()

"""Gráficas de apoyo: Pareto presupuestal, analítica temporal y carga por estación."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from estaciones import HEURISTICAS, busqueda_local_swap, mejor_propuesta_exacta
from estaciones.alcance import con_presupuesto
from estaciones.reportes import asignar_incidentes

COL = {"hurto": "#1f77b4", "accidente": "#ff7f0e", "incendio": "#d62728"}


def mejor_heuristica(al, con_swap=True):
    """Mejor propuesta entre las 4 heurísticas (y su refinamiento por búsqueda local)."""
    mejor = None
    for nombre, f in HEURISTICAS.items():
        p = f(al)
        if con_swap:
            p = busqueda_local_swap(al, p)
        if mejor is None or p.valor > mejor[1].valor:
            mejor = (nombre, p)
    return mejor


def curva_pareto(al, presupuestos, con_exacto=False, limite_nodos=300000):
    """Valor vs presupuesto. Devuelve filas [{presupuesto, heuristica, exacto|None}]."""
    filas = []
    for b in presupuestos:
        ab = con_presupuesto(al, b)
        nom, p = mejor_heuristica(ab)
        ex = None
        if con_exacto:
            try:
                ex = mejor_propuesta_exacta(ab, limite_nodos=limite_nodos)[0].valor
            except TimeoutError:
                ex = None
        filas.append({"presupuesto": b, "heuristica": p.valor, "metodo": nom, "exacto": ex,
                      "costo": p.costo_total, "estaciones": len(p.estaciones)})
    return filas


def graficar_pareto(series, titulo="Curva de Pareto presupuestal"):
    """series: {nombre_instancia: filas}. Una sola figura con valor normalizado y valor absoluto."""
    fig, ax = plt.subplots(1, len(series), figsize=(6.5 * len(series), 4.2), squeeze=False)
    for a, (nom, filas) in zip(ax[0], series.items()):
        x = [f["presupuesto"] for f in filas]
        a.plot(x, [f["heuristica"] for f in filas], "o-", label="mejor heurística + swap", color="#2c3e50")
        if any(f["exacto"] is not None for f in filas):
            xe = [f["presupuesto"] for f in filas if f["exacto"] is not None]
            a.plot(xe, [f["exacto"] for f in filas if f["exacto"] is not None], "s--", color="#e67e22",
                   label="óptimo (B&B)")
        a.set_title(f"{nom}"); a.set_xlabel("Presupuesto (millones COP)"); a.set_ylabel("Valor")
        a.grid(alpha=.3); a.legend()
    fig.suptitle(titulo); fig.tight_layout()
    return fig


def analitica_temporal(inst):
    """Distribución por hora del día, día de la semana y mes, apiladas por tipo."""
    from datetime import date
    horas, dias, meses = {}, {}, {}
    for _, t, f in inst.incidentes.values():
        if len(f) < 16:
            continue
        d = date(int(f[0:4]), int(f[5:7]), int(f[8:10]))
        for dic, k in ((horas, int(f[11:13])), (dias, d.weekday()), (meses, int(f[5:7]))):
            dic.setdefault(t, {}).setdefault(k, 0)
            dic[t][k] += 1
    fig, ax = plt.subplots(1, 3, figsize=(16, 3.8))
    nombres = {1: ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]}
    for a, dic, rango, tit, et in ((ax[0], horas, range(24), "Por hora del día", None),
                                   (ax[1], dias, range(7), "Por día de la semana", nombres[1]),
                                   (ax[2], meses, range(1, 13), "Por mes", None)):
        base = [0] * len(rango)
        for t in COL:
            if t in dic:
                vals = [dic[t].get(k, 0) for k in rango]
                a.bar(range(len(rango)), vals, bottom=base, color=COL[t], label=t)
                base = [b + v for b, v in zip(base, vals)]
        a.set_xticks(range(len(rango)))
        a.set_xticklabels(et if et else [str(k) for k in rango], fontsize=7)
        a.set_title(tit); a.set_ylabel("Incidentes")
    ax[0].legend()
    fig.suptitle(f"Distribución temporal de incidentes – {inst.nombre}"); fig.tight_layout()
    return fig


def carga_por_estacion(al, p):
    """Incidentes atendidos por cada estación (cada incidente va a la estación de su tipo más cercana)."""
    asign = asignar_incidentes(al, p)
    carga = {}
    for i, (l, d) in asign.items():
        carga[l] = carga.get(l, 0) + 1
    fig, ax = plt.subplots(figsize=(max(6, .45 * len(p.estaciones) + 2), 4))
    etiquetas = [f"{l}\n{t[:3]}" for l, t in p.estaciones]
    vals = [carga.get(l, 0) for l, _ in p.estaciones]
    ax.bar(range(len(vals)), vals, color=[COL[t] for _, t in p.estaciones])
    ax.set_xticks(range(len(vals))); ax.set_xticklabels(etiquetas, fontsize=7)
    ax.set_ylabel("Incidentes atendidos"); ax.set_title("Carga por estación construida")
    fig.tight_layout()
    return fig, carga

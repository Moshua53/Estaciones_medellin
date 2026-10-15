"""App interactiva para la Feria de Proyectos de Ingeniería.

Ejecutar:  streamlit run app_feria_streamlit.py
"""
import hashlib
import tempfile
import time
from pathlib import Path

import folium
import pandas as pd
import streamlit as st

from estaciones import (HEURISTICAS, busqueda_local_swap, calcular_alcance, cargar_instancia,
                        mejor_propuesta_exacta)
from estaciones.alcance import con_pesos, con_presupuesto
from estaciones.datos import RAIZ_INSTANCIAS
from estaciones.reportes import (asignar_incidentes, nodos_candidatos, ruta_despacho,
                                 tabla_estaciones)
from visual.graficas import analitica_temporal, carga_por_estacion, curva_pareto
from visual.informe import informe_html, parrafo_justificacion
from visual.mapas import HEX, NOMBRE, crear_mapa, mapa_calor_no_cubiertos

st.set_page_config(page_title="Estaciones Medellín", layout="wide", page_icon="🚒")
ARCHIVOS = ["nodos.csv", "aristas.csv", "lotes.csv", "incidentes.csv", "parametros.json"]


@st.cache_resource(show_spinner="Calculando alcance (Dijkstra por lote)…")
def alcance_cacheado(ruta: str, radios: tuple, huella: str):
    inst = cargar_instancia(ruta, params_override={"tipos": {t: {"radio_m": r} for t, r in radios}})
    return calcular_alcance(inst)


def mostrar_html(doc: str, alto: int):
    """Incrusta HTML (mapas folium). `st.iframe` en Streamlit reciente; `components.html` en versiones previas."""
    if hasattr(st, "iframe"):
        st.iframe(doc, height=alto)
    else:
        import streamlit.components.v1 as components
        components.html(doc, height=alto)


def pm(x):
    return f"{x:,}".replace(",", ".")


# ---------------- barra lateral ----------------
st.sidebar.title("⚙️ Parámetros")
modo = st.sidebar.radio("Origen de datos", ["Instancia incluida", "Sustentación en vivo (subir archivos)"])
ruta, huella = None, ""
if modo == "Instancia incluida":
    nombres = sorted(d.name for d in RAIZ_INSTANCIAS.iterdir() if d.is_dir())
    nombre = st.sidebar.selectbox("Instancia", nombres, index=nombres.index("comuna") if "comuna" in nombres else 0)
    ruta = str(RAIZ_INSTANCIAS / nombre)
else:
    subidos = st.sidebar.file_uploader("Sube los 5 archivos (nodos, aristas, lotes, incidentes, parametros)",
                                       accept_multiple_files=True)
    por_nombre = {f.name: f for f in subidos or []}
    faltan = [a for a in ARCHIVOS if a not in por_nombre]
    if faltan:
        st.info("Faltan archivos: " + ", ".join(faltan))
        st.stop()
    h = hashlib.sha1()
    tmp = Path(tempfile.mkdtemp(prefix="sustentacion_"))
    for a in ARCHIVOS:
        datos = por_nombre[a].getvalue()
        h.update(datos)
        (tmp / a).write_bytes(datos)
    ruta, huella = str(tmp), h.hexdigest()

base = cargar_instancia(ruta)
tipos = list(base.tipos)
st.sidebar.subheader("Presupuesto")
presupuesto = st.sidebar.number_input("Millones COP", 500, 500000, base.presupuesto, step=500)
st.sidebar.subheader("Pesos de prioridad")
pesos = {t: st.sidebar.slider(f"Peso {NOMBRE.get(t, t)}", 1, 20, int(base.tipos[t]["peso"])) for t in tipos}
st.sidebar.subheader("Radios de cobertura (m)")
radios = tuple((t, st.sidebar.slider(f"Radio {NOMBRE.get(t, t)}", 200, 6000, int(base.tipos[t]["radio_m"]), step=100))
               for t in tipos)

al0 = alcance_cacheado(ruta, radios, huella)
al = con_pesos(con_presupuesto(al0, presupuesto), pesos)

metodos = list(HEURISTICAS) + ["EXACTO (Branch & Bound)"]
metodo = st.sidebar.selectbox("Método", metodos, index=len(metodos) - 1 if len(al.inst.lotes) <= 18 else 1)
usar_swap = st.sidebar.checkbox("Refinar con búsqueda local 1-swap", value=True)
if metodo.startswith("EXACTO") and len(al.inst.lotes) > 25:
    st.sidebar.warning("Con muchos lotes el exacto puede tardar mucho; se limita a 3 M de nodos.")


@st.cache_data(show_spinner="Optimizando…")
def resolver(_al, clave, metodo, swap):
    t0 = time.perf_counter()
    if metodo.startswith("EXACTO"):
        try:
            p, st_ = mejor_propuesta_exacta(_al, limite_nodos=3_000_000)
            nota = f"óptimo garantizado ({st_['nodos']} nodos explorados)"
        except TimeoutError:
            p, nota = HEURISTICAS["lookahead_1_paso"](_al), "límite excedido: se muestra heurística"
    else:
        p, nota = HEURISTICAS[metodo](_al), "heurística"
        if swap:
            p = busqueda_local_swap(_al, p)
    return p, nota, time.perf_counter() - t0


clave = (ruta, huella, radios, presupuesto, tuple(sorted(pesos.items())))
p, nota, seg = resolver(al, clave, metodo, usar_swap)
inst = al.inst
totales = {t: sum(1 for v in inst.incidentes.values() if v[1] == t) for t in tipos}

st.title(f"🏙️ Dónde construir – {inst.nombre}")
c = st.columns(5)
c[0].metric("Valor", p.valor)
c[1].metric("Costo (M)", pm(p.costo_total), f"de {pm(presupuesto)}", delta_color="off")
c[2].metric("Estaciones", len(p.estaciones))
c[3].metric("Cobertura", f"{100 * sum(p.casos_cubiertos.values()) / max(1, len(inst.incidentes)):.1f}%")
c[4].metric("Tiempo", f"{seg:.2f}s", nota, delta_color="off")

tabs = st.tabs(["🗺️ Mapa", "📋 Tabla", "⚖️ Comparativa", "📈 Pareto", "📊 Analítica", "🚨 Despacho", "📄 Informe"])

with tabs[0]:
    mapa = crear_mapa(al, p, f"{inst.nombre} – {metodo}")
    mostrar_html(mapa.get_root().render(), 700)

with tabs[1]:
    filas = tabla_estaciones(al, p)
    st.dataframe(pd.DataFrame(filas).rename(columns={
        "lote": "Lote", "tipo": "Tipo", "costo": "Costo (M)", "casos_cubre": "Casos que cubre",
        "casos_nuevos": "Casos nuevos", "valor_aporte": "Valor aportado"}), width="stretch", hide_index=True)
    st.write("**Casos cubiertos:** " + ", ".join(f"{t} {p.casos_cubiertos[t]}/{totales[t]}" for t in tipos))

with tabs[2]:
    if st.button("Calcular comparativa de todos los métodos"):
        rows = []
        for k, f in HEURISTICAS.items():
            t0 = time.perf_counter(); q = f(al); dt = time.perf_counter() - t0
            rows.append({"Método": k, "Valor": q.valor, "Costo": q.costo_total, "Tiempo (s)": round(dt, 3)})
            t0 = time.perf_counter(); q2 = busqueda_local_swap(al, q); dt2 = time.perf_counter() - t0
            rows.append({"Método": k + " + swap", "Valor": q2.valor, "Costo": q2.costo_total, "Tiempo (s)": round(dt + dt2, 3)})
        if len(al.inst.lotes) <= 25:
            t0 = time.perf_counter()
            try:
                q, _ = mejor_propuesta_exacta(al, limite_nodos=3_000_000)
                rows.append({"Método": "EXACTO", "Valor": q.valor, "Costo": q.costo_total,
                             "Tiempo (s)": round(time.perf_counter() - t0, 3)})
            except TimeoutError:
                rows.append({"Método": "EXACTO", "Valor": None, "Costo": None, "Tiempo (s)": None})
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")

with tabs[3]:
    paso = st.slider("Paso del presupuesto (M)", 1000, 10000, 4000, step=1000)
    tope = st.slider("Presupuesto máximo (M)", 10000, 120000, 80000, step=5000)
    if st.button("Calcular curva de Pareto"):
        import plotly.graph_objects as go
        filas = curva_pareto(al, list(range(paso, tope + 1, paso)),
                             con_exacto=len(al.inst.lotes) <= 18)
        fig = go.Figure()
        fig.add_scatter(x=[f["presupuesto"] for f in filas], y=[f["heuristica"] for f in filas],
                        mode="lines+markers", name="mejor heurística + swap")
        if any(f["exacto"] is not None for f in filas):
            fig.add_scatter(x=[f["presupuesto"] for f in filas], y=[f["exacto"] for f in filas],
                            mode="lines+markers", name="óptimo (B&B)", line=dict(dash="dash"))
        fig.update_layout(xaxis_title="Presupuesto (M COP)", yaxis_title="Valor", height=450)
        st.plotly_chart(fig, width="stretch")

with tabs[4]:
    st.pyplot(analitica_temporal(inst))
    fig, carga = carga_por_estacion(al, p)
    st.pyplot(fig)
    m2, cands = mapa_calor_no_cubiertos(al, p)
    mostrar_html(m2.get_root().render(), 520)
    if cands:
        st.write("**Nodos candidatos para futuros lotes:**")
        st.dataframe(pd.DataFrame(cands)[["nodo", "tipo", "valor_adicional", "incidentes", "lat", "lon"]],
                     hide_index=True)

with tabs[5]:
    if not p.estaciones:
        st.info("No hay estaciones construidas.")
    else:
        asign = asignar_incidentes(al, p)
        lote_sel = st.selectbox("Estación", [f"{l} ({t})" for l, t in p.estaciones])
        lote = lote_sel.split()[0]
        ids = sorted(i for i, (l, _) in asign.items() if l == lote)
        if not ids:
            st.info("Esta estación no es la más cercana para ningún incidente.")
        else:
            i_sel = st.selectbox("Incidente atendido", ids,
                                 format_func=lambda i: f"#{i} · {inst.incidentes[i][1]} · {asign[i][1]:.0f} m")
            r = ruta_despacho(al, lote, i_sel)
            st.write(f"**Distancia por la red: {r['total_m']:.0f} m** · {len(r['tramos'])} tramos")
            mm = folium.Map(location=r["coords"][0], zoom_start=15, tiles="OpenStreetMap")
            tipo = dict(p.estaciones)[lote]
            folium.PolyLine(r["coords"], color=HEX[tipo], weight=6, opacity=.85).add_to(mm)
            folium.Marker(r["coords"][0], tooltip=f"Estación {lote}", icon=folium.Icon(color="green")).add_to(mm)
            folium.Marker(r["coords"][-1], tooltip=f"Incidente #{i_sel}", icon=folium.Icon(color="red")).add_to(mm)
            mm.fit_bounds(r["coords"])
            mostrar_html(mm.get_root().render(), 450)
            st.dataframe(pd.DataFrame([{"Paso": k + 1, "Calle": t["calle"], "Metros": round(t["metros"], 1)}
                                       for k, t in enumerate(r["tramos"])]), hide_index=True)

with tabs[6]:
    nombre_m = metodo + (" + swap" if usar_swap and not metodo.startswith("EXACTO") else "")
    st.write(parrafo_justificacion(al, p, nombre_m))
    doc = informe_html(al, p, f"Propuesta para el Concejo – {inst.nombre}", nombre_m, mapa=crear_mapa(al, p, inst.nombre))
    st.download_button("⬇️ Descargar informe HTML", doc, file_name=f"informe_{inst.nombre}.html", mime="text/html")

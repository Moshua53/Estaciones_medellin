"""Parte 4: mapas folium (solo visualización; el cálculo viene del paquete `estaciones`)."""
import folium
from folium.plugins import HeatMap

from estaciones.reportes import asignar_incidentes, html_tabla, nodos_candidatos

COLOR = {"hurto": "blue", "accidente": "orange", "incendio": "red"}
HEX = {"hurto": "#1f77b4", "accidente": "#ff7f0e", "incendio": "#d62728"}
ICONO = {"hurto": "shield", "accidente": "car", "incendio": "fire"}
NOMBRE = {"hurto": "CAI", "accidente": "Tránsito y grúas", "incendio": "Bomberos"}


def _panel(al, p, titulo):
    inst = al.inst
    tot = {t: sum(1 for v in inst.incidentes.values() if v[1] == t) for t in al.pesos}
    cub = p.casos_cubiertos
    pct = 100 * sum(cub.values()) / max(1, sum(tot.values()))
    pm = lambda x: f"{x:,}".replace(",", ".")
    filas = "".join(f"<tr><td><span style='color:{HEX[t]}'>&#9679;</span> {NOMBRE.get(t, t)}</td>"
                    f"<td style='text-align:right'>{cub[t]}/{tot[t]}</td></tr>" for t in al.pesos)
    return f"""
    <div style="position:fixed;top:12px;right:12px;z-index:9999;background:rgba(255,255,255,.95);
         padding:10px 14px;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,.35);
         font:13px/1.35 Arial,sans-serif;max-width:290px;color:#222">
      <div style="font-weight:700;font-size:14px;margin-bottom:4px">{titulo}</div>
      <div><b>Costo:</b> {pm(p.costo_total)} / {pm(inst.presupuesto)} M
        ({100*p.costo_total/inst.presupuesto:.1f}%)</div>
      <div><b>Valor:</b> {p.valor} &nbsp; <b>Estaciones:</b> {len(p.estaciones)}</div>
      <div><b>Cobertura:</b> {pct:.1f}% de {sum(tot.values())} incidentes</div>
      <table style="width:100%;margin-top:4px">{filas}</table>
      <hr style="margin:6px 0">
      <div style="font-weight:700">Leyenda</div>
      <div><span style="color:#d62728">&#9650;</span> Estación (color por tipo)</div>
      <div><span style="color:#777">&#9632;</span> Lote no usado</div>
      <div><span style="color:#2ca02c">&#9679;</span> Incidente cubierto</div>
      <div><span style="color:#000">&#9679;</span> Incidente NO cubierto</div>
      <div><span style="color:#888">&#9473;</span> Subred vial de cobertura (color por tipo)</div>
    </div>"""


def crear_mapa(al, p, titulo="Propuesta", mostrar_rutas=True, agrupar_incidentes=False):
    """Mapa folium con capas: estaciones, lotes no usados, incidentes cubiertos / no cubiertos,
    subred vial de cobertura (aristas alcanzadas por Dijkstra dentro del radio) y panel de KPIs."""
    inst = al.inst
    lat = sum(v[0] for v in inst.nodos.values()) / len(inst.nodos)
    lon = sum(v[1] for v in inst.nodos.values()) / len(inst.nodos)
    m = folium.Map(location=[lat, lon], zoom_start=12 if len(inst.nodos) > 10000 else 14,
                   tiles="OpenStreetMap", control_scale=True)
    f_est = folium.FeatureGroup("Estaciones construidas")
    f_lot = folium.FeatureGroup("Lotes no usados")
    f_cub = folium.FeatureGroup("Incidentes cubiertos", show=True)
    f_nc = folium.FeatureGroup("Incidentes no cubiertos", show=True)
    f_red = folium.FeatureGroup("Rutas / subred vial de cobertura", show=mostrar_rutas)

    usados = {l for l, _ in p.estaciones}
    for lote, nodo, factor in inst.lotes:
        if lote not in usados:
            folium.CircleMarker(inst.nodos[nodo], radius=5, color="#555", fill=True, fill_opacity=.7,
                                tooltip=f"{lote} (libre) – factor {factor}").add_to(f_lot)
    asign = asignar_incidentes(al, p)
    carga = {}
    for i, (l, d) in asign.items():
        carga[l] = carga.get(l, 0) + 1
    nodo_lote = {l: n for l, n, _ in inst.lotes}
    for lote, t in p.estaciones:
        c = al.costo[(lote, t)]
        folium.Marker(inst.nodos[nodo_lote[lote]],
                      icon=folium.Icon(color=COLOR[t], icon=ICONO[t], prefix="fa"),
                      tooltip=f"{lote} – {NOMBRE.get(t, t)}",
                      popup=folium.Popup(f"<b>{lote}</b> · {NOMBRE.get(t, t)}<br>Costo: {c} M<br>"
                                         f"Cubre: {len(al.cubiertos[(lote, t)])} incidentes<br>"
                                         f"Atiende (más cercana): {carga.get(lote, 0)}", max_width=260)
                      ).add_to(f_est)
        # subred vial: aristas padre->hijo dentro del radio del tipo
        r = inst.radio(t)
        d, par = al.dist[lote], al.padre[lote]
        segs = [[inst.nodos[par[v]], inst.nodos[v]] for v, dv in d.items() if v in par and dv <= r]
        if segs:
            folium.PolyLine(segs, color=HEX[t], weight=2, opacity=.4,
                            tooltip=f"Alcance {lote} ({r:.0f} m)").add_to(f_red)

    cubiertos = set(p.ids_cubiertos)
    for i, (n, t, fecha) in inst.incidentes.items():
        pos = inst.nodos[n]
        info = f"#{i} {t} · {fecha}"
        if i in cubiertos:
            folium.CircleMarker(pos, radius=2.5, color="#2ca02c", weight=1, fill=True, fill_opacity=.8,
                                tooltip=info).add_to(f_cub)
        else:
            folium.CircleMarker(pos, radius=3, color="#000", weight=1, fill=True, fill_color=HEX[t],
                                fill_opacity=.9, tooltip=info + " (NO cubierto)").add_to(f_nc)
    for g in (f_red, f_lot, f_cub, f_nc, f_est):
        g.add_to(m)
    folium.LayerControl(collapsed=False, position="topleft").add_to(m)
    m.get_root().html.add_child(folium.Element(_panel(al, p, titulo)))
    return m


def mapa_calor_no_cubiertos(al, p, k=3):
    """Mapa de calor de incidentes no cubiertos + 3 nodos candidatos para futuros lotes."""
    inst = al.inst
    cub = set(p.ids_cubiertos)
    pts = [[*inst.nodos[n], al.pesos[t]] for i, (n, t, _) in inst.incidentes.items() if i not in cub]
    lat = sum(v[0] for v in inst.nodos.values()) / len(inst.nodos)
    lon = sum(v[1] for v in inst.nodos.values()) / len(inst.nodos)
    m = folium.Map(location=[lat, lon], zoom_start=12 if len(inst.nodos) > 10000 else 14, tiles="OpenStreetMap")
    if pts:
        HeatMap(pts, radius=14, blur=18, name="Calor: incidentes no cubiertos").add_to(m)
    cands = nodos_candidatos(al, p, k) if pts else []
    for j, c in enumerate(cands, 1):
        folium.Marker([c["lat"], c["lon"]], icon=folium.Icon(color="green", icon="star", prefix="fa"),
                      tooltip=f"Candidato {j}: nodo {c['nodo']} ({NOMBRE.get(c['tipo'], c['tipo'])}) "
                              f"+{c['valor_adicional']} de valor").add_to(m)
    for l, t in p.estaciones:
        n = next(n for ll, n, _ in inst.lotes if ll == l)
        folium.CircleMarker(inst.nodos[n], radius=6, color=HEX[t], fill=True, tooltip=f"{l} {t}").add_to(m)
    folium.LayerControl().add_to(m)
    return m, cands

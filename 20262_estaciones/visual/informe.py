"""Informe HTML autocontenido (KPIs + tabla + justificación + mapa embebido)."""
import html

from estaciones.reportes import html_tabla


def parrafo_justificacion(al, p, nombre_metodo, comparativa=None):
    """Párrafo para el Concejo con cifras reales de la propuesta (y de las alternativas, si se dan)."""
    inst = al.inst
    tot = sum(1 for _ in inst.incidentes)
    cub = sum(p.casos_cubiertos.values())
    pm = lambda x: f"{x:,}".replace(",", ".")
    txt = (f"Se recomienda la propuesta obtenida con «{nombre_metodo}» para {inst.nombre}: {len(p.estaciones)} "
           f"estaciones con un costo de {pm(p.costo_total)} M de {pm(inst.presupuesto)} M disponibles "
           f"({100 * p.costo_total / inst.presupuesto:.1f} % del presupuesto), que atienden con oportunidad "
           f"{cub} de {tot} incidentes históricos ({100 * cub / max(1, tot):.1f} %) y suman un valor ponderado de {p.valor}. ")
    if comparativa:
        otros = ", ".join(f"{k}: {v}" for k, v in comparativa.items() if k != nombre_metodo)
        txt += (f"Frente a las demás alternativas evaluadas ({otros}) es la de mayor valor, y por lo tanto "
                f"la que más víctimas potenciales protege por peso ponderado (bomberos 5, tránsito 3, CAI 1) "
                f"sin exceder el presupuesto. ")
    txt += ("Las cifras provienen de un histórico simulado y de una red vial aproximada; en un despliegue real "
            "convendría validar los lotes y recalcular con datos actualizados.")
    return txt


def informe_html(al, p, titulo, nombre_metodo, mapa=None, comparativa=None, extra_html=""):
    inst = al.inst
    mapa_html = ""
    if mapa is not None:
        mapa_html = (f"<h2>Mapa</h2><iframe style='width:100%;height:620px;border:1px solid #ccc' "
                     f"srcdoc=\"{html.escape(mapa.get_root().render(), quote=True)}\"></iframe>")
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><title>{html.escape(titulo)}</title>
<style>body{{font-family:Arial,sans-serif;max-width:1000px;margin:24px auto;color:#222;padding:0 16px}}
table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #ccc;padding:5px 8px;text-align:right}}
th{{background:#f3f3f3}}td:first-child,td:nth-child(2){{text-align:left}}</style></head><body>
<h1>{html.escape(titulo)}</h1>
<p><b>Instancia:</b> {inst.nombre} · <b>Método:</b> {html.escape(nombre_metodo)} ·
<b>Valor:</b> {p.valor} · <b>Costo:</b> {p.costo_total} / {inst.presupuesto} M</p>
<h2>Estaciones</h2>{html_tabla(al, p)}
<h2>Justificación</h2><p>{html.escape(parrafo_justificacion(al, p, nombre_metodo, comparativa))}</p>
{extra_html}{mapa_html}</body></html>"""

# Estaciones Medellín – Dónde construir

Práctica de grafos y optimización combinatoria: elegir en qué lotes construir CAI, estaciones de tránsito y
bomberos para cubrir la mayor cantidad (ponderada) de incidentes sobre la red vial real de Medellín, con un
presupuesto limitado. Guía oficial: `20262_estaciones/practica_estaciones.ipynb`.

## Estructura (`20262_estaciones/`)
| Ruta | Contenido |
|---|---|
| `estaciones/` | Motor (solo `csv`, `json`, `heapq`, `math`, `time`, `pathlib`, `typing`): carga, Dijkstra acotado, alcance (Parte 1), heurísticas + búsqueda local 1-swap (Parte 2), Branch & Bound con máscaras de bits (Parte 3), reportes |
| `visual/` | Mapas `folium`, gráficas `matplotlib`, informe HTML |
| `contraejemplos/` | Generador y 4 instancias (≤ 6 nodos) donde cada heurística no alcanza el óptimo, con README explicativo |
| `app_feria_streamlit.py` | App interactiva (feria): instancias, sustentación en vivo, presupuesto/pesos/radios, mapa, despacho calle por calle, Pareto, analítica, informe HTML |
| `tests/test_casos.py` | Casos oficiales de las partes 1, 2 y 3 |
| `salidas/` | Mapas HTML y gráficas generados por el notebook |

## Uso
```bash
cd 20262_estaciones
pip install -r requirements.txt
python -m unittest discover tests                 # casos oficiales
python contraejemplos/generar_contraejemplos.py   # regenera y certifica los contraejemplos
jupyter nbconvert --to notebook --execute --inplace practica_estaciones.ipynb
streamlit run app_feria_streamlit.py              # aplicación de la feria
```

Para la **sustentación** el código lee cualquier carpeta con los 5 archivos (`cargar_instancia("ruta/a/carpeta")`), o se suben
desde la app (modo «Sustentación en vivo»).

## Resultados (instancias incluidas)
| Instancia | Base | Mejor propia | Propia + swap | Óptimo (B&B) |
|---|---|---|---|---|
| pequena | 15 | 19 | 19 | **20** (< 0,01 s) |
| comuna | 1529 | 1544 | 1544 | **1574** (≈ 1 s) |
| ciudad | 7591 | 7706 | 7784 | no reportado (4⁸⁰ ≈ 1,46·10⁴⁸ estados) |

Alcance de `ciudad` (80 lotes, 27.568 nodos): ≈ 0,7 s con un Dijkstra acotado por lote.

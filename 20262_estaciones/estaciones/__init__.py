"""Motor algorítmico de la práctica 'Dónde construir' (solo stdlib permitida)."""
from .datos import cargar_instancia, Instancia, TIPOS, costo_estacion
from .grafo import dijkstra_acotado, reconstruir_ruta
from .alcance import calcular_alcance, Alcance
from .evaluacion import Propuesta, resumen, valor_de
from .heuristicas import (heuristica_base, eficiencia_marginal, lookahead_1_paso,
                          hibrida_adaptativa, busqueda_local_swap, HEURISTICAS)
from .exacto import mejor_propuesta_exacta

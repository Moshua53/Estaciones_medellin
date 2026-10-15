# Eficiencia marginal: lo barato y eficiente bloquea lo grande

Instancia de 3 nodos, presupuesto 5000 M. Cada lote está en su propio nodo con sus incidentes; las calles (4.000 m) superan el radio máximo, así que no hay cobertura cruzada.

## Resultado

- Heurística `eficiencia_marginal`: valor **8** (L2:hurto, L3:hurto).
- Óptimo (Branch & Bound): valor **15** (L1:incendio), costo 5000.

| Heurística | Valor | Costo | Estaciones | |
|---|---|---|---|---|
| base | 15 | 5000 | L1:incendio | ✓ óptima |
| eficiencia_marginal | 8 | 2000 | L2:hurto, L3:hurto | ✗ no óptima |
| lookahead_1_paso | 15 | 5000 | L1:incendio | ✓ óptima |
| hibrida_adaptativa | 15 | 5000 | L1:incendio | ✓ óptima |

## Qué decisión la desvía del óptimo

**Paso 1.** Eficiencia (valor/costo): CAI en L2 = 4/1.000 = **0,0040**; CAI en L3 = 0,0040;
bomberos en L1 = 15/5.000 = **0,0030**. Gana el CAI de L2 (por código de lote).

**Paso 2.** Con 4.000 de remanente, de nuevo el mejor cociente es el CAI de L3 (0,0040).

**Paso 3.** Quedan 3.000 millones: los bomberos de L1 (5.000) ya no caben. Termina con valor **8**.

**Qué hubiera sido mejor.** Bomberos en L1 con todo el presupuesto: **15**. El cociente favorece lo
barato aunque, sumado, deje sin ejecutar la única estación que realmente aprovecha el presupuesto
(el cociente ignora que el dinero sobrante no vale nada).

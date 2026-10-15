# Híbrida adaptativa: el exponente 0,75 aún favorece lo barato

Instancia de 3 nodos, presupuesto 5000 M. Cada lote está en su propio nodo con sus incidentes; las calles (4.000 m) superan el radio máximo, así que no hay cobertura cruzada.

## Resultado

- Heurística `hibrida_adaptativa`: valor **10** (L2:hurto, L3:hurto).
- Óptimo (Branch & Bound): valor **15** (L1:incendio), costo 5000.

| Heurística | Valor | Costo | Estaciones | |
|---|---|---|---|---|
| base | 15 | 5000 | L1:incendio | ✓ óptima |
| eficiencia_marginal | 10 | 2000 | L2:hurto, L3:hurto | ✗ no óptima |
| lookahead_1_paso | 15 | 5000 | L1:incendio | ✓ óptima |
| hibrida_adaptativa | 10 | 2000 | L2:hurto, L3:hurto | ✗ no óptima |

## Qué decisión la desvía del óptimo

**Paso 1 (fase 1, vm/costo^0,75).** Bomberos en L1: 15 / 5.000^0,75 = 15/594,6 = **0,0252**.
CAI en L2: 5 / 1.000^0,75 = 5/177,8 = **0,0281**. Gana el CAI de L2. Remanente 4.000 (> 25 %).

**Paso 2.** CAI en L3 (0,0281). Remanente 3.000 (> 25 % de 5.000), pero ya no hay candidatos con
valor que quepan (bomberos cuesta 5.000), así que la fase de llenado tampoco encuentra nada.
Valor total **10**.

**Qué hubiera sido mejor.** Bomberos en L1: **15**. Penalizar el costo con exponente < 1 es un
compromiso entre valor absoluto y eficiencia, pero con 5 hurtos concentrados por nodo la ponderación
sigue inclinando la balanza hacia las estaciones baratas que luego impiden la grande.

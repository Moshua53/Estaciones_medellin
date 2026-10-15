# Lookahead de 1 paso: el óptimo necesita ver 3 estaciones adelante

Instancia de 5 nodos, presupuesto 6000 M. Cada lote está en su propio nodo con sus incidentes; las calles (4.000 m) superan el radio máximo, así que no hay cobertura cruzada.

## Resultado

- Heurística `lookahead_1_paso`: valor **16** (L1:incendio, L5:hurto).
- Óptimo (Branch & Bound): valor **18** (L2:accidente, L3:accidente, L4:accidente), costo 6000.

| Heurística | Valor | Costo | Estaciones | |
|---|---|---|---|---|
| base | 16 | 6000 | L1:incendio, L5:hurto | ✗ no óptima |
| eficiencia_marginal | 16 | 6000 | L1:incendio, L5:hurto | ✗ no óptima |
| lookahead_1_paso | 16 | 6000 | L1:incendio, L5:hurto | ✗ no óptima |
| hibrida_adaptativa | 16 | 6000 | L1:incendio, L5:hurto | ✗ no óptima |

## Qué decisión la desvía del óptimo

**Paso 1.** Puntaje = valor marginal propio + mejor valor de la siguiente estación:
- Bomberos en L1: 15 + (con los 1.000 restantes, solo un CAI en L5 = 1) = **16**.
- CAI en L5: 1 + (con 5.000 restantes, bomberos en L1 = 15) = **16** (empate).
- Tránsito en L2: 6 + (otra tránsito = 6) = **12**.
Gana L1 (menor código). Se construyen bomberos en L1 (5.000).

**Paso 2.** Quedan 1.000: se construye el CAI de L5. Valor total **16**.

**Qué hubiera sido mejor.** Tres tránsitos (L2, L3, L4) = 18. Mirando solo dos pasos, la secuencia
de tres estaciones parece valer 12 y pierde frente a un par que vale 16; el beneficio de la tercera
estación queda fuera del horizonte del lookahead.

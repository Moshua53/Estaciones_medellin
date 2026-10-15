# Heurística base: la estación 'más valiosa' agota el presupuesto

Instancia de 4 nodos, presupuesto 6000 M. Cada lote está en su propio nodo con sus incidentes; las calles (4.000 m) superan el radio máximo, así que no hay cobertura cruzada.

## Resultado

- Heurística `base`: valor **10** (L1:incendio).
- Óptimo (Branch & Bound): valor **18** (L2:accidente, L3:accidente, L4:accidente), costo 6000.

| Heurística | Valor | Costo | Estaciones | |
|---|---|---|---|---|
| base | 10 | 5000 | L1:incendio | ✗ no óptima |
| eficiencia_marginal | 18 | 6000 | L2:accidente, L3:accidente, L4:accidente | ✓ óptima |
| lookahead_1_paso | 18 | 6000 | L2:accidente, L3:accidente, L4:accidente | ✓ óptima |
| hibrida_adaptativa | 18 | 6000 | L2:accidente, L3:accidente, L4:accidente | ✓ óptima |

## Qué decisión la desvía del óptimo

**Paso 1.** Candidatos y valor marginal: bomberos en L1 = 2 incendios × 5 = **10**;
tránsito en L2, L3 o L4 = 2 accidentes × 3 = **6** cada una. La base solo mira el valor marginal,
así que construye bomberos en L1 (costo 5.000). Quedan 1.000 millones.

**Paso 2.** Con 1.000 millones no cabe ninguna estación con valor (tránsito cuesta 2.000; no hay hurtos).
La base termina con valor **10**.

**Qué hubiera sido mejor.** Tres estaciones de tránsito (L2, L3, L4) cuestan 6.000 y cubren 6 accidentes
= **18**. La decisión que desvía a la base es ignorar el costo: gastó 5.000 para ganar 10 cuando con
ese dinero y 1.000 más se podía ganar 18.

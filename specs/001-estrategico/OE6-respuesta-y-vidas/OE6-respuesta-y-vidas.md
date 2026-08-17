# Módulo: OE6 — Reducción del Tiempo de Respuesta y Seguridad de Vidas

**Ubicación:** `specs/001-estrategico/OE6-respuesta-y-vidas/`
**Objetivo estratégico:** OE6 · **Perspectiva BSC:** Procesos internos / Safety
**Feature paraguas:** `001-estrategico`
**Sustrato:** [`specs/002-tactico/modelo-analitico/`](../../002-tactico/modelo-analitico/)

Índice global del módulo (no es una spec Speckit). La feature activa de Speckit es **una capa**,
apuntada por `.specify/feature.json`.

## Por qué OE6 es el piloto de la capa estratégica

De los seis objetivos, es el único que reúne las cuatro condiciones para fijar el patrón sin pelearse
con nada más:

| | OE6 |
|---|---|
| **Un solo departamento dueño** | Emergencias. Autoridad única: `DirectorOperaciones` |
| **Cero informes ⛔** | Los doce son construibles |
| **Cero tablas nuevas** | El modelo analítico ya sostiene los doce |
| **Ninguna autoridad repartida** | No hay que resolver a la vez el reparto por materia |

Los otros cinco traen al menos una de esas complicaciones. Aquí el trabajo es **la forma de la capa
estratégica**, no el dominio.

## Los doce informes

| # | Informe | Historia |
|---|---|:--:|
| **E6-01** | Tiempo global de respuesta: registro a llegada *(mediana y p95)* | US1 |
| **E6-02** | Tiempo de respuesta por severidad | US1 |
| **E6-03** | Desglose de tiempos por tramo del ciclo | US2 |
| **E6-04** | Asignación automática vs manual y sus tiempos | US2 |
| **E6-07** | Desviación entre la referencia y la llegada real | US2 |
| **E6-05** | Tasa de rechazo y timeout por unidad | US3 |
| **E6-06** | Abortos y misiones fallidas | US3 |
| **E6-09** | Cierres forzados desde central | US3 |
| **E6-10** | Envejecimiento de la cartera de casos abiertos | US3 |
| **E6-08** | Impacto humano agregado | US4 |
| **E6-11** | Escaladas de severidad originadas en sitio | US4 |
| **E6-12** | Cobertura de evidencia por severidad | US4 |

**E3-02, E3-10, E3-11 y E3-12** también sirven a OE6, pero su dueño es **OE3**, que define su meta
`[NORMATIVO]`. Este módulo los **referencia y no los reimplementa** (§7 del contrato).

## Capas

| Capa | Ruta | Estado |
|---|---|---|
| **Backend** | [`backend/`](./backend/) | **activa** — spec redactada |
| Frontend | *(pendiente)* | aplazada |

**Por qué el frontend está aplazado.** Igual que en los módulos tácticos: la ubicación en pantalla no
condiciona el contrato HTTP, y aquí además está sin decidir si el tablero estratégico es una pantalla
propia o una vista del tablero existente. Esa decisión es de CU-E01, no de este módulo.

## Lo que hay que saber antes de tocar este módulo

**Casi todo el cálculo ya existe, en la capa táctica.** Los 26 informes compuestos de Emergencias
(OT21–OT25) se construyeron sobre el mismo modelo y cubren la mayor parte del material de OE6. Lo que
este módulo añade **no es aritmética nueva**: es la ventana comparada, el percentil, el eje de región
y el contraste contra la meta. El detalle, en [`backend/spec.md`](backend/spec.md) §«Qué es nuevo».

**Tres informes arrastran una decisión abierta**, y están deliberadamente aislados en US3 para que no
bloqueen el MVP: `decisiones-pendientes.md` **#34** (E6-05), **#35** (E6-03) y **#36** (E6-09).

**«Por región» no es construible, y ya está resuelto que no lo es.** ⛔ No existe relación
región↔condado en el sistema operativo, y dos regiones comparten estado — unir por estado duplicaría
cada caso sin fallar. **Se agrupa por condado.** Ver [`backend/research.md`](backend/research.md) D1 y
`decisiones-pendientes.md` #38, que **afecta también a OE3**.

**Este módulo no amplía el modelo analítico.** Es el primero del proyecto que no lo necesita: no
añade tablas, dimensiones ni métricas.

## Documentos que lo gobiernan

- [`contrato-informes-estrategicos.md`](../contrato-informes-estrategicos.md) — período, metas,
  cobertura, rutas. Lo allí definido no se repite en la spec.
- [`acceso-estrategico.md`](../acceso-estrategico.md) §4.6 — los doce son de `DirectorOperaciones`.
- [`modelo-analitico/contracts/contrato-consumo.md`](../../002-tactico/modelo-analitico/contracts/contrato-consumo.md)
  — las 8 reglas de consulta.
- `informestacticos/TSI-Informes-Compuestos-Requeridos-por-OE.md` §6 — el catálogo.

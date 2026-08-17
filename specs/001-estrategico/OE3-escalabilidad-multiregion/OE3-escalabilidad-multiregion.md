# Módulo: OE3 — Escalabilidad Multi-Región sin Degradación

**Ubicación:** `specs/001-estrategico/OE3-escalabilidad-multiregion/`
**Objetivo estratégico:** OE3 · **Perspectiva BSC:** Procesos internos
**Feature paraguas:** `001-estrategico`
**Sustrato:** [`specs/002-tactico/modelo-analitico/`](../../002-tactico/modelo-analitico/)

Índice global del módulo (no es una spec Speckit). La feature activa de Speckit es **una capa**,
apuntada por `.specify/feature.json`.

## El titular de este módulo

> **OE3 puede medir que el servicio no se degrada. No puede medir la escalabilidad.**

El objetivo es *escalar a cualquier mercado sin degradar el rendimiento*. De sus dos mitades, **la
segunda es medible hoy y la primera no**: el modelo no sabe cuándo entró en producción ninguna región,
ni qué condados cubre cada una.

Siete de los catorce informes son construibles. Los otros siete están bloqueados, y **se agrupan por
motivo** en dos historias aparte para que el coste de cada bloqueo quede contado por separado.

## Los catorce informes

| # | Informe | Historia | Estado |
|---|---|:--:|:--:|
| **E3-02** | Latencia operativa de asignación *(compartido con OE6)* | US1 | ✅ |
| **E3-03** | Evolución de la latencia p95 | US1 | ✅ |
| **E3-10** | Tasa de error de registro *(compartido)* | US1 | ✅ |
| **E3-11** | Despachos al primer intento *(compartido)* | US1 | ✅ |
| **E3-07** | Ratio demanda / capacidad | US2 | ✅ |
| **E3-08** | Cobertura de respaldo por condado vecino | US2 | ✅ 🆕 dimensión |
| **E3-13** | Pérdida de señal GPS | US2 | ✅ |
| **E3-04** | Tiempo de puesta en operación regional | US3 | ⛔ |
| **E3-05** | Curva de maduración de región nueva | US3 | ⛔ |
| **E3-06** | Rendimiento por cohorte de región | US3 | ⛔ |
| **E3-12** | Tiempo de reasignación manual | US4 | ⛔ suceso no registrado |
| **E3-01** | Uptime global por región | US4 | ⛔ fuente externa |
| **E3-09** | Margen operativo por región | US4 | ⛔ fuente externa |
| **E3-14** | Cobertura de pruebas automatizadas | US4 | ⛔ fuente externa |

> **El reparto cambió en `/plan`** respecto de la primera lectura del catálogo: E3-12 pasó de
> construible a bloqueado y E3-08 al revés. El total no se mueve. Ver
> [`backend/research.md`](backend/research.md) D1–D3.

**OE3 es el dueño de los cuatro informes compartidos con OE6.** Define su meta `[NORMATIVO]`, así que
los implementa; OE6 los referencia y no los reimplementa (§7 del contrato).

## Capas

| Capa | Ruta | Estado |
|---|---|---|
| **Backend** | [`backend/`](./backend/) | **activa** — spec redactada |
| Frontend | *(pendiente)* | aplazada |

## Lo que hay que saber antes de tocar este módulo

**El modelo no sabe cuándo entró en producción una región.** Las tres versiones de `dim_region` llevan
`valido_desde = 1970-01-01` e `inicio_es_real = 0`: es la marca de «desde que empezamos a mirar», no
una fecha conocida. Medir «días hasta la primera emergencia atendida» contra esa fecha daría **más de
veinte mil días**, y no fallaría.

**Y no sabe qué condados cubre.** `decisiones-pendientes.md` #38.

**Es el único OE con tres informes cuya fuente está fuera del sistema**: monitoreo de
infraestructura, costos por región y cobertura de pruebas. No es que falte cargarlos: **no los produce
este sistema**.

## Documentos que lo gobiernan

- [`contrato-informes-estrategicos.md`](../contrato-informes-estrategicos.md)
- [`acceso-estrategico.md`](../acceso-estrategico.md) §4.3 — autoridad **repartida**: Tecnológico
  valida, Expansión decide dónde crecer, Operaciones responde por el despacho
- [`OE6-respuesta-y-vidas/`](../OE6-respuesta-y-vidas/OE6-respuesta-y-vidas.md) — el piloto, cuyas
  piezas transversales este módulo **reutiliza sin rehacer**
- `informestacticos/TSI-Informes-Compuestos-Requeridos-por-OE.md` §3

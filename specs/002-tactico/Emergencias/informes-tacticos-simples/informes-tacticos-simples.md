# Informes Tácticos Simples — Emergencias

**Departamento:** 6. Emergencias
**Objetivos tácticos cubiertos:** OT21 (registro limpio y sin duplicados), OT22 (asignar y despachar),
OT23 (acompañar la misión), OT24 (documentar la verdad del sitio), OT25 (cerrar de forma trazable)
**Creado:** 2026-08-14

Cinco listados llanos de solo lectura sobre el núcleo del sistema. Séptimo módulo de la serie, el que
cubre más objetivos tácticos, y el único que introduce **un eje de acotamiento nuevo**.

## Sobre el nombre de este módulo

Este departamento ya tenía una carpeta `informes-tacticos-simples` con los **19 informes agregados**.
Se renombró a [`informes-tacticos-agregados`](../informes-tacticos-agregados/informes-tacticos-agregados.md)
—que es lo que contiene— y este módulo ocupa el nombre que le corresponde.

**El código de aquel módulo no se tocó**: sigue en producción. Lo que cambió fue la carpeta de su
spec y sus referencias internas. El renombrado corrige de paso el error de nomenclatura que originó
toda esta revisión: aquellos informes se llamaban «simples» porque no usan ClickHouse, no porque no
agreguen.

## Capas

| Capa | Estado | Ruta |
|---|---|---|
| **backend** | Spec redactada · **implementada** | [`backend/spec.md`](backend/spec.md) · `backend/apps/accidentes/views/informes_views.py`, `backend/apps/seguimiento/views/informes_views.py` |
| **frontend** | Spec redactada · **implementada** | [`frontend/spec.md`](frontend/spec.md) · `/emergencias/informes-simples` |

Los **agregados** de Emergencias (workpanels Registro/Despacho/Seguimiento) siguen en
[`../informes-tacticos-agregados/`](../informes-tacticos-agregados/); no son estos listados.

## Los cinco listados

| # | Listado | OT | Tipo de filtro | Acotado por |
|---|---|:--:|---|---|
| 1 | Casos con ubicación, severidad, impacto y situación | OT21, OT25 | Período opcional | **Zona contratada** |
| 2 | Despachos con su origen, unidad y momento | OT22, OT23 | Período opcional | — (roles internos) |
| 3 | Fotografías de evidencia | OT24 | Período opcional | — (roles internos) |
| 4 | Notas de campo | OT24 | Período opcional | — (roles internos) |
| 5 | Cierres con resultado y calificación | OT25 | Período opcional | — (roles internos) |

## El cuarto eje de acotamiento

Los seis módulos anteriores acotaban por **titularidad**: quién es dueño del registro. Aquí no. Un
cliente ve **los casos cerrados de las zonas geográficas que tiene contratadas**, sea quien sea quien
los registró.

Y trae dos exigencias propias:

- **Sin zonas contratadas, resultado vacío** — nunca el listado completo. De las dos lecturas
  posibles de «sin zonas», es la única segura.
- **Solo casos cerrados** — la emergencia en curso es información operativa, no del cliente.

## La corrección de fondo: el estado de un caso no es una propiedad del caso

Tercera vez que el patrón aparece, tras la disponibilidad de una unidad y el motivo de una credencial.

Un caso queda inactivo por **tres razones muy distintas**:

| Razón | Significa |
|---|---|
| **Cerrado** | La emergencia se atendió y terminó |
| **Descartado** | Falsa alarma: nunca hubo emergencia |
| **Fusionado** | Es el mismo hecho que otro caso, que sigue vivo |

**El estado formal vive en el histórico de estados**, no en el caso. El listado expone lo que sí es
propiedad del caso —si sigue activo, si tiene hora de fin, de qué caso es duplicado— y con eso las
tres situaciones se distinguen sin inventar nada. El estado formal es compuesto, y ya lo cubren los
informes agregados.

> Un listado de «casos inactivos» sin distinguir pondría en la misma línea **emergencias atendidas,
> falsas alarmas y duplicados**: presentaría el trabajo realizado y el ruido descartado como la misma
> cosa.

## Doce filas del catálogo → cinco listados

- **Tres filas son el mismo listado de casos** — del período, en borrador, y abiertos sobre umbral.
- **Tres son el mismo listado de despachos** — del período, alertas de agotamiento, y misiones en
  tránsito.
- **Tres se resuelven en dos listados de evidencia** — fotografías y notas son registros distintos.
- **Dos son el mismo listado de cierres** — con resultado, y sin observaciones.
- **Dos ya están construidas** — monitoreo de casos activos y parámetros de asignación.

## Documentos que lo gobiernan

- [`specs/002-tactico/contrato-informes-simples.md`](../../contrato-informes-simples.md)
- `informestacticos/TSI-Informes-Tacticos-Requeridos-por-OT.md` §7
- [`../informes-tacticos-agregados/`](../informes-tacticos-agregados/informes-tacticos-agregados.md) —
  los 19 agregados, que **estos listados no duplican**

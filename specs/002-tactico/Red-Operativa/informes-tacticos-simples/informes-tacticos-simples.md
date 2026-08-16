# Informes Tácticos Simples — Red Operativa

**Departamento:** 4. Red Operativa
**Objetivos tácticos cubiertos:** OT11 (validar y publicar regiones), OT12 (mantener vigente la
flota), OT13 (retirar regiones sin cobertura)
**Creado:** 2026-08-14

Cuatro listados llanos de solo lectura. Cuarto módulo de la serie, tras
[Cuentas y Clientes](../../Cuentas-Clientes/informes-tacticos-simples/informes-tacticos-simples.md),
[Ventas y CRM](../../Ventas-CRM/informes-tacticos-simples/informes-tacticos-simples.md) y
[Suscripciones y Facturación](../../Suscripciones-Facturacion/informes-tacticos-simples/informes-tacticos-simples.md),
cuyas piezas reutiliza sin volver a decidirlas.

**Por qué este departamento fue el cuarto.** Reutiliza el eje de acotamiento por organización recién
construido —una empresa proveedora ve solo su flota— y sirve para confirmar que generaliza. Añade
además dos cosas nuevas: **datos geográficos** con una jerarquía de cinco niveles, y **el primer
informe cuyo error tiene consecuencia operativa, no comercial**.

## Capas

| Capa | Estado | Ruta |
|---|---|---|
| **backend** | Spec redactada | [`backend/spec.md`](backend/spec.md) |
| frontend | **Aplazado deliberadamente** | — |

## Los cuatro listados

| # | Listado | OT | Tipo de filtro | Acotado por |
|---|---|:--:|---|---|
| 1 | Composición de la flota (proveedor, condado, tipo, alta/baja) | OT12 | Estado actual | Empresa proveedora |
| 2 | Bajas de unidad con su tipo y caso afectado | OT12 | Período opcional | Empresa proveedora |
| 3 | Regiones operativas y su estado | OT11, OT13 | Estado actual | — (Administrador) |
| 4 | Intentos de validación de región | OT11 | Período opcional | — (Administrador) |

## La corrección de fondo: existir no es estar disponible

Es lo más importante de este módulo.

Una unidad tiene **dos** nociones de estado que el catálogo trataba como una:

- **Existencia** — dada de alta o de baja. Es una propiedad de la unidad, consultable en un listado.
- **Disponibilidad operativa** — Activa, Ocupada, En Misión o Fuera de servicio. **No es una
  propiedad de la unidad**: solo se conoce leyendo el último registro de su histórico de estados.

Obtener la disponibilidad para N unidades exige una consulta por unidad, o agregar el histórico y
volver a cruzar. **Ambas vías lo hacen compuesto.**

Por eso el listado de flota informa de **composición** —qué unidades tiene cada proveedor, dónde y
de qué tipo— y **no** de cuáles pueden atender un accidente ahora. La cobertura disponible es
**CU-T08**, ya clasificada como compuesta.

> **Por qué se insiste tanto.** Un listado filtrado por «la unidad existe» y presentado como «flota
> disponible» contaría unidades fuera de servicio, ocupadas o ya en camino a otro accidente. En un
> departamento comercial sería un número inflado; aquí es una decisión de cobertura tomada sobre
> unidades que no pueden atender nada.

## Ocho filas del catálogo → cuatro listados

- **Dos filas son el mismo listado de flota** — por estado/condado/proveedor y por tipo/capacidad.
- **Tres filas son el mismo listado de regiones** — por estado, detenidas en validación, y
  despublicadas.
- **Una fila se reclasificó a compuesta** — «unidades de lote pendientes de primer acceso» cruza la
  flota con el estado de las credenciales.
- **Y la disponibilidad operativa salió del listado de flota**, por lo explicado arriba.

## Documentos que lo gobiernan

- [`specs/002-tactico/contrato-informes-simples.md`](../../contrato-informes-simples.md)
- `informestacticos/TSI-Informes-Tacticos-Requeridos-por-OT.md` §5
- `.specify/docs/actors.md`, `.specify/docs/architecture/api-standards.md`

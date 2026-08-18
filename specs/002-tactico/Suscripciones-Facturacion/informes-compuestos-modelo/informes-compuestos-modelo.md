# Módulo: Informes Compuestos sobre el Modelo — Suscripciones y Facturación

**Ubicación:** `specs/002-tactico/Suscripciones-Facturacion/informes-compuestos-modelo/`
**Departamento:** Suscripciones y Facturación
**Feature paraguas:** `002-tactico`
**Sustrato:** [`specs/002-tactico/modelo-analitico/`](../../modelo-analitico/)

Índice global del módulo (no es una spec Speckit). La feature activa de Speckit es **una capa**,
apuntada por `.specify/feature.json`.

## Los 13 informes compuestos de OT05 a OT07

**Aquí viven cinco de los indicadores financieros del BSC** —MRR, ingresos, tasa de renovación,
movimientos de plan y NRR— que hoy **no tienen ninguna fuente**. Es el departamento con más
indicadores comprometidos y menos informes construidos: solo existe un simple, el catálogo de planes.

## Capas

| Capa | Ruta | Estado |
|------|------|--------|
| **Backend** | [`backend/`](./backend/) | **hecha** |
| **Frontend** | [`frontend/`](./frontend/) | **hecha** |

## Lo que hay que saber antes de tocar este departamento

**`activo` no dice si una suscripción está vigente.** Hay canceladas con esa columna en verdadero:
usarla **inflaría el MRR**.

**`motivocancelacion` está poblado en suscripciones activas**, así que no implica cancelación.

**Una suscripción de cuatro tiene la vigencia invertida** —fin antes que inicio— y produciría
duraciones negativas si nadie la aísla.

**`idplan_programado = 0` es un centinela**, no un plan.

## Autoridad repartida ⚠️

El §5.1 del SRS asigna **catálogo y precios al Director de Estrategia** y **facturación, cobro y mora
al Director Financiero**. El mapa exacto está en [`acceso-tactico.md`](../../acceso-tactico.md).

## Relación con los demás módulos del departamento

| Módulo | Qué es |
|---|---|
| [`../informes-tacticos-simples/`](../informes-tacticos-simples/) | Los 10 listados llanos |
| **`informes-compuestos-modelo/`** *(este)* | Los 13 informes agregados |

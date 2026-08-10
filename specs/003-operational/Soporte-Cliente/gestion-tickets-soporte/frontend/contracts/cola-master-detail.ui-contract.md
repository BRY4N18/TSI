# UI Contract: Cola de Soporte — Master-Detail

**Capa**: `gestion-tickets-soporte/frontend`
**Date**: 2026-07-30
**API**: sin endpoints nuevos — `../backend/contracts/gestion-tickets-soporte.openapi.yaml`

## Composición

| Panel | Contenido |
|-------|-----------|
| Lista (izq.) | `id_reclamo`, asunto, badges prioridad/estado/`sla_status`, selección con acento |
| Detalle (der.) | Asunto + id, acciones CU-O84-O87 (tomar/escalar/resolver), historial, composer |

## Filtros

- Prioridad → query `prioridad`
- Estado → query `idestadosoporte`
- Recarga lista al cambiar filtro; mantiene selección si el ticket sigue en resultados

## Empty state

- Título: «Cola de soporte»
- Mensaje: «No hay tickets pendientes.»
- Prohibido: CTA reembolso, «+ Nuevo ticket», pasarela pago

## Responsive (RNF-TIC-004)

- ≥1024px: dos columnas fijas
- <1024px: lista full-width; detalle en panel inferior o vista siguiente al seleccionar

## Deep-link

`/soporte-cliente/tickets/:idReclamo` — misma lógica de detalle; cola no obliga navegar fuera para acciones diarias.

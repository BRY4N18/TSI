# UI Contract: Mapa de Seguimiento (Operador)

**Capa**: `seguimiento-cierre-de-casos/frontend` | **Date**: 2026-07-30
**API**: `GET /seguimiento/mapa`, `GET /seguimiento/stream`, `GET /seguimiento/ruta`

## Marcadores accidente (severidad)

| Severidad | Color token |
|-----------|-------------|
| Leve | verde |
| Moderado | amarillo |
| Grave | naranja |
| Fatal | rojo |

## Marcadores unidad

| Estado | Color |
|--------|-------|
| Activa | azul |
| En Misión | naranja |
| Ocupada / Fuera | gris |

## SSE (RNF-SEG-001)

- EventSource → `/api/v1/seguimiento/stream`
- Eventos: posición GPS, ETA, cambio estado
- Reconexión automática con backoff
- **Prohibido** polling REST periódico para posiciones

## Interacción

- Clic marcador → panel resumen (id, severidad/estado, ETA)
- Unidad en camino: polyline origen→destino; ETA + distancia
- Acción «Forzar retiro» por despacho (O44) desde detalle embebido

## Acceso

- Rol Operador únicamente — Cliente guard 403 (CA-SEG-010)

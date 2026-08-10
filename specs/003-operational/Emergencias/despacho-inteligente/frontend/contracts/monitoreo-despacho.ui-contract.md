# UI Contract: Monitoreo de Despacho (Operador)

**Capa**: `despacho-inteligente/frontend` | **Date**: 2026-07-30
**API**: OpenAPI despacho + SSE stream

## Vista lista (`/despacho/monitoreo`)

- Filas: `idaccidente`, severidad badge, estado despacho, tiempo transcurrido
- Empty: «No hay casos en despacho activo»

## Vista detalle (`/despacho/monitoreo/:idaccidente`)

| Sección | Contenido |
|---------|-----------|
| Estado | Unidad asignada o «Buscando unidad…» |
| Historial | Intentos: Pendiente / Confirmado / Rechazado (+motivo) / Timeout |
| Mapa | Pin accidente + unidades candidatas/asignadas |
| Acciones | Asignar manualmente; Coordinar unidad adicional (O66) |

## Mi despacho (Unidad)

- Notificación activa más reciente
- Mapa ruta + ETA
- Botones: **Aceptar** | **Rechazar** (modal motivo obligatorio)

## SSE

- Eventos cambio estado despacho/notificación
- Complementa carga inicial REST; no sustituye validación server-side

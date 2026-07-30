# Feature Specification: Despacho Inteligente — Frontend

**Feature Branch / capa**: `despacho-inteligente/frontend`
**Created**: 2026-07-30
**Status**: Active (Fase B — Interaction extraída; implementación Angular en código)
**Depends-on**: [`../backend/spec.md`](../backend/spec.md) (RF-DES-*, RNF-DES-*, CA-DES-*, OpenAPI). Esta capa **MUST NOT** redefinir reglas de negocio, estados ni contratos REST.

**Input**: Clarificaciones UI: monitoreo operador RF-DES-011; unidad confirma/rechaza O24/O45; asignación manual O33; parámetros algoritmo RF-DES-010; alerta Admin sin unidades (notificación activa — backend).

## Clarifications

### Session 2026-07-09 / 2026-07-24 (UI — extraído backend)

- Q: ¿Superficie operador? → A: **Monitoreo despacho** — estado proceso, historial intentos, mapa accidente+candidatas (RF-DES-011).
- Q: ¿Unidad responde despacho? → A: Pantalla **Mi despacho** — Aceptar O24 / Rechazar O45 con motivo obligatorio.
- Q: ¿Sin unidades candidatas? → A: UI operador muestra alerta crítica + nota caso; Admin notificado por backend (no CTA reembolso ni flujos fuera spec).

## User Scenarios & Testing

### US-FE-1 — Monitoreo operador (P1)

Operador ve accidentes activos en despacho, historial intentos, tiempos transcurridos, mapa posiciones.

**Independent Test**: `/despacho/monitoreo` y `/despacho/monitoreo/:idaccidente`.

### US-FE-2 — Mi despacho (Unidad) (P1)

Unidad recibe notificación, ve detalle accidente/ruta/ETA, confirma o rechaza con motivo.

**Independent Test**: `/despacho/mi-despacho` — CTAs Aceptar/Rechazar; motivo req en rechazo.

### US-FE-3 — Asignación manual y múltiple (P2)

Operador asigna unidad manual O33 o coordina adicional O38 desde asignación manual.

**Independent Test**: `/despacho/asignacion/:idaccidente` — lista candidatas + confirmar.

### US-FE-4 — Parámetros algoritmo (P2)

Director Tecnológico ajusta timeout, pesos ranking, prioridades severidad→tipo unidad.

**Independent Test**: `/despacho/parametros` — guard con rol director; form validación rangos RF-DES-010.

## Functional Requirements (UI)

- **FR-UI-001**: Página monitoreo: lista casos activos en despacho con estado (Buscando/Asignado/Pendiente confirmación) — RF-DES-011.
- **FR-UI-002**: Detalle monitoreo por `idaccidente`: unidad(es) asignada(s), historial intentos (Confirmado/Rechazado/Timeout/Pendiente + motivo) — RF-DES-011.
- **FR-UI-003**: Detalle: temporizador tiempo desde registro accidente — RF-DES-011.
- **FR-UI-004**: Detalle: mapa accidente + posiciones unidades candidatas/asignadas — RF-DES-011.
- **FR-UI-005**: Actualizaciones monitoreo vía SSE `DespachoSseService` alineado seguimiento — RF-DES-011 / patrón RF-SEG-007.
- **FR-UI-006**: CTA «Asignar manualmente» → ruta asignación — CU-O33.
- **FR-UI-007**: CTA «Coordinar unidad adicional» (despacho múltiple O38) cuando ya hay despacho activo — RF-DES-009.
- **FR-UI-008**: Mi despacho: card notificación con severidad, dirección, coordenadas, ETA, mapa ruta sugerida — RF-DES-002.
- **FR-UI-009**: Mi despacho: Aceptar (O24) y Rechazar (O45) — motivo texto libre **requerido** en rechazo — RF-DES-003/004.
- **FR-UI-010**: Asignación manual: tabla/lista candidatas filtradas (Activa, mismo condado) + selección unidad — RF-DES-007.
- **FR-UI-011**: Asignación manual: confirmación antes de persistir origen Manual — RF-DES-007.
- **FR-UI-012**: Parámetros algoritmo: form timeout (30–300s), pesos distancia/tipo/disponibilidad, mapping severidad→tipo — RF-DES-010.
- **FR-UI-013**: Parámetros: feedback validación rangos inline — RF-DES-010.
- **FR-UI-014**: Guards operador / unidad / director tecnológico en rutas lazy — RBAC backend.
- **FR-UI-015**: Alerta UI «Sin unidades disponibles» cuando backend expone nota/estado crítico — RF-DES-006/008 (lectura; notificación Admin es backend).

## Out of Scope

- Cambiar algoritmo Haversine, jobs timeout O35, workers Kafka O36, hook plan Suscripciones (fail-open).
- Rastreo GPS tránsito (dueño seguimiento-cierre-de-casos).

## ISO/IEC 25010:2023 — Justificación

| Characteristic | Treatment |
|---|---|
| Interaction Capability | Núcleo — monitoreo, mi-despacho, asignación |
| Functional Suitability | FR-UI citan RF-DES-002…011 |
| Security | Guards por rol |
| Performance | RNF-DES-001 meta operativa — heredada |
| Maintainability | Capa FE separada |
| Reliability / Compatibility / Flexibility / Safety | N/A o heredadas |

**Traceability**: Índice [`../despacho-inteligente.md`](../despacho-inteligente.md).

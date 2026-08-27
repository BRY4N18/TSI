# Feature Specification: Despacho Inteligente — Frontend

**Feature Branch / capa**: `despacho-inteligente/frontend`
**Created**: 2026-07-30
**Status**: Active (Fase B — Interaction extraída; implementación Angular en código)
**Depends-on**: [`../backend/spec.md`](../backend/spec.md) (RF-DES-*, RNF-DES-*, CA-DES-*, OpenAPI). Esta capa **MUST NOT** redefinir reglas de negocio, estados ni contratos REST.

**Input**: Clarificaciones UI: monitoreo operador RF-DES-011; unidad confirma/rechaza O61/O62; asignación manual O64; parámetros algoritmo RF-DES-010; alerta Admin sin unidades (notificación activa — backend).

## Clarifications

### Session 2026-07-09 / 2026-07-24 (UI — extraído backend)

- Q: ¿Superficie operador? → A: **Monitoreo despacho** — estado proceso, historial intentos, mapa accidente+candidatas (RF-DES-011).
- Q: ¿Unidad responde despacho? → A: Pantalla **Mi despacho** — Aceptar O61 / Rechazar O62 con motivo obligatorio.
- Q: ¿Sin unidades candidatas? → A: UI operador muestra alerta crítica + nota caso; Admin notificado por backend (no CTA reembolso ni flujos fuera spec).

## User Scenarios & Testing

### US-FE-1 — Monitoreo operador (P1)

Operador ve accidentes activos en despacho, historial intentos, tiempos transcurridos, mapa posiciones.

**Independent Test**: `/despacho/monitoreo` y `/despacho/monitoreo/:idaccidente`.

### US-FE-2 — Mi despacho (Unidad) (P1)

Unidad recibe notificación, ve detalle accidente/ruta/ETA, confirma o rechaza con motivo.

**Independent Test**: `/despacho/mi-despacho` — CTAs Aceptar/Rechazar; motivo req en rechazo.

### US-FE-3 — Asignación manual y múltiple (P2)

Operador asigna unidad manual O64 o coordina adicional O66 desde asignación manual.

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
- **FR-UI-006**: CTA «Asignar unidad» en el detalle de monitoreo → ruta `/despacho/asignacion/:idaccidente` — CU-O64.
  *(Este requisito estaba escrito pero no construido: la ruta existía y ninguna pantalla
  enlazaba a ella, así que la vía manual —red de seguridad que el SRS §3.6.2 exige— solo se
  alcanzaba escribiendo la URL. Corregido el 2026-08-12.)*
- **FR-UI-007**: CTA «Coordinar unidad adicional» (despacho múltiple O66) cuando ya hay despacho activo — RF-DES-009.
- **FR-UI-008**: Mi despacho: card notificación con severidad, dirección, coordenadas, ETA, mapa ruta sugerida — RF-DES-002.
- **FR-UI-009**: Mi despacho: Aceptar (O61) y Rechazar (O62) — motivo texto libre **requerido** en rechazo — RF-DES-003/004.
- **FR-UI-010**: Asignación manual: tabla/lista candidatas filtradas (Activa, mismo condado) + selección unidad — RF-DES-007.
- **FR-UI-011**: Asignación manual: confirmación antes de persistir origen Manual — RF-DES-007.
- **FR-UI-012**: Parámetros algoritmo: form timeout (30–300s), pesos distancia/tipo/disponibilidad, mapping severidad→tipo — RF-DES-010.
- **FR-UI-013**: Parámetros: feedback validación rangos inline — RF-DES-010.
- **FR-UI-014**: Guards operador / unidad / director tecnológico en rutas lazy — RBAC backend.
- **FR-UI-015**: Alerta UI «Sin unidades disponibles» cuando backend expone nota/estado crítico — RF-DES-006/008 (lectura; notificación Admin es backend).

- **FR-UI-016**: Monitoreo: **filtros propios** de búsqueda por texto (identificador o descripción),
  estado y severidad, con conteo «N de M casos» y CTA «Limpiar filtros». El vacío por filtro se
  distingue del vacío por ausencia de casos: son dos situaciones distintas y el mensaje dice cuál
  es. Se filtra en cliente sobre la página ya cargada — la lista viene acotada a los casos en
  despacho activo, así que es instantáneo y no cuesta un viaje por tecla.
  *(Hallazgo #3 de la revisión del 24/08/2026: «a este apartado le hace falta un filtro de
  búsqueda, ya que actualmente solo se muestra una tabla». El aviso de truncado llegaba a remitir
  al usuario a «los filtros de la lista de accidentes» —otra pantalla—: para acotar lo que estaba
  viendo tenía que irse a otro sitio y volver.)*
- **FR-UI-017**: Panel de la unidad: tabla **Historial de despachos** (caso, fecha de despacho,
  llegada y fase), junto al historial de estado que ya existía — RN-DES-012.
  *(Hallazgo #13: «no hay un historial de las unidades de emergencia y su despacho». El historial
  de estado solo cuenta cambios de disponibilidad; no dice a qué acudió la unidad.)*

## Out of Scope

- Cambiar algoritmo Haversine, jobs timeout O63, workers Kafka O63, hook plan Suscripciones (fail-open).
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

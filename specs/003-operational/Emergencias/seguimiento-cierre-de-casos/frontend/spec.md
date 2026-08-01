# Feature Specification: Seguimiento y Cierre de Casos — Frontend

**Feature Branch / capa**: `seguimiento-cierre-de-casos/frontend`
**Created**: 2026-07-30
**Status**: Active (Fase B — Interaction extraída; implementación Angular en código)
**Depends-on**: [`../backend/spec.md`](../backend/spec.md) (RF-SEG-*, RNF-SEG-*, CA-SEG-*, OpenAPI). Esta capa **MUST NOT** redefinir reglas de negocio, estados ni contratos REST.

**Input**: Clarificaciones UI extraídas: mapa operador vía SSE (no polling); Cliente sin mapa ni casos activos; O42 solo motivo vs O28 formulario completo RF-SEG-004.

## Clarifications

### Session 2026-07-09 (UI — extraído backend)

- Q: ¿Actualizaciones mapa operador? → A: **SSE** `GET /seguimiento/stream` — eventos GPS, ETA, estado (RF-SEG-007, RNF-SEG-001).
- Q: ¿Cancelación O42 vs cierre O28? → A: UI cancelar pide **solo motivo**; cierre normal incluye resultado/conteos/calificación RF-SEG-004.
- Q: ¿Cliente ve mapa? → A: **No** — HTTP 403 + guard; solo expedientes cerrados por condado (RN-SEG-005).

## User Scenarios & Testing

### US-FE-1 — Mapa operador en tiempo real (P1)

Operador abre mapa, ve accidentes activos por severidad, unidades en misión, rutas/ETA actualizados por SSE.

**Independent Test**: `/seguimiento/mapa` + EventSource; clic marcador → resumen caso/unidad.

### US-FE-2 — Mi seguimiento (Unidad) (P1)

Unidad en camino reporta GPS, registra llegada, aborta misión o cierra desde móvil.

**Independent Test**: `/seguimiento/mi-seguimiento` — CTA llegada/abortar; posición periódica.

### US-FE-3 — Cierre y cancelación (P1)

Operador cierra caso multi-despacho con formulario RF-SEG-004; cancelación O42 solo motivo.

**Independent Test**: Form cierre vs modal cancelar — campos distintos según flujo.

### US-FE-4 — Historial y expedientes (P2)

Operador filtra historial; Cliente lista expedientes jurisdicción y exporta PDF.

**Independent Test**: Cliente `/seguimiento/expedientes` — sin acceso `/mapa`.

## Functional Requirements (UI)

- **FR-UI-001**: Mapa operador: marcadores accidentes por severidad (verde/amarillo/naranja/rojo) — RF-SEG-007.
- **FR-UI-002**: Mapa: marcadores unidades por estado (Activa azul, En Misión naranja, Ocupada/Fuera gris) — RF-SEG-007.
- **FR-UI-003**: Mapa: polilínea ruta unidad→accidente + ETA/distancia; preferir OSRM proxy con fallback — RF-SEG-007, backend T042b.
- **FR-UI-004**: Consumo SSE vía `SeguimientoSseService` (EventSource); **sin polling REST** para posiciones — RNF-SEG-001.
- **FR-UI-005**: Clic marcador: panel/popover detalle resumido caso o unidad — RF-SEG-007 §5.
- **FR-UI-006**: Mi-seguimiento: envío posición GPS periódico (~10s) mientras Confirmado — CU-O25.
- **FR-UI-007**: Mi-seguimiento: CTA «Registrar llegada» — CU-O26.
- **FR-UI-008**: Mi-seguimiento: CTA «Abortar misión» con confirmación — CU-O39.
- **FR-UI-009**: Formulario cierre caso O28: resultado (req), conteos finales, calificación opcional, observaciones — RF-SEG-004.
- **FR-UI-010**: Cancelar caso O42: modal motivo obligatorio; **sin** campos RF-SEG-004 — RF-SEG-010.
- **FR-UI-011**: Forzar retiro O44: acción por despacho desde detalle/mapa con confirmación — RF-SEG-011.
- **FR-UI-012**: Historial operador: filtros fecha/estado/severidad/ubicación/unidad + cursor pagination — RF-SEG-005.
- **FR-UI-013**: Detalle expediente operador: timeline despachos, GPS, evidencias — RF-SEG-005/006 lectura operador.
- **FR-UI-014**: Expedientes Cliente: solo casos CERRADOS en condados onboarding — RF-SEG-006, RN-SEG-005.
- **FR-UI-014a**: Expedientes Cliente — **listado** en `/seguimiento/expedientes`: tabla `md:table` + cards mobile, columna de acción `eye` (solo lectura, sin `pencil`: el cliente no edita expedientes), paginación por cursor y los tres estados asíncronos con los componentes canónicos `app-list-*`. La navegación «Mis expedientes» apunta aquí, no al detalle — RF-SEG-006. (Agregado 2026-07-31: el enlace cargaba el detalle sin `idaccidente` y renderizaba una página vacía; ver `.specify/docs/changelog.md` F1.)
- **FR-UI-014b**: Expedientes Cliente — **detalle** en `/seguimiento/expedientes/:idaccidente` con el chrome de workpanel en página dedicada del golden sample *Accidente Detalles*: link «Volver a la lista» con `arrow-left`, eyebrow de modo, `h1` + badge de estado en la misma fila, secciones en cards y datos en `<dl>` (`dt` uppercase + `dd`) — **nunca** `<input disabled>` para fingir solo lectura (design-system §5) — RF-SEG-006.
- **FR-UI-015**: Cliente: export PDF expediente — RF-SEG-006 §4.
- **FR-UI-016**: Guards: operador (`mapa`, `historial`), unidad (`mi-seguimiento`), cliente (`expedientes`); Cliente **403** en mapa — CA-SEG-010.
- **FR-UI-017**: Alertas GPS perdido (O37) visibles como notas tipo alerta en detalle caso — RF-SEG-008 (lectura).

## Out of Scope

- Cambiar OpenAPI, geofencing server-side, jobs depuración GPS, cálculo rutas tráfico real-time externo.
- Mapa en tiempo real para Cliente.

## ISO/IEC 25010:2023 — Justificación

| Characteristic | Treatment |
|---|---|
| Interaction Capability | Núcleo — mapa SSE, flujos cierre móvil |
| Functional Suitability | FR-UI citan RF-SEG-004…007, RF-SEG-010/011 |
| Security | Guards rol + RN-SEG-005 |
| Performance | RNF-SEG-001 latencia SSE |
| Maintainability | Capa FE separada |
| Reliability / Compatibility / Flexibility / Safety | N/A o heredadas |

**Traceability**: Índice [`../seguimiento-cierre-de-casos.md`](../seguimiento-cierre-de-casos.md).

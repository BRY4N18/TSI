# Feature Specification: Gestión de Tickets de Soporte — Frontend

**Feature Branch / capa**: `gestion-tickets-soporte/frontend`
**Created**: 2026-07-30
**Status**: Active (Fase B — Interaction extraída; implementación Angular en código)
**Depends-on**: [`../backend/spec.md`](../backend/spec.md) (RF-TIC-*, RNF-TIC-*, CA-TIC-*, OpenAPI). Esta capa **MUST NOT** redefinir reglas de negocio, estados ni contratos REST.

**Input**: Clarificaciones UI extraídas del backend (Session 2026-07-26/29): nombre canónico **Cola de soporte**; layout master-detail; filtros OpenAPI; empty state; sin CTA reembolso ni alta de ticket en cola agente.

## Clarifications

### Session 2026-07-26 (UI — extraído backend)

- Q: ¿Layout de la cola del agente? → A: **Master-detail** en `/soporte-cliente/cola`: lista izquierda + panel detalle/acciones derecha. `detalle-ticket` permanece para deep-link y rol Cliente.
- Q: ¿El agente crea tickets desde la cola? → A: **No** — alta = CU-O91 / Mis tickets (Cliente). Sin CTA «+ Nuevo ticket» en cola.
- Q: ¿Botón reembolso? → A: **No** en ninguna pantalla del módulo (§13 backend).
- Q: ¿Filtros de cola? → A: Prioridad y estado vía query params `prioridad` / `idestadosoporte` (OpenAPI).
- Q: ¿«SLA próximos a vencer» en UI? → A: Badge `sla_status='en riesgo'`; vencidos = `'incumplido'` (RF-TIC-004/007).

### Session 2026-07-29 (UI — extraído backend)

- Q: ¿Superficie canónica del agente? → A: Nav y títulos **Cola de soporte** (no «Cola de agente»).
- Q: ¿`idservicio` en registro Cliente? → A: Select opcional desde catálogo `GET /soporte/servicios` en Mis tickets (CU-O91).

## User Scenarios & Testing

### US-FE-1 — Cola master-detail del agente (P1)

Agente abre Cola de soporte, filtra por prioridad/estado, selecciona ticket, responde o toma/resuelve según estado sin salir de la página.

**Independent Test**: `/soporte-cliente/cola` — lista+detalle visibles ≥1024px; filtros recargan lista; empty state tipado si cero resultados.

### US-FE-2 — Mis tickets (Cliente) (P1)

Cliente registra ticket, ve historial filtrado por rol, confirma cierre o reabre; nunca ve notas internas.

**Independent Test**: Rol Cliente en `/soporte-cliente/mis-tickets` — composer sin toggle nota interna; historial sin entradas `es_nota_interna=true`.

### US-FE-3 — Deep-link detalle (P2)

URL `/soporte-cliente/tickets/:id` funciona para Cliente y agentes; acciones según rol/estado.

**Independent Test**: Agente abre deep-link → mismas acciones CU-O92 que panel embebido de cola.

### US-FE-4 — Administración SLA y dashboard (P2)

Administrador configura reglas versionadas; supervisor consulta métricas RF-TIC-007.

**Independent Test**: `/configuracion-sla` y `/dashboard` protegidos por guards; dashboard muestra agregaciones CA-TIC-016.

## Functional Requirements (UI)

- **FR-UI-001**: Nav canónico **Cola de soporte** (`nav-links.ts`); deprecar sinónimos en labels nuevos.
- **FR-UI-002**: Cola agente = master-detail: lista (id, asunto, badges prioridad/estado/`sla_status`) + panel detalle (historial + composer + acciones CU-O92) — RF-TIC-008, CA-TIC-014.
- **FR-UI-003**: Ítem seleccionado en lista con acento visual design-system (borde/background token).
- **FR-UI-004**: Filtros UI prioridad y estado cableados a `TicketApiService.listar({ prioridad, idestadosoporte })` — RF-TIC-008 §2.
- **FR-UI-005**: Empty state: título «Cola de soporte» + «No hay tickets pendientes.»; sin CTAs de reembolso ni alta — CA-TIC-015.
- **FR-UI-006**: Sin CTA «+ Nuevo ticket» ni «Procesar reembolso» en cola ni detalle agente — §13 backend.
- **FR-UI-007**: Badges prioridad, estado y `sla_status` usan tokens semánticos design-system (no hex ad hoc) — RNF-TIC-004.
- **FR-UI-008**: Viewport ≥1024px: lista + detalle simultáneos sin scroll horizontal de composición — RNF-TIC-004.
- **FR-UI-009**: Viewports menores: stack lista→detalle preservando acciones primarias en panel detalle — RNF-TIC-004.
- **FR-UI-010**: Composer con toggle «Nota interna» solo roles soporte; oculto para Cliente — RN-TIC-002.
- **FR-UI-011**: Cliente en detalle/mis-tickets: historial filtrado (defensa UI; autoridad API) — RN-TIC-002.
- **FR-UI-012**: Mis tickets: formulario registro CU-O91 con select opcional `idservicio` (catálogo servicios) — RF-TIC-001 / T098 backend.
- **FR-UI-013**: Mis tickets: flujo confirmar cierre y reabrir (CU-O97) con CTAs explícitos según estado Resuelto/Cerrado.
- **FR-UI-014**: Configuración SLA: tabla/formulario alta y modificación con feedback éxito/error — CU-O95.
- **FR-UI-015**: Dashboard soporte: tarjetas/tablas métricas RF-TIC-007 (estado, prioridad, SLA en riesgo/incumplido, tiempos, reapertura) — CA-TIC-016.
- **FR-UI-016**: Guards por rol en rutas lazy (`cliente-soporte`, `agente-soporte`, `administrador-sla`) — reutiliza RBAC backend.
- **FR-UI-017**: Acciones primarias tomar/responder/resolver al alcance del panel detalle (Ley de Fitts) — RNF-TIC-004.

## Out of Scope

- Cambiar OpenAPI, validaciones de servidor, job SLA Kafka, lógica de clasificación automática.
- Chat en vivo, NPS, integraciones helpdesk externas, pasarela de pago/reembolsos.
- Alta de ticket desde cola del agente (permanece CU-O91 Cliente).

## ISO/IEC 25010:2023 — Justificación

| Characteristic | Treatment |
|---|---|
| Interaction Capability | Núcleo — master-detail, filtros, empty state, composer (Principio IV) |
| Functional Suitability | FR-UI citan RF-TIC-008, RF-TIC-007, RNF-TIC-004, RN-TIC-002 |
| Security | Guards + ocultamiento notas internas Cliente |
| Usability | RNF-TIC-004 operabilidad bajo presión |
| Maintainability | Capa FE separada de `backend/` |
| Reliability / Performance / Compatibility / Flexibility / Safety | N/A o heredadas del backend |

**Traceability**: Índice módulo [`../gestion-tickets-soporte.md`](../gestion-tickets-soporte.md).

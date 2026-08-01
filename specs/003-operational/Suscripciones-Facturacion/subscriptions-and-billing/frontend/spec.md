# Feature Specification: Suscripciones y Facturación — Frontend

**Feature Branch / capa**: `subscriptions-and-billing/frontend`
**Created**: 2026-07-30
**Status**: Active — delta UX catálogo planes (alineación piloto Accidentes / Alta unidades)
**Depends-on**: [`../backend/spec.md`](../backend/spec.md) (RF-SUSF-*, RNF-SUSF-*, CA-SUSF-*). Esta capa **MUST NOT** redefinir reglas de negocio, estados ni contratos REST.

## Clarifications

### Session 2026-07-30 (UI)

- Q: ¿Quién edita catálogo planes en UI? → A: Solo rol `DirectorEstrategia` — Admin ya no CRUD planes (RF-SUSF-001 enmienda 2026-07-30).
- Q: ¿Home billing por rol? → A: Redirect en `suscripcionesHomeRedirect` — Proveedor → mi-suscripcion; Admin → aprobaciones; Director → catálogo.

### Session 2026-07-30 (catálogo planes — piloto UX)

- Q: ¿Workpanel split en catálogo planes? → A: **No**. Mismo patrón que Alta unidades: **lista + página Detalles (RO) + página Formulario** (crear/editar). Sin comprimir la lista.
- Q: ¿Abrir plan por nombre/ID como enlace? → A: **No**. Solo vía acciones **ojo** / **lápiz** (≥44×44).
- Q: ¿Detalle vs editar? → A: Ruta lectura dedicada **sin Guardar**; editar en `plan-form` con **Guardar cambios** en cabecera (primary arriba).

### Session 2026-07-30 (catálogo planes — filtros + paginación)

- Q: ¿La UI puede pedir el catálogo completo y paginar en el navegador? → A: **No**. El catálogo **MUST** usar el listado **paginado del backend** (Depends-on RF-SUSF-001 listado / RNF-SUSF-005a): página default **20**, cursor para siguiente/anterior.
- Q: ¿Filtros en UI? → A: **Texto** (nombre), **estado** (Activo / Inactivo / Todas — Director), **nivel**. Cambiar filtro reinicia a la primera página.
- Q: ¿Tiempo hasta ver filas? → A: Alineado a SC backend: resultado (filas/vacío/error) en &lt; 2 s p95; timeout UI → error + Reintentar (no skeleton infinito).

## User Scenarios & Testing

### US-FE-1 — Portal Proveedor (P1)

Proveedor gestiona suscripción, método de pago, historial y cambio de plan sobre su `idcliente` (RF-SUSF-010, RF-SUSF-002, RF-SUSF-006, RF-SUSF-003).

**Independent Test**: Login Proveedor → landing mi-suscripcion; no ve CRUD de planes.

**Acceptance Scenarios**:

1. **Given** Proveedor autenticado, **When** entra a `/suscripciones`, **Then** aterriza en mi-suscripcion (no catálogo Director).
2. **Given** suscripción Suspendida (RN-SUSF-017), **When** intenta acción operativa bloqueada, **Then** ve mensaje claro de bloqueo.

### US-FE-2 — Catálogo planes Director (P1) — *delta UX + listado*

Director Estrategia crea/edita/desactiva planes (RF-SUSF-001) con el patrón de catálogo del piloto: lista + ojo (detalle RO) + lápiz (form) + CTA crear arriba; **filtros y paginación** vía listado backend (nunca dump completo).

**Independent Test**: Director → catálogo ≤20 filas; filtros reducen conjunto; Siguiente pide otra página; ojo → Detalles sin Guardar; lápiz → form editar.

**Acceptance Scenarios**:

1. **Given** catálogo con ≥1 plan, **When** pulsa ojo, **Then** abre página Detalles (campos no editables, sin Guardar).
2. **Given** Detalles, **When** pulsa Editar (opcional), **Then** navega al formulario de edición.
3. **Given** catálogo, **When** pulsa lápiz, **Then** abre el mismo componente de formulario en modo editar.
4. **Given** catálogo, **When** pulsa «Crear plan» (header), **Then** abre formulario vacío de alta.
5. **Given** formulario crear/editar, **When** ve la página, **Then** el CTA primario Guardar/Publicar está en la **cabecera** (no solo al pie).
6. **Given** plan activo, **When** desactiva, **Then** confirma en diálogo de 2 pasos antes de aplicar.
7. **Given** fila del catálogo, **When** inspecciona acciones, **Then** no abre detalle/edición haciendo clic en el nombre como único enlace (solo iconos/acciones).
8. **Given** más de 20 planes que cumplen el filtro, **When** abre el catálogo, **Then** ve como máximo una página (default 20) y puede avanzar.
9. **Given** filtros de texto/estado/nivel, **When** los cambia, **Then** vuelve a la primera página y el conjunto visible refleja el filtro.

### US-FE-3 — Aprobaciones downgrade Admin (P1)

Administrador resuelve solicitudes pendientes de downgrade (RF-SUSF-003).

**Independent Test**: Admin → aprobaciones; Director/Proveedor no CRUD Admin.

**Acceptance Scenarios**:

1. **Given** Admin, **When** entra a `/suscripciones`, **Then** aterriza en aprobaciones-downgrade.
2. **Given** solicitud Pendiente, **When** aprueba/rechaza, **Then** ve feedback y la bandeja se actualiza.

### US-FE-4 — Acceso suspendido (P1)

UI refleja RN-SUSF-017 — mensaje cuando suscripción Suspendida bloquea acciones operativas.

**Independent Test**: Estado Suspendida visible; CTA de cobro/reintento solo cuando RN-SUSF-017 lo permite.

## Functional Requirements (UI)

### Baseline (entregado)

- **FR-UI-001**: Shell `billing-shell.page` con tabs/nav por rol.
- **FR-UI-002**: `mi-suscripcion` — alta inicial RF-SUSF-010, estado Activa/Suspendida/Cancelada.
- **FR-UI-003**: `metodos-pago` — alta/reemplazo tokenizado; postcondición reactivación automática visible (RF-SUSF-002, RN-SUSF-021).
- **FR-UI-004**: `historial-facturas` — orden `fecha_emision` desc (RF-SUSF-006).
- **FR-UI-005**: `cambio-plan` — upgrade inmediato / downgrade solicitud Pendiente (RF-SUSF-003).
- **FR-UI-006**: `catalogo-planes` — listado; CRUD solo Director en rutas `planes/nuevo` y `planes/:idplan/editar` (RF-SUSF-001). **Complementado** por FR-UI-014…018 (delta UX).
- **FR-UI-007**: `aprobaciones-downgrade` — bandeja Admin (RF-SUSF-003).
- **FR-UI-008**: Guards `proveedor-billing`, `admin-billing`, `director-estrategia-billing`.
- **FR-UI-009**: `suscripcionesHomeRedirect` — landing por rol al entrar a `/suscripciones`.
- **FR-UI-010**: Servicios API: suscripcion, plan, metodo-pago, factura — tipos desde OpenAPI.
- **FR-UI-011**: CTA «Reintentar cobro» en factura Fallida cuando RN-SUSF-017 lo permite (RF-SUSF-007 UX).
- **FR-UI-012**: Estados async del design-system (loading skeleton, vacío, error+Reintentar) en pages billing; ver checklist humo.
- **FR-UI-013**: Proveedor nunca selecciona otro `idcliente` — scope implícito del token (RNF-SUSF-002).

### Delta — Catálogo planes (piloto UX)

- **FR-UI-014**: Acciones de fila ≥44×44: **ojo** → página Detalles (lectura); **lápiz** → página Formulario (editar). Nombre/ID del plan como texto plano (no único enlace de apertura).
- **FR-UI-015**: Ruta dedicada de **Detalles** (`planes/:idplan` o equivalente), con el chrome de workpanel en página dedicada del golden sample *Accidente Detalles*: link «Volver a la lista» con `arrow-left`, eyebrow de modo («Detalles»), `h1` + badge de estado en la misma fila, y datos en `<dl>` con `dt` uppercase + `dd` texto. **Sin** Guardar; CTA opcional «Editar».
  > Corregido 2026-07-31: este requisito pedía «campos disabled / solo lectura», que contradice el design-system global §5 («en modo Ver, datos como `<dl>`… **nunca** `<input disabled>` para fingir solo lectura»). La implementación usaba `<input disabled readonly>`; ver `.specify/docs/changelog.md` F3. El design-system es la autoridad: un spec de módulo no puede relajar una regla global de diseño.
- **FR-UI-016**: CTA «Crear plan» permanece en el **header** del catálogo (ya presente). **Sin workpanel split** que comprima la lista.
- **FR-UI-017**: En `plan-form` (crear y editar), el CTA primario («Publicar plan» / «Guardar cambios») **MUST** estar en la **cabecera** de la página (además de o en lugar del pie-only).
- **FR-UI-018**: Desactivar / reactivar desde la lista con confirmación explícita (diálogo); no se completa con un solo clic accidental.
- **FR-UI-019**: El catálogo **MUST** consumir el listado **paginado** del backend (`cursor`/`limit`, default **20**, `meta.pagination`). **Prohibido** pedir o cachear el catálogo completo en el cliente para paginar en memoria.
- **FR-UI-020**: Filtros UI: **texto** (nombre), **estado** (Activo / Inactivo / Todas), **nivel**. Cambiar filtros reinicia cursor/página 1.
- **FR-UI-021**: Pager (Anterior/Siguiente o equivalente) según `next_cursor`; «Actualizar» reaplica filtros+página actuales; timeout → error + Reintentar (sin skeleton infinito).

## Success Criteria

- **SC-001**: En &lt;2 minutos guiados, Director abre Detalles de un plan **sin** botón Guardar.
- **SC-002**: 100 % de aperturas detalle/edición desde iconos de acción (no desde el nombre como único enlace).
- **SC-003**: «Crear plan» visible en header del catálogo; alta sin modal/workpanel split.
- **SC-004**: En form crear/editar, Guardar/Publicar reachable en cabecera sin scroll al pie en viewport desktop estándar (≥1280px).
- **SC-005**: Desactivar sin confirmación en 2 pasos no se completa.
- **SC-006**: Admin no alcanza rutas `planes/nuevo` ni `planes/:id/editar` (guard Director).
- **SC-007**: Con más de 20 planes filtrados, el catálogo **nunca** muestra más de una página a la vez; el resto solo vía paginación.
- **SC-008**: En el 95 % de aperturas/Actualizar del catálogo, el Director ve filas, vacío o error en **menos de 2 segundos**.
- **SC-009**: Un filtro por nombre, estado o nivel reduce correctamente el conjunto visible (verificable en humo).

## Edge Cases

- Catálogo vacío + CTA Crear plan.
- Plan inactivo: reactivar desde lista; ojo sigue abriendo Detalles RO.
- Error de carga del plan en Detalles/Form → error + Reintentar / volver.
- Deep-link a editar sin permiso → redirect/denegado por guard.
- Filtros sin coincidencias → vacío explícito (no error genérico).
- `last` página: Siguiente deshabilitado; Anterior recupera página previa.

## Out of Scope

- Pasarela real (simulador backend v1).
- Pricing dinámico por región.
- Jobs batch (Sistema).
- Redefinir RF-SUSF-* en el frontend (el contrato de listado lo define backend).
- Workpanel split para catálogo planes.
- Rehacer portal Proveedor / aprobaciones Admin salvo roturas por listado paginado.
- Dump completo de planes “para combo” de otras pantallas: esas pantallas MUST usar listado activo acotado o endpoint de detalle — no reabrir dump ilimitado.

## Assumptions

- Backend list/get/create/update/deactivate de planes disponibles (Depends-on); **listado paginado+filtros** es requisito vigente de RF-SUSF-001 (enmienda 2026-07-30), no opcional.
- Patrón de referencia: Accidentes + Alta unidades (páginas + listado cursor).
- Lecturas puntuales por `idplan` (detalle/form) no sustituyen el listado paginado.

## ISO/IEC 25010:2023 — Justificación

| Characteristic | Treatment |
|---|---|
| Interaction Capability | **Aplica** — catálogo + Detalles RO + Form; ojo/lápiz; filtros/pager (SC-007…009) |
| Functional Suitability | FR-UI citan RF-SUSF-*; listado conforme RNF-SUSF-005a |
| Security | Guards por rol; Admin sin CRUD planes (SC-006); scope Proveedor |
| Maintainability | Un `plan-form` crear/editar; una página Detalles; list facade parametrizado |
| Reliability | Loading/error+Reintentar; desactivar con confirmación |
| Safety | N/A — facturación comercial, no cadena de despacho de emergencias |
| Performance Efficiency | **Aplica** — SC-007/008; sin dump completo en cliente |
| Compatibility | Listado vía Depends-on OpenAPI (`meta.pagination`) |
| Flexibility | N/A — sin multi-región/pricing regional en este delta |

**Traceability**: [`../subscriptions-and-billing.md`](../subscriptions-and-billing.md).

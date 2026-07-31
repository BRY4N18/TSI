# Feature Specification: Pipeline Comercial y Prospectos — Frontend

**Feature Branch / capa**: `commercial-pipeline-prospects/frontend`
**Created**: 2026-07-30
**Status**: Active (Fase B — Interaction Capability)
**Depends-on**: [`../backend/spec.md`](../backend/spec.md) (RF-CPP-*, RNF-CPP-*, CA-CPP-*). Esta capa **MUST NOT** redefinir reglas de negocio, estados ni contratos REST.

## Clarifications

### Session 2026-07-30 (UI)

- Q: ¿Catálogo planes público duplicado con Suscripciones? → A: RF-CPP-000 lee mismo catálogo; ruta pública `/ventas-crm/planes` es entrada comercial del embudo, sin JWT.
- Q: ¿Conflictos 409 en pipeline? → A: UI muestra mensaje de conflicto optimista y CTA «Refrescar» (RF-CPP-004 clarificación 2026-07-25).
- Q: ¿Retroceso de etapa en board? → A: No permitido en UI — solo avance adyacente + Perdido.

### Session 2026-07-30 (workpanel CRUD)

- Q: ¿Cómo se materializa el workpanel en Prospectos? → A: Lista + página dedicada workpanel (patrón Accidentes); sin modal; split-view no obligatorio. Modo Ver en este delta; Editar/Crear de ficha diferidos (ver Q lápiz).
- Q: ¿Qué hace el lápiz / modo Editar? → A: Solo `eye` (Ver + acciones de dominio). Sin lápiz / sin Guardar de datos de ficha en este delta (no hay PATCH de contacto en Depends-on).
- Q: ¿Qué CTA de “crear” va en el header del listado? → A: Solo Admin: CTA «Entrada directa» → `/entrada-directa`. Gerente: sin CTA crear en listado.
- Q: ¿Cómo se opera el pipeline-board junto al workpanel? → A: Board con botones adyacentes + Perdido; ojo → workpanel; sin drag en este delta.
- Q: ¿Filtros en el listado autenticado? → A: Filtros `activo` + `etapa_actual`; cambio reinicia página 1.

### Session 2026-07-30 (chrome Accidente + UX humano)

- Q: ¿Cómo se presenta el modo Ver? → A: Como Accidente Detalles: link «← Volver», título+badge, cards, **`<dl>` tipográfico** — **no** `<input disabled>`.
- Q: ¿El usuario ingresa IDs técnicos? → A: **No.** Catálogos y dueños se eligen por **nombre** (combobox). IDs solo en API. No mostrar `idcliente`/`idusuario`/`idcondado` como campos de UI.
- Q: ¿Alcance del rediseño? → A: Workpanel + Entrada directa en este feature; formulario alta-unidades en polish cruzado (mismo principio UX) — **no** solo un fragmento de pantalla.

## User Scenarios & Testing

### US-FE-1 — Consultar catálogo público (P1)

Visitante ve planes activos en solo lectura antes de registrarse (RF-CPP-000).

### US-FE-2 — Registro de prospecto (P1)

Formulario público inbound crea prospecto y muestra grant demo si aplica (RF-CPP-001).

### US-FE-3 — Operar pipeline asignado (P1)

Gerente ve listado/board solo de prospectos propios; Admin ve todos (RF-CPP-008). Patrón piloto: **lista + página workpanel** en modo **Ver** (Detalles), sin modal y sin split-view obligatorio. **Sin** lápiz ni edición de ficha en este delta (Depends-on sin PATCH de contacto).

**Independent Test**: Lista con ojo ≥44×44; ojo → Detalles sin Guardar de ficha; acciones de dominio según rol/estado; nombre/ID no son el único enlace de apertura.

**Acceptance Scenarios**:

1. **Given** listado con ≥1 prospecto, **When** pulsa ojo, **Then** abre workpanel «Detalles» con chrome Accidente (`← Volver`, título+badge, `dl` RO), **sin** Guardar de ficha y **sin** inputs disabled fingiendo Ver.
2. **Given** listado, **When** inspecciona acciones de fila, **Then** **no** hay ícono lápiz de edición de ficha.
3. **Given** fila del listado, **When** inspecciona, **Then** nombre/ID son texto plano (no único enlace de apertura).
4. **Given** Admin en listado, **When** ve el header, **Then** hay CTA «Entrada directa»; **Given** Gerente, **Then** no hay CTA de alta en el listado.
5. **Given** filtros de activo/etapa, **When** los cambia, **Then** vuelve a la primera página y el conjunto visible refleja el filtro.
6. **Given** cualquier formulario de este módulo (o asignación en workpanel), **When** elige catálogo/dueño, **Then** usa combobox por nombre — **nunca** teclea un ID numérico de sistema.

### US-FE-4 — Transiciones y pérdida (P1)

Board permite avanzar etapa adyacente o marcar Perdido con motivo mediante **botones** (sin drag); maneja 409 (RF-CPP-004, RF-CPP-005). Las mismas acciones de dominio pueden vivir en el workpanel Ver según estado/rol. Ojo en card → workpanel.

### US-FE-5 — Entrada directa (P2)

Administrador crea cliente sin prospecto previo (RF-CPP-007).

### US-FE-6 — Conversión a cliente (P1)

Desde workpanel Ver, acción convertir con validación NIT (RF-CPP-006).

## Functional Requirements (UI)

- **FR-UI-001**: Página pública `catalogo-planes` — skeleton/vacío/error+retry; CTA a registro (RF-CPP-000).
- **FR-UI-002**: Página `registro-publico` — formulario O116; estados loading/error (RF-CPP-001).
- **FR-UI-003**: Rutas públicas `/ventas-crm/planes` y `/ventas-crm/registro` sin JWT en `app.routes.ts`.
- **FR-UI-004**: `listado-prospectos` — tabla con skeleton/vacío/error; filtro implícito por rol gerente (RF-CPP-008). Filtros UI: **activo** y **etapa_actual** (params del Depends-on); cambiar filtro reinicia a primera página (cursor null). Acción de fila ≥44×44: **ojo** → workpanel Ver. **MUST NOT** mostrar lápiz de edición de ficha en este delta. Nombre/ID como texto plano (no único enlace). Paginación cursor/limit del listado backend.
- **FR-UI-005**: Workpanel `detalle-prospecto` modo **Ver** («Detalles»): chrome = Accidente Detalles (shell, `← Volver`+ícono, título+badge, cards, grid). Lectura = **`<dl>`/`dd` tipográfico** — **MUST NOT** `<input disabled>`. **Sin** Guardar de ficha. Acciones de dominio (asignación, transición, Perdido, conversión) según dueño/rol/estado (RF-CPP-003, RF-CPP-006) con botones+íconos Tabler. Si hay selector de gerente: **combobox por nombre/email**, no ID numérico. Loading/error = shared list-states. Modos Editar/Crear de ficha: **fuera de alcance** hasta exista PATCH en Depends-on.
- **FR-UI-006**: `pipeline-board` — columnas por etapa; **botones** de avance adyacente y Perdido en card (o equivalentes accesibles); **sin** drag-and-drop en este delta; sin retroceso (RF-CPP-004). Vista operativa distinta del workpanel. Cada card expone **ojo** ≥44×44 → workpanel Ver; empresa/nombre como texto plano (no único enlace de apertura).
- **FR-UI-007**: Modal/motivo obligatorio al marcar `Perdido` (RF-CPP-005).
- **FR-UI-008**: Manejo HTTP 409 — toast + refrescar estado prospecto (optimistic check backend).
- **FR-UI-009**: `entrada-directa` — solo Admin; formulario RF-CPP-007 con **mismo chrome** Accidente (Volver link, card secciones, focus ring formularios, submit en carga, error con ícono). Sin campos de ID técnico.
- **FR-UI-010**: Guards `gerente-ventas`, `gerente-cuentas-publicas`, `admin-o-gerente-crm`, `admin-crm`.
- **FR-UI-011**: `ProspectoApiService`, `PipelineApiService`, `ConversionApiService`, `PlanesApiService`.
- **FR-UI-012**: Primera asignación huérfano: acción visible solo Admin (RF-CPP-003 clarificación).
- **FR-UI-013**: Listado Admin sin filtro por `idusuario`; gerente solo asignados.
- **FR-UI-014**: Navegación lazy `ventas-crm.routes.ts` — redirect default a prospectos autenticados.
- **FR-UI-015**: CTA primario en el **header** del listado solo para **Administrador**: «Entrada directa» → ruta `entrada-directa` (RF-CPP-007). **Gerente MUST NOT** ver CTA de alta en el listado. Alta de prospecto inbound permanece en `/ventas-crm/registro` (público). **Sin** modal de alta.
- **FR-UI-016**: Principio UX humano en formularios autenticados de este feature: el usuario **elige** entidades de catálogo/persona por **etiqueta legible** (combobox); **MUST NOT** pedir ni destacar PKs (`idusuario`, `idcliente`, etc.) en la UI. (Mismo principio se aplica en polish cruzado a alta-unidades: Condado por nombre, no “Condado (ID)”.)

## Success Criteria

- **SC-001**: En &lt;2 minutos guiados, Gerente/Admin abre Detalles de un prospecto **sin** botón Guardar de ficha y **sin** inputs disabled de ficha.
- **SC-002**: 100 % de aperturas al workpanel desde el ícono ojo (no desde el nombre como único enlace); cero íconos lápiz de ficha en listado.
- **SC-003**: En workpanel Ver, al menos una acción de dominio aplicable al estado es reachable sin salir de la página (avance, Perdido, convertir o asignar según reglas).
- **SC-004**: Admin ve CTA «Entrada directa» en header del listado; Gerente no ve ningún CTA de alta en ese listado.
- **SC-005**: Un filtro por `activo` o `etapa_actual` reduce correctamente el conjunto visible y reinicia a página 1.
- **SC-006**: Side-by-side vs Accidente Detalles: mismo Volver-link, eyebrow, título+badge, cards/`dl`; Entrada directa no pide IDs técnicos.

## Edge Cases

- Listado vacío: Admin sigue viendo CTA Entrada directa; Gerente ve vacío accionable sin inventar alta autenticada.
- Filtros sin coincidencias → vacío explícito (no error genérico).
- Prospecto `Perdido` / inactivo: ojo sigue abriendo Detalles RO; acciones de dominio deshabilitadas o ocultas según RF.
- 409 en transición: mensaje + Refrescar (FR-UI-008).
- Deep-link a rutas de «editar ficha» no existen en este delta.

## Out of Scope

- Demo interactiva y notificaciones (`notificacion-ventas`).
- Escritura en catálogo `Dim_Plan` (Suscripciones-Facturación).
- Split-view lista+panel lateral obligatorio (diferido; mobile/desktop usan página dedicada workpanel).
- Modo Editar/Crear de ficha de prospecto (lápiz + Guardar campos) — requiere PATCH en backend.
- Drag-and-drop en pipeline-board.

## ISO/IEC 25010:2023 — Justificación

| Characteristic | Treatment |
|---|---|
| Interaction Capability | Núcleo — lista + workpanel Ver (chrome Accidente) + board; SC-001…006 |
| Functional Suitability | FR-UI citan RF-CPP-*; sin inventar PATCH |
| Security | Guards CRM + rutas públicas acotadas |
| Maintainability | Workpanel Ver reutilizable; capa FE separada |
| Reliability | 409 + Refrescar; loading/vacío/error |
| Performance / Compatibility / Flexibility / Safety | N/A o heredadas del backend |

**Traceability**: [`../commercial-pipeline-prospects.md`](../commercial-pipeline-prospects.md).

**Plan artifacts**: [`plan.md`](./plan.md), [`research.md`](./research.md), [`data-model.md`](./data-model.md), [`contracts/prospectos-lista-workpanel.ui-contract.md`](./contracts/prospectos-lista-workpanel.ui-contract.md), [`quickstart.md`](./quickstart.md).

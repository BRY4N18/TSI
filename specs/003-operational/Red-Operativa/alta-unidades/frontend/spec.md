# Feature Specification: Alta de Unidades — Frontend (Lista + páginas)

**Feature Branch / capa**: `alta-unidades/frontend`  
**Created**: 2026-07-30  
**Updated**: 2026-07-30 (paginación, filtros, performance de catálogo)  
**Status**: Draft (**lista paginada + filtros** + página de lectura + formulario crear/editar; SMTP/gmail obligatorio)  
**Depends-on**: [`../backend/spec.md`](../backend/spec.md) (RF-CAM-*, RNF-CAM-*, CA-CAM-*, contrato de listado). Esta capa **MUST NOT** redefinir reglas de negocio, estados, pertenencia de flota ni el contrato REST — sí exige que el FE **observe y comunique** invitación SMTP y que el **listado de flota** soporte **paginación y filtros** acordes a los estándares del proyecto (listados operativos no entregan el catálogo completo de golpe).

**Input**: Catálogo del Proveedor con lista operativa (ojo/lápiz, ID sin enlace). **No workpanel split.** Navegación a páginas full:

- **Ojo** → página de **solo lectura** (Detalles).  
- **Lápiz / Nueva unidad** → **misma página de formulario** (crear vacío o editar poblado).

**Normativa visual**: design-system (lista/tablas operativas, acciones ≥44×44, Alert 2 pasos para baja) + páginas full como registro/detalle de accidentes (sin panel lateral que comprima la lista). Toda **tabla o lectura tabular** de flota en este módulo es **paginada** y ofrece **filtros de búsqueda** necesarios.

## Clarifications

### Session 2026-07-30 (UI — vigente)

- Q: ¿CU-O59 / disponibilidad externa Operador? → A: **Retirado** — sin ruta FE; disponibilidad vía CU-O30 (`evidencia-unidad`).
- Q: ¿Actor UI? → A: Solo **Proveedor** dueño de la flota; Admin sin override sobre flotas ajenas (RN-CAM-002 / RNF-CAM-004).
- Q: ¿Campo geográfico? → A: Selector de condado — no texto libre de zona (RN-CAM-005).

### Session 2026-07-30 (UI — catálogo + workpanel)

- Q: ¿Sustituir catálogo con alta embebida y páginas sueltas de edición/baja por el patrón Lista → Workpanel? → A: **Supersedido** — ver sesiones remediación; **no** se usa workpanel split.
- Q: ¿Importación CSV en lote? → A: Se mantiene como acción secundaria en la lista; reglas RF-CAM-002 sin cambio.
- Q: ¿Layout del workpanel? → A: **N/A** — workpanel descartado para este módulo.

### Session 2026-07-30 (remediación humo + clarify)

- Q: ¿Crear unidad en workpanel split o en página aparte? → A: **Página aparte** (y luego unificado con editar).
- Q: ¿Correo/credenciales tras alta con gmail? → A: **Sí — SMTP Gmail obligatorio**; UI confirma envío o error + reenviar; nunca password en UI/consola.
- Q: ¿Ver/Editar en workpanel o página completa? → A: **Supersedido** por decisión de navegación en dos páginas (abajo).
- Q: ¿Si falla SMTP con gmail en alta individual? → A: **Crear + error SMTP** + CTA **Reenviar invitación** (no rollback). Lote O56 sigue todo-o-nada.
- Q: ¿gmail obligatorio u opcional en alta individual? → A: **Obligatorio** (login/CU-O30 / operación posterior).

### Session 2026-07-30 (navegación páginas)

- Q: ¿Workpanel híbrido (Ver/Editar panel + Crear página) o páginas full? → A: **Dos tipos de página full**: (1) **lectura** solo Detalles; (2) **formulario** compartido para **Crear y Editar**. Sin workpanel split. Lista siempre completa al volver.

### Session 2026-07-30 (catálogo: performance + paginación + filtros)

- Q: ¿El catálogo puede cargar toda la flota de una vez sin paginar? → A: **No**. Toda tabla/lectura de flota debe ser **paginada** (tamaño de página por defecto **20**; el usuario puede pedir la siguiente página de resultados).
- Q: ¿Qué filtros son necesarios en el catálogo? → A: Al menos: **texto** (placa y/o nombre de unidad), **estado** (Activa / Baja / Todas), **tipo de unidad**. Los filtros se aplican al conjunto de la flota propia; cambiar filtro reinicia a la primera página.
- Q: ¿Qué tiempo máximo es aceptable al abrir o pulsar «Actualizar»? → A: El Proveedor debe ver el resultado del catálogo (filas, vacío o error) en **menos de 2 segundos** en el percentil 95 de usos normales de flota. Si se supera un tope de espera razonable, se muestra **error + Reintentar** — **nunca** skeleton infinito.
- Q: ¿La lentitud observada (espera larga con respuesta pequeña) implica qué? → A: El problema de producto es **tiempo hasta ver resultados**, no el tamaño de la pantalla; el listado debe acotarse (página + filtros) y cumplir el umbral de SC de performance.

## User Scenarios & Testing *(mandatory)*

### US-FE-1 — Explorar flota y ver detalle (Priority: P1)

El Proveedor abre el catálogo (primera página de resultados, con filtros disponibles) y con el **ojo** navega a la **página de Detalles** (solo lectura, sin Guardar).

**Independent Test**: Ojo → ruta de detalle; título Detalles; campos no editables; sin botón Guardar. Catálogo muestra como máximo una página de filas (no el universo completo de golpe).

**Acceptance Scenarios**:

1. **Given** flota con al menos una unidad, **When** pulsa «Ver detalles», **Then** abre la página de lectura «Detalles» sin «Guardar cambios».
2. **Given** Detalles, **When** intenta editar un campo, **Then** no puede (solo lectura).
3. **Given** flota con más unidades que el tamaño de página, **When** abre el catálogo, **Then** ve solo la primera página y puede avanzar a la siguiente.

### US-FE-2 — Crear unidad (Priority: P1)

El Proveedor pulsa **Nueva unidad**, abre la **página de formulario** en modo crear (gmail obligatorio), guarda; la unidad aparece en su flota; SMTP envía credenciales o error + reenviar.

**Independent Test**: CTA → ruta formulario crear; gmail required; éxito → lista propia; SMTP feedback.

**Acceptance Scenarios**:

1. **Given** catálogo, **When** pulsa «Nueva unidad», **Then** navega al formulario vacío de alta.
2. **Given** datos válidos con gmail, **When** guarda, **Then** confirmación y la unidad aparece en su lista (tras volver/actualizar).
3. **Given** placa/correo duplicados, **When** guarda, **Then** error sin perder el form.
4. **Given** sin gmail, **When** intenta guardar, **Then** validación bloquea el envío.
5. **Given** SMTP OK / fail, **When** guarda, **Then** ve envío OK o error + Reenviar (unidad creada si SMTP fail).

### US-FE-3 — Editar unidad (Priority: P1)

El Proveedor pulsa el **lápiz** y abre la **misma página de formulario** en modo editar (campos poblados, Guardar cambios). Confirma si despacho activo lo exige (RF-CAM-003).

**Independent Test**: Lápiz → mismo componente de formulario que crear, modo edit; Guardar cambios; idcliente no editable.

**Acceptance Scenarios**:

1. **Given** unidad propia, **When** pulsa Editar, **Then** ve el formulario de edición (misma página/componente que alta).
2. **Given** conflicto despacho activo, **When** guarda cambio crítico, **Then** confirma explícitamente antes de aplicar.

### US-FE-4 — Baja / reactivación (Priority: P1)

Desde la lista, papelera / reactivar con Alert 2 pasos (no página de borrado).

### US-FE-5 — Importación en lote (Priority: P2)

CSV secundario en lista; SMTP por fila según backend.

### US-FE-6 — Orientación al volver (Priority: P2)

Al volver desde Detalles o Formulario, la última unidad queda marcada en la lista (si está en la página/filtro actual; si no, el usuario puede localizarla con filtros).

### US-FE-7 — Filtrar y paginar el catálogo (Priority: P1)

El Proveedor reduce la flota visible con filtros y navega páginas de resultados sin esperar a cargar “todo”.

**Independent Test**: Aplicar filtro por placa/estado/tipo; cambiar de página; Actualizar respeta filtros y página (o vuelve a página 1 si se redefine el filtro).

**Acceptance Scenarios**:

1. **Given** flota mixta, **When** filtra por estado Baja, **Then** solo ve unidades en baja (paginadas).
2. **Given** filtro por texto de placa, **When** busca un fragmento único, **Then** encuentra esa unidad en los resultados.
3. **Given** resultados en varias páginas, **When** pide la siguiente página, **Then** ve el siguiente conjunto sin perder el contexto de filtros.
4. **Given** filtros que no coinciden con ninguna unidad, **When** consulta, **Then** ve estado vacío claro (no error genérico).

## Functional Requirements (UI)

### Catálogo (lista)

- **FR-UI-001**: ID/placa como texto plano; abrir solo vía acciones.
- **FR-UI-002**: Acciones ≥44×44: **ojo** → página Detalles; **lápiz** → página Formulario (editar).
- **FR-UI-003**: «Nueva unidad» → página Formulario (crear).
- **FR-UI-004**: Solo flota del Proveedor; estados loading / vacío / error+Reintentar; unidades que no pertenecen a la flota propia no cuentan como éxito de alta.
- **FR-UI-005**: Marca de orientación de la última unidad visitada al volver de Detalles o Formulario (cuando esa fila está visible en la página/filtro actual).
- **FR-UI-022**: El catálogo **MUST** mostrar resultados **paginados** (tamaño de página por defecto **20**). El Proveedor puede navegar a la página siguiente/anterior (o equivalente “más resultados”). No se presenta la flota completa como una sola tabla sin paginar.
- **FR-UI-023**: El catálogo **MUST** ofrecer filtros de búsqueda: **texto** (placa y/o nombre), **estado** (Activa / Baja / Todas), **tipo de unidad**. Cambiar filtros reinicia a la primera página.
- **FR-UI-024**: «Actualizar» (y la carga inicial) aplican la misma paginación y filtros activos. Tras un tiempo de espera razonable sin resultado, se muestra error + Reintentar; **prohibido** dejar la lista en carga indefinida (skeleton infinito).
- **FR-UI-025**: El tiempo hasta mostrar resultado del catálogo (filas, vacío o error) **MUST** cumplir el umbral de **SC-007** en usos normales.

### Página Detalles (solo lectura)

- **FR-UI-006**: Ruta dedicada de **lectura**. Título «Detalles»; campos disabled; **sin** Guardar.
- **FR-UI-007**: Volver al catálogo; opcional CTA «Editar» que navega al formulario.

### Página Formulario (crear / editar)

- **FR-UI-008**: **Un mismo componente/página** cubre crear y editar. Mismos grupos/orden de campos.
- **FR-UI-009**: Crear: form vacío; **gmail obligatorio**; «Guardar»; sin gmail no envía alta.
- **FR-UI-010**: Editar: form poblado; campos según RF-CAM-003; placa readonly si no es modificable; «Guardar cambios»; foco al primer editable; dueño de flota no editable; condado por catálogo.
- **FR-UI-011**: Feedback éxito/error de conflicto (p. ej. placa/correo ya usados) sin jerga (RNF-CAM-001).
- **FR-UI-012**: Confirmación despacho activo en edición crítica (RF-CAM-003).
- **FR-UI-017**: Alta con gmail: SMTP OK → confirmación envío; SMTP fail → unidad creada + error + Reenviar (sin password en UI).
- **FR-UI-018**: Reenviar invitación para unidad propia con login/envío fallido.
- **FR-UI-019**: Post-alta: volver/actualizar catálogo de forma que la unidad nueva sea localizable (filtros/página); no skeleton infinito.
- **FR-UI-020**: gmail **requerido** en alta individual.
- **FR-UI-021**: **Sin workpanel split** en este módulo.

### Baja, lote y límites

- **FR-UI-013**: Baja/reactivación: Alert 2 pasos desde la lista.
- **FR-UI-014**: Lote CSV en lista (secundario); no sustituye la paginación del catálogo.
- **FR-UI-015**: Sin UI CU-O59.
- **FR-UI-016**: Solo Proveedor + cliente habilitado (guard).

## Success Criteria

- **SC-001**: En menos de 2 minutos de uso guiado, el Proveedor abre Detalles en página de lectura sin Guardar.
- **SC-002**: Alta desde «Nueva unidad» en página formulario; unidad en flota propia; sin modal ni panel split que comprima la lista.
- **SC-003**: 100 % de aperturas de detalle/edición desde iconos de acción (no desde el ID como enlace).
- **SC-004**: Marca de orientación al volver visible en ≥95 % de pruebas de humo cuando la fila está en la página actual.
- **SC-005**: Baja sin confirmación en 2 pasos no se completa.
- **SC-006**: SMTP OK → correo recibido; SMTP fail → error + reenviar; unidad permanece en flota.
- **SC-007**: En el **95 %** de aperturas o pulsaciones de «Actualizar» del catálogo (flota de tamaño operativo habitual), el Proveedor ve filas, vacío o error en **menos de 2 segundos**.
- **SC-008**: Con más de 20 unidades que cumplan el filtro, el catálogo **nunca** muestra más de una página de filas a la vez; el usuario puede obtener el resto solo cambiando de página.
- **SC-009**: Un filtro por estado o por texto de placa reduce correctamente el conjunto visible (verificable por conteo/manual en humo).

## Key Entities (UI)

- Fila de lista (página de resultados); criterios de filtro; ficha **Detalles** (read); formulario **Crear/Editar**; lote; resultado invitación SMTP.

## Assumptions

- Autoridad de navegación: **lista + 2 páginas full** (lectura vs formulario). Design-system workpanel **no** aplica a este módulo tras clarify.
- SMTP con gmail es requisito de producto; entorno sin SMTP no valida SC-006.
- Unidades que no quedan asociadas al cliente del Proveedor son fallo de persistencia de la capa backend.
- El listado paginado/filtrado requiere que la capa backend exponga un listado acotado de la flota propia; el FE no inventa un contrato paralelo.
- “Tamaño operativo habitual” para SC-007: flotas del orden de decenas a cientos de unidades por proveedor (no big-data analítico).
- Alcance de “toda tabla paginada” en este módulo: **catálogo de flota** (la única tabla operativa principal). Detalle y formulario no son tablas de listado.

## Out of Scope

- Redefinir reglas de negocio RF-CAM en el frontend.
- CU-O30 disponibilidad en sitio; override Admin; rediseñar otros módulos.
- Mostrar password temporal en UI/consola.
- Workpanel split para este módulo.
- Dashboards analíticos o exportación masiva fuera del CSV de lote ya definido.

## Edge Cases

- Lista vacía + CTA Nueva unidad.  
- Carga lenta / timeout + Reintentar (sin skeleton infinito).  
- Alta sin gmail bloqueada.  
- SMTP fail + reenviar.  
- Reactivación con placa en conflicto.  
- Proveedor sin cliente Activo → acceso denegado.  
- Filtros sin coincidencias → vacío explícito.  
- Volver a catálogo con `lastId` fuera de la página/filtro actual → marca no visible hasta localizar la unidad.  
- Flota &gt; tamaño de página → obligatorio usar paginación.

## ISO/IEC 25010:2023 — Justificación

| Characteristic | Treatment |
|---|---|
| Interaction Capability | Lista + páginas lectura/formulario; filtros y paginación reducen carga cognitiva |
| Functional Suitability | RF-CAM + gmail/SMTP + ownership + catálogo operable a escala |
| Security | Solo flota propia; secretos fuera de UI |
| Maintainability | Un form crear/editar; una página read; listado acotado |
| Reliability | Loading con tope; SMTP fail visible; Reintentar |
| Safety | Catálogo correcto → despacho (indirecta) |
| **Performance Efficiency** | **Aplica** — SC-007 (&lt;2 s p95 al ver catálogo); listado paginado (SC-008) |
| Compatibility | Listados alineados a convención de paginación del proyecto (vía Depends-on backend) |
| Flexibility | N/A (sin multi-ciudad en este delta) |

**Traceability**: [`../alta-unidades.md`](../alta-unidades.md).

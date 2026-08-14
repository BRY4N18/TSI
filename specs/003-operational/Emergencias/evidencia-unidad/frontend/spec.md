# Feature Specification: Evidencia en Sitio — Frontend

**Feature Branch / capa**: `evidencia-unidad/frontend`
**Created**: 2026-07-30
**Status**: Active (Fase B — Interaction extraída; implementación Angular en código)
**Depends-on**: [`../backend/spec.md`](../backend/spec.md) (RF-EVI-*, RNF-EVI-*, CA-EVI-*, OpenAPI). Esta capa **MUST NOT** redefinir reglas de negocio, estados ni contratos REST.

**Input**: Clarificaciones UI extraídas del backend: captura/enriquecimiento exclusivos Técnico+Unidad; offline mismo patrón CU-O77; `Dim_Implicado` solo ontología; `mode=view` desde registro-accidente.

## Clarifications

### Session 2026-07-09 (UI — extraído backend)

- Q: ¿Evidencia offline visible para otros antes de sync? → A: **Solo en dispositivo capturador** — badge «Pendiente» local; otros usuarios solo ven sincronizados (RF-EVI-005).
- Q: ¿Roles galería? → A: Técnico + Unidad + Administrador — guards en rutas galería/enriquecimiento (RN-EVI-012).

### Session 2026-07-28/29 (UI — extraído backend)

- Q: ¿Enriquecimiento estructurado offline? → A: **Sí** — colas IndexedDB + sync batch CU-O77 (RNF-EVI-001).
- Q: ¿Operador precarga clima en registro? → A: **No** — enriquecimiento solo en este módulo; Operador entra `?mode=view` desde registro-accidente.
- Q: ¿Campos `Dim_Implicado`? → A: UI solo `tipoimplicado`, `estadoimplicado`, `genero?`, `edad?` — sin PII identidad (RF-EVI-010).

## User Scenarios & Testing

### US-FE-1 — Galería y captura en sitio (P1)

Técnico abre galería del caso, captura fotos/notas (modal), ve indicador sincronizado/pendiente; offline guarda local y auto-sync al reconectar.

**Independent Test**: `/evidencia-unidad/accidentes/:id/galeria` — merge local+servidor en capturador; otro rol solo servidor.

### US-FE-2 — Enriquecimiento estructurado (P1)

Técnico completa clima, elementos físicos, conductores/vehículos e implicados en paneles separados; soft-delete con confirmación.

**Independent Test**: `/evidencia-unidad/accidentes/:id/enriquecimiento` — 4 checkboxes estado conductor; lista registrada; tope `numvehiculos`.

### US-FE-3 — Disponibilidad unidad (P1)

Unidad declara Activa/Ocupada/Fuera de servicio; «En Misión» no selectable (422 backend).

**Independent Test**: `/evidencia-unidad/disponibilidad` — botones estado; historial visible.

### US-FE-4 — Consulta solo lectura Operador (P2)

Desde detalle accidente, Operador abre galería/enriquecimiento con `?mode=view` — sin formularios de escritura.

**Independent Test**: Query `mode=view` deshabilita CTAs guardar/alta (integración registro-accidente FR-UI-005/006).

## Functional Requirements (UI)

- **FR-UI-001**: Panel disponibilidad: selector manual Activa / Ocupada / Fuera de servicio; **ocultar/deshabilitar En Misión** — RF-EVI-001.
- **FR-UI-002**: Mostrar estado actual e historial reciente de la unidad autenticada — RF-EVI-004 (rol Unidad).
- **FR-UI-003**: Ruta `/flota` (Administrador): vista flota reutilizando panel con guard `administrador-flota` — RF-EVI-004.
- **FR-UI-004**: Galería: grid/lista fotos+notas ordenadas por `fechahora` desc; filtro por tipo nota — RF-EVI-005.
- **FR-UI-005**: Badge visual sincronizado vs pendiente (`sincronizado`); pendientes solo en dispositivo capturador — RN-EVI-013.
- **FR-UI-006**: Modal captura foto/nota desde galería; compresión cliente antes de subir — RNF-EVI-002.
- **FR-UI-007**: Offline store IndexedDB + indicador «Sin conexión»; auto-sync vía `evidencia-sync-scheduler` al reconectar — RNF-EVI-001/004.
- **FR-UI-008**: Sync parcial: exitosos persisten; fallidos reintentan; UI muestra conteo pendientes — RF-EVI-006, RN-EVI-014.
- **FR-UI-009**: Enriquecimiento — panel Clima: selects catálogo período/clima; upsert único activo — RF-EVI-007, RN-EVI-017.
- **FR-UI-010**: Enriquecimiento — panel Elementos físicos: multi-select catálogo + lista activos + soft-delete confirmado — RF-EVI-008.
- **FR-UI-011**: Enriquecimiento — paneles separados Conductor vs Vehículo; 4 checkboxes (Sobrio, Atento, Ileso, Con seguridad) → `idestadoconductor` — RF-EVI-009.
- **FR-UI-012**: Lista conductores/vehículos registrados con columnas legibles; soft-delete con confirmación — RF-EVI-009.
- **FR-UI-013**: Panel Implicados: form ontología (`tipoimplicado`, `estadoimplicado`, `genero?`, `edad?`); **sin** campos identidad — RF-EVI-010, CA-EVI-015.
- **FR-UI-014**: PII conductor offline cifrada (Web Crypto); bloqueo guardado local si falla cifrado — RNF-EVI-009, RN-EVI-020.
- **FR-UI-015**: Tras sync OK conductor: eliminar borrador local PII — RN-EVI-021.
- **FR-UI-016**: `?mode=view`: deshabilitar altas/edición/borrado; solo consulta — integración registro-accidente.
- **FR-UI-017**: ≤4 acciones primarias visibles por pantalla enriquecimiento; controles ≥44×44 px; validación inline — RNF-EVI-010.
- **FR-UI-018**: Guards `evidencia-gallery`, `unidad-emergencia-disponibilidad`, `administrador-flota` en rutas lazy — RN-EVI-012/015/016.
- **FR-UI-019**: Flujo navegación Técnico: Lista accidentes → Detalle → «Ver galería» / «Completar en sitio» — `nav-links.ts` + `accidentesLecturaGuard`.
- **FR-UI-020**: **Flujo de navegación de la Unidad, distinto del Técnico.** La unidad **no**
  puede abrir el detalle del accidente (`accidentesLecturaGuard` admite solo Operador,
  Técnico y Administrador), así que su acceso a la galería va por *Mi seguimiento* → enlace
  **«Evidencia del caso»** del despacho en curso. Que el rol tenga permiso sobre la galería
  no basta: sin ese enlace la pantalla solo era alcanzable escribiendo la URL, y la unidad
  —el actor que el SRS §3.6.3 pone en el sitio— no podía adjuntar nada.
- **FR-UI-021**: El enlace de vuelta de la galería **depende del rol**: Operador/Técnico/
  Administrador vuelven al detalle del accidente; la Unidad vuelve a *Mi seguimiento*.
  Mandar a todos al detalle dejaba a la unidad en «Acceso denegado», sin vuelta atrás.

## Out of Scope

- Cambiar OpenAPI, Blob/Kafka, algoritmo despacho, registro inicial accidente (CU-O56).
- PII en `Dim_Implicado`; precarga clima desde Operador en registro.

## ISO/IEC 25010:2023 — Justificación

| Characteristic | Treatment |
|---|---|
| Interaction Capability | Núcleo — captura offline, enriquecimiento paneles, galería |
| Functional Suitability | FR-UI citan RF-EVI-005…010, RNF-EVI-001/009/010 |
| Security | Cifrado PII offline + RBAC guards |
| Usability | RNF-EVI-010 design-system campo |
| Maintainability | Capa FE separada |
| Reliability / Performance | RNF-EVI-004 sync ≤30s — heredado |
| Compatibility / Flexibility / Safety | N/A o heredadas |

**Traceability**: Índice módulo [`../evidencia-unidad.md`](../evidencia-unidad.md).

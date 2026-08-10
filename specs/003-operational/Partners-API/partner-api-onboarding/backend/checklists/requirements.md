# Specification Quality Checklist: Onboarding de Partners API

**Purpose**: Validate specification completeness and quality before proceeding to planning  
**Created**: 2026-08-08  
**Feature**: [spec.md](../spec.md)  
**CUs**: CU-O48, CU-O49, CU-O50

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

> **Nota sobre "no implementation details".** La spec nombra tablas Pinot (`Dim_Partner`, `Dim_CredencialAPI`, `Fact_HistorialAccesoPartner`) y códigos HTTP. Es deliberado y consistente con la casa: `registro-accidente/backend/spec.md` hace lo mismo. La capa `backend/` es, por definición del [índice del módulo](../../partner-api-onboarding.md), la autoridad de dominio, API y modelo de datos. No hay fuga de framework, lenguaje ni estructura de código.

## Requirement Completeness

- [x] **No [NEEDS CLARIFICATION] markers remain** — resuelto 2026-08-08: `Dim_VersionContratoAPI` con FK obligatoria a `Dim_Servicio` (§ 15 D1).
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic
- [x] All acceptance scenarios are defined — 10 escenarios (§ 10), 14 criterios de aceptación (§ 11)
- [x] Edge cases are identified — segundo partner (E2), sin suscripción (E3), sin plan (E4), vencimiento (E6), rechazo sin motivo (E8), atajo a producción (E9)
- [x] Scope is clearly bounded — § 13 reparte propiedad de escritura frente a los otros dos módulos del departamento
- [x] Dependencies and assumptions identified — § 12 y § 14

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Constitution Compliance (Golden Rule)

- [x] Las 9 características ISO/IEC 25010:2023 declaradas explícitamente — § 5.1
- [x] Las no aplicables justifican por qué — **Safety: no aplica**, con razón (fuera de la cadena crítica de despacho)
- [x] Al menos un criterio de aceptación medible por sub-característica — CA-PON-005 (Security/Confidencialidad), CA-PON-014 (Performance/Comportamiento temporal), CA-PON-011 (Security/Responsabilidad), CA-PON-013 (Compatibility/Interoperabilidad)
- [x] Tie-Breaker Mechanism invocado y documentado — Security > Interaction Capability en RN-PON-005, con trade-off explícito
- [x] Trazabilidad obligatoria a CU documentado — CU-O48/O49/O50 del catálogo canónico

## Trazabilidad al catálogo canónico

| RF del catálogo | Cubierto por | Estado |
|---|---|---|
| RF-O48.1 | RF-PON-001 | ✅ |
| RF-O48.2 | RF-PON-002, RN-PON-002 | ✅ |
| RF-O48.3 | RF-PON-003, RN-PON-003 | ✅ |
| RF-O48.4 | RF-PON-001 punto 2, RN-PON-011 | ✅ |
| RF-O49.1 | RF-PON-004, RF-PON-005 | ✅ |
| RF-O49.2 | RF-PON-004 punto 3, RN-PON-005 | ✅ |
| RF-O49.3 | RF-PON-005 punto 3 | ✅ |
| RF-O49.4 | RF-PON-006, RN-PON-006 | ✅ |
| RF-O50.1 | RF-PON-011 punto 1, § 15 D1 | ✅ |
| RF-O50.2 | RF-PON-011 punto 2, § 15 D1 | ✅ |
| RF-O50.3 | RF-PON-011 puntos 3 y 6, RN-PON-012 | ✅ |

## Cobertura del SRS §3.4.1

Los 11 párrafos normativos del SRS L362–L388 están cubiertos: L368 → RF-PON-001 · L370 → RN-PON-002 · L372 → RF-PON-005 · L374 → RF-PON-001 (cierre) · L376 → RF-PON-003 · L378 → RF-PON-004, RNF-PON-001 · L380 → RF-PON-006 · L382 → RF-PON-008 · L384 → RN-PON-007 · L386 → RN-PON-004 · L388 → RF-PON-009, RN-PON-008.

## Dependencias externas que este módulo abre

| Cambio | Archivo | Bloquea | Estado |
|---|---|---|---|
| Centinelas `defaultNullValue` en `Dim_Partner`, `Dim_CredencialAPI`, `Fact_HistorialAccesoPartner` (§ 15 D2) | `database/esquemas.json` | RF-PON-004, RF-PON-008, CU-O54 | ✅ **aplicado y verificado** |
| `timeColumnName` + `comparisonColumn` → `fecha_actualizacion` en las dos dimensiones mutables | `database/tablas.json` | gestión de segmentos | ✅ **aplicado y verificado** |
| Tabla nueva `Dim_VersionContratoAPI` (con FK `id_servicio`) + topic Kafka | `database/esquemas.json`, `database/tablas.json` | CU-O50 | ✅ **aplicado y verificado** |
| `nombre_credencial` (STRING) en `Dim_CredencialAPI` | `database/esquemas.json` | RF-PON-005 | ✅ **aplicado y verificado** |
| `fecha_expiracion` (LONG, centinela año 9999) en `Dim_CredencialAPI` | `database/esquemas.json` | RF-PON-006, RF-PON-008 | ✅ **aplicado y verificado** |
| `tipo` (STRING, default `suscripcion`) en `Fact_Factura` | `database/esquemas.json` | CU-O54 (módulo #08) | ✅ **aplicado y verificado** |
| `Fact_Reclamo.idfactura` INT → STRING + código y tests de Soporte | `database/esquemas.json`, `backend/apps/soporte_cliente/`, OpenAPI de Soporte | CU-O83 / RF-O83.2 | ✅ **aplicado y verificado** (8 tickets migrados sin pérdida) |
| `api_calls_minuto` en el JSON `Dim_Plan.limites` (RN-SUSF-019) | `database/esquemas.json` (JSON), `backend/apps/suscripciones/`, `frontend/src/app/modules/suscripciones/` | RF-PON-003 | ✅ **aplicado y verificado** — validado en backend, editable por el Director de Estrategia en el formulario de plan, 5 planes sembrados |
| Rol `PartnerIntegracion` (idrol 15) en `Dim_Rol` | `backend/scripts/_demo_seed_common.py`, `autenticacion-y-rbac/backend/spec.md`, `.specify/docs/actors.md` | RF-PON-004 | ✅ **creado y verificado** (+ corregida la descripción de `DesarrolladorAPIs`) |
| Renumeración CU-O48–O55 y decisiones de esquema | `decisiones-pendientes.md` #15, #16 | — | ✅ registrado |
| Renumeración en §4 e índice rápido | `.specify/docs/architecture/module-map.md` | — | ✅ aplicado |

### Verificación de los cambios ya aplicados (2026-08-08)

| Comprobación | Resultado |
|---|---|
| `database/verifica_partners.py` | **16/16 correctas** |
| `database/verifica_factura_reclamo.py` | **15/15 correctas** |
| Suite completa del backend | **1042 pasan, 2 saltados** (los mismos de antes) |
| `test_doble_pinot_vs_esquemas.py` | 3 pasan |
| Consistencia `tablas.json` ↔ Pinot | 79 declaradas = 79 desplegadas |
| Las 4 tablas del departamento | 0 filas (topics Kafka purgados) |
| Datos de otros departamentos | intactos: `Fact_Reclamo` 8, `Fact_Historial_Ticket` 9 |

Scripts reutilizables creados en `database/`: `migra_partners_esquema.py`, `despliega_partners.py`, `verifica_partners.py`, `migra_factura_reclamo.py`, `verifica_factura_reclamo.py`.

> **Los tests del backend no habrían detectado ninguno de estos defectos.** Corren contra el doble en memoria de `conftest.py`, que no reproduce los tipos del esquema ni los centinelas de Pinot: pasaban en verde con `idfactura` INT y con STRING por igual. De ahí los verificadores contra Pinot real.

## Notes

- **Nada bloquea `/speckit-plan`.** La spec está completa y sin marcadores abiertos.
- **D2 está resuelto**, no pendiente. La primera redacción atribuía el fallo al `comparisonColumn` del upsert; esa hipótesis se **refutó empíricamente** (Pinot compara con `>=`) y la spec lleva la rectificación explícita. El problema real era la ausencia de `NULL` en Pinot, ya corregida con centinelas explícitos.
- **No queda ninguna dependencia externa abierta.** Las 9 filas de la tabla anterior están aplicadas y verificadas. `Fact_Factura.tipo` y `Fact_Reclamo.idfactura` se migraron con exportación previa porque tocaban tablas con datos reales (`Fact_Reclamo_topic` estaba purgado, así que Pinot era la única copia de los 8 tickets). El rol `PartnerIntegracion` y `api_calls_minuto` se resolvieron el mismo día.
- **`api_calls_minuto` se implementó como parámetro configurable, no como constante.** Lo edita el Director de Estrategia en el formulario de plan (CU-O26 / RF-O26.1), conforme a RNF-20. Los valores sembrados (30/120/600 por nivel) son iniciales y reconfigurables.
- ⚠️ `database/` está en `.gitignore`: los cambios de esquema **no se versionan**. Respaldar a mano antes de tocarlos.

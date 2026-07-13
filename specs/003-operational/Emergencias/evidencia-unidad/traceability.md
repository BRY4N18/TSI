# Trazabilidad — Evidencia en Sitio y Disponibilidad de Unidad

**Feature**: `specs/003-operational/Emergencias/evidencia-unidad/`  
**Fecha validación**: 2026-07-09

## Matriz CU / RF / CA → Tasks

| ID | Descripción | Tasks | Estado |
|----|-------------|-------|--------|
| CU-O27 | Adjuntar evidencias en sitio | T040–T057 | ✓ |
| CU-O30 | Gestionar disponibilidad de unidad | T025–T039 | ✓ |
| CU-O43 | Sincronización diferida offline | T059–T069 | ✓ |
| RF-EVI-001 | Declarar estado disponibilidad | T031, T033, T034–T038 | ✓ |
| RF-EVI-002 | Subir evidencia fotográfica | T046, T049, T050, T057 | ✓ |
| RF-EVI-003 | Registrar nota de campo | T047, T049, T050, T057 | ✓ |
| RF-EVI-004 | Consultar disponibilidad/flota | T032, T033, T034, T038 | ✓ |
| RF-EVI-005 | Galería evidencias sincronizadas | T048, T049, T056 | ✓ |
| RF-EVI-006 | Sync diferida batch parcial | T062–T068 | ✓ |
| CA-EVI-001 | Unidad declara Ocupada | T025, T029, T031, T039 | ✓ |
| CA-EVI-002 | Default Fuera de servicio sin historial | T029, T031, T039 | ✓ |
| CA-EVI-003 | Subida foto en línea | T041, T043, T046, T058 | ✓ |
| CA-EVI-004 | Sync parcial con reintento | T059–T060, T062–T066, T069 | ✓ |
| CA-EVI-005 | Nota de campo registrada | T042, T044, T047, T058 | ✓ |
| CA-EVI-006 | Evidencia offline solo en capturador | T061, T064–T065, T069 | ✓ |
| CA-EVI-007 | Galería RBAC | T040, T045, T048, T052, T058 | ✓ |
| CA-EVI-008 | Caso inactivo rechaza captura | T043–T046, T058 | ✓ |
| CA-EVI-009 | Historial estado trazable | T028, T031, T039 | ✓ |
| RN-EVI-012 | Roles galería | T020, T052, T071 | ✓ |
| RN-EVI-015 | RBAC consulta disponibilidad | T022, T036, T054, T071 | ✓ |

## Validación quickstart (escenarios A–I)

| Escenario | Descripción | Validación | Resultado |
|-----------|-------------|------------|-----------|
| A | Subida foto en línea | `test_subir_foto_contract.py`, `test_evidencia_foto_service.py` | ✓ 79 tests backend PASS |
| B | Nota de campo | `test_registrar_nota_contract.py`, `test_nota_campo_service.py` | ✓ |
| C | Galería RBAC | `test_listar_evidencias_contract.py`, `test_evidencia_permissions.py` | ✓ |
| D | Cambio disponibilidad unidad | `test_declarar_mi_disponibilidad_contract.py`, `test_disponibilidad_unidad_service.py` | ✓ |
| E | Estado default sin historial | `test_disponibilidad_unidad_service.py::test_consultar_when_no_historial` | ✓ |
| F | RBAC disponibilidad | `test_listar_unidades_contract.py`, `test_disponibilidad_permissions.py` | ✓ |
| G | Sync diferida parcial | `test_sincronizar_evidencia_contract.py`, `test_sincronizar_evidencia_service.py` | ✓ |
| H | Caso inactivo | `test_evidencia_foto_service.py`, `test_subir_foto_contract.py` | ✓ |
| I | Integración disponibilidad→despacho | `test_disponibilidad_despacho_integration.py` | ✓ |

## Cobertura backend (T077)

Ejecutado: `pytest apps/accidentes/tests/ apps/despacho/tests/ --cov=...`

| Capa | Umbral | Resultado |
|------|--------|-----------|
| Servicios evidencia/disponibilidad | ≥80% | 86–95% |
| Repositorios evidencia/despacho | ≥85% | 90–96% |
| Total módulo | — | 88% |

## Frontend

| Artefacto | Ruta | Estado |
|-----------|------|--------|
| Types OpenAPI | `frontend/.../evidencia-unidad.types.ts` | ✓ |
| API services | `evidencia-api.service.ts`, `disponibilidad-unidad-api.service.ts` | ✓ |
| Offline store | `evidencia-offline-store.service.ts` | ✓ |
| Sync scheduler | `evidencia-sync-scheduler.service.ts` | ✓ |
| Guards + rutas lazy | `evidencia-unidad.routes.ts` | ✓ |
| Páginas | galería, captura, panel disponibilidad | ✓ |
| Build Angular | `ng build` | ✓ PASS |

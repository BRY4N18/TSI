# Matriz de Trazabilidad — Autenticación y RBAC

**Feature**: `specs/003-operational/Cuentas-Clientes/autenticacion-y-rbac/`  
**Última actualización**: 2026-07-09  
**Objetivo Operacional**: OP-TSI-SEG-01

---

## 1. Trazabilidad OE/OT/OP/CU → RF/RNF/CA

| OP/UC | RF/RNF | CA | Descripción | Tasks |
|-------|--------|-----|-------------|-------|
| OP-TSI-SEG-01 | RF-AUT-001, RF-AUT-002 | CA-AUT-001, CA-AUT-009 | Acceso seguro con JWT + validación de sesión | T026, T011, T029, T031-T033 |
| CU-O05 | RF-AUT-001 | CA-AUT-001, CA-AUT-002, CA-AUT-003, CA-AUT-010 | Iniciar sesión | T019, T022, T026, T065-T066, T073 |
| CU-O04 | RF-AUT-003 | CA-AUT-004 | Gestión de usuarios | T034, T036, T038, T041, T043, T045, T047 |
| CU-O13 | RF-AUT-004 | CA-AUT-005 | Gestión de roles de negocio | T035, T037, T039, T042, T044, T046 |
| CU-O15 | RF-AUT-005 | CA-AUT-006 | Acceso a infraestructura (servidor) | T048-T055 |
| CU-O06 | RF-AUT-006 | CA-AUT-003, CA-AUT-007 | Recuperar/restablecer contraseña | T056-T064 |
| CU-O07 | RF-AUT-007 | CA-AUT-008 | Revocar sesión activa | T021, T024, T028, T029 |
| — | RF-AUT-008 | CA-AUT-008 | Cierre de sesión voluntario | T020, T023, T027, T029 |
| — | RF-AUT-002 | CA-AUT-009 | Validación JWT + Fact_Session por request | T011, T012, T015, T032 |
| — | RNF-AUT-004 | CA-AUT-010 | SLO login p95 ≤ 500 ms, disponibilidad ≥ 99.5% | T065, T066, T073 |
| — | RNF-AUT-005 | — | Rate limiting diferido | T018 |

---

## 2. RF/RNF/CA → Task IDs

| ID | Requisito | Tasks de implementación | Tasks de validación |
|----|-----------|-------------------------|---------------------|
| RF-AUT-001 | Login con credenciales | T026, T029 | T019, T022, T069 |
| RF-AUT-002 | Validación token + sesión | T011, T015 | T012, T025, T032, T069 |
| RF-AUT-003 | Gestión usuarios | T041, T043, T045 | T034, T036, T038, T070 |
| RF-AUT-004 | Gestión roles negocio | T042, T044, T045 | T035, T037, T039, T070 |
| RF-AUT-005 | Acceso servidor CU-O15 | T052-T055 | T048-T051, T071 |
| RF-AUT-006 | Password reset | T060-T062 | T056-T059, T072 |
| RF-AUT-007 | Revocar sesión | T028, T029 | T021, T024, T069 |
| RF-AUT-008 | Logout | T027, T029 | T020, T023, T069 |
| RNF-AUT-004 | Performance login | T065 | T066, T073 |
| RNF-AUT-005 | Rate limiting (diferido) | T018 | — |

---

## 3. Criterios de Aceptación — Evidencia de Cumplimiento

| CA | Estado | Evidencia |
|----|--------|-----------|
| **CA-AUT-001** | ✓ PASS | `test_auth_service.py::test_login_when_valid_credentials_returns_tokens`; `test_auth_login_contract.py` — login 200 + tokens + Fact_Session vía Kafka |
| **CA-AUT-002** | ✓ PASS | `test_auth_service.py::test_login_when_inactive_user_raises_error` — HTTP 401 |
| **CA-AUT-003** | ✓ PASS | `auth_service.py` retorna `requiresPasswordChange=true`; `session.guard.ts` redirige a cambio obligado |
| **CA-AUT-004** | ✓ PASS | `test_user_management_service.py`; `user_repository.deactivate` publica `activo=false` |
| **CA-AUT-005** | ✓ PASS | `test_business_rbac_service.py`; `test_roles_contract.py` — CRUD roles + asignación |
| **CA-AUT-006** | ✓ PASS | `test_server_access_service.py`; `test_server_access_contract.py` — Admin/Director Tecnológico |
| **CA-AUT-007** | ✓ PASS | `test_password_reset_service.py`; `test_password_reset_contract.py` — estado `Cambio contraseña` |
| **CA-AUT-008** | ✓ PASS | `test_revoke_session_service.py`; `test_auth_revoke_contract.py` — estado `Expulsado` |
| **CA-AUT-009** | ✓ PASS | `test_session_validation_service.py` — rechaza sesiones `Cierre sesion`/`Expulsado`; `authentication.py` en cada request |
| **CA-AUT-010** | ✓ PASS | `test_login_p95.py` — p95 ≤ 500 ms (20 muestras, mocks). Disponibilidad ≥ 99.5% documentada como objetivo operativo (ver `quickstart.md` §6) |

---

## 4. Gates por Historia de Usuario

| Gate | CAs validados | Estado |
|------|---------------|--------|
| T069 US1 | CA-AUT-001, CA-AUT-008, CA-AUT-009 | ✓ PASS |
| T070 US2 | CA-AUT-004, CA-AUT-005 | ✓ PASS |
| T071 US3 | CA-AUT-006 | ✓ PASS |
| T072 US4 | CA-AUT-003, CA-AUT-007 | ✓ PASS |
| T073 Polish | CA-AUT-010 | ✓ PASS |

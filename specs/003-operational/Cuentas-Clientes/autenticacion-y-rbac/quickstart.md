# Quickstart - Validacion de Autenticacion y RBAC

Esta guia valida de extremo a extremo el flujo contract-first backend+frontend para autenticacion y RBAC.

## Prerequisitos

- Contrato disponible en `contracts/auth-rbac.openapi.yaml`
- Spec y plan en la carpeta de feature
- Entorno con servicios de backend/frontend y Kafka/Pinot habilitados

## 1) Validar contrato REST (backend contract-first)

1. Revisar endpoints definidos:
   - `POST /api/v1/auth/login`
   - `POST /api/v1/auth/logout`
   - `POST /api/v1/auth/revoke-session`
   - `POST /api/v1/auth/password-reset`
2. Verificar convenciones de `api-standards.md`:
   - Versionado en path (`/api/v1`)
   - Envelope de exito (`data`, `meta`)
   - Envelope de error (`error`, `detail`, `code`)

Resultado esperado: contrato sin inconsistencias semanticas frente al spec.

## 2) Validar flujo backend (Django Vista->Servicio->Repositorio)

Escenarios minimos:

1. **Login exitoso**
   - Request: credenciales validas
   - Expected: HTTP 200 + `accessToken` + `refreshToken` + perfil en `data`
2. **Logout**
   - Request autenticada a `/auth/logout`
   - Expected: estado de sesion `Cierre sesion`
3. **Revocacion administrativa**
   - Admin ejecuta `/auth/revoke-session`
   - Expected: sesion en `Expulsado` y bloqueo inmediato
4. **Recuperacion de contraseña**
   - Request con correo registrado
   - Expected: estado `Cambio contraseña` y correo enviado

Validaciones transversales:
- Cada request protegida valida JWT y estado de sesion.
- Escrituras publican evento Kafka (no escritura directa a Pinot).

## 3) Validar consumo frontend (Angular)

Componentes a validar:

- `AuthApiService` consume endpoints del contrato.
- `AuthStateService` mantiene estado de sesión.
- `AuthInterceptor` agrega bearer token.
- `SessionGuard` bloquea no autenticados.
- `RoleGuard` restringe rutas por rol.

Escenarios UI:

1. Usuario sin token redirigido a login al entrar a ruta protegida.
2. Usuario autenticado sin rol requerido recibe 403 UI flow (pantalla/redirect de acceso denegado).
3. Usuario con rol valido accede a modulo.
4. Sesion revocada desde backend invalida navegacion protegida en siguiente request.

## 4) Pruebas sugeridas

- Backend:
  - Pruebas de contrato de endpoints y codigos HTTP.
  - Pruebas de servicio para reglas `activo`, `estadocredencial` y estados de sesion.
- Frontend:
  - Unit tests de guards e interceptor.
  - Integracion de login/logout con mocks del contrato OpenAPI.

## 5) Criterios de salida

- Contrato REST aprobado y alineado con spec.
- Flujo auth/rbac funcional para login, logout, revoke-session y password-reset.
- Validacion de sesion por request comprobada.
- Patrón Vista->Servicio->Repositorio y regla Kafka-only-write respetados.

## 6) Evidencia de performance (CA-AUT-010 / RNF-AUT-004)

**Fecha de ejecución**: 2026-07-09  
**Herramienta**: pytest (`test_login_p95.py`, marker `slow` + `api`)  
**Entorno**: mocks Pinot/Kafka (sin infra real)

| Métrica | Umbral | Resultado |
|---------|--------|-----------|
| Login p95 | ≤ 500 ms | **PASS** — 20 muestras, p95 dentro del umbral con mocks |
| Disponibilidad mensual | ≥ 99.5% | Objetivo operativo — requiere monitoreo en despliegue productivo |

```bash
cd backend
pytest apps/cuentas_clientes/tests/performance/test_login_p95.py -v -m slow
```

## 7) Validación E2E ejecutada (T068)

| Paso | Comando / acción | Resultado |
|------|------------------|-----------|
| Tests backend | `pytest -v` (62 tests) | **62 passed** |
| Contrato login | `test_auth_login_contract.py` | PASS |
| Contrato logout | `test_auth_logout_contract.py` | PASS |
| Contrato revoke | `test_auth_revoke_contract.py` | PASS |
| Contrato password-reset | `test_password_reset_contract.py` | PASS |
| US2 usuarios/roles | `test_users_contract.py`, `test_roles_contract.py` | PASS |
| US3 server access | `test_server_access_contract.py` | PASS |
| Performance login | `test_login_p95.py` | PASS |

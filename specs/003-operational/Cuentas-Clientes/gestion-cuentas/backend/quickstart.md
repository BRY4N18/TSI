# Quickstart - Validación de Gestión de Cuenta de Cliente

Guía de validación end-to-end contract-first para CU-O13 (perfil), CU-O14 (preferencias), CU-O15 (transferencia) y CU-O16 (baja). Numeración corregida 2026-08-08 al catálogo vigente; el CU-O03 histórico de este módulo (perfil+preferencias combinado) se dividió en CU-O13/CU-O14.

## Prerequisitos

- Contrato: `contracts/gestion-cuentas.openapi.yaml`
- Spec y plan en `specs/003-operational/Cuentas-Clientes/gestion-cuentas/backend/`
- Módulo **autenticacion-y-rbac** operativo (login JWT + validación de sesión)
- Cuenta de cliente creada vía **incorporacion-clientes** (onboarding completado)
- Variables SMTP configuradas para pruebas de notificación (opcional en dev; fallo debe loguearse sin revertir)

```bash
# Variables SMTP (backend/.env — ver backend/env.example)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...   # contraseña de aplicación Gmail
DEFAULT_FROM_EMAIL=Tráfico Seguro Integral <...>
```

## 1) Validar contrato REST (backend contract-first)

Revisar endpoints definidos:

| Método | Ruta | UC | Rol |
|--------|------|-----|-----|
| GET | `/api/v1/cuentas-clientes/{idcliente}/perfil` | CU-O13 | Cliente / Administrador |
| PATCH | `/api/v1/cuentas-clientes/{idcliente}/perfil` | CU-O13 | Cliente / Administrador |
| GET | `/api/v1/cuentas-clientes/{idcliente}/preferencias` | CU-O14 | Cliente |
| PATCH | `/api/v1/cuentas-clientes/{idcliente}/preferencias` | CU-O14 | Cliente |
| GET | `/api/v1/cuentas-clientes/{idcliente}/usuarios-elegibles` | CU-O15 | Cliente (admin local) |
| POST | `/api/v1/cuentas-clientes/{idcliente}/transferencia-propiedad` | CU-O15 | Cliente (admin local) |
| POST | `/api/v1/cuentas-clientes/{idcliente}/baja` | CU-O16 | Administrador |
| POST | `/api/v1/cuentas-clientes/{idcliente}/logo/upload-url` | CU-O13 | Cliente / Administrador |

Convenciones (`api-standards.md`):

- Envelope éxito: `{ "data": {...}, "meta": {} }`
- Envelope error: `{ "error", "detail", "code" }`
- Header `Idempotency-Key` en PATCH/POST de escritura

**Resultado esperado**: contrato alineado con spec y sin campos contradictorios.

## 2) Validar flujo backend (Vista → Servicio → Repositorio)

### Escenario A — Perfil y preferencias (CU-O13 / CU-O14)

1. Login como Cliente → obtener JWT.
2. `GET .../perfil` → 200 con `tipo` y `nit_identificacion` en respuesta.
3. `PATCH .../perfil` con `{ "razon_social": "...", "nombre": "..." }` → 200 + `campos_modificados`.
4. `PATCH .../preferencias` con `telefono_sms` y `umbrales_alerta` → 200.
5. Verificar eventos Kafka en `Dim_Cliente_topic` y `Dim_Preferencias_Cliente_topic` (no escritura directa Pinot).

### Escenario B — Logo (CU-O13)

1. `POST .../logo/upload-url` con `content_type: image/png` → `upload_url` + `logo_url`.
2. Subir binario a `upload_url` (PUT Azure Blob).
3. `PATCH .../perfil` con `{ "logo_url": "<logo_url del paso 1>" }` → 200.

### Escenario C — Transferencia inmediata (CU-O15)

1. Login como admin local actual.
2. `GET .../usuarios-elegibles` → lista con usuarios activos de la cuenta.
3. `POST .../transferencia-propiedad` con `Idempotency-Key` y `id_nuevo_responsable` → 200.
4. Verificar `Dim_Cliente_topic` con nuevo `admin_local_id`.
5. Verificar emails enviados a nuevo y anterior admin (o log si SMTP no configurado).

### Escenario D — Baja con expulsión de sesiones (CU-O16)

1. Login como Administrador.
2. `POST .../baja` con `{ "motivo": "Cierre contractual" }` → 200, `estado: Dado de baja`, `sesiones_expulsadas >= 1`.
3. Intentar request autenticada con usuario de la cuenta → 401/403 (sesión expulsada).
4. Verificar `Fact_Session_topic` con `estadosession: Expulsado`.
5. Verificar motivo solo en logs (no en `Dim_Cliente`).

### Validaciones transversales

- Cliente accediendo a `idcliente` ajeno → 403.
- Cliente no admin local en transferencia → 403.
- Operación en cuenta `Dado de baja` → 409.
- `tipo` / `nit_identificacion` en PATCH → ignorados o 400.

## 3) Validar consumo frontend (Angular)

### Servicios (`typescript-expert`)

- `models/cuenta-cliente.contract.ts` — tipos alineados al OpenAPI.
- `CuentaClienteApiService` — un método por `operationId`.
- `CuentaClienteFacadeService` — orquesta flujos UI (logo upload + patch perfil).

### Guards (`angular-architect`)

| Guard | Comportamiento esperado |
|-------|-------------------------|
| `CuentaScopeGuard` | Cliente solo accede a su `idcliente` en ruta |
| `AdminLocalGuard` | Bloquea `/transferencia` si no es `admin_local_id` |
| `CuentaActivaGuard` | Redirige si cuenta en `Dado de baja` |
| `AdministradorGuard` | Solo Administrador en ruta `/baja` |

### Escenarios UI

1. Cliente edita perfil y preferencias → toast éxito; campos readonly visibles pero no editables.
2. Admin local abre transferencia → selector poblado desde `usuarios-elegibles`.
3. Tras transferencia, usuario anterior pierde acciones de admin local en UI.
4. Administrador ejecuta baja → confirmación modal con motivo opcional.

## 4) Pruebas sugeridas

```bash
cd backend
pytest apps/cuentas_clientes/tests/api/test_cuenta_perfil_contract.py -v -m api
pytest apps/cuentas_clientes/tests/api/test_cuenta_preferencias_contract.py -v -m api
pytest apps/cuentas_clientes/tests/api/test_transferencia_propiedad_contract.py -v -m api
pytest apps/cuentas_clientes/tests/api/test_baja_cuenta_contract.py -v -m api
pytest apps/cuentas_clientes/tests/services/ -v -m service
```

```bash
cd frontend
npm test -- --include='**/gestion-cuenta/**/*.spec.ts'
```

## 5) Criterios de salida

- [X] Contrato OpenAPI aprobado y alineado con spec clarificada.
- [X] CU-O13/CU-O14: perfil, preferencias y logo operativos con auditoría en logs.
- [X] CU-O15: transferencia inmediata + notificación SMTP (o log de fallo).
- [X] CU-O16: baja lógica + expulsión masiva de sesiones + notificación.
- [X] Patrón Vista→Servicio→Repositorio y Kafka-only-write verificados.
- [X] Guards Angular restringen scope, admin local y rol Administrador.

## 6) Evidencia de performance (2026-07-09)

Ejecutado con mocks Pinot/Kafka (`pytest -m slow`):

| Endpoint / operación | Umbral p95 | Resultado |
|----------------------|------------|-----------|
| `GET /perfil` (servicio) | ≤ 300 ms | PASS |
| `POST /transferencia-propiedad` (servicio) | ≤ 500 ms | PASS |
| `POST /baja` (servicio) | ≤ 500 ms | PASS |

Suite backend: `pytest apps/cuentas_clientes/tests/ -v` — 94+ tests PASS.

Disponibilidad 99.9% (RNF-CTA-003): validación de infraestructura fuera de alcance de tests unitarios; arquitectura stateless + Kafka replay documentada en `plan.md`.

## 7) Validación E2E ejecutada

```bash
cd backend && python -m pytest apps/cuentas_clientes/tests/ -v --tb=short
```

Escenarios A–D del quickstart cubiertos por tests de contrato API y servicio con fixtures `cliente_auth_headers` / `auth_headers`.

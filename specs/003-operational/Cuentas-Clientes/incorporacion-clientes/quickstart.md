# Quickstart - Validación de Incorporación de Clientes

Guía de validación end-to-end contract-first para CU-O01, O12, O02, O09 y O08.

## Prerequisitos

- Contrato: `contracts/incorporacion-clientes.openapi.yaml`
- Spec y plan en `specs/003-operational/Cuentas-Clientes/incorporacion-clientes/`
- Módulo **autenticacion-y-rbac** operativo (login JWT + validación de sesión)
- Topic `Fact_Onboarding_topic` registrado en `backend/config/settings.py` → `KAFKA_TOPICS`
- Variables SMTP para O01/O08/recordatorios (opcional en dev; fallo debe loguearse sin revertir)

```bash
# Variables SMTP (backend/.env — ver backend/env.example)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...
DEFAULT_FROM_EMAIL=Tráfico Seguro Integral <...>
```

## 1) Validar contrato REST (backend contract-first)

| Método | Ruta | UC | Rol |
|--------|------|-----|-----|
| POST | `/api/v1/cuentas-clientes` | O01 | Administrador |
| PATCH | `/api/v1/cuentas-clientes/{idcliente}/configuracion` | O12 | Administrador |
| POST | `/api/v1/cuentas-clientes/{idcliente}/logo/upload-url` | O12 | Administrador |
| GET | `/api/v1/cuentas-clientes/{idcliente}/onboarding/progreso` | O09 | Cliente (admin local) / Admin |
| POST | `/api/v1/cuentas-clientes/{idcliente}/onboarding/etapas` | O02 | Cliente (admin local) / Admin |
| POST | `/api/v1/cuentas-clientes/{idcliente}/invitacion/reenviar` | O08 | Administrador / Cliente |

Convenciones (`api-standards.md`):

- Envelope éxito: `{ "data": {...}, "meta": {} }`
- Envelope error: `{ "error", "detail", "code" }`
- Header `Idempotency-Key` en POST/PATCH de escritura

**Resultado esperado**: contrato alineado con spec clarificada (sesión 2026-07-09).

## 2) Validar flujo backend (Vista → Servicio → Repositorio)

### Escenario A — Registro de cuenta (O01)

1. Login como **Administrador** → JWT.
2. `POST /api/v1/cuentas-clientes` con `Idempotency-Key` y cuerpo:

```json
{
  "razon_social": "Seguros Demo SA",
  "nombre": "Seguros Demo",
  "tipo": "Aseguradora",
  "nit_identificacion": "900123456-1",
  "fecha_inicio_contrato": 1720500000000,
  "admin_local": {
    "nombres": "Ana",
    "apellidos": "García",
    "gmail": "ana.garcia@demo.com"
  }
}
```

3. Esperar **201** con `idcliente`, `estado: Activo`, `admin_local_id`.
4. Verificar eventos Kafka: `Dim_Cliente_topic`, `Dim_Usuarios_topic`, `Dim_Credencial_topic`, `Dim_Usuario_Rol_topic`.
5. Verificar email de invitación (o log SMTP si no configurado).
6. Repetir mismo NIT → **409**.

### Escenario B — Configuración (O12)

1. Login como **Administrador**.
2. `POST .../logo/upload-url` → subir PNG a Azure Blob.
3. `PATCH .../configuracion` con `{ "plan_suscripcion": "Plan Básico", "logo_url": "..." }` → **200**, `estado_onboarding: Pendiente`.
4. Verificar `Dim_Cliente_topic` con `plan_suscripcion` y `estado_onboarding`.

### Escenario C — Onboarding con progreso (O02 + O09)

1. Login como **Cliente** (admin local creado en O01) con credencial temporal → cambiar contraseña si aplica.
2. `GET .../onboarding/progreso` → `etapa_actual: cambio_password`, `estado_onboarding: Pendiente` o `En progreso`.
3. `POST .../onboarding/etapas` con `{ "etapa": "cambio_password" }` → **200**.
4. `POST .../etapas` con `{ "etapa": "perfil_corporativo", "datos_etapa": { "razon_social": "..." } }` → **200**.
5. `POST .../etapas` con `{ "etapa": "preferencias", "datos_etapa": { "canales_notificacion": "email", ... } }` → **200**; verificar `Dim_Preferencias_Cliente_topic` (primera fila).
6. `GET .../progreso` → `estado_onboarding: Completado`, `etapa_actual: null`.
7. Cerrar sesión, re-login → `GET progreso` confirma etapas sin reinicio (CA-ONB-005).

### Escenario D — Reenviar invitación (O08)

1. Login como **Administrador**.
2. `POST .../invitacion/reenviar` con `{ "id_usuario": <admin_local_id> }` → **200**.
3. Verificar `Dim_Credencial_topic` con `estadocredencial: Cambio contraseña`.
4. Login Cliente con nueva temp password → fuerza cambio.

### Escenario E — Recordatorios (RN-ONB-004)

1. Fixture cuenta con `estado_onboarding: En progreso` y `fecha_inicio_contrato` > 30 días atrás.
2. Ejecutar: `python manage.py send_onboarding_reminders`
3. Verificar un correo al gmail del admin local (máximo uno por semana por cuenta).
4. Con `estado_onboarding: Completado` → sin envío.

### Validaciones transversales

- Cliente accediendo a `idcliente` donde no es `admin_local_id` → **403**.
- Operador sin rol Administrador en O01/O12 → **403**.
- Etapa `preferencias` antes de `perfil_corporativo` → **400**.
- `etapa` fuera de catálogo → **400**.

## 3) Validar consumo frontend (Angular)

### Servicios (`typescript-expert`)

- `models/incorporacion-cliente.contract.ts` — tipos alineados al OpenAPI.
- `IncorporacionClienteApiService` — un método por `operationId`.
- `OnboardingFacadeService` — orquesta wizard según `GET progreso`.

### Guards (`angular-architect`)

| Guard | Comportamiento esperado |
|-------|-------------------------|
| `AdministradorGuard` | Solo Admin en `/registro` y `/configuracion` |
| `AdminLocalOnboardingGuard` | Cliente solo si `user.id === cuenta.admin_local_id` |
| `OnboardingPendienteGuard` | Redirige a wizard si onboarding incompleto |
| `OnboardingCompletadoGuard` | Impide re-entrar al wizard si `Completado` |

### Escenarios UI

1. Admin registra cliente → formulario O01 → toast 201 → navega a configuración.
2. Admin configura plan/logo → estado Pendiente visible.
3. Cliente completa wizard 3 pasos → pantalla de éxito al `Completado`.
4. Admin reenvía invitación desde panel de cuenta.

## 4) Pruebas sugeridas

```bash
cd backend
pytest apps/cuentas_clientes/tests/api/test_registro_cuenta_contract.py -v -m api
pytest apps/cuentas_clientes/tests/api/test_configuracion_cuenta_contract.py -v -m api
pytest apps/cuentas_clientes/tests/api/test_onboarding_contract.py -v -m api
pytest apps/cuentas_clientes/tests/api/test_reenviar_invitacion_contract.py -v -m api
pytest apps/cuentas_clientes/tests/services/test_onboarding_service.py -v -m service
```

```bash
cd frontend
npm test -- --include='**/incorporacion-clientes/**/*.spec.ts'
```

## 5) Criterios de salida

- [ ] Contrato OpenAPI aprobado y alineado con spec clarificada.
- [ ] CU-O01: registro con `estado=Activo`, admin local, credencial temp, email.
- [ ] CU-O12: configuración plan/logo, `estado_onboarding=Pendiente`.
- [ ] CU-O02/O09: etapas canónicas, progreso reanudable, `Dim_Preferencias_Cliente` en etapa preferencias.
- [ ] CU-O08: reenvío invitación con `estadocredencial=Cambio contraseña`.
- [ ] RN-ONB-004: job semanal documentado y probable en dev.
- [ ] Patrón Vista→Servicio→Repositorio y Kafka-only-write verificados.
- [ ] Guards Angular restringen Admin, admin local y estado onboarding.

## 6) Cron recordatorios (producción)

```bash
# Ejemplo: lunes 08:00 UTC
0 8 * * 1 cd /app/backend && python manage.py send_onboarding_reminders
```

## 7) Post-validación: gestion-cuentas

Tras onboarding `Completado`, validar que **gestion-cuentas** opera sobre la misma cuenta:

```bash
# Login admin local → GET /api/v1/cuentas-clientes/{idcliente}/perfil → 200
```

Si `CuentaUsuarioRepository` aún usa `Dim_Usuario_Cliente`, ejecutar refactor de alineación documentado en `plan.md` § Complexity Tracking.

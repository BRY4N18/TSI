# Quickstart - Validación de Incorporación de Clientes

Guía de validación end-to-end contract-first para **CU-O14, O16, O02, O09 y O08**.
CU-O01 y CU-O12 están retirados (HTTP 410).

## Prerequisitos

- Contrato: `contracts/incorporacion-clientes.openapi.yaml`
- Spec y plan en `specs/003-operational/Cuentas-Clientes/incorporacion-clientes/backend/`
- Módulo **autenticacion-y-rbac** operativo (login JWT + validación de sesión)
- Topic `Fact_Onboarding_topic` registrado en `backend/config/settings.py` → `KAFKA_TOPICS`
- Variables SMTP para O14/O16/O08/recordatorios (opcional en dev; fallo debe loguearse sin revertir)

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
| POST | `/api/v1/cuentas-clientes/autorregistro` | O14 | público |
| GET | `/api/v1/cuentas-clientes/solicitudes` | O16 | Administrador |
| POST | `/api/v1/cuentas-clientes/{idcliente}/aprobacion` | O16 | Administrador |
| POST | `/api/v1/cuentas-clientes/{idcliente}/anular-rechazo` | O16 | Administrador |
| POST | `/api/v1/cuentas-clientes/{idcliente}/logo/upload-url` | O02 | Cliente (admin local) |
| GET | `/api/v1/cuentas-clientes/{idcliente}/onboarding/progreso` | O09 | Cliente (admin local) / Admin |
| POST | `/api/v1/cuentas-clientes/{idcliente}/onboarding/etapas` | O02 | Cliente (admin local) / Admin |
| POST | `/api/v1/cuentas-clientes/{idcliente}/invitacion/reenviar` | O08 | Administrador / Cliente |
| POST | `/api/v1/cuentas-clientes` | O01 | **410 Gone** |
| PATCH | `/api/v1/cuentas-clientes/{idcliente}/configuracion` | O12 | **410 Gone** |

Convenciones (`api-standards.md`):

- Envelope éxito: `{ "data": {...}, "meta": {} }`
- Envelope error: `{ "error", "detail", "code" }`
- Header `Idempotency-Key` en POST/PATCH de escritura

**Resultado esperado**: contrato alineado con decisiones 2026-07-25 (O14→O16 canónico).

## 2) Validar flujo backend (Vista → Servicio → Repositorio)

### Escenario A — Autorregistro (O14)

1. `POST /api/v1/cuentas-clientes/autorregistro` (sin auth) con cuerpo:

```json
{
  "razon_social": "Flota Demo SA",
  "nombre": "Flota Demo",
  "tipo": "Proveedor",
  "nit_identificacion": "900999888-1",
  "admin_local": {
    "nombres": "Ana",
    "apellidos": "García",
    "gmail": "ana.garcia@demo.com"
  }
}
```

2. Esperar **201** con `estado: Pendiente_Aprobación`.
3. Mismo NIT → **409**.
4. Login con ese usuario: **permitido** (gate en módulos, no en auth).

### Escenario B — Aprobación / rechazo / anular (O16)

1. Login **Administrador**.
2. `GET .../solicitudes` → lista pendientes.
3. `POST .../{id}/aprobacion` `{ "decision": "aprobar" }` → **200**, `Activo`, email.
4. Alternativa rechazo: `{ "decision": "rechazar", "motivo": "..." }` → email.
5. `POST .../{id}/anular-rechazo` → `Rechazado_Anulado`; nuevo O14 mismo NIT → **201**.

### Escenario B2 — O01/O12 retirados

1. `POST /api/v1/cuentas-clientes` → **410**.
2. `PATCH .../configuracion` → **410**.

### Escenario C — Onboarding (O02 + O09)

1. Login Cliente admin local de cuenta **Activo**.
2. `GET .../onboarding/progreso` → etapa actual.
3. Completar `cambio_password` → `perfil_corporativo` (logo) → `preferencias`.
4. Si cuenta `Pendiente_Aprobación` → **403**.

### Escenario D — Reenviar invitación (O08)

1. Admin desde UI Solicitudes o `POST .../invitacion/reenviar`.
2. Cliente desde wizard onboarding.

### Escenario E — Recordatorios (RN-ONB-004)

1. Fixture `Activo` con onboarding incompleto >30 días post-aprobación.
2. `python manage.py send_onboarding_reminders`.

### Validaciones transversales

- Cliente en `idcliente` ajeno → **403**.
- Etapa fuera de orden / catálogo → **400**.

## 3) Validar consumo frontend (Angular)

| Ruta | Actor |
|------|-------|
| `/cuentas-clientes/incorporacion-clientes/autorregistro` | Público |
| `/cuentas-clientes/incorporacion-clientes/solicitudes` | Administrador |
| `/cuentas-clientes/incorporacion-clientes/:id/onboarding` | Admin local Activo |

Guards: `sessionGuard` + `roleGuard` (solicitudes); `adminLocalOnboardingGuard` + `onboardingPendienteGuard` (wizard).

## 4) Pruebas sugeridas

```bash
cd backend
pytest apps/cuentas_clientes/tests -q
```

```bash
cd frontend
npm test -- --include='**/incorporacion-clientes/**/*.spec.ts'
```

## 5) Criterios de salida

- [x] OpenAPI alineado (1.2.0) con Session 2026-07-25.
- [x] CU-O14 → Pendiente_Aprobación.
- [x] CU-O16 aprobar/rechazar/anular + email.
- [x] CU-O01/O12 → 410.
- [x] CU-O02/O09 solo Activo; logo cliente.
- [x] CU-O08 en solicitudes + wizard.
- [x] RN-ONB-004 job documentado.

## 6) Cron recordatorios (producción)

```bash
0 8 * * 1 cd /app/backend && python manage.py send_onboarding_reminders
```

## 7) Post-validación: gestion-cuentas

Tras onboarding `Completado`:

```bash
# Login admin local → GET /api/v1/cuentas-clientes/{idcliente}/perfil → 200
```

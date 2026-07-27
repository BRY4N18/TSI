# Avance: Notificación de Prospectos a Ventas (`notificacion-ventas`)

**Feature SpecKit:** `specs/003-operational/Ventas-CRM/notificacion-ventas/`  
**CUs:** O118 (demo interactiva), O122 (notificar a ventas) + RF-NV-004 (consulta)  
**App Django:** `backend/apps/ventas_crm/` (extensión del módulo ya existente de pipeline #04)  
**Fecha de avance:** 2026-07-25 / 2026-07-26  
**Base URL API:** `/api/v1`

Este documento describe **qué se agregó en código**, **qué envía cada endpoint**, **qué hace cada capa** y **cómo se conecta el flujo extremo a extremo**, para verificación manual.

---

## 1. Resumen del flujo

```text
Prospecto se registra (#04)
        │
        ▼
POST /ventas-crm/prospectos  ──►  respuesta incluye demo_grant (HMAC)
        │
        ▼
POST /ventas-crm/demo/sesiones  (público, grant)
        │  primer_canje: fija demo_expiracion (+30 min), Kafka inicio_sesion
        │  resume: mismo grant + demo activa → nuevo token, SIN segundo inicio_sesion
        ▼
Bearer demo_session_token (HS256, typ=demo_session)
        │
        ▼
POST /ventas-crm/demo/interacciones  ──►  Kafka Fact_Interaccion_Demo
        │
        ▼
Job interno run_evaluacion_reglas_demo()  (≤60 s; NO es endpoint público)
        │  evalúa reglas MVP sobre sesión histórica
        │  si hay idusuario + regla cumplida + no dedup → Kafka Fact_NotificacionVentas
        │  despacha email o push (slack → error explícito, sin fallback)
        ▼
GET /ventas-crm/notificaciones  (JWT gerente/admin) ──► historial Pinot
```

**Principios de arquitectura respetados:**

- Vista → Servicio → Repositorio.
- Escrituras **solo por Kafka**; lecturas **Pinot**.
- No hay columna `estado_envio` en Pinot.
- Slack está en el enum de canal, pero **no hay adaptador Slack** en MVP.
- El JWT de usuario (RS256 RBAC) **no** sirve para `/demo/interacciones`; hace falta el token de demo.

---

## 2. Configuración agregada / tocada

### 2.1 Settings (`backend/config/settings.py`)

| Clave | Valor / default | Uso |
|-------|-----------------|-----|
| `KAFKA_TOPICS["interaccion_demo"]` | `Fact_Interaccion_Demo_topic` | Publicación de eventos demo |
| `KAFKA_TOPICS["notificacion_ventas"]` | `Fact_NotificacionVentas_topic` | Publicación de notificaciones |
| `DEMO_GRANT_SECRET` | env / secret ≥32 chars | Firma HMAC del grant |
| `DEMO_SESSION_SECRET` | env / secret ≥32 chars | Firma JWT HS256 de sesión demo |
| `DEMO_SESSION_MINUTES` | `30` | Duración absoluta de `demo_expiracion` en primer canje |
| `DEMO_REEVAL_DAYS` | `7` | Ventana de reevaluación del job |
| `EVALUACION_REGLAS_DEMO_INTERVAL_SECONDS` | `60` | Cadencia objetivo del scheduler |
| Throttle `demo_sesion_ip` | `20/min` | Abrir/reanudar sesión |
| Throttle `demo_interaccion_token` | `60/min` | Ingesta por token |

También documentado en `backend/.env.example`:

```env
DEMO_GRANT_SECRET=dev-demo-grant-secret-min-32-chars!!
DEMO_SESSION_SECRET=dev-demo-session-secret-min-32-chars!
```

---

## 3. Tokens y autenticación (lo más crítico)

### 3.1 `demo_grant` (no es JWT)

**Archivo:** `backend/apps/ventas_crm/demo_tokens.py`

- Se emite al registrar el prospecto (`issue_demo_grant(idprospecto)`).
- Formato: `{idprospecto}.{nonce}.{hmac_sha256_hex}`
- Mensaje firmado: `"{idprospecto}:{nonce}"` con `DEMO_GRANT_SECRET`.
- Verificación: `verify_demo_grant(grant, idprospecto)` (comparación constante + match de id).

**No se persiste en Pinot.** El “canje” se deduce porque `Dim_Prospecto.demo_expiracion` deja de ser `NULL`.

### 3.2 `demo_session_token` (JWT HS256)

Claims:

| Claim | Significado |
|-------|-------------|
| `typ` | Debe ser exactamente `"demo_session"` |
| `idprospecto` | Prospecto dueño de la sesión |
| `exp` | Epoch = `demo_expiracion` (no se prolonga en resume) |
| `iat` | Emitido ahora |
| `jti` | Random hex — garantiza token distinto en resume aunque sea el mismo segundo |

Autenticación DRF: `backend/apps/ventas_crm/authentication.py` → `DemoSessionAuthentication`

- Lee `Authorization: Bearer <token>`.
- Decodifica con `DEMO_SESSION_SECRET`.
- Si `typ != demo_session` → 401.
- Construye un user sintético: `is_demo_session=True`, `idprospecto=...`, `roles=["DemoProspecto"]`.

### 3.3 JWT de usuario (RBAC existente)

- Se usa en `GET /ventas-crm/notificaciones`.
- Roles permitidos: `Administrador`, `GerenteVentas`, `GerenteCuentasPublicas` (`IsGerenteOrAdminNotificaciones`).
- Si se manda a `/demo/interacciones` → falla (token no es `demo_session`).

---

## 4. API REST — endpoints agregados / extendidos

Contrato OpenAPI:  
`specs/003-operational/Ventas-CRM/notificacion-ventas/contracts/notificacion-ventas.openapi.yaml`

Rutas Django: `backend/apps/ventas_crm/urls.py`

Envelope de éxito del proyecto: `{ "data": ..., "meta": ...? }`  
Errores: `{ "error", "detail", "code" }` vía `crm_error`.

---

### 4.1 Handoff #04 (extendido, no endpoint nuevo)

#### `POST /api/v1/ventas-crm/prospectos`

**Qué se agregó en código:**  
`RegistroProspectoService` ahora llama `issue_demo_grant(...)` y **devuelve** `demo_grant` en `data`.

**Request (igual que antes):**

```json
{
  "nombres": "Laura",
  "apellidos": "Comercial",
  "gmail": "laura@example.com",
  "empresa": "Acme",
  "tipo_organizacion": "Privado",
  "cargo": "Compras",
  "telefono": "3000000000",
  "como_nos_conocio": "web"
}
```

**Response 201 — campos relevantes nuevos / clave:**

```json
{
  "data": {
    "idprospecto": 123,
    "demo_grant": "123.a1b2c3d4e5f67890.<hmac...>",
    "idusuario": 20,
    "etapa_actual": "Nuevo",
    "asignacion_automatica": { "ok": true }
  }
}
```

- `demo_grant` es **aditivo** (sin breaking change sobre #04).
- Si no hay gerente en pool, `idusuario` puede ser `null` (huérfano): el job de reglas **no** inserta notificación hasta que haya dueño.

---

### 4.2 Abrir / reanudar sesión demo (O118)

#### `POST /api/v1/ventas-crm/demo/sesiones`

| Atributo | Valor |
|----------|-------|
| Vista | `DemoSesionView` |
| Servicio | `DemoSesionService.abrir` |
| Auth | Ninguna (público) |
| Permiso | `AllowAny` |
| Throttle | `DemoSesionIpThrottle` (`20/min` por IP) |

**Request:**

```http
POST /api/v1/ventas-crm/demo/sesiones
Content-Type: application/json

{
  "idprospecto": 123,
  "demo_grant": "123.<nonce>.<sig>"
}
```

**Qué hace el servicio (paso a paso):**

1. Valida que vengan `idprospecto` y `demo_grant`.
2. Verifica HMAC del grant contra ese id → si falla → **401**.
3. Busca prospecto en Pinot → si no existe → **404**.
4. Si `activo=false` → **403**.
5. **Primer canje** (`demo_expiracion` es `NULL`):
   - Calcula `demo_expiracion = now + DEMO_SESSION_MINUTES` (ISO UTC `...Z`).
   - Publica update parcial a Kafka `Dim_Prospecto_topic` (`update_demo_expiracion`).
   - Publica evento `inicio_sesion` a `Fact_Interaccion_Demo_topic`.
   - Emite `demo_session_token`.
   - Responde `modo: "primer_canje"`.
6. **Resume** (ya hay `demo_expiracion` y `now < demo_expiracion`):
   - Reemite token nuevo (`jti` distinto).
   - **Misma** `demo_expiracion` (no se alarga).
   - **No** publica segundo `inicio_sesion`.
   - Responde `modo: "resume"`.
7. Si `now >= demo_expiracion` → **403** “demo expirada” (sin renovación).

**Response 200:**

```json
{
  "data": {
    "idprospecto": 123,
    "demo_session_token": "<jwt-hs256>",
    "demo_expiracion": "2026-07-25T20:40:00Z",
    "modo": "primer_canje"
  }
}
```

**Códigos de error esperados:**

| Caso | HTTP |
|------|------|
| Grant inválido / id mismatch | 401 |
| Prospecto inactivo / demo expirada | 403 |
| Prospecto inexistente | 404 |
| Rate limit IP | 429 |
| Body incompleto | 400 |

---

### 4.3 Ingesta de interacciones (O118)

#### `POST /api/v1/ventas-crm/demo/interacciones`

| Atributo | Valor |
|----------|-------|
| Vista | `DemoInteraccionView` |
| Servicio | `IngestaInteraccionDemoService.registrar` |
| Auth | `DemoSessionAuthentication` |
| Throttle | `DemoInteraccionTokenThrottle` (`60/min` por token) |

**Request:**

```http
POST /api/v1/ventas-crm/demo/interacciones
Authorization: Bearer <demo_session_token>
Content-Type: application/json

{
  "idprospecto": 123,
  "tipo_evento": "tiempo_seccion",
  "seccion": "precios",
  "metadata": { "duracion_ms": 300000 },
  "timestamp_evento": 1721900000000
}
```

**Campos:**

| Campo | Requerido | Notas |
|-------|-----------|-------|
| `idprospecto` | Sí | Debe coincidir con el del token |
| `tipo_evento` | Sí | `click` \| `tiempo_seccion` \| `inicio_sesion` \| `fin_sesion` |
| `seccion` | Sí | string no vacío (ej. `precios`, `pricing`) |
| `metadata` | Condicional | Para `tiempo_seccion` **debe** incluir `duracion_ms` |
| `timestamp_evento` | Sí (contrato) | Epoch ms; si falta, el servicio usa “ahora” |

**Qué hace:**

1. Exige que `request.user.is_demo_session` sea true.
2. Compara `idprospecto` body vs token → mismatch → **403**.
3. Valida enum de `tipo_evento` y `seccion`.
4. Si `tiempo_seccion`, exige `metadata.duracion_ms`.
5. Verifica que el prospecto exista y que la demo no esté expirada.
6. Serializa `metadata` a **string JSON** (así viaja a Pinot).
7. Publica a Kafka `Fact_Interaccion_Demo_topic` (repo genera `idinteraccion` + `fecha_actualizacion`).
8. **No** dispara evaluación de reglas en línea (eso es del job).

**Response 201:**

```json
{
  "data": {
    "idinteraccion": 45,
    "idprospecto": 123,
    "tipo_evento": "tiempo_seccion",
    "seccion": "precios",
    "metadata": "{\"duracion_ms\": 300000}",
    "timestamp_evento": 1721900000000,
    "fecha_actualizacion": 1721900000500
  }
}
```

**Para disparar reglas MVP en la práctica:**

1. Un `tiempo_seccion` en `precios` con `duracion_ms >= 300000` → regla `tiempo_seccion_precios_5min` (canal `email`).
2. Al menos **3** eventos (que no sean `inicio_sesion`) con `seccion ∈ {precios, pricing}` → regla `visito_pricing_3x` (canal `push`).

**Errores:**

| Caso | HTTP |
|------|------|
| Sin token / JWT usuario / tip incorrecto | 401 (o 403 en algunos caminos de vista) |
| Token de otro prospecto / demo expirada | 403 |
| Validación de campos | 400 |
| >60/min por token | 429 |

---

### 4.4 Listar notificaciones (RF-NV-004)

#### `GET /api/v1/ventas-crm/notificaciones`

| Atributo | Valor |
|----------|-------|
| Vista | `NotificacionVentasListView` |
| Servicio | `ConsultaNotificacionVentasService.listar` |
| Auth | JWT usuario (cadena RBAC existente) |
| Permisos | `IsAuthenticated401` + `IsGerenteOrAdminNotificaciones` |

**Query params:**

| Param | Descripción |
|-------|-------------|
| `limit` | 1–100, default 20 |
| `cursor` | `idnotificacion` para paginación cursor |
| `idusuario` | Solo Admin: filtra destinatario; Gerente no puede pedir otro id |
| `regladisparada` | Filtro opcional |
| `id_prospecto` | Filtro opcional |

**Request ejemplo:**

```http
GET /api/v1/ventas-crm/notificaciones?limit=20&id_prospecto=123
Authorization: Bearer <jwt-gerente-o-admin>
```

**Reglas RBAC en servicio:**

- `GerenteVentas` / `GerenteCuentasPublicas`: solo filas con `idusuariogerentenotificado = user_id`.
- `Administrador`: ve todas; puede pasar `idusuario` para filtrar.
- Otro rol → 403.

**Response 200:**

```json
{
  "data": [
    {
      "idnotificacion": 10,
      "id_prospecto": 123,
      "idinteraccion": 45,
      "idusuariogerentenotificado": 20,
      "regladisparada": "tiempo_seccion_precios_5min",
      "canal": "email",
      "fechahoranotificacion": 1721900060000
    }
  ],
  "meta": {
    "pagination": {
      "next_cursor": null,
      "limit": 20
    }
  }
}
```

`next_cursor` = último `idnotificacion` de la página si `len(data) == limit`; si no, `null`.

---

## 5. Job interno de evaluación (O122) — no es API pública

**Archivos:**

- `backend/apps/ventas_crm/tasks.py` → `run_evaluacion_reglas_demo()` (+ opcional `@shared_task` si Celery está instalado)
- `backend/apps/ventas_crm/services/evaluacion_reglas_demo_service.py`
- `backend/apps/ventas_crm/services/reglas_demo_catalog.py`
- `backend/apps/ventas_crm/services/despacho_notificacion_ventas_service.py`

### 5.1 Qué hace el job

1. Lista eventos `inicio_sesion` recientes (ventana `DEMO_REEVAL_DAYS`).
2. Por cada sesión histórica `[inicio_sesion, demo_expiracion)`:
   - Carga prospecto.
   - Si no hay `demo_expiracion` o está fuera de ventana → skip.
   - Agrega eventos de esa sesión y evalúa catálogo MVP.
3. Si el prospecto **no tiene** `idusuario` y hay reglas cumplidas → cuenta `skipped_orphan` (no inserta).
4. Si hay dueño:
   - Dedup día UTC por (`id_prospecto`, `regladisparada`) → si ya existe, `skipped_dedup`.
   - Si no: publica fila a `Fact_NotificacionVentas_topic`.
   - Intenta despacho por canal.
5. Retorna métricas:

```json
{
  "created": 2,
  "skipped_orphan": 0,
  "skipped_dedup": 0,
  "skipped_expired_window": 0,
  "sessions_scanned": 1
}
```

### 5.2 Catálogo de reglas MVP

| `regladisparada` | Condición (por sesión histórica) | `canal` |
|-----------------|----------------------------------|---------|
| `tiempo_seccion_precios_5min` | Σ `duracion_ms` de eventos `tiempo_seccion` + `seccion=precios` ≥ **300000** | `email` |
| `visito_pricing_3x` | COUNT eventos con `seccion ∈ {precios,pricing}` (excluye `inicio_sesion`) ≥ **3** | `push` |

### 5.3 Despacho

| Canal | Comportamiento |
|-------|----------------|
| `email` | `EmailNotificationSender` (si no hay SMTP configurado, log warning y no falla) |
| `push` | `PushNotificationSender` al `idusuariogerentenotificado` |
| `slack` | `CanalNoDisponibleError` — se loguea; **no** hay fallback a email |
| otro | `CanalNoDisponibleError` |

**Importante:** la fila en `Fact_NotificacionVentas` ya se publicó antes del despacho; no hay `estado_envio` en Pinot.

Invocación manual (dev/tests):

```python
from apps.ventas_crm.tasks import run_evaluacion_reglas_demo
run_evaluacion_reglas_demo()
```

---

## 6. Repositorios / Kafka / Pinot

| Repositorio | Tabla | Topic Kafka | Métodos clave |
|-------------|-------|-------------|---------------|
| `InteraccionDemoRepository` | `Fact_Interaccion_Demo` | `Fact_Interaccion_Demo_topic` | `create`, `list_by_prospecto`, `list_inicio_sesion_recent` |
| `NotificacionVentasRepository` | `Fact_NotificacionVentas` | `Fact_NotificacionVentas_topic` | `create`, `list`, `exists_dedup_dia_utc` |
| `ProspectoRepository` (extendido) | `Dim_Prospecto` | `Dim_Prospecto_topic` | `update_demo_expiracion` |

**Rutas de archivos:**

- `backend/core/repositories/ventas_crm/interaccion_demo_repository.py`
- `backend/core/repositories/ventas_crm/notificacion_ventas_repository.py`
- `backend/core/repositories/ventas_crm/prospecto_repository.py` (`update_demo_expiracion`)

Servicios **no** llaman Kafka directamente; solo repositorios.

---

## 7. Frontend Angular agregado

Módulo: `frontend/src/app/modules/ventas-crm/`

| Pieza | Ruta de archivo | Qué hace |
|-------|-----------------|----------|
| Tipos | `models/notificacion-ventas.types.ts` | DTOs alineados al OpenAPI |
| `DemoApiService` | `services/demo-api.service.ts` | `POST .../demo/sesiones`, `POST .../demo/interacciones` |
| `NotificacionApiService` | `services/notificacion-api.service.ts` | `GET .../notificaciones` |
| Interceptor | `interceptors/demo-session.interceptor.ts` | Adjunta Bearer demo solo a `/demo/interacciones`; guarda token en `localStorage` clave `tsi.demo_session_token` |
| Página demo | `pages/demo-interactiva/` | UI: grant → abrir sesión → click precios; estados loading/error |
| Página notificaciones | `pages/notificaciones-ventas/` | Lista con skeleton / vacío / error+retry |
| Rutas | `ventas-crm.routes.ts` | `/ventas-crm/demo` (público), `/ventas-crm/notificaciones` (guard admin/gerente) |

**Wire global** en `frontend/src/app/app.config.ts`:

```ts
provideHttpClient(withInterceptors([authInterceptor, demoSessionInterceptor]))
```

`authInterceptor` **omite** `/ventas-crm/demo/interacciones` para no pisar el token demo con el JWT de usuario.

---

## 8. Inventario de archivos de código (backend focus)

### Nuevos / núcleo feature

```text
backend/apps/ventas_crm/demo_tokens.py
backend/apps/ventas_crm/authentication.py          # DemoSessionAuthentication
backend/apps/ventas_crm/tasks.py
backend/apps/ventas_crm/views/demo_views.py
backend/apps/ventas_crm/views/notificacion_views.py
backend/apps/ventas_crm/services/demo_sesion_service.py
backend/apps/ventas_crm/services/ingesta_interaccion_demo_service.py
backend/apps/ventas_crm/services/reglas_demo_catalog.py
backend/apps/ventas_crm/services/evaluacion_reglas_demo_service.py
backend/apps/ventas_crm/services/despacho_notificacion_ventas_service.py
backend/apps/ventas_crm/services/consulta_notificacion_ventas_service.py
backend/core/repositories/ventas_crm/interaccion_demo_repository.py
backend/core/repositories/ventas_crm/notificacion_ventas_repository.py
```

### Extendidos

```text
backend/apps/ventas_crm/urls.py
backend/apps/ventas_crm/permissions.py             # IsGerenteOrAdminNotificaciones
backend/apps/ventas_crm/throttles.py               # DemoSesionIp / DemoInteraccionToken
backend/apps/ventas_crm/services/registro_prospecto_service.py  # demo_grant
backend/core/repositories/ventas_crm/prospecto_repository.py    # update_demo_expiracion
backend/config/settings.py
backend/conftest.py                                # fixtures demo_grant / demo_session + mirrors Pinot
backend/.env.example
```

### Tests relevantes

```text
backend/apps/ventas_crm/tests/api/test_demo_sesiones_contract.py
backend/apps/ventas_crm/tests/api/test_demo_interacciones_contract.py
backend/apps/ventas_crm/tests/api/test_notificaciones_ventas_contract.py
backend/apps/ventas_crm/tests/api/test_registro_prospecto_demo_grant_contract.py
backend/apps/ventas_crm/tests/e2e/test_notificacion_ventas_quickstart_e2e.py
backend/apps/ventas_crm/tests/services/test_*.py   # sesión, ingesta, evaluación, despacho, consulta, SLA, task
backend/apps/ventas_crm/tests/unit/test_demo_*.py
backend/apps/ventas_crm/tests/repositories/test_*demo*.py / test_notificacion_*.py
```

---

## 9. Ejemplo E2E mínimo (para verificar a mano)

Asumiendo API en `http://localhost:8000` **y** Pinot/Kafka operativos:

```bash
# 1) Registro → guardar idprospecto + demo_grant
curl -s -X POST http://localhost:8000/api/v1/ventas-crm/prospectos \
  -H "Content-Type: application/json" \
  -d "{\"nombres\":\"E2E\",\"apellidos\":\"Test\",\"gmail\":\"e2e$(date +%s)@ex.com\",\"empresa\":\"Acme\",\"tipo_organizacion\":\"Privado\",\"cargo\":\"C\",\"telefono\":\"1\",\"como_nos_conocio\":\"web\"}"

# 2) Abrir sesión
curl -s -X POST http://localhost:8000/api/v1/ventas-crm/demo/sesiones \
  -H "Content-Type: application/json" \
  -d "{\"idprospecto\":ID,\"demo_grant\":\"GRANT\"}"

# 3) Interacciones (Bearer = demo_session_token)
curl -s -X POST http://localhost:8000/api/v1/ventas-crm/demo/interacciones \
  -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" \
  -d "{\"idprospecto\":ID,\"tipo_evento\":\"tiempo_seccion\",\"seccion\":\"precios\",\"metadata\":{\"duracion_ms\":300000},\"timestamp_evento\":$(date +%s000)}"

# 4) Resume (mismo grant) → modo=resume, misma demo_expiracion

# 5) Esperar ≤60s al job Celery/cron, o invocar run_evaluacion_reglas_demo()

# 6) GET notificaciones con JWT GerenteVentas / Admin
```

**Sin infra Kafka/Pinot**, el flujo se validó con:

```bash
cd backend
python -m pytest apps/ventas_crm/tests/e2e/test_notificacion_ventas_quickstart_e2e.py -vv -s
```

Resultado de esa corrida: **PASS** (registro → sesión → interacciones → job crea 2 notificaciones → dedup → listado gerente/admin).

---

## 10. Checklist de verificación para el lector

Usa esta lista al revisar el código:

- [ ] `POST /prospectos` incluye `data.demo_grant` firmado y usable.
- [ ] `POST /demo/sesiones` con grant malo responde **401**.
- [ ] Primer canje fija `demo_expiracion` y crea exactamente un `inicio_sesion`.
- [ ] Resume no crea segundo `inicio_sesion` y conserva la misma `demo_expiracion`.
- [ ] Resume emite un `demo_session_token` distinto (`jti`).
- [ ] Interacciones requieren Bearer `typ=demo_session`; JWT de usuario no alcanza.
- [ ] `tiempo_seccion` sin `metadata.duracion_ms` → 400.
- [ ] Job no inserta si `idusuario` es null (huérfano).
- [ ] Con dueño + reglas cumplidas → filas en `Fact_NotificacionVentas` con canales correctos.
- [ ] Segunda evaluación el mismo día UTC no duplica la misma regla (dedup).
- [ ] Slack no se envía; error explícito de canal.
- [ ] Gerente solo ve sus notificaciones; Admin puede ver todas.
- [ ] No existe campo/columna `estado_envio` en el modelo de este feature.
- [ ] Kafka solo se publica desde repositorios, no desde vistas/servicios de dominio.

---

## 11. Referencias SpecKit

| Documento | Ruta |
|-----------|------|
| Spec | `specs/003-operational/Ventas-CRM/notificacion-ventas/spec.md` |
| Plan | `.../plan.md` |
| Tasks (60/60) | `.../tasks.md` |
| Data model | `.../data-model.md` |
| Quickstart + resultado E2E | `.../quickstart.md` |
| OpenAPI | `.../contracts/notificacion-ventas.openapi.yaml` |
| Module map (#05) | `.specify/docs/architecture/module-map.md` |

---

*Documento generado para revisión de avance de implementación — feature `notificacion-ventas`.*

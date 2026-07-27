# Avance: Suscripciones y Facturación (`subscriptions-and-billing`)

**Feature SpecKit:** `specs/003-operational/Suscripciones-Facturacion/subscriptions-and-billing/`  
**App Django:** `backend/apps/suscripciones/`  
**Repos canónicos:** `backend/core/repositories/suscripciones/`  
**Frontend:** `frontend/src/app/modules/suscripciones/`  
**CUs / RFs:** O101–O111 · RF-SUSF-001…010  
**Fecha de avance:** 2026-07-26  
**Base URL API:** `/api/v1`  
**Ruta de este documento:** `avances-spec/avance-suscripciones-facturacion.md`

Este documento describe **qué se agregó en código**, **qué envía cada endpoint**, **qué hace cada capa**, **cómo se ve en el frontend** y **cómo verificarlo**, para revisión manual.

---

## 1. Resumen ejecutivo

Se implementó el módulo de **Suscripciones y Facturación** de punta a punta:

| Capa | Qué se agregó |
|------|----------------|
| Backend app | `apps.suscripciones` (views, services, jobs, permissions, throttles, idempotency, pasarela simulada) |
| Repositorios | Plan, MetodoPago, Suscripcion, Factura, SolicitudCambioPlan (lectura Pinot + escritura Kafka) |
| API REST | Rutas bajo `/api/v1/suscripciones/...` según OpenAPI |
| Jobs | Facturación mensual, dunning, renovación, mantenimiento `activo` |
| Frontend | Shell con tabs, 6 pantallas con HTML/CSS (design-system), sidebar, guards, API services |
| Tests | `pytest apps/suscripciones` → **62 passed** (`-m "not integration"`) |

**Flujo de negocio (alto nivel):**

```text
Proveedor autentica (JWT)
        │
        ├─ POST /suscripciones              → Alta Activa + sync plan_suscripcion
        ├─ POST /suscripciones/metodos-pago → Tokenización (sin PAN) + RN-021 si Suspendida
        ├─ Jobs facturación/dunning         → Fact_Factura + cobro simulador
        ├─ GET  /suscripciones/mia          → Estado + acceso (RN-017)
        ├─ POST .../cambio-plan             → Upgrade auto / Downgrade Pendiente
        └─ Admin aprueba/rechaza downgrade
```

**Principios respetados:**

- Vista → Servicio → Repositorio.
- Escrituras **solo Kafka**; lecturas **Pinot**.
- Sync denormalizado `Dim_Cliente.plan_suscripcion` **solo** vía `ClienteRepository.update` (no Kafka directo desde el service de billing).
- Estados Title Case: `Activa` / `Suspendida` / `Cancelada`; facturas `Pendiente` / `Pagada` / `Fallida`.
- Impuestos = `0` en MVP. Numeración `FAC-{YYYYMM}-{seq8}`.

---

## 2. Configuración agregada / tocada

### 2.1 `backend/config/settings.py`

| Clave | Valor | Uso |
|-------|-------|-----|
| `INSTALLED_APPS` | `apps.suscripciones` | App Django |
| `KAFKA_TOPICS["plan"]` | `Dim_Plan_topic` | Catálogo planes |
| `KAFKA_TOPICS["metodo_pago"]` | `Dim_MetodoPago_topic` | Métodos de pago |
| `KAFKA_TOPICS["suscripcion"]` | `Fact_Suscripcion_topic` | Suscripciones |
| `KAFKA_TOPICS["factura"]` | `Fact_Factura_topic` | Facturas |
| `KAFKA_TOPICS["solicitud_cambio_plan"]` | `Fact_Solicitud_Cambio_Plan_topic` | Solicitudes cambio |

### 2.2 `backend/config/urls.py`

```python
path("api/v1/", include("apps.suscripciones.urls")),
```

### 2.3 Env / simulador

| Variable | Default | Efecto |
|----------|---------|--------|
| `BILLING_SIMULATOR_FAIL_RATE` | `0` | Probabilidad de rechazo del simulador de pasarela (0–1) |

### 2.4 Fixtures de test (`backend/conftest.py`)

- Seeds `Dim_Plan` con `limites` JSON (`unidades_max`, `usuarios_max`, `api_calls_mes`).
- `Fact_Suscripcion` con `estado: "Activa"` + `fecha_fin`.
- Tablas vacías: `Dim_MetodoPago`, `Fact_Factura`, `Fact_Solicitud_Cambio_Plan`.
- Mirror Kafka → Pinot para topics de billing.
- Fixtures: `proveedor_billing_auth_headers`, `admin_billing_auth_headers`.

---

## 3. Arquitectura de código (backend)

```text
apps/suscripciones/
  views/          → thin DRF (envelope success/error)
  services/       → reglas de negocio
  services/pasarela/ → PasarelaPagoPort + SimuladorPasarela
  jobs/           → batch facturación / dunning / renovación / mantenimiento
  management/commands/ → run_*_job
  permissions.py  → IsProveedorCuenta, IsAdministradorBilling
  idempotency.py  → cache por Idempotency-Key (TTL 300s)
  throttles.py    → 60/min proveedor write; 100/min admin (SimpleRateThrottle + idusuario)

core/repositories/suscripciones/
  plan_repository.py
  metodo_pago_repository.py
  suscripcion_repository.py   ← canónico Title Case
  factura_repository.py
  solicitud_cambio_plan_repository.py
  kafka_writer.py             ← reexport del writer de cuentas_clientes

core/repositories/soporte/suscripcion_repository.py
  → thin wrapper que delega find_idplan_activo al canónico (estado "Activa")
```

### 3.1 Capas típicas de un request

1. **View** valida auth/perm + `Idempotency-Key` (escrituras) + throttle.
2. **Service** aplica reglas (conflicto 409, RN-017, dunning, upgrade auto, etc.).
3. **Repository** lee Pinot; en create/update hace `kafka.publish(topic, payload)`.
4. En tests, `mock_kafka` espeja el payload en `PINOT_STORE` para read-after-write.

---

## 4. API HTTP — detalle por endpoint

Envelope estándar:

```json
{ "data": { ... } }
```

Error:

```json
{ "error": "<code>", "detail": "<mensaje>", "code": "<http>" }
```

Auth: `Authorization: Bearer <JWT RS256>` salvo que se indique lo contrario.  
Escrituras: header **`Idempotency-Key`** (recomendado / exigido por contrato).

---

### 4.1 `POST /api/v1/suscripciones` — Alta (CU-O111 / RF-SUSF-010)

| Campo | Valor |
|-------|--------|
| Rol | Proveedor / Cliente admin_local de cuenta `Activo` |
| Body | `{ "idplan": number, "renovacionautomatica"?: boolean }` |
| Éxito | `201` → `Fact_Suscripcion` `estado=Activa`, `activo=true`, `fecha_fin` = +1 mes Guayaquil |
| Conflictos | `409` si ya hay suscripción `activo=true` |
| Side effects | `ClienteRepository.update(..., { plan_suscripcion: nombre_plan })` → `Dim_Cliente_topic`. Si hay método activo → genera factura + intenta cobro. |

**Ejemplo request:**

```http
POST /api/v1/suscripciones HTTP/1.1
Authorization: Bearer <jwt>
Idempotency-Key: alta-001
Content-Type: application/json

{ "idplan": 2, "renovacionautomatica": true }
```

**Ejemplo `data` respuesta:**

```json
{
  "id_suscripcion": 2,
  "idcliente": 1,
  "idplan": 2,
  "precio": 149.0,
  "estado": "Activa",
  "activo": true,
  "renovacionautomatica": true,
  "fecha_inicio": 1720000000000,
  "fecha_fin": 1722678400000
}
```

**Código:** `views/suscripcion_views.py` → `AltaSuscripcionService`.

---

### 4.2 `GET /api/v1/suscripciones/mia` — Mi suscripción + acceso (RN-017)

| Campo | Valor |
|-------|--------|
| Rol | Proveedor |
| Body | — |
| Éxito | `200` con suscripción + `acceso_permitido`, `plan_nombre`, `nivel` |
| 404 | Sin suscripción `activo=true` |

**Reglas de acceso (`EvaluacionAccesoService`):**

| Estado | Acceso |
|--------|--------|
| `Activa` | Permitido |
| `Suspendida` | Denegado |
| `Cancelada` | Permitido solo si `now ≤ fecha_fin` (America/Guayaquil) |

**Código:** `MiSuscripcionView` enriquece con `PlanRepository.find_by_id`.

---

### 4.3 `POST /api/v1/suscripciones/mia/cancelar` — Cancelación (CU-O110 / RF-SUSF-009)

| Campo | Valor |
|-------|--------|
| Body | `{ "motivocancelacion": string }` (requerido, no vacío) |
| Efecto | `estado=Cancelada`, `renovacionautomatica=false`, `activo` sigue `true` hasta job de mantenimiento post `fecha_fin` |

---

### 4.4 `POST /api/v1/suscripciones/mia/reintentar-cobro` — Regularización (RN-028 / RF-SUSF-007)

| Campo | Valor |
|-------|--------|
| Condición | Suscripción `Suspendida` + factura vigente `Fallida` |
| Body | vacío |
| Éxito | `{ estado_pago, estado_suscripcion, resultado_ultimo_reintento }` |
| 409 | No Suspendida / sin Fallida |

Clave de cobro de reactivación: `{id_factura}-reactivacion-{idmetodopago}`.

---

### 4.5 `GET|POST /api/v1/suscripciones/metodos-pago` — RF-SUSF-002

**GET** — lista métodos del `idcliente` del token.

**POST body:**

```json
{
  "tipo": "tarjeta" | "transferencia" | "paypal",
  "datos_pasarela": { "numero": "4111...", "fechaexpiracion": "12/30" }
}
```

**Qué hace el service:**

1. Tokeniza → `tokenpasarela = tok_sim_{idcliente}_{tipo}_{ultimos4}` (nunca persiste PAN).
2. Crea método `activo=true`; desactiva el anterior.
3. Si suscripción `Suspendida` → dispara `MoraSuscripcionService.regularizar` (RN-021).

---

### 4.6 `GET|POST /api/v1/suscripciones/solicitudes-cambio-plan` — RF-SUSF-003 / CU-O104

**GET**

- Proveedor: solo sus solicitudes (`idcliente` del token).
- Admin: todas (filtro opcional `?estado=Pendiente&idcliente=`).

**POST body (Proveedor):**

```json
{ "idplansolicitado": 2, "motivo": "necesito más unidades" }
```

**Regla de nivel:**

| Comparación `nivel` | Resultado |
|---------------------|-----------|
| Upgrade (Básico→Profesional→Empresarial) | Auto-`Aprobada` + update suscripción + sync `plan_suscripcion` |
| Downgrade | Queda `Pendiente` hasta admin |
| Ya hay `Pendiente` | `409` (RN-023) |

---

### 4.7 `POST .../solicitudes-cambio-plan/{id}/aprobar|rechazar` — Admin

- **Aprobar:** aplica plan destino + sync cliente + `estado=Aprobada`.
- **Rechazar body:** `{ "motivo_rechazo": "..." }` → `estado=Rechazada`.

---

### 4.8 `GET|POST /api/v1/suscripciones/planes` · `PATCH .../planes/{idplan}` — RF-SUSF-001

| Método | Rol | Body / efecto |
|--------|-----|----------------|
| GET | Proveedor o Admin | Lista planes (activos) |
| POST | Admin | `{ nombre, precio, limites:{unidades_max,usuarios_max,api_calls_mes}, nivel }` → `201` |
| PATCH | Admin | cambios parciales |

`nivel` ∈ {`Básico`,`Profesional`,`Empresarial`}.

---

### 4.9 `GET /api/v1/suscripciones/facturas` · `GET .../facturas/{id_factura}` — RF-SUSF-006

- Solo facturas del `idcliente` del Proveedor.
- Campos clave: `numero_factura`, `periodo`, `estado_pago`, `monto_*`, `impuestos=0`, `desglose_cargos`, `reintentos`.

---

## 5. Jobs (sin HTTP público)

Zona: **America/Guayaquil**. Ventana operativa típica 02:00–05:00 (ops).

| Command | Archivo | Qué hace |
|---------|---------|----------|
| `python manage.py run_facturacion_mensual_job` | `jobs/facturacion_mensual_job.py` | Por cada `Activa`: crea factura del periodo si hay método; intenta cobro día 0 |
| `python manage.py run_dunning_job` | `jobs/dunning_job.py` | Reintento si `Pendiente` y (`reintentos==1` y ≥3 días) o (`reintentos==2` y ≥5 días) |
| `python manage.py run_renovacion_job` | `jobs/renovacion_job.py` | Si `fecha_fin ≤ now` y renovación auto: extiende +1 mes, factura, cobro |
| `python manage.py run_mantenimiento_activo_job` | `jobs/mantenimiento_activo_job.py` | `Cancelada` con `fecha_fin` vencida → `activo=false` |

### 5.1 Cobro (`CobroService`)

- Idempotency de pasarela: `{id_factura}-{reintentos}` (o override en reactivación).
- Éxito → `Pagada`.
- Fallo → `reintentos++`; al llegar a **3** → `Fallida` + suspensión (`estado=Suspendida`).

### 5.2 Numeración factura (`FacturaRepository`)

- Formato `FAC-{YYYYMM}-{seq8}` con max+1 por mes y retry si colisión (RN-026).

---

## 6. Frontend — qué se ve y qué llama

### 6.1 Rutas (lazy bajo shell autenticado)

Registrado en `app.routes.ts` → `path: 'suscripciones'`.

Shell: `BillingShellPage` con tabs por rol.

| URL | Guard | Pantalla |
|-----|-------|----------|
| `/suscripciones/mi-suscripcion` | Proveedor | Estado, alta, cancelar, reintentar cobro |
| `/suscripciones/metodos-pago` | Proveedor | Tabla + formulario tokenización |
| `/suscripciones/historial-facturas` | Proveedor | Tabla + panel detalle |
| `/suscripciones/cambio-plan` | Proveedor | Form solicitud + historial |
| `/suscripciones/catalogo-planes` | sesión | Cards de planes |
| `/suscripciones/aprobaciones-downgrade` | Admin | Aprobar / rechazar pendientes |

### 6.2 Sidebar (`nav-links.ts`)

Grupo **Suscripciones** con enlaces a mi suscripción, métodos, facturas, catálogo y aprobaciones (admin).

### 6.3 UI / estilo

- Tokens del design-system: `--bg-page`, `--bg-surface`, `--accent-primary`, badges semánticos.
- Tipografía Inter; radios 8–10px; botones min-height 44px.
- Estilos compartidos: `modules/suscripciones/styles/billing-shared.scss`.
- Cada página: `.html` + `.scss` + lógica en `.page.ts` (signals + OnPush).

### 6.4 Services Angular → API

| Service | Base | Métodos |
|---------|------|---------|
| `SuscripcionApiService` | `/api/v1/suscripciones` | alta, mia, cancelar, reintentarCobro, solicitudes CRUD/approve/reject |
| `PlanApiService` | `/api/v1/suscripciones/planes` | listar, crear, actualizar |
| `MetodoPagoApiService` | `/api/v1/suscripciones/metodos-pago` | listar, registrar |
| `FacturaApiService` | `/api/v1/suscripciones/facturas` | listar, obtener |

Todas las mutaciones envían `Idempotency-Key: crypto.randomUUID()`.

### 6.5 Mapa pantalla → request

| Acción en UI | Request |
|--------------|---------|
| Contratar plan (sin suscripción) | `POST /suscripciones` `{idplan}` |
| Cancelar | `POST /suscripciones/mia/cancelar` `{motivocancelacion}` |
| Reintentar cobro | `POST /suscripciones/mia/reintentar-cobro` |
| Guardar método | `POST /suscripciones/metodos-pago` `{tipo, datos_pasarela}` |
| Enviar cambio de plan | `POST /suscripciones/solicitudes-cambio-plan` |
| Aprobar / rechazar | `POST .../aprobar` · `POST .../rechazar` |
| Ver facturas | `GET /suscripciones/facturas` · detalle `GET .../{id}` |
| Catálogo | `GET /suscripciones/planes?solo_activos=true` |

---

## 7. Archivos clave (inventario)

### Backend (nuevos / relevantes)

- `backend/apps/suscripciones/**` (app completa)
- `backend/core/repositories/suscripciones/**`
- `backend/core/repositories/soporte/suscripcion_repository.py` (wrapper)
- `backend/apps/suscripciones/tests/**`
- `backend/config/settings.py`, `urls.py`
- `backend/conftest.py` (seeds + kafka mirror + fixtures)

### Frontend

- `frontend/src/app/modules/suscripciones/**`
- `frontend/src/app/shared/layout/nav-links.ts`
- `frontend/src/app/app.routes.ts`

### Spec / contrato

- `specs/.../subscriptions-and-billing/{spec,plan,tasks,data-model,research,quickstart}.md`
- `contracts/subscriptions-and-billing.openapi.yaml`

---

## 8. Cómo verificar (checklist)

### Backend

```bash
cd backend
pytest apps/suscripciones -m "not integration"
# Esperado: 62 passed
```

### Frontend

```bash
cd frontend
npx ng build --configuration=development
# Abrir app logueado como Cliente (user seed id=3) → sidebar Suscripciones
```

### Manual API (PowerShell / curl)

1. Login → JWT Proveedor.
2. `GET /api/v1/suscripciones/mia` → ver `Activa` + `acceso_permitido`.
3. `POST /api/v1/suscripciones/metodos-pago` con tarjeta de prueba.
4. `python manage.py run_facturacion_mensual_job` → factura + cobro.
5. Forzar fallos (`BILLING_SIMULATOR_FAIL_RATE` o `force_fail` en tests) hasta `Suspendida`.
6. Reintentar cobro desde UI o `POST .../reintentar-cobro`.
7. Downgrade a plan inferior → Admin aprueba en `/suscripciones/aprobaciones-downgrade`.

### Seguridad / calidad a revisar

- [ ] No aparece PAN/CVV en respuestas ni en Pinot (`ultimosdigitos` + `tokenpasarela` sí).
- [ ] Proveedor no ve facturas de otro `idcliente`.
- [ ] Admin no puede POST alta/método sin ser admin_local (permisos Proveedor).
- [ ] Replay con mismo `Idempotency-Key` no duplica create exitoso (cache 201).
- [ ] Soporte SLA sigue resolviendo `idplan` vía wrapper Title Case (`Activa`).

---

## 9. Diferencias importantes vs stubs previos

| Antes | Ahora |
|-------|-------|
| Páginas con `<ul>` mínimo | HTML/CSS completo (KPIs, tablas, forms, badges, skeleton) |
| Sin tabs ni sidebar | Shell de tabs + grupo sidebar **Suscripciones** |
| GET solicitudes solo Admin | Proveedor lista las suyas; Admin lista/filtra todas |
| Upgrade quedaba Pendiente | Upgrade auto-aprobado por orden de `nivel` |
| `mia` sin nombre de plan | Incluye `plan_nombre` + `nivel` |

---

## 10. Fuera de alcance / notas MVP

- Pasarela real (solo `SimuladorPasarela`).
- Impuestos / notas de crédito / anulación fiscal compleja.
- Cron real en producción (hay management commands; scheduling ops aparte).
- Edición admin de catálogo desde UI (API PATCH existe; pantalla admin de CRUD planes no se construyó — catálogo es lectura).
- Warnings Sass `@import` en shared styles (compatibles; migrable a `@use` después).

---

**Conclusión para verificación:** el módulo está cableado backend↔frontend con contrato OpenAPI, estados Title Case, Kafka-only writes, UI usable en el shell autenticado y suite de tests verde. Usa este documento como mapa de endpoints y pantallas al recorrer la app.

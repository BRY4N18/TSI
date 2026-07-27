# Avance: Portal público de planes (RF-CPP-000)

**Feature Spec Kit:** `commercial-pipeline-prospects`  
**Módulo:** Ventas-CRM  
**Fecha del avance:** 2026-07-26  
**Requisito:** RF-CPP-000 — Consultar catálogo público de planes  
**Alias documental:** CU-O123 (ID canónico oficial **aún no** asignado en `module-map.md`)  
**Ruta de este documento:** `avances-spec/`

---

## 1. Resumen ejecutivo

Se incorporó al embudo comercial un **paso previo de solo lectura**: el Visitante (sin sesión, sin JWT) puede consultar el catálogo de planes activos almacenado en `Dim_Plan` (tabla propiedad de **Suscripciones-Facturación**).

| Qué sí hace | Qué no hace |
|-------------|-------------|
| Lista planes con `activo=true` | Crear / editar / desactivar planes |
| Expone nombre, precio, límites, nivel y severidades derivadas | Escribir en Kafka (`Dim_Plan_topic`) |
| Sirve UI pública en `/ventas-crm/planes` | Exigir login o seleccionar plan obligatorio en el registro |
| Enlaza CTA al registro de prospecto (`RF-CPP-001`) | Persistirse `idplan` en `Dim_Prospecto` |

**Flujo de negocio:**

```text
Visitante → GET /planes (catálogo) → (opcional) CTA → POST /prospectos (registro)
```

---

## 2. Origen en Spec / Plan / Tasks

| Artefacto | Cambio |
|-----------|--------|
| `specs/.../commercial-pipeline-prospects/spec.md` | RF-CPP-000, actor Visitante, CA-CPP-000, §13 `GET /planes`, dependencia lectura `Dim_Plan` |
| `plan.md` / `research.md` (Decision 10) / `data-model.md` / `quickstart.md` §0 | Diseño de lectura Pinot + mapa nivel→severidades |
| `contracts/commercial-pipeline-prospects.openapi.yaml` | Path `GET /ventas-crm/planes` + schema `PlanPublico` |
| `tasks.md` | US8 / T070–T086 (implementadas) |

Antes esto estaba en **§15 Fuera de alcance**; ahora es requisito del embudo.

---

## 3. API HTTP

### 3.1 Endpoint

| Campo | Valor |
|-------|--------|
| **Método** | `GET` |
| **URL** | `/api/v1/ventas-crm/planes` |
| **Auth** | **Ninguna** (`AllowAny`, `authentication_classes = []`) |
| **Body request** | No aplica (sin body) |
| **Query params** | Ninguno en este alcance |
| **Headers requeridos** | Ninguno (`Authorization` no se exige ni se usa) |

### 3.2 Ejemplo de llamada

```http
GET /api/v1/ventas-crm/planes HTTP/1.1
Host: localhost:8000
Accept: application/json
```

```bash
curl -s http://localhost:8000/api/v1/ventas-crm/planes
```

### 3.3 Respuesta exitosa (`200`)

Envelope estándar del proyecto (`success_response`):

```json
{
  "data": [
    {
      "idplan": 1,
      "nombre": "Básico",
      "precio": 49.0,
      "limites": "{\"unidades\": 5}",
      "nivel": "Básico",
      "severidades_desbloqueadas": ["Baja"]
    },
    {
      "idplan": 2,
      "nombre": "Profesional",
      "precio": 149.0,
      "limites": "{\"unidades\": 25}",
      "nivel": "Profesional",
      "severidades_desbloqueadas": ["Baja", "Media"]
    },
    {
      "idplan": 3,
      "nombre": "Empresarial",
      "precio": 399.0,
      "limites": "{\"unidades\": 100}",
      "nivel": "Empresarial",
      "severidades_desbloqueadas": ["Baja", "Media", "Alta"]
    }
  ]
}
```

**Catálogo vacío** (ningún plan activo): sigue siendo `200` con `data: []` (no es error de negocio).

### 3.4 Campos de cada ítem (`PlanPublico`)

| Campo | Tipo | Origen | Notas |
|-------|------|--------|-------|
| `idplan` | number (int) | `Dim_Plan.idplan` | PK |
| `nombre` | string | `Dim_Plan.nombre` | Nombre comercial del plan |
| `precio` | number (double) | `Dim_Plan.precio` | Precio del plan |
| `limites` | string | `Dim_Plan.limites` | STRING canónico del esquema; a menudo JSON serializado (ej. `{"unidades": 25}`). Si viene `null` en Pinot, la API envía `""` |
| `nivel` | string | `Dim_Plan.nivel` | Valor crudo (Básico / Profesional / Empresarial) |
| `severidades_desbloqueadas` | string[] | **Derivado** en servicio | No es columna física. Valores: `Baja`, `Media`, `Alta` |

### 3.5 Lo que la API **no** envía / no hace

- No incluye planes con `activo=false`.
- No envía `fecha_actualizacion` ni campos internos no listados.
- No acepta `POST`/`PUT`/`PATCH`/`DELETE` en este path.
- No publica eventos Kafka.
- No exige ni valida JWT (si el cliente manda Bearer, se ignora porque no hay autenticación en la vista).

### 3.6 Errores

| Situación | Comportamiento |
|-----------|----------------|
| Fallo inesperado en servicio/repo | Pasa por `crm_error` (mapeo de excepciones de dominio si aplica; genéricas se re-lanzan) |
| Lista vacía | `200` + `data: []` |

No hay códigos de negocio específicos tipo `409` en este endpoint (es solo lectura).

---

## 4. Lógica de negocio (backend)

### 4.1 Capas (Vista → Servicio → Repositorio)

```text
GET /ventas-crm/planes
        │
        ▼
PlanListView                    apps/ventas_crm/views/plan_views.py
        │
        ▼
ConsultaPlanesPublicosService   apps/ventas_crm/services/consulta_planes_publicos_service.py
        │
        ▼
PlanLecturaRepository           core/repositories/ventas_crm/plan_lectura_repository.py
        │
        ▼
PinotClient.query(...)          SELECT * FROM Dim_Plan WHERE activo = true ORDER BY idplan
```

### 4.2 Repositorio — `PlanLecturaRepository`

**Archivo:** `backend/core/repositories/ventas_crm/plan_lectura_repository.py`

- Solo método de lectura: `list_activos()`.
- **No** tiene `create`, `update`, `publish`, ni `KafkaWriter`.
- Query Pinot:

```sql
SELECT * FROM Dim_Plan WHERE activo = true ORDER BY idplan
```

### 4.3 Servicio — mapa `nivel` → severidades (Decision 10)

**Archivo:** `backend/apps/ventas_crm/services/consulta_planes_publicos_service.py`

Normalización: minúsculas + quitar acentos (`Básico` → `basico`).

| `nivel` (canónico) | `severidades_desbloqueadas` |
|--------------------|-----------------------------|
| Básico / Basico | `["Baja"]` |
| Profesional | `["Baja", "Media"]` |
| Empresarial | `["Baja", "Media", "Alta"]` |
| Cualquier otro (ej. `premium`, `gold`) | `[]` — **el plan igual se lista**; se registra warning en log |

### 4.4 Vista — `PlanListView`

**Archivo:** `backend/apps/ventas_crm/views/plan_views.py`

- `authentication_classes = []`
- `permission_classes = [AllowAny]`
- `GET` → `success_response(ConsultaPlanesPublicosService().listar())`

### 4.5 Registro de URL

**Archivo:** `backend/apps/ventas_crm/urls.py`

```python
path("ventas-crm/planes", PlanListView.as_view()),
```

Montado bajo `/api/v1/` (config global del backend).

---

## 5. Datos de prueba (seed / mirror)

**Archivo:** `backend/conftest.py`

Se reemplazó el plan único `Premium` / `nivel=premium` por semillas canónicas:

| idplan | nombre | nivel | activo | precio (ejemplo) |
|--------|--------|-------|--------|------------------|
| 1 | Básico | Básico | true | 49.0 |
| 2 | Profesional | Profesional | true | 149.0 |
| 3 | Empresarial | Empresarial | true | 399.0 |
| 4 | Legacy Off | Básico | **false** | 9.0 |

También se añadió en el mock Pinot el routing de consultas `FROM DIM_PLAN` con filtro `activo`.

`Fact_Suscripcion` de tests sigue apuntando a `idplan=1` (ahora Básico).

---

## 6. Frontend (UI + cliente HTTP)

### 6.1 Cliente HTTP

**Archivo:** `frontend/src/app/modules/ventas-crm/services/planes-api.service.ts`

| Método | HTTP | URL |
|--------|------|-----|
| `listar()` | `GET` | `/api/v1/ventas-crm/planes` |

Tipos en `models/prospectos.types.ts`:

```typescript
export type SeveridadPlan = 'Baja' | 'Media' | 'Alta';

export interface PlanPublico {
  idplan: number;
  nombre: string;
  precio: number;
  limites: string;
  nivel: string;
  severidades_desbloqueadas: SeveridadPlan[];
}
```

Spec unitario: `planes-api.service.spec.ts`.

### 6.2 Página visual

| Archivo | Rol |
|---------|-----|
| `pages/catalogo-planes/catalogo-planes.page.ts` | Lógica (signals loading/error/planes, parseo de límites JSON) |
| `pages/catalogo-planes/catalogo-planes.page.html` | Markup completo |
| `pages/catalogo-planes/catalogo-planes.page.scss` | Estilos con tokens del design system (`--bg-page`, `--accent-primary`, badges de severidad, skeleton) |

**Ruta pública (sin login):**

- `http://127.0.0.1:4200/ventas-crm/planes` — registrada en `app.routes.ts` (fuera del shell con `sessionGuard`)
- También `path: 'planes'` en `ventas-crm.routes.ts` (módulo lazy autenticado; la entrada pública principal es la de `app.routes.ts`)

**Estados UI:**

1. **Loading:** 3 skeleton cards  
2. **Error:** mensaje + botón Reintentar  
3. **Vacío:** mensaje + CTA a `/ventas-crm/registro`  
4. **Datos:** grid de cards (nombre, precio USD, chip de nivel, badges de severidad, límites legibles, CTA “Me interesa este plan”)

Los límites JSON se muestran legibles (`unidades: 25`); si no es JSON válido, se muestra el string crudo.

### 6.3 Fix colateral de build

**Archivo:** `detalle-prospecto.page.ts`  
Se corrigió `@else if (prospecto(); as p)` → `@let p = prospecto()!` para que `ng build` compile (el alias `as` fallaba en `@else if` con signals).

---

## 7. Contrato OpenAPI

**Archivo:** `specs/003-operational/Ventas-CRM/commercial-pipeline-prospects/contracts/commercial-pipeline-prospects.openapi.yaml`

- Tag: `Planes`
- `GET /ventas-crm/planes` → `operationId: listarPlanesPublicos`
- `security: []`
- Schema: `PlanPublico` + `PlanesListEnvelope`

---

## 8. Tests añadidos / extendidos

| Archivo | Qué valida |
|---------|------------|
| `tests/repositories/test_plan_lectura_repository.py` | Solo activos; sin métodos de escritura Kafka |
| `tests/services/test_consulta_planes_publicos_service.py` | Mapa severidades + proyección; nivel desconocido → `[]` pero plan incluido |
| `tests/api/test_planes_publicos_contract.py` | Sin JWT → 200; oculta inactivos; lista vacía → 200 |
| `tests/e2e/test_commercial_pipeline_quickstart_e2e.py` | Paso **0** del quickstart (catálogo antes del registro) |
| `planes-api.service.spec.ts` | GET al path correcto |

Comandos útiles:

```bash
cd backend
python -m pytest apps/ventas_crm/tests -k "plan or planes" -q
python -m pytest apps/ventas_crm/tests/e2e/test_commercial_pipeline_quickstart_e2e.py -q
```

---

## 9. Checklist de verificación manual (para ti)

### Backend / API

- [ ] `GET http://localhost:8000/api/v1/ventas-crm/planes` sin header Authorization → `200`
- [ ] En `data[]` solo aparecen planes activos (no “Legacy Off” / `activo=false`)
- [ ] Profesional trae `severidades_desbloqueadas: ["Baja","Media"]`
- [ ] Empresarial trae las tres severidades
- [ ] Confirmar que **no** hay publish a `Dim_Plan_topic` (este path no escribe)

### Frontend

- [ ] Abrir `http://127.0.0.1:4200/ventas-crm/planes` **sin** login
- [ ] Ver topbar TSI, hero, cards con precio y badges
- [ ] CTA lleva a `/ventas-crm/registro`
- [ ] Con API caída / error: mensaje + Reintentar
- [ ] Skeleton visible un instante al cargar

### Spec / trazabilidad

- [ ] RF-CPP-000 documentado como precondición de RF-CPP-001
- [ ] CU-O123 tratado solo como alias (sin inventar O-number en module-map)
- [ ] Administración de planes sigue fuera de alcance (Suscripciones-Facturación)

---

## 10. Inventario de archivos tocados / creados (código)

### Backend (nuevos)

- `backend/core/repositories/ventas_crm/plan_lectura_repository.py`
- `backend/apps/ventas_crm/services/consulta_planes_publicos_service.py`
- `backend/apps/ventas_crm/views/plan_views.py`
- `backend/apps/ventas_crm/tests/repositories/test_plan_lectura_repository.py`
- `backend/apps/ventas_crm/tests/services/test_consulta_planes_publicos_service.py`
- `backend/apps/ventas_crm/tests/api/test_planes_publicos_contract.py`

### Backend (modificados)

- `backend/apps/ventas_crm/urls.py` — ruta `ventas-crm/planes`
- `backend/conftest.py` — seed `Dim_Plan` + mock query
- `backend/apps/ventas_crm/tests/e2e/test_commercial_pipeline_quickstart_e2e.py` — paso 0

### Frontend (nuevos)

- `frontend/src/app/modules/ventas-crm/services/planes-api.service.ts`
- `frontend/src/app/modules/ventas-crm/services/planes-api.service.spec.ts`
- `frontend/src/app/modules/ventas-crm/pages/catalogo-planes/catalogo-planes.page.ts`
- `frontend/src/app/modules/ventas-crm/pages/catalogo-planes/catalogo-planes.page.html`
- `frontend/src/app/modules/ventas-crm/pages/catalogo-planes/catalogo-planes.page.scss`

### Frontend (modificados)

- `frontend/src/app/modules/ventas-crm/models/prospectos.types.ts` — `PlanPublico`
- `frontend/src/app/modules/ventas-crm/ventas-crm.routes.ts`
- `frontend/src/app/app.routes.ts` — ruta pública `/ventas-crm/planes`
- `frontend/src/app/modules/ventas-crm/pages/detalle-prospecto/detalle-prospecto.page.ts` — fix build `@let`

### Spec / docs (contexto)

- Spec, plan, research, data-model, quickstart, OpenAPI, tasks, module-map (#4 menciona lectura `Dim_Plan`)

---

## 11. Alcance explícitamente fuera de este avance

- Alta/edición/desactivación de planes (módulo Suscripciones-Facturación).
- Forzar selección de plan en el registro de prospecto.
- Cobertura mínima formal / P95 de listado en CI (quedan abiertos en quickstart Done when).
- Infra real Pinot `:8099` / Kafka `:9092` / `runserver` — la validación E2E del quickstart usó mirrors in-memory cuando la infra local no estaba arriba.

---

## 12. Cómo probar extremo a extremo (cuando tengas API + front)

1. Backend: `python manage.py runserver 8000` (con Pinot/seed o entorno de tests).
2. Frontend: `npx ng serve --host 127.0.0.1 --port 4200`.
3. Navegador: `http://127.0.0.1:4200/ventas-crm/planes`.
4. Verificar cards ↔ respuesta de `GET /api/v1/ventas-crm/planes`.
5. Clic en CTA → formulario de registro en `/ventas-crm/registro`.

---

*Documento generado para verificación del avance RF-CPP-000 (portal público de planes) sobre `commercial-pipeline-prospects`.*

# Quickstart: Pipeline Comercial y Prospectos

Guía de validación **contract-first** end-to-end para **RF-CPP-000** (catálogo público) + O116 / O117 / O119 / O121 y entrada directa.

**Contrato:** [`contracts/commercial-pipeline-prospects.openapi.yaml`](contracts/commercial-pipeline-prospects.openapi.yaml)  
**Modelo:** [`data-model.md`](data-model.md) · **Plan:** [`plan.md`](plan.md)

## Prerequisites

1. Backend API en `/api/v1` con app `ventas_crm` montada.
2. Kafka topics: `Dim_Prospecto_topic`, `Fact_Asignacion_topic`, `Fact_Pipeline_topic`, `Dim_Cliente_topic` (escritura embudo). **No** se publica a `Dim_Plan_topic` desde este módulo.
3. Pinot ingest operativo para esas tablas **y** `Dim_Plan` (lectura RF-CPP-000).
4. Al menos un plan con `activo=true` y `nivel` ∈ {Básico, Profesional, Empresarial} sembrado en Pinot (o mirror de tests).
5. Roles seed: `Administrador`, `GerenteVentas`, `GerenteCuentasPublicas` (y al menos un usuario activo por pool de prueba).
6. JWT de prueba (login vía `autenticacion-y-rbac`) para Admin y un GerenteVentas (no necesarios para el paso 0).

Base URL ejemplo: `http://localhost:8000/api/v1`

## 0. Catálogo público de planes (RF-CPP-000)

```http
GET /ventas-crm/planes
```

**Sin** header `Authorization`.

**Esperado:** `200` + `data[]` solo planes `activo=true`. Cada ítem incluye `nombre`, `precio`, `limites`, `nivel`, `severidades_desbloqueadas` (p. ej. Profesional → `["Baja","Media"]`). Catálogo vacío → `200` + `data: []`.

**Negativos / checks:**
- Plan con `activo=false` no aparece.
- Ningún evento Kafka a `Dim_Plan_topic` (cero escrituras).
- No requiere JWT.

## 1. Registro público (O116) + asignación automática (O117)

```http
POST /ventas-crm/prospectos
Content-Type: application/json

{
  "nombres": "Ana",
  "apellidos": "Pérez",
  "gmail": "ana.perez.demo@example.com",
  "empresa": "Seguros Demo SA",
  "tipo_organizacion": "Privado",
  "cargo": "Compras",
  "telefono": "+593999000111",
  "como_nos_conocio": "web"
}
```

**Esperado:** `201` + `data.etapa_actual=Nuevo`. Si hay GerenteVentas en pool → `idusuario` no null y `asignacion_automatica.ok=true`. Si pool vacío → `idusuario=null` y `asignacion_automatica.ok=false` (huérfano).

**Negativo:** mismo `gmail` → `409`. Más de 10 POST/min misma IP → `429`.

## 2. Listado / detalle (RF-CPP-008)

```http
GET /ventas-crm/prospectos?limit=20
Authorization: Bearer <token_gerente>
```

**Esperado:** Gerente solo ve prospectos con su `idusuario`. Admin ve todos.

```http
GET /ventas-crm/prospectos/{idprospecto}
Authorization: Bearer <token_gerente>
```

**Negativo:** Gerente ajeno → `403`.

## 3. Pipeline hasta Negociación (O119)

Avance adyacente con optimistic check:

```http
POST /ventas-crm/prospectos/{idprospecto}/pipeline
Authorization: Bearer <token_dueno_o_admin>
Content-Type: application/json

{
  "etapa_nueva": "Contactado",
  "etapa_actual_esperada": "Nuevo",
  "notas": "Primer contacto OK"
}
```

Repetir: Contactado→Calificado→Propuesta→Negociación (actualizando `etapa_actual_esperada`).

**Negativos:** salto `Nuevo`→`Propuesta` → `400`/`409`; retroceso → rechazo; `etapa_nueva=Ganado` → rechazo; `etapa_actual_esperada` obsoleta → `409`.

## 4. Pérdida (opcional)

```http
POST /ventas-crm/prospectos/{idprospecto}/pipeline
Authorization: Bearer <token_dueno_o_admin>
Content-Type: application/json

{
  "etapa_nueva": "Perdido",
  "etapa_actual_esperada": "Contactado",
  "motivo_perdida": "precio"
}
```

**Esperado:** `activo=false`, `motivo_inactividad=perdido`. Reasignación posterior → rechazo.

## 5. Conversión (O121)

Con prospecto en `Negociación`:

```http
POST /ventas-crm/prospectos/{idprospecto}/conversion
Authorization: Bearer <token_dueno_o_admin>
Idempotency-Key: 11111111-1111-1111-1111-111111111111
Content-Type: application/json

{
  "tipo": "Aseguradora",
  "nit_identificacion": "1790000001001",
  "etapa_actual_esperada": "Negociación"
}
```

**Esperado:** `201` con `cliente.estado=Activo`, `estado_onboarding=Pendiente`, `idprospecto` seteado; prospecto `convertido` / `Ganado`.

**Negativos:** NIT ya existente → `409`; etapa ≠ Negociación → rechazo; sin `Idempotency-Key` → `400`.

## 6. Entrada directa (RF-CPP-007)

```http
POST /ventas-crm/clientes/entrada-directa
Authorization: Bearer <token_admin>
Content-Type: application/json

{
  "nombre": "Municipio Demo",
  "razon_social": "GAD Demo",
  "tipo": "Municipio",
  "nit_identificacion": "1760000002002"
}
```

**Esperado:** `201`, `idprospecto=null`. Gerente token → `403`.

## 7. Huérfano → Admin asigna

Si el paso 1 dejó `idusuario=null`:

```http
PATCH /ventas-crm/prospectos/{idprospecto}/asignacion
Authorization: Bearer <token_admin>
Content-Type: application/json

{
  "idusuariogerenteactual": 42,
  "motivo": "pool vacío — asignación inicial",
  "idusuario_esperado": null
}
```

**Negativo:** mismo body con token Gerente → `403`.

## Frontend smoke (tras implementar módulo)

1. Abrir **catálogo público de planes** → ver planes activos + CTA a registro; vacío/error visibles.
2. Abrir formulario público de registro → confirmar mensaje de éxito.
3. Login GerenteVentas → listado solo propios; skeleton/vacío/error visibles.
4. Board/detalle: avanzar etapas; conflicto 409 muestra reintento.
5. Login Admin → entrada directa + asignación de huérfano.

## Done when

- [x] `GET /ventas-crm/planes` responde según RF-CPP-000 / CA-CPP-000 (paso 0)
- [x] Los paths del embudo OpenAPI (1–7 previos) responden según esta guía
- [x] Contract tests verdes contra `commercial-pipeline-prospects.openapi.yaml` (embudo + `/planes`)
- [ ] Cobertura mínima repos ≥85% / services ≥80% / views ≥75% (incl. delta planes)
- [ ] Listado P95 ≤500ms en ambiente de prueba

## Validación E2E (última corrida)

Infra local al momento de la validación: **Pinot `:8099` y Kafka `:9092` no disponibles**; `localhost:8000` sin listener activo.

```bash
cd backend
python -m pytest apps/ventas_crm/tests/e2e/test_commercial_pipeline_quickstart_e2e.py -vv -s
python -m pytest apps/ventas_crm/tests -k "plan or planes" -q
```

Resultado: embudo + **paso 0 RF-CPP-000** PASS (mirrors in-memory).

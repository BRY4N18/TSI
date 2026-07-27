# Quickstart: Notificación de Prospectos a Ventas

Guía de validación **contract-first** end-to-end para O118 / O122 / RF-NV-004.

**Contrato:** [`contracts/notificacion-ventas.openapi.yaml`](contracts/notificacion-ventas.openapi.yaml)  
**Modelo:** [`data-model.md`](data-model.md) · **Plan:** [`plan.md`](plan.md)  
**Dependencia:** registro de prospecto en [`../commercial-pipeline-prospects/`](../commercial-pipeline-prospects/) debe devolver `demo_grant`.

## Prerequisites

1. API `/api/v1` con app `ventas_crm` (pipeline + este feature).
2. Kafka topics: `Fact_Interaccion_Demo_topic`, `Fact_NotificacionVentas_topic`, `Dim_Prospecto_topic`.
3. Pinot ingest para esas tablas.
4. Celery beat con tarea de evaluación cada ≤ 60 s.
5. `core/notificaciones` con EmailNotifier + PushNotifier (Slack **no** requerido).
6. Roles JWT: `Administrador`, `GerenteVentas` (o `GerenteCuentasPublicas`).
7. Secretos: `DEMO_GRANT_SECRET`, `DEMO_SESSION_SECRET`.

Base URL: `http://localhost:8000/api/v1`

## 1. Obtener grant (handoff #04)

```http
POST /ventas-crm/prospectos
Content-Type: application/json

{ ...registro prospecto... }
```

**Esperado:** `201` con `data.idprospecto` y `data.demo_grant` (string firmado).

## 2. Abrir sesión de demo (O118 — primer canje)

```http
POST /ventas-crm/demo/sesiones
Content-Type: application/json

{
  "idprospecto": 123,
  "demo_grant": "<grant_del_paso_1>"
}
```

**Esperado:** `200`, `data.modo=primer_canje`, `demo_session_token`, `demo_expiracion` ISO-8601 UTC (~now+30min). En Pinot: `Dim_Prospecto.demo_expiracion` seteado + evento `inicio_sesion`.

**Negativos:** grant malo → `401`; prospecto inactivo → `403`; id inexistente → `404`.

## 3. Ingestar interacciones

```http
POST /ventas-crm/demo/interacciones
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

Repetir visitas a `precios`/`pricing` (≥3) para disparar `visito_pricing_3x`.

**Esperado:** `201` + `data.idinteraccion`.  
**Negativos:** sin token / tipado user JWT → `401`; >60/min → `429`; demo expirada → `403`.

## 4. Resume (mismo grant, demo activa)

```http
POST /ventas-crm/demo/sesiones
Content-Type: application/json

{
  "idprospecto": 123,
  "demo_grant": "<mismo_grant>"
}
```

**Esperado:** `200`, `modo=resume`, nuevo `demo_session_token`, **misma** `demo_expiracion`, sin segundo `inicio_sesion`.

## 5. Evaluación de reglas (O122 — job)

Esperar ≤ 60 s (o invocar tarea Celery de prueba).

**Con `idusuario` asignado:** fila nueva en `Fact_NotificacionVentas` + envío email/push según regla.  
**Sin `idusuario`:** no hay fila; tras asignar en pipeline (#04) y otra corrida del job (dentro de 7 días de `demo_expiracion`) → se inserta.

**Dedup:** segunda evaluación el mismo día UTC con misma regla → 0 filas nuevas.

## 6. Consultar historial (RF-NV-004)

```http
GET /ventas-crm/notificaciones?limit=20
Authorization: Bearer <token_gerente>
```

**Esperado:** Gerente solo ve `idusuariogerentenotificado` = su id. Admin ve todas.

**UI:** skeleton → datos | vacío accionable | error con reintento.

## 7. Checks rápidos de contrato

| Caso | Esperado |
|------|----------|
| Interacción con JWT de usuario (no demo) | 401 |
| `canal` inválido en datos internos / test de servicio | rechazo |
| Job con regla slack (si se fuerza) | error explícito canal no disponible; sin fallback email |
| SLA | INSERT notificación ≤ 2 min tras cumplimiento (CA-NV-004) |

## Done when (checklist)

- [x] `POST /prospectos` devuelve `demo_grant` verificable
- [x] `POST /demo/sesiones` primer canje + resume con misma `demo_expiracion`
- [x] `POST /demo/interacciones` con Bearer `typ=demo_session` (user JWT → 401)
- [x] Job `run_evaluacion_reglas_demo` crea `Fact_NotificacionVentas` (dedup día UTC; slack → error)
- [x] `GET /notificaciones` filtra por gerente; admin ve todas
- [x] UI: rutas `/ventas-crm/demo` y `/ventas-crm/notificaciones` + interceptor demo
- [x] Suite pytest `repository|service|api` de notificacion-ventas verde

## Validación E2E (última corrida)

Infra local al momento de la validación: **Pinot `:8099` y Kafka `:9092` no disponibles**; `localhost:8000` sin listener activo.

Se ejecutó el flujo completo del quickstart vía capa API Django + mirrors in-memory (mismo harness que contract tests):

```bash
cd backend
python -m pytest apps/ventas_crm/tests/e2e/test_notificacion_ventas_quickstart_e2e.py -vv -s
```

Resultado: **PASS** (pasos 1–6 + negativos grant/JWT + dedup + listado gerente/admin).  
Reglas disparadas: `tiempo_seccion_precios_5min`, `visito_pricing_3x`. Job 2ª corrida: `created=0` (dedup).

Cuando Pinot/Kafka y `runserver` estén arriba, repetir los mismos HTTP calls contra `http://localhost:8000/api/v1`.

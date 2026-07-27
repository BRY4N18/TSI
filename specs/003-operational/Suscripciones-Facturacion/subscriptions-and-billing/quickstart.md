# Quickstart — Suscripciones y Facturación

Guía de validación end-to-end **contract-first** para RF-SUSF-001…010.

## Prerrequisitos

- Backend Django con JWT de `cuentas_clientes` operativo.
- Kafka + Pinot (o fakes de test como en `conftest.py`) con topics del data-model.
- Contrato: `contracts/subscriptions-and-billing.openapi.yaml`.
- Dependencias: cliente `Dim_Cliente` activo; roles Proveedor y Administrador.
- Zona horaria de jobs: `America/Guayaquil`. Env: `BILLING_SIMULATOR_FAIL_RATE=0`.

## Endpoints clave (base `/api/v1`)

| Método | Path | CU/RF |
|--------|------|-------|
| POST | `/suscripciones` | O111 alta |
| GET | `/suscripciones/mia` | estado + acceso |
| POST | `/suscripciones/mia/cancelar` | O110 |
| POST | `/suscripciones/mia/reintentar-cobro` | O105 |
| GET/POST | `/suscripciones/metodos-pago` | O101 |
| POST | `/suscripciones/solicitudes-cambio-plan` | O104 |
| POST | `/suscripciones/solicitudes-cambio-plan/{id}/aprobar` | O104 admin |
| POST | `/suscripciones/solicitudes-cambio-plan/{id}/rechazar` | O104 admin |
| GET/POST | `/suscripciones/planes` | O106 admin |
| PATCH | `/suscripciones/planes/{idplan}` | O106 admin |
| GET | `/suscripciones/facturas` | O108 |

Headers: `Authorization: Bearer <jwt>`, escrituras con `Idempotency-Key`.

## Escenarios de validación

### A — Alta + método + primera factura

1. Login Proveedor → `POST /suscripciones` con `idplan` activo, `renovacionautomatica=true`.
2. Esperado: `201`, `Fact_Suscripcion.estado=Activa`, `Dim_Cliente.plan_suscripcion` = nombre del plan.
3. `POST /suscripciones/metodos-pago` (si no había método) → único `activo=true`.
4. Si el alta ya tenía método: existe `Fact_Factura` del `periodo` actual `Pagada` o `Pendiente` según simulador.

### B — Upgrade autoaprobado

1. `POST /suscripciones/solicitudes-cambio-plan` Básico→Profesional.
2. Esperado: solicitud `Aprobada`, `idplan`/`precio` actualizados; factura del ciclo en curso intacta.

### C — Downgrade + admin

1. Solicitud Empresarial→Profesional → `Pendiente`.
2. Admin `POST .../aprobar` o `.../rechazar`.
3. Segunda solicitud con otra `Pendiente` → `400` (RN-023).

### D — Dunning → suspensión → reintento

1. Forzar fallos de pasarela (`force_fail` / fail-rate) hasta `reintentos=3` → `Fallida` → suscripción `Suspendida` (sin acceso).
2. Proveedor actualiza método o `POST .../reintentar-cobro`.
3. Éxito → `Pagada` + `Activa`.

### E — Cancelación

1. `POST /suscripciones/mia/cancelar` con motivo.
2. Esperado: `Cancelada`, `renovacionautomatica=false`, acceso hasta `fecha_fin`; tras job mantenimiento `activo=false`.

### F — Historial

1. `GET /suscripciones/facturas` → orden `fecha_emision` desc; envelope `{data, meta.pagination}`; ≤3 s.

## Jobs (management commands)

Desde `backend/`:

```bash
python manage.py run_facturacion_mensual_job
python manage.py run_dunning_job
python manage.py run_renovacion_job
python manage.py run_mantenimiento_activo_job
```

- `facturacion_mensual_job` — una factura por elegible/periodo + cobro día 0.
- `dunning_job` — reintentos D+3 / D+5.
- `renovacion_job` — extiende ciclo + factura + cobro.
- `mantenimiento_activo_job` — `activo=false` en canceladas vencidas.

## Tests

```bash
cd backend
pytest apps/suscripciones -m "not integration"
```

Markers: `unit`, `repository`, `service`, `api` (ver `pytest.ini` / `testing.md`).

## Checklist rápido

- [x] OpenAPI validado contra respuestas reales (contract tests).
- [x] Ningún INSERT/UPDATE directo a Pinot en repos.
- [x] Proveedor no lee facturas de otro `idcliente`.
- [x] Sin PAN/CVV en payloads persistidos.
- [x] Guards Angular bloquean rutas admin a Proveedor y viceversa.

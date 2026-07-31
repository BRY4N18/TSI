# Quickstart — Suscripciones y Facturación

Guía de validación end-to-end **contract-first** para RF-SUSF-001…010.

## Prerrequisitos

- Backend Django con JWT de `cuentas_clientes` operativo.
- Kafka + Pinot (o fakes de test como en `conftest.py`) con topics del data-model.
- Contrato: `contracts/subscriptions-and-billing.openapi.yaml`.
- Dependencias: cliente `Dim_Cliente` activo; roles Proveedor, Administrador y `DirectorEstrategia`.
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
| GET/POST | `/suscripciones/planes` | O106 — GET: Proveedor/Admin/Director; POST: Director |
| PATCH | `/suscripciones/planes/{idplan}` | O106 — Director |
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

### G — Catálogo de planes (Director de Estrategia)

1. Seed: `python /app/scripts/seed_demo_director_estrategia.py` (esperar indexación Pinot ~30–60 s).
2. Login demo: `elena.nunez.estrategia@demo.tsi.com` / `password123` (JWT rol `DirectorEstrategia`) → home `/suscripciones/catalogo-planes`.
3. `POST /suscripciones/planes` con `nombre`, `precio`, `limites`, `nivel`, `Idempotency-Key` → `201`.
4. `PATCH /suscripciones/planes/{idplan}` desactivar (`activo=false`) → plan no aparece en listados `activo=true` / `solo_activos=true`; suscripciones existentes intactas.
5. Login **Administrador** → mismo POST → `403`.
6. UI: `/suscripciones/catalogo-planes` muestra crear/desactivar solo para Director; Admin ve aprobaciones, no crear plan.

### H — Listado paginado + filtros (RNF-SUSF-005a / CA-016)

1. Con JWT Director: `GET /api/v1/suscripciones/planes?limit=20` → `200`, `data.length ≤ 20`, `meta.pagination.limit=20`, `meta.pagination.next_cursor` presente solo si hay más.
2. Si hay `next_cursor`: `GET ...?cursor=<next>&limit=20` → siguiente página sin solapar ids de la anterior.
3. `GET ...?q=<fragmento_nombre>&limit=20` → solo planes cuyo nombre contiene el fragmento.
4. `GET ...?activo=false&limit=20` (Director) → solo inactivos; Proveedor con `activo=false` o dump forzado → no expone inactivos ajenos a la regla de rol (no-Director → activos).
5. `GET ...?nivel=Profesional&limit=20` → solo ese nivel.
6. **Negativo de diseño:** la implementación **no** debe cargar el catálogo completo en memoria para armar la página (verificar en code review / test de repo).

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
- [x] POST/PATCH planes solo `DirectorEstrategia` (T091); Admin 403 (Phase 12).
- [x] UI CRUD planes + redirect `/suscripciones` por rol (T093–T094).

# Implementation Plan: Monitoreo y Facturación de API

**Capa**: `api-monitoring-and-billing/backend` | **Date**: 2026-08-08 | **Spec**: `specs/003-operational/Partners-API/api-monitoring-and-billing/backend/spec.md`

**Input**: Feature specification desde `backend/spec.md` (Clarifications Session 2026-08-08 integradas; decisiones D1 y D2 cerradas y aplicadas).
**Capa hermana (UI):** `../frontend/` — ver [`../api-monitoring-and-billing.md`](../api-monitoring-and-billing.md).
**Módulo previo:** [`../../partner-api-onboarding/`](../../partner-api-onboarding/) (#07) — sin partners con credenciales no hay nada que medir.

## Summary

Implementar la medición, el control de límites y la tarificación del consumo de API con enfoque **contract-first**, en **dos superficies separadas**: la **API de datos** que el partner consume (autenticada por credencial, medida por middleware) y la **API de gestión** (métricas, consola de logs y reportes, autenticada por JWT). Más dos procesos periódicos: alertas de cuota y corte mensual de excedente con reintentos escalonados.

Cubre CU-O51, CU-O52, CU-O53 y CU-O54. **Es el módulo que convierte la integración en dinero**: el SRS declara que la línea de ingresos por consumo de datos «está vendida en el plan y no es exigible» hasta que exista este componente.

## Traceability

- **Objetivo operacional:** hacer exigible la línea de ingresos por consumo de datos.
- **CU cubiertos:** CU-O51, CU-O52, CU-O53, CU-O54 (catálogo canónico §5.5).
- **RF del catálogo:** RF-O51.1–3, RF-O52.1–3, RF-O53.1–3, RF-O54.1–4 — **12 de 13 sin reservas**; RF-O53.2 es divergencia documentada a favor del SRS.
- **Dependencias:** `partner-api-onboarding` (#07), `autenticacion-y-rbac`, `subscriptions-and-billing`, `incorporacion-clientes`, `seguimiento-cierre-de-casos` (solo lectura).
- **Consumidor downstream:** `partner-access-management` (#09) — la mora que dispara la suspensión nace de las facturas de excedente que emite este módulo.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: Django 5 + DRF (autenticación propia por credencial, throttling propio por partner), `bcrypt` (verificación de credenciales), JWT RS256 (API de gestión)

**Storage**: Apache Pinot (lectura y agregación), Kafka (único canal de escritura)

**Testing**: pytest + contract tests OpenAPI, **más verificación obligatoria contra Pinot real** (`database/verifica_monitoreo_api.py`, a crear) — ver Riesgos

**Target Platform**: Linux containerizado (API)

**Project Type**: Web application (esta capa: solo backend)

**Performance Goals**: `GET /datos/*` p95 ≤ 2 s con registro activo (RNF-APM-002); **decenas de escrituras/segundo sostenidas** (RNF-APM-003)

**Constraints**: API `/api/v1/`, envelope estándar, paginación por cursor, sin INSERT directo a Pinot, **sin `NULL`** (centinelas), **toda agregación con `entorno='Producción'` y `LIMIT` explícito**

**Scale/Scope**: **el flujo de mayor frecuencia del departamento**; fuera de la cadena crítica de despacho

## Constitution Check

*GATE: debe pasar antes de Phase 0. Re-evaluado tras Phase 1.*

| Característica ISO 25010 | Estado | Justificación |
|---|---|---|
| Functional Suitability | PASS | CU-O51/O52/O53/O54 + CA-APM-001–016 trazables. 12/13 RF del catálogo sin reservas |
| Reliability | PASS | **Muy relevante.** Reintentos escalonados por estado persistido (sobreviven a reinicios) y fallo de medición que no tumba la API. Comportamiento ante fallo definido antes de `/plan`, como exige el Principio II |
| Performance Efficiency | PASS | RNF-APM-002 y RNF-APM-003 con umbrales y método de medición en `quickstart.md` §6 |
| Interaction Capability | PARCIAL | Alcance BE limitado a RF-APM-007/008/009. El detalle de la consola vive en `../frontend/spec.md` |
| Security | PASS | **Dominante.** Es la única superficie que entrega datos de siniestralidad a terceros: autenticación por credencial, nivel de acceso, filtro de zonas fail-closed, auditoría por credencial |
| Compatibility | PASS | Contract-first con dos superficies y esquemas de autenticación separados; su documentación versionada es CU-O50 (#07) |
| Maintainability | PASS | Propiedad de escritura repartida y documentada frente a #07, #09, Suscripciones y Soporte |
| Flexibility | PASS | Cupo, tarifa y umbrales configurables (RNF-APM-007) |
| Safety | **NO APLICA** | Fuera de la cadena crítica registro → asignación → despacho → confirmación. La API es de **solo lectura sobre casos ya cerrados**: un fallo impide cobrar o medir, pero no retrasa la atención de ninguna víctima ni influye en severidad o asignación de unidades. Declarado explícitamente conforme a la Golden Rule |

**Post-Design Gate:** PASS — sin violaciones ni excepciones abiertas.

**Tie-Breaker invocado:** Reliability vs Functional Suitability en RF-APM-004 (si falla la medición, ¿se rechaza la petición o se responde igual?). Resuelto a favor de **responder al partner**, con el fallo registrado para reconciliación. Trade-off documentado en `research.md`.

## Project Structure

### Documentation (this feature)

```text
specs/003-operational/Partners-API/api-monitoring-and-billing/
├── api-monitoring-and-billing.md       # índice del módulo
├── backend/
│   ├── spec.md
│   ├── plan.md
│   ├── research.md
│   ├── data-model.md
│   ├── quickstart.md
│   ├── traceability.md
│   ├── checklists/requirements.md
│   ├── contracts/
│   │   └── api-monitoring-and-billing.openapi.yaml
│   └── tasks.md                        # pendiente: /speckit-tasks
└── frontend/                           # Interaction Capability (stub)
```

### Source Code (repository root)

```text
backend/
├── apps/
│   └── partners/                              # app compartida del departamento (creada en #07)
│       ├── authentication.py                  # CredencialAPIAuthentication (bcrypt)
│       ├── throttling.py                      # PartnerRateThrottle -> 429 (§ 15 D2)
│       ├── middleware/
│       │   └── registro_consumo.py            # mide y publica; NUNCA rompe la respuesta
│       ├── views/
│       │   ├── datos_views.py                 # CU-O51 — API de datos (credencial)
│       │   ├── metricas_views.py              # CU-O52 — métricas del partner (JWT)
│       │   ├── consola_views.py               # CU-O52 — logs en tiempo real (JWT)
│       │   └── reportes_views.py              # CU-O52 — reporte mensual (JWT)
│       ├── services/
│       │   ├── consumo_datos_service.py       # CU-O51 — nivel de acceso + zonas
│       │   ├── registro_consumo_service.py    # CU-O52 — escribe las dos filas
│       │   ├── metricas_consumo_service.py    # CU-O52 — agregaciones
│       │   ├── limites_consumo_service.py     # CU-O53 — comparación y alertas
│       │   └── tarificacion_excedente_service.py  # CU-O54 — cálculo, no duplicación, reintentos
│       └── jobs/
│           ├── alertas_cuota_job.py           # CU-O53
│           └── facturacion_excedente_job.py   # CU-O54 (hermano del de Suscripciones)
└── core/
    └── repositories/
        └── partners/
            ├── api_integracion_repository.py   # Fact_APIIntegracion (escritura + agregación)
            ├── log_llamada_repository.py       # Fact_LogLlamadaAPI
            └── estado_integracion_repository.py
```

**Structure Decision:** se reutiliza la app `partners/` creada en #07, con servicios separados por caso de uso. La **emisión** del documento de factura usa `FacturaRepository` de Suscripciones: este módulo calcula y decide, Suscripciones persiste.

## Phase 0: Research (completado)

Ver `research.md` — 12 decisiones: contract-first con dos superficies, autenticación por credencial, registro que no bloquea, middleware único de medición, agregación en tiempo de consulta, job propio hermano del de Suscripciones, reintentos por estado persistido, no duplicación contra Pinot, throttle con la infraestructura actual, alertas evaluadas en job, nivel de acceso y zonas por composición, y siembra de `Dim_EstadoIntegracion`.

## Phase 1: Design & Contracts (completado)

### Contrato REST — dos superficies separadas

Artefacto: `contracts/api-monitoring-and-billing.openapi.yaml` — **4 paths, 7 schemas**, validado sin referencias rotas.

| Superficie | Endpoint | Auth | Consumidor |
|---|---|---|---|
| **Datos** | `GET /datos/accidentes` | `credencialAuth` | El sistema del partner |
| **Gestión** | `GET /partners/{id}/metricas` | `bearerAuth` | Partner de integración (solo el suyo) |
| **Gestión** | `GET /logs-api` | `bearerAuth` | Desarrollador de APIs |
| **Gestión** | `GET /reportes-consumo` | `bearerAuth` | Cliente / Administrador |

**Invariante verificable:** solo `/datos/*` lleva `credencialAuth`. Si un endpoint de gestión lo llevara, una credencial de máquina entraría al portal; si `/datos/*` llevara `bearerAuth`, el partner necesitaría sesión humana. Comprobación automatizada en `quickstart.md` §1.

### Backend — mapeo Vista → Servicio → Repositorio

| Vista / proceso | Servicio | Repositorio / externo |
|---|---|---|
| `ConsultarAccidentesView` (credencial) | `ConsumoDatosService` | Repos de Emergencias (**solo lectura**), `Dim_Plan`, `Dim_Preferencias_Cliente` |
| *(middleware)* `registro_consumo` | `RegistroConsumoService` | `ApiIntegracionRepository`, `LogLlamadaRepository`, `EstadoIntegracionRepository` |
| `MetricasPartnerView` | `MetricasConsumoService` | `ApiIntegracionRepository` (agregación) |
| `ConsolaLogsView` | `MetricasConsumoService` | `LogLlamadaRepository` |
| `ReporteConsumoView` | `MetricasConsumoService` | `ApiIntegracionRepository` (agregación) |
| *(job)* `alertas_cuota_job` | `LimitesConsumoService` | `ApiIntegracionRepository`, `PartnerRepository`, notificación |
| *(job)* `facturacion_excedente_job` | `TarificacionExcedenteService` | `ApiIntegracionRepository`, `PlanReadRepository`, **`FacturaRepository` (Suscripciones)** |

**Flujo de una petición de datos:**

```text
GET /datos/accidentes
  → CredencialAPIAuthentication: bcrypt contra Dim_CredencialAPI
        inexistente / activo=false / vencida ──► 401   (sin consumo)
  → Dim_Partner.activo=false                  ──► 403   (sin consumo)
  → PartnerRateThrottle (limitellamadasminuto)
        superado ──► 429 + Retry-After
                     └─ SÍ log, NO consumo facturable   (§ 15 D2)
  → ConsumoDatosService: severidades del plan ──► 403 si no habilitado
                         zonas contratadas    ──► conjunto vacío si no hay (fail-closed)
  → responder al partner
  → [middleware, fuera del camino crítico, en try/except]
        LogLlamadaRepository.publish()      → Fact_LogLlamadaAPI_topic
        ApiIntegracionRepository.publish()  → Fact_APIIntegracion_topic
        si falla ──► se registra el fallo; la respuesta NO se altera  (RN-APM-005)
```

### Data model

Ver `data-model.md` — dos tablas de escritura de alta frecuencia, el catálogo a sembrar, la escritura cruzada en `Fact_Factura`, los centinelas y los dos flujos completos.

### Validación E2E

Ver `quickstart.md` — escenarios A–N, criterios de salida y el verificador obligatorio contra Pinot.

## Phase 2: Task Decomposition (siguiente comando)

Ejecutar `/speckit-tasks` para producir `tasks.md`:

1. Seed de `Dim_EstadoIntegracion` (bloquea el registro de consumo)
2. Throttle rate por partner en `REST_FRAMEWORK.DEFAULT_THROTTLE_RATES`
3. Contract tests esqueleto desde el OpenAPI
4. Repositorios de consumo + productores Kafka
5. `CredencialAPIAuthentication` + `PartnerRateThrottle` con sus tests de seguridad
6. Middleware de registro (incluido el caso «falla y no rompe»)
7. `ConsumoDatosService` (nivel de acceso + zonas fail-closed)
8. Servicios de métricas, consola y reporte
9. `LimitesConsumoService` + job de alertas
10. `TarificacionExcedenteService` + job de corte con reintentos persistidos
11. `database/verifica_monitoreo_api.py`
12. Tests de integración de los escenarios del quickstart

## Riesgos

| Riesgo | Mitigación |
|---|---|
| **Los tests con doble no ven los defectos de la capa Pinot.** Este módulo vive de agregaciones reales; tres defectos del departamento ya pasaron en verde con mocks (`decisiones-pendientes.md` #18) | `database/verifica_monitoreo_api.py` como criterio de salida obligatorio. `quickstart.md` §5 lista las 6 comprobaciones que solo valen contra Pinot |
| **Doble cobro** por reintento del corte | RF-APM-012: verificación por `id_cliente`+`periodo`+`tipo` antes de emitir, más `Idempotency-Key` como segunda red |
| **Ingreso no cobrado en silencio**: reintentos que mueren con el proceso, o factura de importe cero por tarifa sin configurar | Reintentos por **estado persistido**, no por `sleep` (Decision 7). Centinela `-1.0` que **alerta en vez de facturar cero** (§ 15 D1) |
| **Fuga de datos sensibles**: única superficie que entrega siniestralidad a terceros | Filtro de zonas **fail-closed**, nivel de acceso por severidades, auditoría por credencial en `Fact_LogLlamadaAPI` |
| **Confundir throttle técnico con cuota comercial** | Tabla comparativa en RF-APM-010; el 429 no cuenta como consumo facturable |
| **Coste de bcrypt en cada petición** frente al p95 | Medir con y sin registro (`quickstart.md` §6). Si domina, cachear el resultado de verificación por ventana corta — **nunca** bajar el factor de coste |
| **`LIMIT 10` implícito de Pinot** en agregaciones sin `LIMIT` | Regla explícita en `data-model.md`; incluida en las validaciones transversales del quickstart |

## Deuda técnica declarada

**El throttle por minuto solo es exacto con un proceso.** Django usa `LocMemCache`, que es por proceso: con N procesos el límite efectivo sería N veces mayor. **No bloquea hoy** (el despliegue es de un proceso), pero escalar horizontalmente exigirá un contador compartido. Registrado en § 15 D2 y en `decisiones-pendientes.md` #20.

## Complexity Tracking

Sin violaciones de la constitución que requieran excepción.

## ISO 25010 — Impacto Security y Reliability (características dominantes)

**Security** — es la única superficie que entrega datos de siniestralidad a terceros:

- Autenticación por credencial con bcrypt en cada petición, sin sesión que secuestrar.
- Filtro de zonas **fail-closed**: sin zonas configuradas, conjunto vacío, nunca el completo.
- Nivel de acceso por severidades del plan; conjunto no habilitado devuelve 403, no una lista vacía que el partner confundiría con «no hay datos».
- `Fact_LogLlamadaAPI` **es** la auditoría de acceso: cada entrega queda ligada a la credencial que la originó.

**Reliability** — el dinero depende de que nada se pierda en silencio:

- El fallo de medición no tumba la API, pero **se registra** para reconciliación.
- Los reintentos sobreviven a reinicios porque viven en los datos, no en el proceso.
- Una tarifa sin configurar **alerta**; nunca emite una factura de importe cero.
- La verificación de no duplicación protege del error que el SRS señala como peor que no cobrar.

## Artifacts Generated

| Artefacto | Ruta |
|---|---|
| Spec | `…/api-monitoring-and-billing/backend/spec.md` |
| Plan | `…/api-monitoring-and-billing/backend/plan.md` |
| Research | `…/api-monitoring-and-billing/backend/research.md` |
| Data model | `…/api-monitoring-and-billing/backend/data-model.md` |
| Quickstart | `…/api-monitoring-and-billing/backend/quickstart.md` |
| Traceability | `…/api-monitoring-and-billing/backend/traceability.md` |
| OpenAPI contract | `…/api-monitoring-and-billing/backend/contracts/api-monitoring-and-billing.openapi.yaml` |
| Checklist | `…/api-monitoring-and-billing/backend/checklists/requirements.md` |

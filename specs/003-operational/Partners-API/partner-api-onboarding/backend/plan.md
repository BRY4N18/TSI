# Implementation Plan: Onboarding de Partners API

**Capa**: `partner-api-onboarding/backend` | **Date**: 2026-08-08 | **Spec**: `specs/003-operational/Partners-API/partner-api-onboarding/backend/spec.md`

**Input**: Feature specification desde `backend/spec.md` (Clarifications Session 2026-08-08 integradas; decisiones de esquema D1 y D2 aplicadas y verificadas).
**Capa hermana (UI):** `../frontend/` — ver [`../partner-api-onboarding.md`](../partner-api-onboarding.md).
**Autoridad UI:** Interaction Capability en [`../frontend/spec.md`](../frontend/spec.md). Este plan BE no es superficie de trabajo UI.

## Summary

Implementar el onboarding de partners con enfoque **contract-first**: primero el contrato OpenAPI (`/api/v1/partners/*` y `/api/v1/contrato-integracion`) alineado a `api-standards.md`; luego backend Django/DRF en capas **Vista → Servicio → Repositorio** con escritura exclusiva vía **Kafka**. Cubre CU-O48 (registro y derivación del cupo), CU-O49 (emisión de credenciales nombradas y promoción semiautomática a producción) y CU-O50 (contrato versionado por servicio).

**El módulo es prerrequisito habilitante de los otros dos del departamento**: sin partner incorporado con credenciales, `api-monitoring-and-billing` no tiene consumo que medir y `partner-access-management` no tiene acceso que revocar.

## Traceability

- **Objetivo operacional:** habilitar la línea de ingresos por consumo de datos, que el SRS declara vendida en el plan pero **no exigible** hasta que exista este departamento.
- **CU cubiertos:** CU-O48, CU-O49, CU-O50 (numeración canónica `TSI-Catalogo-CU-RF-RNF.md` §5.5).
- **RF del catálogo:** RF-O48.1–4, RF-O49.1–4, RF-O50.1–3 — los 11, sin huecos.
- **Dependencias:** `autenticacion-y-rbac`, `incorporacion-clientes`, `subscriptions-and-billing`.
- **Consumidores downstream:** `api-monitoring-and-billing` (#08), `partner-access-management` (#09).

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: Django 5 + DRF, JWT RS256 (auth existente), `bcrypt` (hash de secretos, ya usado en `cuentas_clientes`), `secrets` (generación)

**Storage**: Apache Pinot (lectura vía repositorios), Kafka (único canal de escritura)

**Testing**: pytest + contract tests OpenAPI, **más verificación obligatoria contra Pinot real** (`database/verifica_partners.py`) — ver Riesgos

**Target Platform**: Linux containerizado (API)

**Project Type**: Web application (esta capa: solo backend)

**Performance Goals**: emisión de credencial p95 ≤ 2 s (RNF-PON-001, frente al compromiso de 24 h del SRS)

**Constraints**: API `/api/v1/`, envelope estándar, paginación por cursor, idempotencia en escrituras, sin INSERT directo a Pinot, **sin `NULL`** (centinelas explícitos)

**Scale/Scope**: bajo volumen de escritura (registrar un partner es una acción manual de un Administrador); fuera de la cadena crítica de despacho

## Constitution Check

*GATE: debe pasar antes de Phase 0. Re-evaluado tras Phase 1.*

| Característica ISO 25010 | Estado | Justificación |
|---|---|---|
| Functional Suitability | PASS | CU-O48/O49/O50 + CA-PON-001–014 trazables; los 11 RF del catálogo cubiertos |
| Reliability | PASS | Expiración por cálculo perezoso (fail-safe: no depende del job); rechazo de promoción sin pérdida de estado |
| Performance Efficiency | PASS | RNF-PON-001 con umbral declarado y medición en `quickstart.md` §5 |
| Interaction Capability | PARCIAL | Alcance BE limitado a RF-PON-012. La entrega única del secreto es el mayor riesgo de error de usuario del módulo; su tratamiento vive en `../frontend/spec.md` |
| Security | PASS | **Característica dominante.** bcrypt + secreto irrecuperable + bitácora inmutable + control de propiedad en todo endpoint de autoservicio |
| Compatibility | PASS | Contract-first versionado; CU-O50 materializa el Principio VI como funcionalidad de negocio, no solo como documentación |
| Maintainability | PASS | Vista→Servicio→Repositorio; un servicio por caso de uso; propiedad de escritura repartida y documentada frente a los módulos #08 y #09 |
| Flexibility | PASS | Cupo derivado de `Dim_Plan.limites` (configurable, RNF-20); vigencias parametrizadas |
| Safety | **NO APLICA** | Fuera de la cadena crítica registro → asignación → despacho → confirmación. Un partner sin incorporar no retrasa la atención de ninguna víctima, y ningún flujo de este módulo influye en la clasificación de severidad ni en la asignación de unidades. Declarado explícitamente conforme exige la Golden Rule |

**Post-Design Gate:** PASS — sin violaciones ni excepciones abiertas.

**Tie-Breaker invocado:** Security vs Interaction Capability en RN-PON-005 (secreto irrecuperable). Resuelto a favor de **Security** por la excepción de dominio (regla 3: datos sensibles). Trade-off documentado en `research.md`.

## Project Structure

### Documentation (this feature)

```text
specs/003-operational/Partners-API/partner-api-onboarding/
├── partner-api-onboarding.md       # índice del módulo
├── backend/                        # esta capa (dominio + OpenAPI)
│   ├── spec.md
│   ├── plan.md
│   ├── research.md
│   ├── data-model.md
│   ├── quickstart.md
│   ├── traceability.md
│   ├── checklists/requirements.md
│   ├── contracts/
│   │   └── partner-api-onboarding.openapi.yaml
│   └── tasks.md                    # pendiente: /speckit-tasks
└── frontend/                       # Interaction Capability (stub)
```

### Source Code (repository root)

```text
backend/
├── apps/
│   └── partners/                          # app nueva, compartida por los 3 módulos del depto.
│       ├── views/
│       │   ├── partner_views.py           # registro, listado, detalle
│       │   ├── credencial_views.py        # emisión, listado
│       │   ├── promocion_views.py         # solicitud y resolución
│       │   ├── contrato_views.py          # CU-O50
│       │   └── urls.py
│       ├── services/
│       │   ├── registro_partner_service.py         # CU-O48 / RF-PON-001, 002
│       │   ├── asignar_plan_acceso_service.py      # CU-O48 / RF-PON-003
│       │   ├── emitir_credencial_service.py        # CU-O49 / RF-PON-004, 005
│       │   ├── expiracion_credencial_service.py    # CU-O49 / RF-PON-006
│       │   ├── promocion_produccion_service.py     # CU-O49 / RF-PON-007, 008
│       │   ├── consulta_partner_service.py         # RF-PON-012
│       │   ├── contrato_integracion_service.py     # CU-O50 / RF-PON-011
│       │   └── secreto_service.py                  # generación + hash bcrypt
│       ├── jobs/
│       │   └── expiracion_credenciales_job.py      # avisos T-7 y al vencer
│       ├── permissions.py                 # EsAdministrador, EsDesarrolladorAPIs, EsPartner
│       └── tests/
│           ├── api/                       # contract tests OpenAPI
│           └── services/
└── core/
    └── repositories/
        └── partners/
            ├── partner_repository.py
            ├── credencial_repository.py
            ├── historial_acceso_repository.py
            ├── version_contrato_repository.py
            └── plan_read_repository.py    # lectura Fact_Suscripcion + Dim_Plan
```

**Structure Decision:** app Django `partners/` según `project-structure.md`, con servicios separados por caso de uso para que los módulos #08 y #09 no tengan que reabrir archivos de este. Repositorios en `core/repositories/partners/`, compartidos por el departamento.

## Phase 0: Research (completado)

Ver `research.md` — 11 decisiones resueltas: contract-first, capas Django, Kafka-only-write, JWT con rol nuevo y control de propiedad, bcrypt para secretos, unicidad a nivel de aplicación, cupo derivado y congelado, expiración perezosa + job de aviso, centinelas en lugar de `NULL`, versionado por servicio y notificaciones al contacto técnico.

## Phase 1: Design & Contracts (completado)

### Contrato REST (prioridad 1 — contract-first)

Artefacto: `contracts/partner-api-onboarding.openapi.yaml` — **7 paths, 17 schemas**, validado sin referencias rotas.

| Rol | Endpoints |
|---|---|
| Administrador | registro, asignación de plan, listado, detalle, **resolución de promoción (exclusivo)** |
| Desarrollador de APIs | registro, asignación de plan, listado, detalle |
| Partner de integración | emisión de credencial `Sandbox`, listado de sus credenciales, solicitud de promoción, su detalle, contrato de integración — **siempre sobre su propio perfil** |

**Invariante de seguridad del contrato:** `client_secret` existe únicamente en `CredencialCreadaResponse` y `ResolucionProduccionResponse`. El schema `Credencial`, que usan todos los GET, no lo declara. Es verificable automáticamente (`quickstart.md` §1).

### Backend — mapeo Vista → Servicio → Repositorio

| Vista (DRF) | Servicio | Repositorio / externo |
|---|---|---|
| `RegistrarPartnerView` | `RegistroPartnerService` | `PartnerRepository`, `PlanReadRepository`, `HistorialAccesoRepository`, Kafka |
| `ListarPartnersView` / `DetallePartnerView` | `ConsultaPartnerService` | `PartnerRepository`, `CredencialRepository`, `HistorialAccesoRepository` (Pinot read) |
| `AsignarPlanAccesoView` | `AsignarPlanAccesoService` | `PlanReadRepository` (`Fact_Suscripcion` ⋈ `Dim_Plan`), `PartnerRepository`, `HistorialAccesoRepository` |
| `EmitirCredencialView` | `EmitirCredencialService` + `SecretoService` | `CredencialRepository`, `PartnerRepository`, `HistorialAccesoRepository` |
| `ListarCredencialesView` | `ConsultaPartnerService` | `CredencialRepository` |
| `SolicitarPromocionView` | `PromocionProduccionService` | `HistorialAccesoRepository`, notificación |
| `ResolverPromocionView` | `PromocionProduccionService` + `SecretoService` | `CredencialRepository`, `HistorialAccesoRepository`, notificación |
| `ContratoIntegracionView` | `ContratoIntegracionService` | `VersionContratoRepository` (⋈ `Dim_Servicio`) |
| *(job)* `expiracion_credenciales_job` | `ExpiracionCredencialService` | `CredencialRepository`, `HistorialAccesoRepository`, notificación |

**Flujo de escritura (emisión de credencial):**

```text
POST /partners/{id}/credenciales
  → verificar propiedad (idpartner del path ⟷ idcliente del token)   → 403
  → PartnerRepository.get()   →  activo=true (409)  y  planapi <> '' (409)
  → CredencialRepository.find_activas(idpartner, entorno)  →  nombre duplicado (409)
  → SecretoService.generar()        # secrets.token_urlsafe(32)
  → SecretoService.hash()           # bcrypt
  → CredencialRepository.publish_create()   → Dim_CredencialAPI_topic   (SOLO el hash)
  → HistorialAccesoRepository.publish()     → Fact_HistorialAccesoPartner_topic
  → Response 201 construida EN MEMORIA con el secreto en claro
      (nunca releer de Pinot: la ingesta tarda 5–15 s)
```

### Data model

Ver `data-model.md` — cuatro entidades, sus centinelas, estados derivados, validaciones, topics Kafka y mapeo API ↔ persistencia.

### Validación E2E

Ver `quickstart.md` — escenarios A–L y criterios de salida.

## Phase 2: Task Decomposition (siguiente comando)

No generado por este plan. Ejecutar `/speckit-tasks` para producir `tasks.md` ordenado:

1. Alta del rol «Partner de integración» y `permissions.py` (bloquea todo lo demás)
2. Contract tests esqueleto desde el OpenAPI
3. Repositorios + productores Kafka
4. `SecretoService` (generación + bcrypt) con sus tests de seguridad
5. Servicios de dominio: registro → plan → emisión → promoción → expiración
6. Vistas DRF + control de propiedad
7. `ContratoIntegracionService` y siembra de `Dim_VersionContratoAPI`
8. Job de expiración y avisos
9. Tests de integración de los escenarios del quickstart

## Riesgos

| Riesgo | Mitigación |
|---|---|
| **Los tests con doble no ven los defectos de la capa Pinot.** Tres defectos reales de este departamento pasaron en verde hasta probarlos contra la base real (`decisiones-pendientes.md` #18) | `verifica_partners.py` es criterio de salida **obligatorio**, no opcional. Ninguna regla que dependa de un valor ausente se da por buena solo con `pytest` |
| **Fuga del secreto en claro** por logs, trazas o el evento Kafka | Al topic solo viaja el hash. El quickstart incluye una búsqueda explícita del secreto en logs (esperado: 0 ocurrencias) |
| **Falta el control de propiedad** en endpoints de autoservicio — ya ocurrió tres veces en el proyecto (Red Operativa, Emergencias, Soporte) | Documentado en `research.md` Decision 4, con test dedicado (403) en cada endpoint de partner |
| **Duplicados por concurrencia** en las validaciones de unicidad, por el retraso de ingesta | Aceptado y declarado: volumen muy bajo y daño reparable. **No** extrapolable a CU-O52, de alta frecuencia |
| Dependencias externas sin aplicar: rol nuevo y `api_calls_minuto` | Listadas en `checklists/requirements.md` con su bloqueo. `api_calls_minuto` ausente → 422, nunca un valor asumido |

## Complexity Tracking

Sin violaciones de la constitución que requieran excepción.

## ISO 25010 — Impacto Security (característica dominante)

Este módulo no toca Safety, pero **emite las credenciales que dan acceso a los datos de TSI**. Decisiones de diseño con impacto en seguridad:

- Secreto irrecuperable por diseño: solo hash bcrypt, entregado una vez (fail-closed ante pérdida).
- Control de propiedad obligatorio en todo endpoint de autoservicio.
- Expiración derivada de los datos, no dependiente de un job: si el job cae, las credenciales vencidas **no** siguen operativas.
- Centinela de «no expira» en el futuro (9999-12-31), para que ningún job de expiración alcance a producción por accidente.
- Bitácora inmutable: la trazabilidad de quién emitió y quién aprobó no se puede reescribir.
- Promoción a producción deliberadamente semiautomática: el partner pide, una persona aprueba.

## Artifacts Generated

| Artefacto | Ruta |
|---|---|
| Spec | `…/partner-api-onboarding/backend/spec.md` |
| Plan | `…/partner-api-onboarding/backend/plan.md` |
| Research | `…/partner-api-onboarding/backend/research.md` |
| Data model | `…/partner-api-onboarding/backend/data-model.md` |
| Quickstart | `…/partner-api-onboarding/backend/quickstart.md` |
| Traceability | `…/partner-api-onboarding/backend/traceability.md` |
| OpenAPI contract | `…/partner-api-onboarding/backend/contracts/partner-api-onboarding.openapi.yaml` |
| Checklist | `…/partner-api-onboarding/backend/checklists/requirements.md` |

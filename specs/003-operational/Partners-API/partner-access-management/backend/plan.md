# Implementation Plan: Gestión de Acceso de Partners

**Capa**: `partner-access-management/backend` | **Date**: 2026-08-08 | **Spec**: `specs/003-operational/Partners-API/partner-access-management/backend/spec.md`

**Input**: Feature specification desde `backend/spec.md` (Clarifications Session 2026-08-08 integradas; decisiones D1 y D2 cerradas).
**Capa hermana (UI):** `../frontend/` — ver [`../partner-access-management.md`](../partner-access-management.md).
**Módulos previos:** [`#07`](../../partner-api-onboarding/) emite las credenciales que este invalida; [`#08`](../../api-monitoring-and-billing/) emite las facturas cuya mora dispara la suspensión y **aplica** el corte en cada llamada.

## Summary

Implementar el corte y la restitución del acceso del partner con enfoque **contract-first**. Cuatro flujos bajo un solo CU: **revocación de autoservicio** con reemplazo inmediato ante credencial comprometida, **avisos previos** de suspensión por mora, **suspensión automática** con cascada sobre todas las credenciales, y **suspensión/reactivación manual** por un Administrador.

**Este módulo cierra el departamento.** No lo consume ningún otro.

**No añade nada al esquema:** es el único de los tres que se implementa entero sobre tablas y campos existentes.

## Traceability

- **Objetivo operacional:** garantizar que un acceso comprometido o impagado se retire, y que restituirlo no reintroduzca el riesgo.
- **CU cubierto:** CU-O55 (catálogo canónico §5.5), con sus cuatro RF.
- **RF del catálogo:** RF-O55.1–4 — **4 de 4 sin reservas**.
- **Dependencias:** `partner-api-onboarding` (#07), `api-monitoring-and-billing` (#08), `subscriptions-and-billing`, `gestion-tickets-soporte`, `autenticacion-y-rbac`.
- **Consumidores downstream:** ninguno.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: Django 5 + DRF, JWT RS256, caché de Django (lista de denegación), servicio de emisión de credenciales de #07 (reutilizado, no duplicado)

**Storage**: Apache Pinot (lectura), Kafka (único canal de escritura), caché en memoria para la lista de denegación

**Testing**: pytest + contract tests OpenAPI, **más verificación obligatoria contra Pinot real** (`database/verifica_acceso_partners.py`, a crear)

**Target Platform**: Linux containerizado (API)

**Project Type**: Web application (esta capa: solo backend)

**Performance Goals**: revocación efectiva en **p95 ≤ 2 s** (RNF-PAC-001) — medida hasta que la credencial deja de servir, **sin esperas artificiales**

**Constraints**: API `/api/v1/`, envelope estándar, idempotencia, sin INSERT directo a Pinot, **sin `NULL`** (centinelas), bitácora **solo-INSERT**

**Scale/Scope**: volumen bajísimo (revocaciones y suspensiones son eventos raros), pero **alta criticidad por evento**

## Constitution Check

*GATE: debe pasar antes de Phase 0. Re-evaluado tras Phase 1.*

| Característica ISO 25010 | Estado | Justificación |
|---|---|---|
| Functional Suitability | PASS | CU-O55 + CA-PAC-001–015 trazables. 4/4 RF del catálogo |
| Reliability | PASS | La suspensión y su cascada deben ser consistentes en efecto: un partner suspendido con credenciales activas es un estado contradictorio (RF-PAC-006) |
| Performance Efficiency | PASS | RNF-PAC-001 con umbral y método de medición explícito; la lista de denegación existe precisamente para cumplirlo |
| Interaction Capability | PARCIAL | Alcance BE limitado a RF-PAC-009. La revocación es destructiva y su presentación vive en `../frontend/spec.md` |
| Security | PASS | **Dominante.** Es el mecanismo de respuesta ante incidente: revocación inmediata con ventana cerrada, control de propiedad, **no resurrección** de credenciales comprometidas, bitácora inmutable |
| Compatibility | PARCIAL | Consume el contrato del departamento; no expone integraciones externas propias |
| Maintainability | PASS | Reutiliza la emisión de #07 en vez de duplicarla; propiedad de escritura documentada (§ 13) |
| Flexibility | PASS | Momentos de aviso y límite de mora configurables (RNF-PAC-005) |
| Safety | **NO APLICA** | Fuera de la cadena crítica registro → asignación → despacho → confirmación. Cortar el acceso de un partner impide consultar datos de casos **ya cerrados**; no retrasa la atención de ninguna víctima ni influye en severidad o asignación de unidades |

**Post-Design Gate:** PASS — sin violaciones ni excepciones abiertas.

**Tie-Breaker invocado (dos veces):** Security vs Functional Suitability en RF-PAC-006 (cascada inversa selectiva) y Security vs Performance Efficiency en la lista de denegación. Ambos resueltos a favor de **Security** por la excepción de dominio. Trade-offs en `research.md`.

## Project Structure

### Documentation (this feature)

```text
specs/003-operational/Partners-API/partner-access-management/
├── partner-access-management.md
├── backend/
│   ├── spec.md
│   ├── plan.md
│   ├── research.md
│   ├── data-model.md
│   ├── quickstart.md
│   ├── traceability.md
│   ├── checklists/requirements.md
│   ├── contracts/
│   │   └── partner-access-management.openapi.yaml
│   └── tasks.md                        # pendiente: /speckit-tasks
└── frontend/                           # Interaction Capability (stub)
```

### Source Code (repository root)

```text
backend/
├── apps/
│   └── partners/                              # app compartida del departamento
│       ├── views/
│       │   ├── revocacion_views.py            # RF-PAC-001, RF-PAC-002
│       │   ├── suspension_views.py            # RF-PAC-005
│       │   └── estado_acceso_views.py         # RF-PAC-009
│       ├── services/
│       │   ├── revocar_credencial_service.py  # revocación + reemplazo (usa la emisión de #07)
│       │   ├── suspender_partner_service.py   # RF-PAC-004, RF-PAC-005 + cascada
│       │   ├── reactivar_partner_service.py   # RF-PAC-005 + cascada inversa selectiva
│       │   ├── evaluacion_mora_service.py     # RF-PAC-007 + avisos
│       │   └── denylist_credenciales.py       # cierra la ventana de ingesta
│       └── jobs/
│           └── evaluacion_mora_job.py         # diario: avisos y suspensión
└── core/
    └── repositories/
        └── partners/
            └── historial_acceso_repository.py  # creado en #07; aquí se le añaden
                                                # las lecturas de la cascada
```

**Structure Decision:** se reutiliza la app `partners/` de #07 y #08. `CredencialRepository`, `PartnerRepository` e `HistorialAccesoRepository` ya existen desde #07; este módulo **añade lecturas** (el conjunto de la cascada) y **usa** las escrituras existentes. No se crean repositorios nuevos.

## Phase 0: Research (completado)

Ver `research.md` — 10 decisiones. Las de mayor impacto: **cerrar la ventana de exposición con una lista de denegación** (Decision 2), **reutilizar la emisión de #07** en vez de duplicar la generación de secretos (Decision 3), y **resolver en memoria la colisión de nombre** del reemplazo para que la revocación no falle por un dato que aún no se ha ingerido (Decision 4).

## Phase 1: Design & Contracts (completado)

### Contrato REST

Artefacto: `contracts/partner-access-management.openapi.yaml` — **4 paths, 10 schemas**, validado sin referencias rotas.

| Endpoint | Actor | Nota |
|---|---|---|
| `POST /credenciales/{id}/revocar` | Partner | Autoservicio, sin aprobación |
| `POST /partners/{id}/suspender` | **Administrador** | Motivo obligatorio |
| `POST /partners/{id}/reactivar` | **Administrador** | El sistema nunca lo hace solo |
| `GET /partners/{id}/estado-acceso` | Partner (el suyo) / Administrador | Accesible estando suspendido |

**Todos con JWT.** Deliberadamente **no** se acepta la credencial de API para revocar: una credencial comprometida podría entonces usarse para revocar las demás del partner, dándole al atacante la herramienta de sabotaje.

**Invariante:** el secreto solo aparece en `RevocacionResponse`. El schema `Credencial`, que usa el endpoint de estado, no lo declara.

### Backend — mapeo Vista → Servicio → Repositorio

| Vista / proceso | Servicio | Repositorio / externo |
|---|---|---|
| `RevocarCredencialView` | `RevocarCredencialService` + **servicio de emisión de #07** | `CredencialRepository`, `HistorialAccesoRepository`, `DenylistCredenciales` |
| `SuspenderPartnerView` | `SuspenderPartnerService` | `PartnerRepository`, `CredencialRepository`, `HistorialAccesoRepository` |
| `ReactivarPartnerView` | `ReactivarPartnerService` | `HistorialAccesoRepository` (lee la cascada), `CredencialRepository`, `PartnerRepository` |
| `EstadoAccesoView` | `EvaluacionMoraService` (solo lectura) | `PartnerRepository`, `CredencialRepository`, `HistorialAccesoRepository`, `FacturaRepository` |
| *(job)* `evaluacion_mora_job` | `EvaluacionMoraService` | `FacturaRepository`, `HistorialAccesoRepository`, notificación, `SuspenderPartnerService` |

**Flujo de la revocación — el orden importa:**

```text
POST /credenciales/{id}/revocar
  → ¿pertenece al partner del token?          no ──► 403 (sin escribir)
  → ¿ya está inactiva?                        sí ──► 409 (sin escribir)
  → CredencialRepository: activo=false                    → Dim_CredencialAPI_topic
  → DenylistCredenciales.add(client_id, ttl=60s)   ← CIERRA la ventana de 5–15 s
  → emisión de #07: reemplazo mismo entorno + MISMO NOMBRE
        la unicidad excluye la recién revocada, conocida EN MEMORIA
        (releer Pinot daría una colisión falsa y haría fallar la revocación)
  → HistorialAccesoRepository: `revocacion_credencial`    → bitácora
  → 200 con la revocada + el reemplazo (secreto una sola vez)
```

**Flujo de suspensión y reactivación:**

```text
SUSPENSIÓN                              REACTIVACIÓN (solo Administrador)
  leer credenciales ACTIVAS               ¿está suspendido?  no ──► 409
  por cada una:                           leer filas `desactivacion_por_cascada`
     activo=false                            del ÚLTIMO evento de suspensión
     + bitácora `desactivacion_por_cascada`  restituir activo=true SOLO en esas
  Dim_Partner.activo=false                Dim_Partner.activo=true, snapshot = ""
  + bitácora `suspension_*`               + bitácora `reactivacion`

  Las ya inactivas NO generan fila  ──►   ...y por eso NO se restituyen.
                                          La seguridad sale por construcción.
```

### Data model

Ver `data-model.md` — tres tablas escritas, ningún cambio de esquema, y los dos flujos con su orden de operaciones.

### Validación E2E

Ver `quickstart.md` — escenarios A–O, con **B (ventana cerrada), I (reactivación selectiva) y J (no reactiva solo)** como los críticos.

## Phase 2: Task Decomposition (siguiente comando)

Ejecutar `/speckit-tasks` para producir `tasks.md`:

1. `DenylistCredenciales` y su integración con la autenticación de #08 (**orden crítico**)
2. Contract tests esqueleto desde el OpenAPI
3. Lecturas de cascada en `HistorialAccesoRepository`
4. `RevocarCredencialService` (con reemplazo vía #07 y unicidad en memoria)
5. `SuspenderPartnerService` + cascada con bitácora por credencial
6. `ReactivarPartnerService` + cascada inversa selectiva
7. `EvaluacionMoraService` + job diario de avisos y suspensión
8. Vistas DRF + control de propiedad y de rol
9. `database/verifica_acceso_partners.py`
10. Tests de integración de los escenarios del quickstart

## Riesgos

| Riesgo | Mitigación |
|---|---|
| **Resucitar una credencial comprometida** al reactivar — el peor fallo posible de este módulo | La reactivación solo restituye lo que aparece en la cascada; una credencial ya inactiva **no genera fila**, así que es inalcanzable **por construcción** (§ 15 D1). Test dedicado: escenario I |
| **Ventana de exposición de 5–15 s** tras revocar, por la ingesta de Pinot | Lista de denegación en memoria (`research.md` Decision 2). Test **sin esperas**: escenario B |
| **Orden invertido entre la caché de #08 y la lista de denegación** — convertiría una optimización en un agujero | Documentado en `research.md` Decision 2 y en las tareas; la caché positiva debe consultarse **después** |
| **Colisión falsa de nombre** al emitir el reemplazo, que haría fallar la operación urgente | Unicidad resuelta en memoria, sin releer Pinot (Decision 4). Escenario E |
| **Reactivación automática introducida por un refactor** («si ya pagó, ¿por qué no?») | Test dedicado que exige que siga suspendido tras pagar: escenario J. Choca además con RN-SUSF-011 de Suscripciones |
| **Estado contradictorio**: partner suspendido con credenciales activas | Cascada con actualización explícita de cada fila, verificada contra Pinot |
| **Los tests con doble no ven el estado real en tres tablas** | `database/verifica_acceso_partners.py` como criterio de salida obligatorio |

## Deuda técnica declarada

**La lista de denegación vive en `LocMemCache`, que es por proceso.** Con un proceso es exacta; con N, la revocación solo cerraría la ventana en el proceso que la atendió. **No bloquea hoy**, pero es **la misma deuda que el throttle de #08**: escalar horizontalmente exige un almacén compartido. Se registra una sola vez para todo el departamento.

**Hallazgo fuera de alcance:** `LogoutService` de `cuentas_clientes` tiene el mismo patrón sin resolver — cierra la sesión vía Kafka, así que un JWT robado sigue siendo válido durante la ventana de ingesta. No es competencia de este módulo, pero conviene que esté anotado.

## Complexity Tracking

Sin violaciones de la constitución que requieran excepción.

## ISO 25010 — Impacto Security (característica dominante)

Este módulo **es** el mecanismo de respuesta ante incidente del departamento. Decisiones con impacto directo:

- **La revocación no espera a nadie**: autoservicio sin aprobación, porque esperar autorización ante una credencial expuesta es el peor comportamiento posible.
- **Y no espera a la base**: la lista de denegación cierra la ventana de ingesta que dejaría la credencial sirviendo 15 s más.
- **No se puede revocar con una credencial de API**: se lo impediría al atacante que ya tiene una.
- **La reactivación no resucita lo comprometido**, y la garantía es estructural, no una comprobación que se pueda olvidar.
- **La bitácora es inmutable**: si se pudiera editar, se podría alterar qué credenciales se restituyen — no es solo auditoría, es el mecanismo.
- **El sistema nunca reactiva solo**: reabrir un acceso es siempre una decisión humana.

## Artifacts Generated

| Artefacto | Ruta |
|---|---|
| Spec | `…/partner-access-management/backend/spec.md` |
| Plan | `…/partner-access-management/backend/plan.md` |
| Research | `…/partner-access-management/backend/research.md` |
| Data model | `…/partner-access-management/backend/data-model.md` |
| Quickstart | `…/partner-access-management/backend/quickstart.md` |
| Traceability | `…/partner-access-management/backend/traceability.md` |
| OpenAPI contract | `…/partner-access-management/backend/contracts/partner-access-management.openapi.yaml` |
| Checklist | `…/partner-access-management/backend/checklists/requirements.md` |

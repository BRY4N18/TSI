# Implementation Plan: Informes Tácticos Simples de Cuentas y Clientes (Backend)

**Branch**: `informes-tacticos-simples-cuentas-clientes` | **Date**: 2026-08-14 | **Spec**: [`spec.md`](spec.md)

**Input**: Feature specification from `specs/002-tactico/Cuentas-Clientes/informes-tacticos-simples/backend/spec.md`

**Capa hermana (UI):** aplazada deliberadamente — ver [`../informes-tacticos-simples.md`](../informes-tacticos-simples.md).
Este plan no es superficie de trabajo UI y ningún endpoint asume una pantalla.

## Summary

Implementar **8 endpoints de listado de solo lectura** sobre Apache Pinot dentro de la app existente
`backend/apps/cuentas_clientes`, en capas **Vista → Servicio → Repositorio**, más un paquete nuevo
`backend/core/informes/` con los ayudantes que los 64 listados de los 8 departamentos compartirán
(período opcional, paginación por cursor, envelope con paginación).

Ninguno agrega, ninguno escribe, ninguno publica en Kafka. Es una capa de lectura pura sobre datos
que ya produce el módulo operativo de Cuentas y Clientes.

**Es el módulo piloto**: fija el patrón que replicarán los siete departamentos restantes, y por eso
el trabajo transversal (`core/informes/`) se hace aquí aunque solo lo use un departamento todavía.

## Traceability

- **Objetivos tácticos:** OT04 (incorporación autoguiada y verificable), OT17 (ciclo de vida de la
  cuenta), OT18 (acceso seguro y controlado por rol).
- **Objetivos operativos / casos de uso:** OP02, OP04, OP05, OP07, CU-O04, CU-O05, CU-O08, CU-O15.
  Los ocho listados se trazan al marco; **ninguno es criterio propio**.
- **Catálogo:** `informestacticos/TSI-Informes-Tacticos-Requeridos-por-OT.md` §2.
- **Contrato común:** [`../../contrato-informes-simples.md`](../../contrato-informes-simples.md).
- **Dependencias:** ninguna app nueva; se extiende `apps/cuentas_clientes` sin tocar su lógica
  operativa. **`apps/informes_tacticos` no se modifica** (ver research D1).
- **Consumidores downstream:** los 7 departamentos restantes reutilizarán `core/informes/`.

## Technical Context

**Language/Version**: Python 3.11 (Django 5 + DRF), como el resto de `backend/apps/*`.

**Primary Dependencies**: Django 5 + DRF; `PinotClient` (`core/pinot/client.py`, existente);
JWT + RBAC existente; `core/api/response_envelope.py`. **Sin dependencias nuevas.**

**Storage**: Apache Pinot, exclusivamente de solo lectura — `Dim_Cliente`, `Fact_Onboarding`,
`Fact_HistorialTransferenciaPropiedad`, `Dim_Usuarios`, `Dim_Usuario_Rol`, `Dim_Rol`, `Fact_Session`,
`Dim_Credencial`, `Dim_UsuariosServidor`, `Dim_RolesServidor`, `Dim_UsuariosServidorRolesServidor`,
`Dim_RolesServidorRoles`. **Ninguna tabla nueva, ningún cambio de esquema.**

**Testing**: pytest con el layout de `apps/cuentas_clientes/tests/` (`tests/repositories/`,
`tests/services/`, `tests/api/`) y el fixture `mock_pinot`. **Con la salvedad conocida**: el doble en
memoria no valida tipos ni centinelas, así que las pruebas de D3 y D7 miran el código fuente o el
esquema, no el doble.

**Target Platform**: Linux containerizado, mismo backend ya desplegado (`docker/accidentes.yml`).
Sin infraestructura nueva. **No requiere ClickHouse** — esa es la razón de empezar por aquí.

**Project Type**: Web application (solo capa backend en esta spec).

**Performance Goals**: SC-002 — primera página de cualquiera de los 8 listados en menos de 2 s con el
volumen actual.

**Constraints**: rutas `/api/v1/informes/cuentas-clientes/*`; envelope estándar con `pagination`;
cursor keyset, nunca `OFFSET`; `LIMIT` explícito derivado del `limit` de la petición; filtros y orden
en SQL, nunca en Python; prohibido `SELECT *` sobre tablas con material sensible (research D7).

**Scale/Scope**: 8 endpoints, 0 apps nuevas, 1 paquete transversal nuevo (`core/informes/`),
0 tablas nuevas.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Característica ISO 25010 | Estado | Justificación |
|---|---|---|
| **Functional Suitability** | PASS | 8 FR trazables 1:1 a un OP o CU del marco (§Traceability). Ninguno "porque sí" — el propio catálogo marca que ninguno es ±. |
| **Reliability** | PASS | Solo lectura y **fuera del camino crítico**: un fallo aquí no afecta registro→asignación→despacho→confirmación. Degradación declarada: listado vacío devuelve `200 data:[]`, nunca `404`; el retraso de ingesta de 5–15 s se documenta, no se compensa. |
| **Performance Efficiency** | PASS | SC-002 (<2 s) declarado. `LIMIT` derivado del `limit` de la petición evita traer 10.000 filas para mostrar 50; keyset evita el coste creciente de `OFFSET`. |
| **Interaction Capability** | **N/A** | Capa backend sin superficie de usuario. La UI está aplazada por decisión explícita y se evaluará en su propio plan. La única obligación que sí se hereda aquí es `design-system.md` §8 — no exponer identificadores internos —, recogida en FR-010. |
| **Security** | PASS | RBAC por rol real (FR-017 a FR-019); acotamiento nunca más amplio que la pantalla operativa (FR-020); **enumeración explícita de columnas** en los tres listados que tocan `contrasena` o `token`, con prueba que falla si se filtran (research D7). |
| **Compatibility** | PASS | Contrato versionado bajo `/api/v1/`, endpoints nuevos y aditivos. **Ningún cambio rompe integraciones existentes**: `apps/informes_tacticos` y sus 19 endpoints quedan intactos (research D1). |
| **Maintainability** | PASS | Vista→Servicio→Repositorio, igual que el resto. Lo transversal va a `core/informes/`, no se duplica ocho veces. La app operativa `cuentas_clientes` se extiende sin tocar su lógica. |
| **Flexibility** | PASS | Cada listado es independiente: añadir o quitar uno no afecta a los demás. `core/informes/` está diseñado para los 8 departamentos desde el primer día, que es el objetivo de escalar el patrón. |
| **Safety** | **N/A** | Listados históricos y de estado administrativo, fuera del camino crítico de seguridad física. Ningún endpoint influye en asignación, despacho ni clasificación de severidad. |

### Tie-Breaker Mechanism

**Conflicto identificado: Maintainability vs. Compatibility** en la decisión D1 (período opcional).

- **En conflicto:** reutilizar `parse_periodo` modificándolo (menos código, más mantenible por no
  duplicar) frente a no tocar aquello de lo que dependen 19 endpoints en producción (compatibilidad).
- **Priorizado:** se evitó modificar `parse_periodo`, creando `core/informes/periodo.py` aparte.
- **Regla aplicada:** Safety no está en juego, así que rige la prioridad por defecto de
  **Maintainability y Functional Suitability**. Aquí ambas apuntan al mismo lado: duplicar ~40 líneas
  acotadas y auditables es más mantenible que ampliar la superficie de riesgo de 19 endpoints
  verificados, y no compromete la corrección funcional de ninguno.
- **Trade-off aceptado:** convivirán dos implementaciones del período durante un tiempo. El coste es
  la duplicación; el beneficio es que ningún informe existente puede romperse por este trabajo. Si
  los 19 migraran algún día a `core/informes`, la copia de la app desaparece.

**Sin más conflictos identificados.**

## Project Structure

### Documentation (this feature)

```text
specs/002-tactico/Cuentas-Clientes/informes-tacticos-simples/
├── informes-tacticos-simples.md          # índice del módulo
└── backend/
    ├── spec.md
    ├── plan.md                           # este archivo
    ├── research.md                       # Fase 0
    ├── data-model.md                     # Fase 1
    ├── quickstart.md                     # Fase 1
    ├── contracts/
    │   └── informes-tacticos-simples.openapi.yaml
    ├── checklists/
    │   └── requirements.md
    └── tasks.md                          # Fase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
backend/
├── core/
│   └── informes/                         # NUEVO — transversal a los 8 departamentos
│       ├── __init__.py
│       ├── periodo.py                    # rango opcional (research D1)
│       ├── paginacion.py                 # cursor keyset (research D2)
│       ├── envelope.py                   # {data, meta:{pagination, filtros}}
│       └── vistas.py                     # ListadoBaseView: valida limit, rango y enumeraciones
├── apps/
│   └── cuentas_clientes/                 # EXISTENTE — se extiende, no se reescribe
│       ├── views/
│       │   ├── informes_acceso_views.py          # US1 — 4 vistas
│       │   ├── informes_incorporacion_views.py   # US2 — 2 vistas
│       │   └── informes_cuenta_views.py          # US3 — 2 vistas
│       ├── services/
│       │   ├── informes_acceso_service.py        # US1
│       │   ├── informes_incorporacion_service.py # US2 — reloj inyectable
│       │   └── informes_cuenta_service.py        # US3
│       ├── permissions.py                # se añaden las clases de permiso de informes
│       ├── urls.py                       # se añaden 8 rutas
│       └── tests/{unit,repositories,services,api,performance}/
└── core/repositories/cuentas_clientes/
    ├── informes_acceso_repository.py         # US1 — SQL de L5–L8
    ├── informes_incorporacion_repository.py  # US2 — SQL de L1–L2
    └── informes_cuenta_repository.py         # US3 — SQL de L3–L4
```

**Reparto por user story.** Repositorios, servicios y vistas se parten por historia en lugar de un
fichero único por capa. Con un solo fichero, las tres historias colisionarían en él y dejarían de ser
implementables en paralelo — que es justamente por lo que se organizan así. El único fichero
compartido es `urls.py`, tocado en tres puntos sin solapamiento.

**Structure Decision.** Los listados viven **dentro de la app del departamento** —decisión ya tomada
para los 8— y no en una app de informes central. Lo único que sube a `core/` es lo que los ocho
departamentos compartirán, para no reimplementarlo siete veces más. `apps/informes_tacticos` queda
tal cual: es el módulo de los agregados y no se toca.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Paquete nuevo `core/informes/` con lógica que hoy usa un solo departamento | Los 64 listados de los 8 departamentos necesitan el mismo período opcional, la misma paginación y el mismo envelope | Implementarlo dentro de `apps/cuentas_clientes` obligaría a duplicarlo siete veces o a que las apps de departamento se importen entre sí, dependencia que hoy no existe |
| Duplicación deliberada del parseo de período respecto a `apps/informes_tacticos/periodo.py` | Los 19 informes agregados en producción dependen de que el rango sea obligatorio | Modificar la función compartida cambia el comportamiento de 19 endpoints verificados por un ahorro de ~40 líneas (ver Tie-Breaker) |

## Phase Status

- [x] **Phase 0 — Research**: [`research.md`](research.md), 7 decisiones cerradas, 0 NEEDS CLARIFICATION.
- [x] **Phase 1 — Design**: [`data-model.md`](data-model.md), [`contracts/`](contracts/), [`quickstart.md`](quickstart.md).
- [x] **Post-Design Constitution Check**: PASS — sin violaciones sin justificar. Las dos entradas de
  Complexity Tracking están argumentadas y aceptadas vía Tie-Breaker.
- [ ] **Phase 2 — Tasks**: pendiente de `/speckit-tasks`.

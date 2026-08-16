# Implementation Plan: Informes Tácticos Simples de Suscripciones y Facturación (Backend)

**Branch**: `informes-tacticos-simples-suscripciones-facturacion` | **Date**: 2026-08-14 | **Spec**: [`spec.md`](spec.md)

**Input**: Feature specification from `specs/002-tactico/Suscripciones-Facturacion/informes-tacticos-simples/backend/spec.md`

**Capa hermana (UI):** aplazada deliberadamente — ver [`../informes-tacticos-simples.md`](../informes-tacticos-simples.md).

## Summary

Implementar **4 endpoints de listado de solo lectura** dentro de `backend/apps/suscripciones`, en
capas **Vista → Servicio → Repositorio**, reutilizando la capa transversal `backend/core/informes/`
y **ampliándola con un segundo eje de acotamiento: la organización**, que tres departamentos más
necesitarán.

Ninguno agrega, ninguno escribe. Lo que distingue a este módulo es que **el dato que maneja es
económico**: importes, estados de cobro y el medio con el que se cobra.

## Traceability

- **Objetivos tácticos:** OT05 (catálogo diferenciado), OT06 (ciclo de suscripción, facturación y
  cobro), OT07 (cambios de plan y estado comercial).
- **Objetivos operativos / casos de uso:** OP15, OP16, OP17, CU-O34, CU-O35, CU-O37, CU-O38.
- **Catálogo:** `informestacticos/TSI-Informes-Tacticos-Requeridos-por-OT.md` §4.
- **Contrato común:** [`../../contrato-informes-simples.md`](../../contrato-informes-simples.md).
- **Módulos previos:** `Cuentas-Clientes/` (capa transversal) y `Ventas-CRM/` (acotamiento por
  persona). Se reutilizan y **no se vuelven a decidir**.
- **Dependencias:** ninguna app nueva. `apps/informes_tacticos` sigue sin tocarse, y **tampoco se
  tocan** las cuatro implementaciones operativas de resolución de cuenta (research D1).

## Technical Context

**Language/Version**: Python 3.11 (Django 5 + DRF).

**Primary Dependencies**: `PinotClient`; `core/informes/` (período, paginación, envelope, vista base,
acotamiento por persona); JWT + RBAC existente. **Sin dependencias nuevas.**

**Storage**: Apache Pinot, solo lectura — `Fact_Suscripcion`, `Fact_Factura`,
`Fact_Solicitud_Cambio_Plan`, `Dim_MetodoPago`, más `Dim_Plan`, `Dim_Cliente` y `Dim_Usuarios` como
catálogos. **Ninguna tabla nueva, ningún cambio de esquema.**

**Testing**: pytest con el layout de `apps/suscripciones/tests/`. Las pruebas de D2 (centinela de
plan programado) y D4 (identificador de cobro) **deben mirar el código o la respuesta serializada
completa**, no el doble en memoria ni los campos declarados en el contrato.

**Target Platform**: Linux containerizado. **No requiere ClickHouse.**

**Project Type**: Web application (solo capa backend).

**Performance Goals**: SC-006 — primera página de los cuatro listados en menos de 2 s.

**Constraints**: rutas `/api/v1/informes/suscripciones-facturacion/*`; cursor keyset; `LIMIT`
explícito; **prohibido `SELECT *` sobre el método de pago** (research D4); **prohibido tratar el
plan programado como comprobación de nulidad** (research D2); el filtro de vencidas **excluye las
facturas en disputa** (research D3).

**Scale/Scope**: 4 endpoints, 0 apps nuevas, 1 eje de acotamiento nuevo en la capa transversal,
0 tablas nuevas.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Característica ISO 25010 | Estado | Justificación |
|---|---|---|
| **Functional Suitability** | PASS | 5 FR de listado trazables a un OP o CU, salvo FR-005 marcado como criterio propio en la spec. **Corrección reforzada por research D2 y D3**: el filtro de cambios programados distingue el centinela de un plan real, y el de vencidas excluye las facturas en disputa. |
| **Reliability** | PASS | Solo lectura, fuera del camino crítico. Listado vacío devuelve `200 data:[]`; el retraso de ingesta se documenta y no se compensa. |
| **Performance Efficiency** | PASS | SC-006 (<2 s). `LIMIT` derivado de la petición; keyset. El filtro de caducidad se resuelve **entero en la base**, porque la columna es numérica (research D5). |
| **Interaction Capability** | **N/A** | Capa backend sin superficie de usuario. Se hereda `design-system.md` §8, recogido en FR-014. |
| **Security** | PASS | **Es la característica dominante.** El identificador de cobro no sale en ninguna respuesta (FR-006), con prueba sobre la respuesta serializada completa. Acotamiento por organización con negativa explícita. Una cuenta suspendida conserva acceso a lo suyo (FR-011), que es lo que le permite regularizar. |
| **Compatibility** | PASS | Endpoints nuevos y aditivos bajo `/api/v1/`. No se modifica ningún contrato existente ni las cuatro resoluciones operativas de cuenta. |
| **Maintainability** | PASS | El segundo eje de acotamiento sube a `core/informes/` en vez de convertirse en la quinta copia del mismo salto. Vista→Servicio→Repositorio como el resto. |
| **Flexibility** | PASS | El eje «organización» se diseña para Red Operativa, Partners y Soporte, que acotan igual. |
| **Safety** | **N/A** | Listados comerciales, fuera del camino crítico de seguridad física. |

### Tie-Breaker Mechanism

**Conflicto identificado: Security vs. Maintainability** en la decisión D1 (dónde vive la resolución
de cuenta).

- **En conflicto:** lo más mantenible a corto plazo sería reutilizar el permiso operativo existente
  (cero código nuevo) frente a construir el eje en la capa transversal.
- **Priorizado:** construirlo en la capa transversal.
- **Regla aplicada:** prioridad por defecto de **Maintainability** — no hay Safety en juego, y aquí
  Maintainability apunta al lado contrario del atajo. Reutilizar el permiso operativo dejaría fuera
  al Administrador, obligando a un segundo camino de acceso por listado; y consolidaría la quinta
  copia de una resolución que ya está escrita cuatro veces.
- **Trade-off aceptado:** una función más en la capa transversal, y una duplicación temporal
  respecto a las cuatro implementaciones operativas, que **no se tocan** por no mover código
  verificado de cuatro departamentos.

**Segundo conflicto: Security vs. Performance Efficiency** en D4 (prueba del identificador de cobro).

- **En conflicto:** inspeccionar la respuesta serializada completa en cada prueba de contrato es más
  costoso que comprobar los campos declarados.
- **Priorizado:** **Security**, por la excepción de dominio del mecanismo de desempate — dato cuyo
  compromiso tiene consecuencia económica directa.
- **Trade-off aceptado:** pruebas algo más lentas. Es irrelevante frente a filtrar un medio de cobro.

## Project Structure

### Documentation (this feature)

```text
specs/002-tactico/Suscripciones-Facturacion/informes-tacticos-simples/
├── informes-tacticos-simples.md
└── backend/
    ├── spec.md · plan.md · research.md · data-model.md · quickstart.md
    ├── contracts/informes-tacticos-simples.openapi.yaml
    ├── checklists/requirements.md
    └── tasks.md                          # Fase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
backend/
├── core/
│   └── informes/                         # de los módulos previos — se REUTILIZA
│       ├── periodo.py · paginacion.py · envelope.py · vistas.py
│       └── acotamiento.py                # se AMPLÍA con el eje «organización» (research D1)
├── apps/
│   └── suscripciones/                    # EXISTENTE — se extiende
│       ├── views/
│       │   ├── informes_suscripcion_views.py     # US1
│       │   ├── informes_facturacion_views.py     # US2 — facturas y métodos de pago
│       │   └── informes_cambio_plan_views.py     # US3
│       ├── services/
│       │   ├── informes_suscripcion_service.py   # US1
│       │   ├── informes_facturacion_service.py   # US2 — reloj inyectable (mora, caducidad)
│       │   └── informes_cambio_plan_service.py   # US3 — reloj inyectable (días de espera)
│       ├── permissions.py                # clases de permiso de informes
│       ├── urls.py                       # 4 rutas nuevas
│       └── tests/{unit,repositories,services,api,performance}/
└── core/repositories/suscripciones/
    ├── informes_suscripcion_repository.py    # US1 — Fact_Suscripcion
    ├── informes_facturacion_repository.py    # US2 — Fact_Factura + Dim_MetodoPago
    └── informes_cambio_plan_repository.py    # US3 — Fact_Solicitud_Cambio_Plan
```

**Structure Decision.** Mismo criterio que los dos módulos anteriores. La única pieza transversal
nueva es el eje «organización» del acotamiento, y se construye aquí porque es aquí donde aparece —
pero diseñada para Red Operativa, Partners y Soporte, que acotan por el mismo eje.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Segundo eje de acotamiento en `core/informes/`, cuando ya existe una resolución equivalente en cuatro sitios operativos | El listado táctico necesita **además** el comportamiento del Administrador, que ninguna de las cuatro contempla; y tres departamentos más acotarán igual | Reutilizar el permiso operativo deja fuera al Administrador y obliga a dos caminos de acceso por listado; copiarlo sería la quinta implementación del mismo salto |
| Prueba de seguridad que inspecciona la respuesta serializada completa, no los campos del contrato | Un `SELECT *` filtra el identificador de cobro **aunque el contrato no lo declare**: el contrato describe la intención, no el resultado | Comprobar solo los campos declarados no detecta precisamente el fallo que se quiere prevenir |

## Phase Status

- [x] **Phase 0 — Research**: [`research.md`](research.md), 7 decisiones, 0 NEEDS CLARIFICATION.
- [x] **Phase 1 — Design**: [`data-model.md`](data-model.md), [`contracts/`](contracts/), [`quickstart.md`](quickstart.md).
- [x] **Post-Design Constitution Check**: PASS. Dos conflictos resueltos vía Tie-Breaker; dos
  entradas de Complexity Tracking justificadas.
- [ ] **Phase 2 — Tasks**: pendiente de `/speckit-tasks`.

# Implementation Plan: Informes Tácticos Simples de Soporte al Cliente (Backend)

**Branch**: `informes-tacticos-simples-soporte-cliente` | **Date**: 2026-08-14 | **Spec**: [`spec.md`](spec.md)

**Input**: Feature specification from `specs/002-tactico/Soporte-Cliente/informes-tacticos-simples/backend/spec.md`

**Capa hermana (UI):** aplazada deliberadamente — ver [`../informes-tacticos-simples.md`](../informes-tacticos-simples.md).

## Summary

Implementar **2 endpoints de listado de solo lectura** dentro de `backend/apps/soporte_cliente`, en
capas **Vista → Servicio → Repositorio**, reutilizando íntegramente la capa transversal
`backend/core/informes/` **sin modificarla**.

Es el módulo más pequeño de la serie y el primero que **no necesita tocar la capa compartida**. Ese
es su valor de verificación: si la parametrización del acotamiento hecha en Red Operativa era
correcta, aquí se usa sin cambios.

## Traceability

- **Objetivos tácticos:** OT19 (resolver dentro del SLA comprometido), OT20 (vigilar y escalar).
- **Objetivos operativos / casos de uso:** OP47, OP48, OP50, CU-O84.
- **Catálogo:** `informestacticos/TSI-Informes-Tacticos-Requeridos-por-OT.md` §8.
- **Contrato común:** [`../../contrato-informes-simples.md`](../../contrato-informes-simples.md).
- **Módulos previos:** los cuatro anteriores. Se reutilizan **sin modificarlos**.
- **Dependencias:** ninguna app nueva, ninguna corrección transversal.

## Technical Context

**Language/Version**: Python 3.11 (Django 5 + DRF).

**Primary Dependencies**: `PinotClient`; `core/informes/` completo. **Sin dependencias nuevas y sin
cambios en la capa compartida.**

**Storage**: Apache Pinot, solo lectura — `Fact_Reclamo`, `Fact_Historial_Ticket`, más
`Dim_Cliente`, `Dim_Usuarios`, `Dim_Servicio` y `Dim_Estado_Soporte` como catálogos. **Ninguna tabla
nueva, ningún cambio de esquema.**

**Testing**: pytest con el layout de `apps/soporte_cliente/tests/`. Las pruebas de D3 (coherencia de
las dos señales de autoría) y D4 (ausencia del texto) **deben inspeccionar la respuesta completa y el
código**, no el doble en memoria.

**Target Platform**: Linux containerizado. **No requiere ClickHouse.**

**Project Type**: Web application (solo capa backend).

**Performance Goals**: SC-007 — primera página de los dos listados en menos de 2 s.

**Constraints**: rutas `/api/v1/informes/soporte-cliente/*`; cursor keyset; `LIMIT` explícito;
**prohibido consultar el texto de los mensajes** (research D4); **el filtro de escalados incluye
exactamente dos tipos de acción** (research D2); **la ausencia de autor decide la autoría del
sistema** (research D3).

**Scale/Scope**: 2 endpoints, 0 apps nuevas, **0 cambios en la capa transversal**, 0 tablas nuevas.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Característica ISO 25010 | Estado | Justificación |
|---|---|---|
| **Functional Suitability** | PASS | 3 FR de listado trazables a un OP o CU. **Corrección reforzada por research D2 y D5**: el filtro de escalados excluye avisos y cierres automáticos, y la situación «sin compromiso» se lista en vez de omitirse. |
| **Reliability** | PASS | Solo lectura, fuera del camino crítico. Listado vacío devuelve `200 data:[]`; el retraso de ingesta se documenta y no se compensa. |
| **Performance Efficiency** | PASS | SC-007 (<2 s). `LIMIT` derivado de la petición; keyset. No consultar el texto de los mensajes reduce además el peso de la respuesta. |
| **Interaction Capability** | **N/A** | Capa backend sin superficie de usuario. Se hereda `design-system.md` §8, recogido en FR-016. |
| **Security** | PASS | **Doble protección.** El acotamiento se decide por ausencia de rol de atención, no por presencia de un rol de reporte (FR-011), que es lo que impide que el Partner vea tickets ajenos. Y el contenido interno **no se consulta**, en vez de consultarse y filtrarse (FR-007, research D4). |
| **Compatibility** | PASS | Endpoints nuevos y aditivos. **Ningún cambio en la capa transversal ni en las cuatro implementaciones operativas de resolución de cuenta.** |
| **Maintainability** | PASS | Vista→Servicio→Repositorio. Reutiliza la condición de acotamiento ya implementada en el módulo operativo en vez de reimplementarla. |
| **Flexibility** | PASS | Es el módulo que **verifica** que la parametrización del acotamiento generaliza sin cambios. |
| **Safety** | **N/A** | Listados de atención al cliente, fuera del camino crítico de seguridad física. |

### Tie-Breaker Mechanism

**Conflicto identificado: Security vs. Functional Suitability** en D4 (texto de los mensajes).

- **En conflicto:** un listado de escalados **con** el mensaje sería más informativo; ese texto es
  donde viven las notas internas que no pueden llegar al reportador.
- **Priorizado:** **Security** — no se consulta el texto.
- **Regla aplicada:** excepción de dominio del mecanismo de desempate; el dato en juego es contenido
  interno sobre la cuenta de un cliente. Y el coste funcional es bajo: un listado táctico responde
  qué pasó, cuándo y quién lo hizo, no la prosa.
- **Trade-off aceptado:** para leer el mensaje hay que abrir el ticket, que ya tiene su control de
  acceso y su filtrado. A cambio, **no existe un filtro que alguien pueda olvidar**: la fragilidad
  desaparece en vez de gestionarse.

**Sin más conflictos identificados.**

## Project Structure

### Documentation (this feature)

```text
specs/002-tactico/Soporte-Cliente/informes-tacticos-simples/
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
├── core/informes/                        # se REUTILIZA SIN CAMBIOS
├── apps/
│   └── soporte_cliente/                  # EXISTENTE — se extiende
│       ├── views/informes_views.py               # 2 vistas
│       ├── services/
│       │   ├── informes_tickets_service.py       # US1
│       │   └── informes_escalados_service.py     # US2
│       ├── permissions.py                # clases de permiso de informes
│       ├── urls.py                       # 2 rutas nuevas
│       └── tests/{unit,repositories,services,api,performance}/
└── core/repositories/soporte/
    ├── informes_tickets_repository.py        # US1 — Fact_Reclamo
    └── informes_escalados_repository.py      # US2 — Fact_Historial_Ticket
```

**Structure Decision.** Con solo dos listados, las vistas caben en un fichero; los servicios y
repositorios se separan por historia para que ambas sigan siendo implementables en paralelo. El
módulo `views.py` existente de la app no se toca: las vistas de informes van en su propio módulo.

## Complexity Tracking

*Sin violaciones que justificar.* Es el primer módulo de la serie sin entradas en esta tabla: no
añade piezas transversales, no corrige nada compartido y no introduce patrones nuevos.

## Riesgo declarado, fuera del alcance de este plan

**El criterio de pertenencia amplio no está poblado** (research D1). La tabla de vínculos
usuario-cuenta existe y tiene su topic declarado, pero **ningún código de producción escribe en
ella**: en la práctica, todos los departamentos resuelven por administrador local.

**Consecuencia:** una organización con varios usuarios tiene **uno solo** que puede consultar los
listados acotados a su cuenta.

Este plan **no lo corrige**: poblar esa tabla decide quién de una organización ve qué, y es una
decisión de negocio que excede un módulo de listados. Queda anotado para `decisiones-pendientes.md`.

**Lo que sí hace este plan** es no ocultarlo: sin esta nota, el primero que pruebe con un usuario que
no sea administrador local leería el rechazo como un defecto de estos endpoints.

## Phase Status

- [x] **Phase 0 — Research**: [`research.md`](research.md), 7 decisiones, 0 NEEDS CLARIFICATION.
- [x] **Phase 1 — Design**: [`data-model.md`](data-model.md), [`contracts/`](contracts/), [`quickstart.md`](quickstart.md).
- [x] **Post-Design Constitution Check**: PASS, sin violaciones. Un conflicto resuelto vía
  Tie-Breaker.
- [ ] **Phase 2 — Tasks**: pendiente de `/speckit-tasks`.

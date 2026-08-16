# Implementation Plan: Informes Tácticos Simples de Ventas y CRM (Backend)

**Branch**: `informes-tacticos-simples-ventas-crm` | **Date**: 2026-08-14 | **Spec**: [`spec.md`](spec.md)

**Input**: Feature specification from `specs/002-tactico/Ventas-CRM/informes-tacticos-simples/backend/spec.md`

**Capa hermana (UI):** aplazada deliberadamente — ver [`../informes-tacticos-simples.md`](../informes-tacticos-simples.md).

## Summary

Implementar **4 endpoints de listado de solo lectura** dentro de `backend/apps/ventas_crm`, en capas
**Vista → Servicio → Repositorio**, reutilizando la capa transversal `backend/core/informes/`
construida en el módulo piloto y **ampliándola con una pieza nueva: el resolutor de acotamiento por
titularidad**, que los seis departamentos restantes necesitarán.

Ninguno agrega, ninguno escribe. Lo que distingue a este módulo del piloto es que **el resultado
depende de quién pregunta**.

## Traceability

- **Objetivos tácticos:** OT01 (captación digital), OT02 (embudo hasta la conversión), OT03
  (nutrición con demo y alertas).
- **Objetivos operativos / casos de uso:** OP09, OP10, CU-O19, CU-O21, CU-O23, CU-O25.
- **Catálogo:** `informestacticos/TSI-Informes-Tacticos-Requeridos-por-OT.md` §3.
- **Contrato común:** [`../../contrato-informes-simples.md`](../../contrato-informes-simples.md).
- **Módulo piloto:** `specs/002-tactico/Cuentas-Clientes/informes-tacticos-simples/` — su capa
  transversal se reutiliza y **no se vuelve a decidir**.
- **Dependencias:** ninguna app nueva; se extiende `apps/ventas_crm` sin tocar su lógica operativa.
  `apps/informes_tacticos` sigue sin tocarse.

## Technical Context

**Language/Version**: Python 3.11 (Django 5 + DRF).

**Primary Dependencies**: `PinotClient`; `core/informes/` (período, paginación, envelope, vista base)
del módulo piloto; JWT + RBAC existente. **Sin dependencias nuevas.**

**Storage**: Apache Pinot, solo lectura — `Dim_Prospecto`, `Fact_Asignacion`,
`Fact_NotificacionVentas`, más `Dim_Usuarios` como catálogo. **Ninguna tabla nueva, ningún cambio de
esquema.**

**Testing**: pytest con el layout de `apps/ventas_crm/tests/`. Las pruebas de D1 (perdido vs
convertido) y D3 (formato de fecha) **deben mirar el código o el esquema**, no el doble en memoria,
que no reproduce ninguno de los dos problemas.

**Target Platform**: Linux containerizado, mismo backend ya desplegado. **No requiere ClickHouse.**

**Project Type**: Web application (solo capa backend).

**Performance Goals**: SC-004 — primera página de los cuatro listados en menos de 2 s.

**Constraints**: rutas `/api/v1/informes/ventas-crm/*`; cursor keyset; `LIMIT` explícito; prohibido
`SELECT *` sobre `Dim_Prospecto` (research D4); prohibido usar `activo = false` como equivalente de
«perdido» (research D1); prohibido comparar `demo_expiracion` completa en SQL (research D3).

**Scale/Scope**: 4 endpoints, 0 apps nuevas, 1 módulo transversal nuevo (`acotamiento.py`),
0 tablas nuevas.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Característica ISO 25010 | Estado | Justificación |
|---|---|---|
| **Functional Suitability** | PASS | 5 FR de listado trazables a un OP o CU. **Y corrección funcional reforzada por research D1**: el filtro de perdidos distingue perdido de convertido, evitando presentar éxitos como fracasos. |
| **Reliability** | PASS | Solo lectura, fuera del camino crítico. Degradación declarada: listado vacío devuelve `200 data:[]`; el retraso de ingesta se documenta y no se compensa. |
| **Performance Efficiency** | PASS | SC-004 (<2 s). `LIMIT` derivado de la petición; keyset. El prefiltro por prefijo de fecha de D3 mantiene el filtrado en la base, no en memoria. |
| **Interaction Capability** | **N/A** | Capa backend sin superficie de usuario. Se hereda `design-system.md` §8 (no exponer identificadores), recogido en FR-013. |
| **Security** | PASS | **Es la característica central de este módulo.** Acotamiento por titularidad (FR-006 a FR-009) resuelto en una pieza única y auditable; negativa explícita en vez de sustitución silenciosa; dato personal de contacto **excluido por defecto** (research D4). |
| **Compatibility** | PASS | Endpoints nuevos y aditivos bajo `/api/v1/`. No se modifica ningún contrato existente. `apps/informes_tacticos` intacto. |
| **Maintainability** | PASS | El acotamiento sube a `core/informes/` en vez de reimplementarse por departamento. Vista→Servicio→Repositorio como el resto. |
| **Flexibility** | PASS | El resolutor de acotamiento se diseña para los seis departamentos que faltan, cuyos ejes de titularidad son distintos (cliente, partner, proveedor). |
| **Safety** | **N/A** | Listados comerciales, fuera del camino crítico de seguridad física. |

### Tie-Breaker Mechanism

**Conflicto identificado: Security vs. Functional Suitability** en la decisión D4 (datos de contacto).

- **En conflicto:** exponer `gmail` y `telefono` haría el listado más útil de inmediato
  (completitud funcional) frente a limitar la difusión de dato personal (confidencialidad).
- **Priorizado:** **Security**. El listado no expone datos de contacto.
- **Regla aplicada:** excepción de dominio del mecanismo de desempate — cuando intervienen datos de
  identidad de personas, Information Security puede prevalecer sobre las características que ganan
  por defecto. Aquí además el coste funcional es mínimo: el propósito táctico es supervisar la
  cartera, y para contactar existe la pantalla operativa con su propio control de acceso.
- **Trade-off aceptado:** si al usar el listado se comprueba que el contacto hace falta, añadir una
  columna es trivial. Retirar un dato que ya circuló, no.

**Segundo conflicto: Performance Efficiency vs. Functional Correctness** en D3 (filtro de demos).

- **En conflicto:** filtrar íntegramente en la base es más eficiente, pero sobre esa columna de texto
  con formatos mixtos da resultados incorrectos sin avisar.
- **Priorizado:** **Functional Correctness**, mediante prefiltro seguro en la base y refinamiento
  exacto en el servicio.
- **Regla aplicada:** prioridad por defecto de Functional Suitability, al no estar Safety en juego.
- **Trade-off aceptado:** una página puede devolver menos filas que el `limit` pedido. Se declara en
  el contrato para que el consumidor no lo interprete como fin de resultados.

## Project Structure

### Documentation (this feature)

```text
specs/002-tactico/Ventas-CRM/informes-tacticos-simples/
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
│   └── informes/                         # del piloto — se REUTILIZA
│       ├── periodo.py · paginacion.py · envelope.py · vistas.py
│       └── acotamiento.py                # NUEVO — resolutor de titularidad (research D2)
├── apps/
│   └── ventas_crm/                       # EXISTENTE — se extiende
│       ├── views/
│       │   ├── informes_cartera_views.py         # US1 — prospectos
│       │   ├── informes_asignacion_views.py      # US2 — reasignaciones
│       │   └── informes_nutricion_views.py       # US3 — demos y notificaciones
│       ├── services/
│       │   ├── informes_cartera_service.py       # US1
│       │   ├── informes_asignacion_service.py    # US2
│       │   └── informes_nutricion_service.py     # US3 — reloj inyectable (D3, D5)
│       ├── permissions.py                # clases de permiso de informes
│       ├── urls.py                       # 4 rutas nuevas
│       └── tests/{unit,repositories,services,api,performance}/
└── core/repositories/ventas_crm/
    ├── informes_cartera_repository.py        # US1 — Dim_Prospecto
    ├── informes_asignacion_repository.py     # US2 — Fact_Asignacion
    └── informes_nutricion_repository.py      # US3 — Dim_Prospecto (demos) + Fact_NotificacionVentas
```

**Structure Decision.** Mismo criterio que el piloto: los listados viven en la app del departamento,
y solo sube a `core/` lo que los ocho compartirán. El reparto por user story evita que las tres
historias colisionen en el mismo fichero.

**La única pieza transversal nueva es `acotamiento.py`**, y se construye aquí porque es aquí donde
aparece la necesidad por primera vez — pero se diseña para los seis departamentos restantes, cuyos
ejes de titularidad son distintos.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Filtro de demos en dos pasos (base + servicio) en vez de uno solo en la base | La columna de expiración es texto con formatos mixtos; compararla entera en la base da resultados incorrectos sin error visible (research D3) | Filtrar todo en la base es más simple y está mal; traerlo todo a memoria rompe la paginación |
| `acotamiento.py` en `core/` usado hoy por un solo departamento | Seis departamentos más necesitan acotar por titularidad, cada uno por un eje distinto | Resolverlo por departamento lo reimplementa siete veces; la primera divergencia es una fuga de datos entre carteras |

## Phase Status

- [x] **Phase 0 — Research**: [`research.md`](research.md), 7 decisiones, 0 NEEDS CLARIFICATION.
- [x] **Phase 1 — Design**: [`data-model.md`](data-model.md), [`contracts/`](contracts/), [`quickstart.md`](quickstart.md).
- [x] **Post-Design Constitution Check**: PASS. Dos conflictos resueltos y documentados vía
  Tie-Breaker; dos entradas de Complexity Tracking justificadas.
- [ ] **Phase 2 — Tasks**: pendiente de `/speckit-tasks`.

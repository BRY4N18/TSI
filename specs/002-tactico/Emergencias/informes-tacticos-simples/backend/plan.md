# Implementation Plan: Informes Tácticos Simples de Emergencias (Backend)

**Branch**: `informes-tacticos-simples-emergencias` | **Date**: 2026-08-14 | **Spec**: [`spec.md`](spec.md)

**Input**: Feature specification from `specs/002-tactico/Emergencias/informes-tacticos-simples/backend/spec.md`

**Capa hermana (UI):** aplazada deliberadamente — ver [`../informes-tacticos-simples.md`](../informes-tacticos-simples.md).

**Módulo vecino:** [`../../informes-tacticos-agregados/`](../../Emergencias/informes-tacticos-agregados/informes-tacticos-agregados.md)
contiene los 19 informes **agregados** en producción. **Estos listados no los duplican ni los tocan.**

## Summary

Implementar **5 endpoints de listado de solo lectura** repartidos entre `backend/apps/accidentes` y
`backend/apps/seguimiento`, en capas **Vista → Servicio → Repositorio**, reutilizando la capa
transversal `backend/core/informes/` y **ampliándola con un eje de acotamiento nuevo: la cobertura
geográfica contratada**.

Es el módulo que cubre más objetivos tácticos y el único con un eje de acotamiento propio.

## Traceability

- **Objetivos tácticos:** OT21 (registro limpio), OT22 (asignar y despachar), OT23 (acompañar la
  misión), OT24 (documentar el sitio), OT25 (cerrar de forma trazable).
- **Objetivos operativos / casos de uso:** OP32, OP33, OP35, OP36, OP37, OP38, OP40, OP42, OP45.
- **Catálogo:** `informestacticos/TSI-Informes-Tacticos-Requeridos-por-OT.md` §7.
- **Contrato común:** [`../../contrato-informes-simples.md`](../../contrato-informes-simples.md).
- **Módulos previos:** los seis anteriores. Se reutilizan; solo se amplía el resolutor de
  acotamiento.
- **Dependencias:** ninguna app nueva. `apps/informes_tacticos` sigue sin tocarse.

## Technical Context

**Language/Version**: Python 3.11 (Django 5 + DRF).

**Primary Dependencies**: `PinotClient`; `core/informes/` completo; el repositorio de catálogo
geográfico, que ya resuelve niveles a conjuntos de calles. **Sin dependencias nuevas.**

**Storage**: Apache Pinot, solo lectura — `Fact_Accidente`, `Fact_Despacho`, `Dim_EvidenciaFoto`,
`Dim_NotaAccidente`, `Fact_CierreAccidente`, más `Dim_Severidad`, `Dim_Calle`, `Dim_Ciudad`,
`Dim_Condado`, `Dim_TipoReportado`, `Dim_UnidadEmergencia`, `Dim_OrigenDespacho`, `Dim_Usuarios` y
`Dim_Preferencias_Cliente` como catálogos. **Ninguna tabla nueva, ningún cambio de esquema.**

**Tablas deliberadamente NO leídas:** los históricos de estado de caso y de despacho (research D2,
D5), y las tablas de conductores, implicados y vehículos (research D4).

**Testing**: pytest con el layout de `apps/accidentes/tests/` y `apps/seguimiento/tests/`. Las
pruebas de D3 (hora de captura) y D6 (calificación ausente) **deben mirar el dato real**, no el doble
en memoria.

**Target Platform**: Linux containerizado. **No requiere ClickHouse.**

**Project Type**: Web application (solo capa backend).

**Performance Goals**: SC-007 — primera página de los cinco listados en menos de 2 s, **incluido el
listado de casos acotado a varias zonas contratadas**.

**Constraints**: rutas `/api/v1/informes/emergencias/*`; cursor keyset; `LIMIT` explícito; **columnas
enumeradas** en todos los repositorios; **prohibido devolver coordenadas ni identidad de personas**
(research D4); **prohibido inferir un campo de estado** a partir de las tres columnas del caso
(research D2); **prohibido comprobar la zona fila a fila** (research D1).

**Scale/Scope**: 5 endpoints, 0 apps nuevas, 1 eje de acotamiento nuevo, 0 tablas nuevas.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Característica ISO 25010 | Estado | Justificación |
|---|---|---|
| **Functional Suitability** | PASS | 5 FR de listado trazables a un OP o CU. **Corrección reforzada por research D2 y D6**: no se infiere un estado que la fuente no guarda, y una calificación ausente no se presenta como cero. |
| **Reliability** | PASS | Solo lectura y **fuera del camino crítico**: ningún endpoint participa en registro, asignación ni despacho. Listado vacío devuelve `200 data:[]`; el retraso de ingesta se documenta y no se compensa. |
| **Performance Efficiency** | PASS | SC-007 (<2 s). El acotamiento por zona se resuelve **como conjunto antes de consultar** (research D1), no fila a fila. Se descarta leer los históricos de estado precisamente porque exigirían el último registro por entidad. |
| **Interaction Capability** | **N/A** | Capa backend sin superficie de usuario. Se hereda `design-system.md` §8, recogido en FR-018. |
| **Security** | PASS | **Es la característica dominante.** Ni coordenadas del accidente ni identidad de conductores, implicados o víctimas (research D4, FR-015, FR-016). Acotamiento por zona contratada con lectura segura del caso vacío (FR-011). El cliente ve **solo casos cerrados**, igual que su pantalla operativa. |
| **Compatibility** | PASS | Endpoints nuevos y aditivos. **Los 19 informes agregados y su módulo no se tocan**; el renombrado de su carpeta de spec no afectó a su código. |
| **Maintainability** | PASS | El eje nuevo sube a `core/informes/`. La resolución geográfica **reutiliza el patrón ya documentado como estándar** en vez de crear otro. |
| **Flexibility** | PASS | El eje «cobertura contratada» queda disponible para cualquier futuro listado que acote por zona. |
| **Safety** | ⚠️ **Relevante, y por eso se declara** | Ningún endpoint influye en asignación, despacho ni clasificación de severidad: son listados históricos y de supervisión. **Pero operan sobre el dato del camino crítico**, así que la exclusión de coordenadas e identidad no es cautela genérica: es el tratamiento que la constitución exige para el dato de accidentes. |

### Tie-Breaker Mechanism

**Conflicto identificado: Functional Suitability vs. Security** en D4 (coordenadas del accidente).

- **En conflicto:** un listado con coordenadas permitiría situar los casos con precisión; las
  coordenadas de accidentes son dato sensible bajo control de acceso y auditoría.
- **Priorizado:** **Security** — se expone la ubicación por nombre, no por coordenada.
- **Regla aplicada:** excepción de dominio del mecanismo de desempate, que permite a Information
  Security prevalecer cuando intervienen datos de identidad o localización sensibles. El coste
  funcional es bajo: la pregunta táctica es *dónde y de qué gravedad*, y calle, ciudad y condado la
  responden.
- **Trade-off aceptado:** para situar un caso en un mapa hay que entrar al expediente, que tiene su
  propio control. A cambio, **un volcado de este listado no es un mapa de siniestralidad
  exportable**.

**Segundo conflicto: Functional Suitability vs. Maintainability** en D2 (campo de estado inferido).

- **En conflicto:** devolver un campo «estado» calculado sería más cómodo de consumir; sería una
  inferencia apoyada en una garantía que vive en otro módulo.
- **Priorizado:** **devolver los hechos**, no la inferencia.
- **Regla aplicada:** prioridad por defecto de Functional Suitability y Maintainability, que aquí
  coinciden. La exclusividad entre cerrado, descartado y fusionado la garantiza el módulo de fusión;
  si cambiara, este listado empezaría a mentir sin que nadie lo tocara.
- **Trade-off aceptado:** el consumidor combina tres campos en vez de leer uno. A cambio, el listado
  no depende de una regla que no controla.

## Project Structure

### Documentation (this feature)

```text
specs/002-tactico/Emergencias/informes-tacticos-simples/
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
│   └── informes/                         # se REUTILIZA
│       └── acotamiento.py                # se AMPLÍA con el eje «cobertura contratada» (research D1)
├── apps/
│   ├── accidentes/                       # EXISTENTE — se extiende
│   │   ├── views/informes_views.py               # US1, US3 — casos y evidencia
│   │   ├── services/
│   │   │   ├── informes_casos_service.py         # US1
│   │   │   └── informes_evidencia_service.py     # US3
│   │   ├── permissions.py · urls.py
│   │   └── tests/{unit,repositories,services,api,performance}/
│   └── seguimiento/                      # EXISTENTE — se extiende
│       ├── views/informes_views.py               # US2, US4 — despachos y cierres
│       ├── services/
│       │   ├── informes_despachos_service.py     # US2
│       │   └── informes_cierres_service.py       # US4
│       ├── permissions.py · urls.py
│       └── tests/{...}/
└── core/repositories/
    ├── accidentes/informes_casos_repository.py       # US1 — Fact_Accidente
    ├── accidentes/informes_evidencia_repository.py   # US3 — fotos y notas
    ├── seguimiento/informes_despachos_repository.py  # US2 — Fact_Despacho
    └── seguimiento/informes_cierres_repository.py    # US4 — Fact_CierreAccidente
```

**Structure Decision.** Es el primer módulo repartido entre **dos apps**, y no por capricho:
`accidentes` es dueña del caso y de su evidencia; `seguimiento` lo es del despacho y del cierre. Cada
listado vive donde vive el dato que lee, igual que en los seis módulos anteriores — solo que aquí el
departamento abarca dos apps.

**La resolución geográfica no se reimplementa**: se reutiliza el repositorio de catálogo que ya
resuelve un nivel a un conjunto de calles.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Eje de acotamiento nuevo en `core/informes/` | Ninguno de los tres ejes anteriores acota por cobertura geográfica: aquí el cliente no es titular de nada, tiene zonas contratadas | Reutilizar el eje «organización» daría al cliente los casos que él registró, que no es lo que contrató ni lo que su pantalla operativa le muestra |
| Módulo repartido entre dos apps Django | El departamento abarca el ciclo completo del caso, que el sistema reparte entre dos apps por dueño del dato | Concentrar los cinco listados en una app obligaría a que una leyera tablas de las que no es dueña, rompiendo el criterio de los seis módulos anteriores |

## Phase Status

- [x] **Phase 0 — Research**: [`research.md`](research.md), 7 decisiones, 0 NEEDS CLARIFICATION.
  **El riesgo que podía eliminar la User Story 1 quedó descartado** (D1).
- [x] **Phase 1 — Design**: [`data-model.md`](data-model.md), [`contracts/`](contracts/), [`quickstart.md`](quickstart.md).
- [x] **Post-Design Constitution Check**: PASS. Dos conflictos resueltos vía Tie-Breaker; dos
  entradas de Complexity Tracking justificadas. **Safety declarada como relevante** por operar sobre
  el dato del camino crítico.
- [ ] **Phase 2 — Tasks**: pendiente de `/speckit-tasks`.

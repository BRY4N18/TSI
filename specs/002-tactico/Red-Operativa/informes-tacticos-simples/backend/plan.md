# Implementation Plan: Informes Tácticos Simples de Red Operativa (Backend)

**Branch**: `informes-tacticos-simples-red-operativa` | **Date**: 2026-08-14 | **Spec**: [`spec.md`](spec.md)

**Input**: Feature specification from `specs/002-tactico/Red-Operativa/informes-tacticos-simples/backend/spec.md`

**Capa hermana (UI):** aplazada deliberadamente — ver [`../informes-tacticos-simples.md`](../informes-tacticos-simples.md).

## Summary

Implementar **4 endpoints de listado de solo lectura** dentro de `backend/apps/red_operativa`, en
capas **Vista → Servicio → Repositorio**, reutilizando la capa transversal `backend/core/informes/`
y **corrigiendo el eje «organización»** que Suscripciones dejó a medias: la pertenencia de un
usuario a una cuenta no es un concepto único en este sistema, y el resolutor debe admitir el
criterio como parámetro.

Ninguno agrega, ninguno escribe. Lo que distingue a este módulo es que **el coste de un dato falso
es operativo, no comercial**.

## Traceability

- **Objetivos tácticos:** OT11 (validar y publicar regiones), OT12 (mantener vigente la flota),
  OT13 (retirar regiones sin cobertura).
- **Objetivos operativos / casos de uso:** OP21, OP22, OP23, OP24, OP25, CU-O42, CU-O44.
- **Catálogo:** `informestacticos/TSI-Informes-Tacticos-Requeridos-por-OT.md` §5.
- **Contrato común:** [`../../contrato-informes-simples.md`](../../contrato-informes-simples.md).
- **Módulos previos:** `Cuentas-Clientes/`, `Ventas-CRM/`, `Suscripciones-Facturacion/`. Se reutilizan;
  el eje «organización» de Suscripciones **se corrige** (research D1).
- **Dependencias:** ninguna app nueva. `apps/informes_tacticos` sigue sin tocarse, y **tampoco se
  tocan** las implementaciones operativas de resolución de cuenta.

## Technical Context

**Language/Version**: Python 3.11 (Django 5 + DRF).

**Primary Dependencies**: `PinotClient`; `core/informes/` (período, paginación, envelope, vista base,
acotamiento con sus dos ejes); `ubicacion_catalogo_repository` para la resolución geográfica por
lotes. **Sin dependencias nuevas.**

**Storage**: Apache Pinot, solo lectura — `Dim_UnidadEmergencia`, `Fact_BajaUnidad`,
`Dim_RegionOperativa`, `Dim_ValidacionRegion`, más `Dim_Condado`, `Dim_Estado`, `Dim_Cliente` y
`Dim_Usuarios` como catálogos. **Ninguna tabla nueva, ningún cambio de esquema.**

**Testing**: pytest con el layout de `apps/red_operativa/tests/`. Las pruebas de D1 (criterio de
pertenencia) y D2 (existencia frente a disponibilidad) **deben mirar el código**, no el doble en
memoria, que no reproduce ninguno de los dos.

**Target Platform**: Linux containerizado. **No requiere ClickHouse.**

**Project Type**: Web application (solo capa backend).

**Performance Goals**: SC-006 — primera página de los cuatro listados en menos de 2 s, con **dos
consultas de catálogo por página** para la geografía, no una por fila (research D3).

**Constraints**: rutas `/api/v1/informes/red-operativa/*`; cursor keyset; `LIMIT` explícito;
**prohibido `SELECT *` sobre la unidad** (research D6); **prohibido presentar la condición de alta
como disponibilidad operativa** (research D2); **prohibido agrupar `En_Alerta` con `Despublicada`**
(research D4).

**Scale/Scope**: 4 endpoints, 0 apps nuevas, 1 corrección en la capa transversal, 0 tablas nuevas.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Característica ISO 25010 | Estado | Justificación |
|---|---|---|
| **Functional Suitability** | PASS | 5 FR de listado trazables a un OP o CU. **Corrección reforzada por research D2 y D4**: la composición de flota no se presenta como disponibilidad, y `En_Alerta` no se agrupa con `Despublicada`. |
| **Reliability** | PASS | Solo lectura, fuera del camino crítico. Listado vacío devuelve `200 data:[]`; el retraso de ingesta se documenta y no se compensa. |
| **Performance Efficiency** | PASS | SC-006 (<2 s). La geografía se resuelve por lotes —dos consultas por página, no una por fila (research D3)—, y se descarta incluir el estado operativo precisamente porque exigiría N+1 consultas. |
| **Interaction Capability** | **N/A** | Capa backend sin superficie de usuario. Se hereda `design-system.md` §8, recogido en FR-015. |
| **Security** | PASS | Acotamiento por organización con el criterio de pertenencia **correcto para este departamento** (research D1). **Posición geográfica y contacto del proveedor excluidos** (research D6), coherente con el trato de dato sensible que exige el Principio V. |
| **Compatibility** | PASS | Endpoints nuevos y aditivos. La corrección del resolutor es **parametrización**, no cambio de comportamiento por defecto: los módulos previos conservan el suyo. |
| **Maintainability** | PASS | La corrección sube a `core/informes/` en vez de bifurcarse por departamento. Vista→Servicio→Repositorio como el resto. |
| **Flexibility** | PASS | El criterio de pertenencia parametrizado deja preparados Partners y Soporte, que usan criterios distintos entre sí. |
| **Safety** | ⚠️ **Relevante, y por eso se declara** | Ningún endpoint participa en el despacho ni influye en una asignación. **Pero es el primer módulo cuya lectura errónea afecta a decisiones de cobertura**, y por eso FR-006 a FR-008 son requisitos, no aclaraciones: el listado debe declarar su propio alcance para que nadie lo confunda con disponibilidad real. |

### Tie-Breaker Mechanism

**Conflicto identificado: Functional Suitability vs. Performance Efficiency** en D2 (estado
operativo en el listado de flota).

- **En conflicto:** un listado de flota **con** su estado operativo sería funcionalmente más
  completo; obtenerlo cuesta una consulta por unidad o una agregación con cruce.
- **Priorizado:** **excluirlo**, y declararlo explícitamente en la respuesta.
- **Regla aplicada:** aquí no decide el rendimiento sino la corrección funcional. Aun con coste
  aceptable, el dato devuelto sería el del instante de la consulta y se leería como disponibilidad
  vigente. **La respuesta correcta a esta pregunta no es un listado**, es el informe compuesto de
  cobertura (CU-T08).
- **Trade-off aceptado:** el listado responde «qué flota hay», no «qué flota puede acudir». Se
  compensa obligando a que la respuesta lo declare (FR-008), en vez de dejarlo en la documentación.

**Segundo conflicto: Security vs. Maintainability** en D1 (criterio de pertenencia).

- **En conflicto:** un resolutor con un solo criterio sería más simple de mantener; los
  departamentos usan dos criterios distintos en sus pantallas operativas.
- **Priorizado:** **Security** — parametrizar el criterio.
- **Regla aplicada:** excepción de dominio del mecanismo de desempate. Unificar al criterio amplio
  **ampliaría por informe el acceso que la pantalla operativa restringe**, que es precisamente la
  puerta trasera que el contrato común prohíbe.
- **Trade-off aceptado:** un parámetro más en el resolutor, y la obligación de que cada listado
  declare cuál usa. A cambio, ningún informe abre acceso que su pantalla no daba.

## Project Structure

### Documentation (this feature)

```text
specs/002-tactico/Red-Operativa/informes-tacticos-simples/
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
│       └── acotamiento.py                # se CORRIGE: criterio de pertenencia parametrizable
├── apps/
│   └── red_operativa/                    # EXISTENTE — se extiende
│       ├── views/
│       │   ├── informes_flota_views.py           # US1
│       │   ├── informes_baja_views.py            # US2
│       │   └── informes_region_views.py          # US3 — regiones y validaciones
│       ├── services/
│       │   ├── informes_flota_service.py         # US1
│       │   ├── informes_baja_service.py          # US2
│       │   └── informes_region_service.py        # US3 — reloj inyectable (días detenida)
│       ├── permissions.py                # clases de permiso de informes
│       ├── urls.py                       # 4 rutas nuevas
│       └── tests/{unit,repositories,services,api,performance}/
└── core/repositories/red_operativa/
    ├── informes_flota_repository.py          # US1 — Dim_UnidadEmergencia
    ├── informes_baja_repository.py           # US2 — Fact_BajaUnidad
    └── informes_region_repository.py         # US3 — Dim_RegionOperativa + Dim_ValidacionRegion
```

**Structure Decision.** Mismo criterio que los tres módulos anteriores. La resolución geográfica
**no se reimplementa**: se usa el repositorio de catálogo de ubicación que ya resuelve por lotes.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Criterio de pertenencia parametrizable en el resolutor de acotamiento | Los departamentos usan dos criterios distintos en sus pantallas operativas, y un informe no puede ser más amplio que su pantalla | Un criterio único rompe la regla en un departamento u otro: el amplio abre acceso indebido en Red Operativa y Suscripciones; el estricto lo cierra indebidamente en Soporte |
| Campo en la respuesta que declara el alcance del listado de flota | Quien consuma el endpoint sin leer el contrato es exactamente quien confundiría composición con disponibilidad | Documentarlo solo en el contrato no protege al consumidor que no lo lee, y el coste de esa confusión es una decisión de cobertura equivocada |

## Phase Status

- [x] **Phase 0 — Research**: [`research.md`](research.md), 7 decisiones, 0 NEEDS CLARIFICATION.
- [x] **Phase 1 — Design**: [`data-model.md`](data-model.md), [`contracts/`](contracts/), [`quickstart.md`](quickstart.md).
- [x] **Post-Design Constitution Check**: PASS. Dos conflictos resueltos vía Tie-Breaker; dos
  entradas de Complexity Tracking justificadas. **Safety declarada como relevante** aunque el módulo
  no toque el camino crítico.
- [ ] **Phase 2 — Tasks**: pendiente de `/speckit-tasks`.

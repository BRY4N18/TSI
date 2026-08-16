# Implementation Plan: Informes Tácticos Simples de Partners y API (Backend)

**Branch**: `informes-tacticos-simples-partners-api` | **Date**: 2026-08-14 | **Spec**: [`spec.md`](spec.md)

**Input**: Feature specification from `specs/002-tactico/Partners-API/informes-tacticos-simples/backend/spec.md`

**Capa hermana (UI):** aplazada deliberadamente — ver [`../informes-tacticos-simples.md`](../informes-tacticos-simples.md).

## Summary

Implementar **5 endpoints de listado de solo lectura** dentro de `backend/apps/partners`, en capas
**Vista → Servicio → Repositorio**, reutilizando íntegramente la capa transversal
`backend/core/informes/` **y el mecanismo de propiedad ya existente en el propio módulo**.

Es el segundo módulo consecutivo que **no toca nada compartido**, y el último que acota por
organización.

## Traceability

- **Objetivos tácticos:** OT08 (incorporar partners con contrato estable), OT09 (controlar y
  tarificar el consumo), OT10 (entregar datos conforme al alcance contratado).
- **Objetivos operativos / casos de uso:** OP26, OP31, CU-O49, CU-O50, CU-T11, CU-T12.
- **Catálogo:** `informestacticos/TSI-Informes-Tacticos-Requeridos-por-OT.md` §6.
- **Contrato común:** [`../../contrato-informes-simples.md`](../../contrato-informes-simples.md).
- **Módulos previos:** los cinco anteriores. Se reutilizan **sin modificarlos**.
- **Dependencias:** ninguna app nueva, ninguna corrección transversal.

## Technical Context

**Language/Version**: Python 3.11 (Django 5 + DRF).

**Primary Dependencies**: `PinotClient`; `core/informes/` completo; `verificar_propiedad` y las
enumeraciones de dominio del propio módulo. **Sin dependencias nuevas.**

**Storage**: Apache Pinot, solo lectura — `Dim_Partner`, `Dim_CredencialAPI`,
`Fact_HistorialAccesoPartner`, `Dim_VersionContratoAPI`, `Dim_Preferencias_Cliente`, más
`Dim_Cliente`, `Dim_Usuarios` y `Dim_Servicio` como catálogos. **Ninguna tabla nueva, ningún cambio
de esquema.**

**Testing**: pytest con el layout de `apps/partners/tests/`. Las pruebas de D2 (el motivo no se
afirma) y D3 (lista blanca de columnas) **deben inspeccionar el código y la respuesta serializada
completa**, no el doble en memoria.

**Target Platform**: Linux containerizado. **No requiere ClickHouse.**

**Project Type**: Web application (solo capa backend).

**Performance Goals**: SC-007 — primera página de los cinco listados en menos de 2 s.

**Constraints**: rutas `/api/v1/informes/partners-api/*`; cursor keyset; `LIMIT` explícito;
**columnas enumeradas en todos los repositorios** (research D3); **el listado de credenciales no
afirma el motivo de inactividad** (research D2); **los filtros de enumeración importan los valores
del dominio, no los copian** (research D5).

**Scale/Scope**: 5 endpoints, 0 apps nuevas, **0 cambios en la capa transversal**, 0 tablas nuevas.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Característica ISO 25010 | Estado | Justificación |
|---|---|---|
| **Functional Suitability** | PASS | 5 FR de listado trazables a un OP o CU. **Corrección reforzada por research D2**: el listado de credenciales no afirma un motivo que su fuente no puede sostener. |
| **Reliability** | PASS | Solo lectura, fuera del camino crítico. Listado vacío devuelve `200 data:[]`; el retraso de ingesta se documenta y no se compensa. |
| **Performance Efficiency** | PASS | SC-007 (<2 s). El filtro de caducidad se resuelve **entero en la base** por ser marca de tiempo numérica (research D7). Se descarta resolver el motivo de inactividad precisamente porque exigiría N+1 consultas. |
| **Interaction Capability** | **N/A** | Capa backend sin superficie de usuario. Se hereda `design-system.md` §8, recogido en FR-016. |
| **Security** | PASS | **Doble refuerzo.** El secreto de autenticación se protege con **lista blanca de columnas**, no con lista negra (research D3), y la lista negra existente queda como segunda línea. El acotamiento reutiliza una comprobación que **lanza en vez de devolver un booleano**, para que no pueda ignorarse por descuido. |
| **Compatibility** | PASS | Endpoints nuevos y aditivos. **Ningún cambio en la capa transversal, en la consola de registros ni en el servicio de consulta existente.** |
| **Maintainability** | PASS | Reutiliza `verificar_propiedad` y las enumeraciones del dominio **importándolas**, de modo que un estado nuevo no obliga a tocar el módulo de informes. |
| **Flexibility** | PASS | Segundo módulo consecutivo que solo consume la capa compartida. |
| **Safety** | **N/A** | Listados de integración, fuera del camino crítico de seguridad física. |

### Tie-Breaker Mechanism

**Conflicto identificado: Functional Suitability vs. Performance Efficiency** en D2 (motivo de
inactividad de una credencial).

- **En conflicto:** un listado de credenciales **con** el motivo sería más completo; obtenerlo exige
  una consulta a la bitácora por credencial, o una agregación con cruce.
- **Priorizado:** **excluir el motivo**, y ofrecerlo en el listado de bitácora.
- **Regla aplicada:** aquí no decide el rendimiento sino la corrección funcional. La fuente **no
  contiene** el dato: cualquier motivo que el listado mostrara sería una inferencia, y una inferencia
  equivocada en este punto lleva a resucitar una credencial comprometida.
- **Trade-off aceptado:** para saber por qué una credencial está inactiva hay que mirar la bitácora.
  Se compensa listando allí los motivos con su tipo propio, de modo que la pregunta tiene respuesta
  aunque no en la misma fila.

**Segundo conflicto: Security vs. Maintainability** en D3 (lista blanca frente a lista negra).

- **En conflicto:** reutilizar la lista negra existente sería menos código; enumerar columnas en cada
  repositorio es más verboso.
- **Priorizado:** **Security** — lista blanca.
- **Regla aplicada:** excepción de dominio del mecanismo de desempate; el dato en juego es el secreto
  con el que un partner se autentica.
- **Trade-off aceptado:** unas líneas más por repositorio. A cambio, **una columna sensible añadida
  mañana no se filtra sola**: la lista negra falla abierta, la blanca falla cerrada.

## Project Structure

### Documentation (this feature)

```text
specs/002-tactico/Partners-API/informes-tacticos-simples/
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
│   └── partners/                         # EXISTENTE — se extiende
│       ├── views/informes_views.py               # 5 vistas
│       ├── services/
│       │   ├── informes_acceso_service.py        # US1 — partners y credenciales
│       │   ├── informes_bitacora_service.py      # US2 — cambios de acceso
│       │   └── informes_contrato_service.py      # US3 — versiones y alcance
│       ├── permissions.py                # se AÑADEN clases de informes; `verificar_propiedad` NO se toca
│       ├── urls.py                       # 5 rutas nuevas
│       └── tests/{unit,repositories,services,api,performance}/
└── core/repositories/partners/
    ├── informes_acceso_repository.py         # US1 — Dim_Partner + Dim_CredencialAPI
    ├── informes_bitacora_repository.py       # US2 — Fact_HistorialAccesoPartner
    └── informes_contrato_repository.py       # US3 — Dim_VersionContratoAPI + Dim_Preferencias_Cliente
```

**Structure Decision.** Mismo criterio que los módulos anteriores. Las cinco vistas caben en un
fichero por ser finas; servicios y repositorios se separan por historia para que las tres sigan
siendo implementables en paralelo. **`verificar_propiedad` y el servicio de consulta existente no se
modifican**: se importan.

## Complexity Tracking

*Sin violaciones que justificar.* Segundo módulo consecutivo con esta tabla vacía: no añade piezas
transversales, no corrige nada compartido y no introduce patrones nuevos. La lista blanca de D3 no es
complejidad añadida sino una forma más segura de hacer lo mismo.

## Riesgo heredado, ya anotado

**La resolución de cuenta cae en el administrador local** (research D1), porque la tabla de vínculos
usuario-cuenta no la escribe ningún código de producción. Un usuario de partner que no sea
administrador local de su cuenta recibirá una negativa.

Es la limitación anotada en el módulo de Soporte, **no un defecto de estos listados**, y su
resolución sigue siendo una decisión de negocio pendiente.

## Phase Status

- [x] **Phase 0 — Research**: [`research.md`](research.md), 7 decisiones, 0 NEEDS CLARIFICATION.
- [x] **Phase 1 — Design**: [`data-model.md`](data-model.md), [`contracts/`](contracts/), [`quickstart.md`](quickstart.md).
- [x] **Post-Design Constitution Check**: PASS, sin violaciones. Dos conflictos resueltos vía
  Tie-Breaker.
- [ ] **Phase 2 — Tasks**: pendiente de `/speckit-tasks`.

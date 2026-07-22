---

description: "Task list for incorporacion-regional (Onboarding y Validación de Región Operativa)"
---

# Tasks: Onboarding y Validación de Región Operativa

**Input**: Design documents from `specs/003-operational/Red-Operativa/incorporacion-regional/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/incorporacion-regional.openapi.yaml, quickstart.md

**Tests**: Incluidos explícitamente (instrucción de usuario: cada task de servicio/repositorio trae su test según `testing.md` — markers `unit`/`repository`/`service`/`api`, patrón AAA). Escribir el test antes de la implementación y confirmar que falla primero.

**Organization**: Tareas agrupadas por historia de usuario para permitir implementación y prueba independientes.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Puede ejecutarse en paralelo (archivos distintos, sin dependencias)
- **[Story]**: Historia de usuario a la que pertenece (US1..US4)
- Rutas de archivo exactas en cada descripción

## Path Conventions (de `plan.md`)

- Backend: `backend/apps/red_operativa/` (app existente, compartida con `alta-unidades`), `backend/core/repositories/red_operativa/`
- Frontend: `frontend/src/app/modules/red-operativa/incorporacion-regional/`
- Tests backend: `backend/apps/red_operativa/tests/{api,services}/`, `backend/core/repositories/red_operativa/../tests` sigue convención existente en `backend/apps/red_operativa/tests/repositories/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirmar que la infraestructura compartida de `red_operativa` (creada por `alta-unidades`) está lista para extenderse; no requiere inicialización nueva de proyecto.

- [X] T001 Verificar que `backend/apps/red_operativa/` y `backend/core/repositories/red_operativa/kafka_writer.py` existen y están registrados en `backend/config/urls.py` (no crear app nueva, ver `plan.md` Structure Decision)
- [X] T002 [P] Confirmar tópicos Kafka `Dim_RegionOperativa_topic` y `Dim_ValidacionRegion_topic` en `backend/config/settings.py` (`KAFKA_TOPICS`), agregando entradas `"region_operativa_snapshot": "Dim_RegionOperativa_topic"` y `"validacion_region_snapshot": "Dim_ValidacionRegion_topic"` si no existen, siguiendo el patrón de `"unidad_emergencia_snapshot": "Dim_UnidadEmergencia_topic"`
- [X] T003 [P] Confirmar que el módulo Angular `frontend/src/app/modules/red-operativa/` existe y crear la subcarpeta `incorporacion-regional/` con `models/`, `services/`, `guards/`, `pages/`

**Checkpoint**: Infraestructura compartida confirmada — listo para foundational.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Repositorios base y permisos que TODAS las historias de usuario necesitan.

**⚠️ CRITICAL**: Ninguna historia de usuario puede comenzar hasta completar esta fase.

- [X] T004 [P] Documentar la forma esperada de `RegionOperativa` (campos `data-model.md` §1) como comentario/type hint `dict[str, Any]` en el docstring de `region_operativa_repository.py` — sin `models.py` ni dataclass, siguiendo el patrón real ya usado por `unidad_emergencia_repository.py` (retorno `dict[str, Any]` directo de Pinot, sin capa de dataclass en esta app)
- [X] T005 [P] Documentar la forma esperada de `ValidacionRegion` (campos `data-model.md` §2) como comentario/type hint `dict[str, Any]` en el docstring de `validacion_region_repository.py`, mismo patrón que T004
- [X] T006 [P] Implementar `RegionOperativaRepository` en `backend/core/repositories/red_operativa/region_operativa_repository.py` (get, list con cursor/estadoregion, create, update estadoregion/activo — lectura Pinot, escritura Kafka vía `kafka_writer.py`; retorna `dict[str, Any]`, mismo estilo que `unidad_emergencia_repository.py`)
- [X] T007 [P] [unit/repository, AAA] Test de `RegionOperativaRepository` en `backend/apps/red_operativa/tests/repositories/test_region_operativa_repository.py` (marker `repository`, mocks `mock_pinot`/`mock_kafka` de `conftest.py`; casos: get existente, get inexistente, create publica evento, update estadoregion publica evento) — escribir primero, debe fallar antes de T006
- [X] T008 [P] Implementar `ValidacionRegionRepository` en `backend/core/repositories/red_operativa/validacion_region_repository.py` (insert append-only, list histórico ordenado por `fechahora` ascendente, `existe_aprobada(idregionoperativa)` para RN-REGON-003)
- [X] T009 [P] [unit/repository, AAA] Test de `ValidacionRegionRepository` en `backend/apps/red_operativa/tests/repositories/test_validacion_region_repository.py` (marker `repository`; casos: insert nunca sobrescribe, list ordenado por fechahora, `existe_aprobada` true/false) — escribir primero, debe fallar antes de T008
- [X] T010 [P] Implementar `AccidenteActivoReadRepository` (solo lectura) en `backend/core/repositories/red_operativa/accidente_activo_read_repository.py` (`existen_casos_activos(idregionoperativa)` consultando `Fact_Accidente` sin cierre, módulo Emergencias)
- [X] T011 [P] [unit/repository, AAA] Test de `AccidenteActivoReadRepository` en `backend/apps/red_operativa/tests/repositories/test_accidente_activo_read_repository.py` (marker `repository`; casos: con casos activos, sin casos activos) — escribir primero, debe fallar antes de T010
- [X] T012 Extender `backend/apps/red_operativa/permissions.py` con `IsAdministradorRedOperativa` (reutilizar si ya existe de `alta-unidades`) y `IsDirectorTecnologico` (nuevo)
- [X] T013 [P] [unit, AAA] Test de permisos en `backend/apps/red_operativa/tests/unit/test_incorporacion_regional_permissions.py` (marker `unit`; casos: Administrador permitido/denegado, Director Tecnológico permitido/denegado por operación) — escribir primero, debe fallar antes de T012

**Checkpoint**: Repositorios y permisos listos — las historias de usuario pueden implementarse en paralelo.

---

## Phase 3: User Story 1 - Ejecutar protocolo de validación de operatividad (Priority: P1) 🎯 MVP

**UC**: CU-O55 | **CA**: CA-REGON-001, CA-REGON-002, CA-REGON-003

**Goal**: El Administrador ejecuta el protocolo (revisión manual) y el Director Tecnológico queda registrado como aprobador; el resultado mueve `estadoregion` a `Producción` solo si es `Aprobada`. Incluye alta de región nueva y reingreso/reactivación desde `En_Alerta`/`Despublicada`.

**Independent Test**: `POST /api/v1/red-operativa/regiones/validaciones` con `resultado="Aprobada"` sobre una región nueva devuelve `200` con `estadoregion="Producción"`; con `resultado="Rechazada"` devuelve `200` con `estadoregion="En_Validación"` (Quickstart Escenario A/B/E).

### Tests for User Story 1 ⚠️

> Escribir primero, confirmar que fallan antes de implementar.

- [X] T014 [P] [US1] [api, AAA] Contract test `POST /red-operativa/regiones/validaciones` en `backend/apps/red_operativa/tests/api/test_ejecutar_validacion_contract.py` (marker `api`; casos: alta+aprobada→201/200 con Producción, alta+rechazada→En_Validación, motivo obligatorio si Rechazada→400, reingreso desde Despublicada→Producción, sin auth→401, rol no autorizado→403)
- [X] T015 [P] [US1] [service, AAA] Test de `ValidacionRegionService` en `backend/apps/red_operativa/tests/services/test_validacion_region_service.py` (marker `service`, repos mockeados; casos: crea región si no existe, inserta validación siempre, Aprobada actualiza estadoregion, Rechazada no cambia estadoregion, reingreso desde cualquier estado no-inactivo, concurrencia last-write-wins simulada con dos inserts consecutivos)

### Implementation for User Story 1

- [X] T016 [US1] Implementar `ValidacionRegionService` en `backend/apps/red_operativa/services/validacion_region_service.py` (depende de T006, T008; alta condicional, insert validación, transición `estadoregion`, sin checklist automatizado per Clarifications) — depende de T014, T015 en rojo
- [X] T017 [US1] Implementar vista DRF `POST /red-operativa/regiones/validaciones` en `backend/apps/red_operativa/views/region_views.py` (usa `ValidacionRegionService`, valida `Idempotency-Key`, aplica `IsAdministradorRedOperativa`/`IsDirectorTecnologico`)
- [X] T018 [US1] Registrar ruta en `backend/apps/red_operativa/views/urls.py` según contrato OpenAPI
- [X] T019 [P] [US1] Crear modelo TS `RegionOperativa`/`ValidacionRegionRequest`/`Response` en `frontend/src/app/modules/red-operativa/incorporacion-regional/models/region-operativa.contract.ts` (alineado 1:1 al schema OpenAPI)
- [X] T020 [US1] Implementar `RegionOperativaApiService.ejecutarValidacion()` en `frontend/src/app/modules/red-operativa/incorporacion-regional/services/region-operativa-api.service.ts`
- [X] T021 [US1] Implementar `RegionOperativaFacadeService` en `frontend/src/app/modules/red-operativa/incorporacion-regional/services/region-operativa-facade.service.ts` (orquesta llamada + estado de UI, sin lógica de negocio en componentes)
- [X] T022 [US1] Página `frontend/src/app/modules/red-operativa/incorporacion-regional/pages/validacion/` (formulario alta/validación, muestra `estadoregion_actual` tras respuesta)
- [X] T023 [US1] Guard `frontend/src/app/modules/red-operativa/incorporacion-regional/guards/administrador-red-operativa.guard.ts` (reutilizar el de `alta-unidades` si existe, si no crear siguiendo su mismo patrón)

**Checkpoint**: US1 completamente funcional y probable de forma independiente — MVP entregable.

---

## Phase 4: User Story 2 - Gestionar resultado fallido y remediación (Priority: P2)

**UC**: CU-O60 | **CA**: CA-REGON-004, CA-REGON-005

**Goal**: Consultar el historial completo de intentos de validación por región y marcar rechazo definitivo (`activo=false`) sin insertar un nuevo estado.

**Independent Test**: `GET /api/v1/red-operativa/regiones/{id}/validaciones` devuelve las filas ordenadas por `fechahora`; `POST /api/v1/red-operativa/regiones/{id}/rechazo-definitivo` devuelve `200` con `activo=false` (Quickstart Escenario C).

### Tests for User Story 2 ⚠️

- [X] T024 [P] [US2] [api, AAA] Contract test `GET /red-operativa/regiones/{id}/validaciones` en `backend/apps/red_operativa/tests/api/test_historial_validacion_contract.py` (marker `api`; casos: historial ordenado, región inexistente→404, sin auth→401)
- [X] T025 [P] [US2] [api, AAA] Contract test `POST /red-operativa/regiones/{id}/rechazo-definitivo` en `backend/apps/red_operativa/tests/api/test_rechazo_definitivo_contract.py` (marker `api`; casos: región en En_Validación→200/activo=false, región en Producción→409, región inexistente→404)
- [X] T026 [P] [US2] [service, AAA] Test de `RemediacionRegionService` en `backend/apps/red_operativa/tests/services/test_remediacion_region_service.py` (marker `service`, repos mockeados; casos: historial delega a repositorio sin transformar orden, rechazo definitivo solo permitido si estadoregion=En_Validación, rechazo definitivo no inserta fila de validación)

### Implementation for User Story 2

- [X] T027 [US2] Implementar `RemediacionRegionService` en `backend/apps/red_operativa/services/remediacion_region_service.py` (depende de T006, T008) — depende de T024-T026 en rojo
- [X] T028 [US2] Implementar vistas DRF `GET .../validaciones` y `POST .../rechazo-definitivo` en `backend/apps/red_operativa/views/region_views.py`
- [X] T029 [US2] Registrar rutas en `backend/apps/red_operativa/views/urls.py`
- [X] T030 [P] [US2] Extender `region-operativa-api.service.ts` con `listarHistorialValidacion()` y `rechazarDefinitivamente()`
- [X] T031 [US2] Extender página `pages/validacion/` con tabla de historial y acción de rechazo definitivo (reutiliza `RegionOperativaFacadeService`)

**Checkpoint**: US1 y US2 funcionan de forma independiente y en conjunto.

---

## Phase 5: User Story 3 - Re-evaluar/despublicar región habilitada (Priority: P2)

**UC**: CU-O61 | **CA**: CA-REGON-006, CA-REGON-007

**Goal**: El Director Tecnológico degrada (`En_Alerta`) o despublica (`Despublicada`) una región en `Producción`, sin cancelar casos activos.

**Independent Test**: `POST /api/v1/red-operativa/regiones/{id}/reevaluacion` con `estadoregion="Despublicada"` sobre una región en `Producción` con casos activos devuelve `200`, y los casos activos permanecen consultables (Quickstart Escenario D).

### Tests for User Story 3 ⚠️

- [X] T032 [P] [US3] [api, AAA] Contract test `POST /red-operativa/regiones/{id}/reevaluacion` en `backend/apps/red_operativa/tests/api/test_reevaluacion_region_contract.py` (marker `api`; casos: Producción→En_Alerta 200, Producción→Despublicada con casos activos 200 (no cancela), estado origen inválido→409, rol Administrador→403, rol Director Tecnológico→200)
- [X] T033 [P] [US3] [service, AAA] Test de `ReevaluacionRegionService` en `backend/apps/red_operativa/tests/services/test_reevaluacion_region_service.py` (marker `service`, repos mockeados incl. `AccidenteActivoReadRepository`; casos: transición válida actualiza estadoregion, transición inválida lanza conflicto, consulta de continuidad no bloquea la despublicación, solo bloquea casos nuevos — no cancela)

### Implementation for User Story 3

- [X] T034 [US3] Implementar `ReevaluacionRegionService` en `backend/apps/red_operativa/services/reevaluacion_region_service.py` (depende de T006, T010) — depende de T032, T033 en rojo
- [X] T035 [US3] Implementar vista DRF `POST .../reevaluacion` en `backend/apps/red_operativa/views/region_views.py` con `IsDirectorTecnologico`
- [X] T036 [US3] Registrar ruta en `backend/apps/red_operativa/views/urls.py`
- [X] T037 [P] [US3] Extender `region-operativa-api.service.ts` con `reevaluarRegion()`
- [X] T038 [P] [US3] Guard `frontend/src/app/modules/red-operativa/incorporacion-regional/guards/director-tecnologico.guard.ts`
- [X] T039 [US3] Página `frontend/src/app/modules/red-operativa/incorporacion-regional/pages/reevaluacion/` (degradar/despublicar, protegida por `director-tecnologico.guard.ts`)

**Checkpoint**: US1, US2 y US3 funcionan de forma independiente.

---

## Phase 6: User Story 4 - Despublicación automática por pérdida total de cobertura (Priority: P3)

**UC**: CU-O62 | **CA**: CA-REGON-008

**Goal**: Servicio idempotente que despublica una región sin actor humano. Expuesto vía endpoint invocable manual/cron; **sin disparador automático conectado** (RN-REGON-005, ver `plan.md` Complexity Tracking).

**Independent Test**: `POST /api/v1/red-operativa/regiones/{id}/despublicacion-automatica` sobre una región en `Producción` o `En_Alerta` devuelve `200` con `estadoregion="Despublicada"` y sin `idusuario` (Quickstart Escenario F).

### Tests for User Story 4 ⚠️

- [X] T040 [P] [US4] [api, AAA] Contract test `POST /red-operativa/regiones/{id}/despublicacion-automatica` en `backend/apps/red_operativa/tests/api/test_despublicacion_automatica_contract.py` (marker `api`; casos: Producción→Despublicada 200, En_Alerta→Despublicada 200, ya Despublicada→409, sin idusuario en la respuesta)
- [X] T041 [P] [US4] [service, AAA] Test de `DespublicacionAutomaticaService` en `backend/apps/red_operativa/tests/services/test_despublicacion_automatica_service.py` (marker `service`, repos mockeados; casos: idempotencia — invocar dos veces no duplica transición, no requiere idusuario, transición inválida lanza conflicto)

### Implementation for User Story 4

- [X] T042 [US4] Implementar `DespublicacionAutomaticaService` en `backend/apps/red_operativa/services/despublicacion_automatica_service.py` (depende de T006) — depende de T040, T041 en rojo
- [X] T043 [US4] Implementar vista DRF `POST .../despublicacion-automatica` en `backend/apps/red_operativa/views/region_views.py` (sin `idusuario`, ver RF-REGON-004)
- [X] T044 [US4] Registrar ruta en `backend/apps/red_operativa/views/urls.py`

**Checkpoint**: Las 4 historias de usuario funcionan de forma independiente. `CU-O62` queda documentado como servicio invocable sin disparador automático conectado (excepción explícita en `plan.md`).

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Mejoras que afectan a varias historias.

- [X] T045 [P] Ejecutar y confirmar cobertura ≥80% en `backend/apps/red_operativa/services/` y ≥85% en `backend/core/repositories/red_operativa/` (umbral de `testing.md`)
- [X] T046 [P] Ejecutar `pytest -m critical_path -v` si alguno de los flujos toca el camino crítico (despublicación con casos activos, RF-REGON-003) y confirmar <1s por test
- [DEFERRED] T047 Ejecutar `quickstart.md` completo (Escenarios A–G) contra un entorno local con docker-compose — requiere infraestructura (Pinot/Kafka reales) no disponible en este entorno de implementación; los escenarios A-G están cubiertos equivalentemente por los tests de contrato (`pytest -m api`), que usan el mismo Pinot/Kafka in-memory de `conftest.py`
- [X] T048 [P] Revisar que ningún endpoint nuevo escriba directo a Pinot (regla vinculante `architectural-patterns.md` §1)
- [X] T049 Actualizar `module-map.md` §7 marcando `incorporacion-regional` como "✅ Implementado (backend + Angular, app `red_operativa`)" tras completar frontend

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias — inicia de inmediato.
- **Foundational (Phase 2)**: depende de Setup — BLOQUEA todas las historias de usuario.
- **User Stories (Phase 3-6)**: todas dependen de Foundational.
  - US1 (P1) es el MVP y no depende de US2/US3/US4.
  - US2 (P2) depende de datos creados por US1 en runtime (una región debe existir para tener historial), pero es una historia técnicamente independiente — usa fixtures propias en sus tests.
  - US3 (P2) depende de que exista una región en `Producción` en runtime, pero no depende del código de US1/US2.
  - US4 (P3) es independiente de US1-US3 en código; en runtime opera sobre regiones ya en `Producción`/`En_Alerta`.
- **Polish (Phase 7)**: depende de que las historias deseadas estén completas.

### Parallel Opportunities

- Todas las tareas [P] de Setup y Foundational en paralelo.
- Una vez Foundational completo, US1, US2, US3 y US4 pueden trabajarse en paralelo (equipos distintos), aunque US2/US3/US4 se prueban de forma más realista después de tener US1 desplegado.
- Dentro de cada historia: tests [P] en paralelo entre sí; implementación de servicio depende de que su(s) test(s) estén en rojo primero.

---

## Parallel Example: User Story 1

```bash
# Tests primero (deben fallar):
Task: "Contract test POST /red-operativa/regiones/validaciones en backend/apps/red_operativa/tests/api/test_ejecutar_validacion_contract.py"
Task: "Service test ValidacionRegionService en backend/apps/red_operativa/tests/services/test_validacion_region_service.py"

# Luego implementación:
Task: "Implementar ValidacionRegionService en backend/apps/red_operativa/services/validacion_region_service.py"
Task: "Implementar vista DRF en backend/apps/red_operativa/views/region_views.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 solamente)

1. Completar Phase 1: Setup
2. Completar Phase 2: Foundational (bloqueante)
3. Completar Phase 3: User Story 1 (CU-O55 aprobado/rechazado + alta + reingreso)
4. **Detener y validar**: Quickstart Escenarios A, B, E
5. Desplegar/demo si está listo (habilita que `registro-accidente` empiece a validar `estadoregion='Producción'`)

### Incremental Delivery

1. Setup + Foundational → base lista.
2. US1 → probar independientemente → Deploy/Demo (MVP).
3. US2 (historial + rechazo definitivo) → probar independientemente → Deploy/Demo.
4. US3 (degradar/despublicar) → probar independientemente → Deploy/Demo.
5. US4 (despublicación automática, sin disparador) → probar independientemente → Deploy/Demo.
6. Cada historia agrega valor sin romper las anteriores.

---

## Notes

- [P] = archivos distintos, sin dependencias.
- [Story] mapea cada tarea a su historia de usuario para trazabilidad.
- Tests obligatorios por instrucción explícita del usuario: cada servicio/repositorio trae su test con marker (`unit`/`repository`/`service`/`api`) y patrón AAA, siguiendo `testing.md`. Escribir el test primero y confirmar que falla antes de implementar.
- `CU-O62` (US4) es una excepción documentada: el servicio y endpoint quedan completos, pero el disparador automático real (evento de cero-unidades-activas) no se conecta en este ciclo — ver `plan.md` Complexity Tracking y `research.md` Decision 4.
- Commitear después de cada tarea o grupo lógico.
- Evitar: tareas vagas, conflictos de mismo archivo entre tareas paralelas, dependencias cruzadas entre historias que rompan su independencia.
- **Pasada de diseño (post-implementación, 2026-07-22):** las 6 páginas del módulo `red-operativa` (2 de `incorporacion-regional` + 4 de `alta-unidades`, que estaban sin estilo desde antes) se estilizaron con Tailwind + los tokens de `design-system.md`/`styles.css` (cards `bg-bg-surface`/`border-border-default`, botones/badges semánticos por `estadoregion`, íconos Tabler para alertas). Verificado con `tsc --noEmit` y `ng build` limpios. Este gap de estilo era sistémico en casi todo el frontend (32/35 páginas sin CSS) — solo se corrigió el módulo Red-Operativa por alcance explícito del usuario; el resto de módulos sigue pendiente si se requiere más adelante.

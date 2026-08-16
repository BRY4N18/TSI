---

description: "Task list for feature implementation"
---

# Tasks: Informes Tácticos Simples de Emergencias (Backend)

**Input**: Design documents from `specs/002-tactico/Emergencias/informes-tacticos-agregados/backend/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/informes-tacticos-agregados.openapi.yaml](contracts/informes-tacticos-agregados.openapi.yaml), [quickstart.md](quickstart.md)

**Tests**: Incluidos, siguiendo la convención ya establecida en el proyecto (`testing.md`, ver `specs/003-operational/Emergencias/registro-accidente/backend/tasks.md`): markers pytest `repository`/`service`/`api`, patrón AAA, fixture `mock_pinot` para simular `PinotClient.query` sin red real.

**Organization**: Tareas agrupadas por historia de usuario de `spec.md`. US1 (Registro) y US2 (Despacho) son P1; US3 (Seguimiento) es P2.

> **Revisión final contra el sistema real (2026-08-02).** Los 19 endpoints (16 simples + 3 compuestos) probados con `curl` real, con datos reales de Pinot/ClickHouse, incluyendo casos límite (sin datos, parámetros faltantes, control de acceso). Se encontraron y corrigieron 3 bugs reales que los tests con mock no habían detectado:
> 1. **`IN (%(ids)s)` con paréntesis duplicados** — el cliente Pinot ya envuelve listas en paréntesis; escribir `IN (%(param)s)` genera `IN ((v1, v2))`, que Pinot interpreta como constructor de fila (ROW) y rechaza con `SQLParsingError`. Solo se manifestaba con listas de 2+ elementos (por eso `ratio-demanda-capacidad` pasó el primer recorrido: tenía un único `idcalle` distinto). Corregido en 6 sitios de `despacho_repository.py`/`seguimiento_repository.py` → patrón correcto `IN %(param)s` (confirmado contra otros repositorios ya existentes del proyecto).
> 2. **`DATETRUNC(...)` de Pinot real devuelve epoch milliseconds, no un string de fecha** — asunción incorrecta arrastrada del mock de Pinot (`mock_pinot`), que yo mismo escribí devolviendo strings. Afectaba a `volumen-casos`, `completitud-campos-criticos`, `descarte-fusion` y `cierres-forzados` (el campo `periodo` salía como `1783814400000` en vez de `"2026-07-12"`). Corregido con un helper `periodo_str()` nuevo en `core/repositories/informes_tacticos/_periodo_utils.py`, y el mock de `conftest.py` ajustado para devolver epoch ms (igual que Pinot real) en vez de strings — el mock ahora refleja la realidad en vez de una simulación conveniente.
> 3. **`IS NOT NULL` de Pinot no filtra el sentinel de "sin valor"** (`enableColumnBasedNullHandling=false`, documentado en `PinotClient`) — `fechahorallegada IS NOT NULL` en SQL dejaba pasar despachos sin llegada real, causando `TypeError` al restar `None - int`. Corregido filtrando en Python después de la coerción de tipos del cliente.
>
> **Bug preexistente ajeno, encontrado y corregido con autorización explícita**: `HistorialUbicacionRepository` (`core/repositories/seguimiento/`) usaba la columna `idhistorialubicacion` en 3 archivos consistentes entre sí (repositorio, servicio `GpsDepuracionService`, tests) pero inexistente en el esquema real de Pinot (`idhistorialunidademergencia`). Nunca se detectó porque el mock de `conftest.py` también usaba el nombre equivocado, así que todo el conjunto quedaba autoconsistente sin tocar Pinot real. Corregido en los 4 archivos + 2 branches adicionales del mock que usaban el nombre viejo en mayúsculas (sed no las alcanzó por case-sensitivity). Verificado con una escritura real GPS contra Pinot tras el fix.
>
> Suite completa del backend tras todos los fixes: **1006 passed, 0 rotos**.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Ejecutable en paralelo (archivos distintos, sin dependencia directa)
- **[Story]**: US1 (Registro de Accidente, 7 informes), US2 (Despacho Inteligente, 6 informes), US3 (Seguimiento y Cierre de Casos, 3 informes)
- Cada descripción incluye ruta exacta de archivo

## Path Conventions

Web application (backend Django existente): `backend/apps/informes_tacticos/` (app nueva) + `backend/core/pinot/client.py` (reutilizado, sin cambios). Ver estructura completa en `plan.md`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Crear la app Django nueva y su esqueleto, sin lógica de negocio todavía.

- [X] T001 Crear la estructura de carpetas `backend/apps/informes_tacticos/{repositories,services,views,tests/{repositories,services,api}}` con los `__init__.py` correspondientes
- [X] T002 Crear `backend/apps/informes_tacticos/apps.py` (`InformesTacticosConfig`) y registrar la app en `backend/config/settings.py` (`INSTALLED_APPS`)
- [X] T003 [P] Crear `backend/apps/informes_tacticos/urls.py` con el prefijo `/api/v1/informes-tacticos/` y montarlo en el `urls.py` raíz del proyecto
- [X] T004 [P] Verificar que los markers pytest `repository`, `service`, `api` ya declarados en `backend/pytest.ini` cubren esta app (sin añadir markers nuevos, reutilizar los existentes)

**Checkpoint**: La app existe, está registrada y montada, sin endpoints funcionales todavía.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Piezas compartidas por las 3 historias — permisos, envelope, utilidades de período — sin las cuales ningún endpoint puede implementarse consistentemente.

**⚠️ CRITICAL**: Ninguna historia de usuario puede completarse hasta que esta fase esté lista.

- [X] T005 Crear `backend/apps/informes_tacticos/permissions.py` reutilizando `backend/core/auth/permissions.py` para exigir rol Operador o Supervisor de Emergencias (FR-007)
- [X] T006 [P] Crear `backend/apps/informes_tacticos/serializers_meta.py` con el helper de construcción de `meta.periodo`/`meta.filtros` (formato común descrito en `data-model.md`, reutilizado por las 16 vistas)
- [X] T007 [P] Crear `backend/apps/informes_tacticos/periodo.py` con el parseo/validación de `desde`/`hasta`/`granularidad` (query params comunes de `contracts/informes-tacticos-agregados.openapi.yaml`) y la construcción de la expresión `DATETRUNC` para Pinot (research.md §5)
- [X] T008 [P] Crear test unitario de `periodo.py` en `backend/apps/informes_tacticos/tests/unit/test_periodo.py` (marker: unit) cubriendo granularidades `dia`/`semana`/`mes` y rango inválido (`desde > hasta`)
- [X] T009 Verificar en `backend/conftest.py` que el fixture `mock_pinot` y las fixtures de auth (`operador_auth_headers`, ya existentes) están disponibles para `backend/apps/informes_tacticos/tests/`

**Checkpoint**: Permisos, período y envelope compartidos listos — las 3 historias ya pueden implementarse en paralelo.

---

## Phase 3: User Story 1 - Informes de Registro de Accidente (Priority: P1) 🎯 MVP

**Goal**: 7 endpoints de agregación sobre `Fact_Accidente`/`Fact_AccidenteTipoEstadoAccidente` (volumen, severidad, zona, completitud, descarte/fusión, ranking de ubicaciones, impacto humano).

**Independent Test**: Con Phase 1-2 completas, se puede levantar el backend y ejecutar los pasos 1, 3, 4 y 6 (informes de registro) de `quickstart.md`, obteniendo respuestas correctas sin que US2/US3 existan todavía.

> **US1 completa (2026-08-01):** los 7 informes de Registro están implementados de punta a punta y verificados con `pytest` real (41 tests del módulo, suite completa del backend: 955 passed, 0 rotos).
> **Desviación de `plan.md` corregida durante la implementación:** los repositorios viven en `backend/core/repositories/informes_tacticos/` (convención real del proyecto — ver `backend/core/repositories/despacho/`, etc.), no en `backend/apps/informes_tacticos/repositories/` como decía el plan original.
> **Desviación de `spec.md` corregida:** el rol "Supervisor" no existe en el sistema (`.specify/docs/actors.md`); `InformesTacticosLecturaPermission` usa los roles reales `Operador` + `Administrador`.
> **Desviaciones de alcance en `data-model.md` (MVP, documentadas en el código):** `distribucion-zona` e `impacto-humano` agrupan por `idcalle` en vez de resolver la cadena `Dim_Calle→Dim_Ciudad→Dim_Condado→Dim_Estado` (fuera de alcance de este primer corte); `impacto-humano` no particiona por período, solo por ubicación (suma del rango completo).

**Progreso por informe (Registro):**

| Informe | Repo | Service | Vista | Test repo | Test service | Test API |
|---|---|---|---|---|---|---|
| volumen-casos | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| distribucion-severidad | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| distribucion-zona | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| completitud-campos-criticos | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| descarte-fusion | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| ranking-ubicaciones | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| impacto-humano | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

### Tests for User Story 1 ⚠️

- [X] T010 [P] [US1] Test de repositorio (marker: repository, AAA) en `backend/apps/informes_tacticos/tests/repositories/test_registro_repository.py` cubriendo los 7 métodos contra `mock_pinot`, incluyendo el caso "sin datos" (FR-006)
- [X] T011 [P] [US1] Test de servicio (marker: service, AAA) en `backend/apps/informes_tacticos/tests/services/test_registro_informes_service.py` verificando que cada método delega en el repositorio y arma la `meta` correcta
- [X] T012 [P] [US1] Test de API (marker: api, AAA) en `backend/apps/informes_tacticos/tests/api/test_registro_views.py` cubriendo los 7 endpoints: `200` con datos, `200` con `data: []` sin datos, `401` sin token (FR-007)

### Implementation for User Story 1

- [X] T013 [US1] Implementar `backend/apps/informes_tacticos/repositories/registro_repository.py` con 7 métodos (uno por informe de `data-model.md` §Registro), cada uno con su propia consulta SQL a `PinotClient.query` con `GROUP BY`/`LIMIT` explícito (depende de T007, T009)
- [X] T014 [US1] Implementar `backend/apps/informes_tacticos/services/registro_informes_service.py` invocando `registro_repository.py` y construyendo la respuesta con el helper de T006 (depende de T013)
- [X] T015 [US1] Implementar `backend/apps/informes_tacticos/views/registro_views.py` (7 vistas DRF, una por endpoint `/registro/*` de `contracts/informes-tacticos-agregados.openapi.yaml`), aplicando el permiso de T005 (depende de T014)
- [X] T016 [US1] Registrar las 7 rutas de `registro_views.py` en `backend/apps/informes_tacticos/urls.py` (depende de T015, T003)
- [X] T017 [US1] Ejecutar los pasos 1, 3, 4 y 6 (subset Registro) de `quickstart.md` contra el backend real y confirmar `200`/`401` y formas de respuesta correctas

**Checkpoint**: Los 7 informes de Registro son consultables de punta a punta, de forma independiente de Despacho y Seguimiento.

---

## Phase 4: User Story 2 - Informes de Despacho Inteligente (Priority: P1)

**Goal**: 6 endpoints de agregación sobre `Fact_Despacho`/`Fact_HistorialDespachoUnidad`/`Dim_UnidadEmergencia` (asignación automática/manual, tiempos, rechazo/timeout, carga por unidad, ratio demanda/capacidad).

**Independent Test**: Con Phase 1-2 completas, se puede levantar el backend y ejecutar los pasos 2 y 5 de `quickstart.md` (ratio demanda/capacidad y tiempo de respuesta), sin depender de que US1/US3 estén implementadas.

> **US2 completa (2026-08-01).** Pinot no soporta JOIN entre tablas: los cruces (unidad→condado, despacho→severidad del accidente, historial→unidad) se resuelven con una segunda consulta acotada por el mismo rango de fechas y merge en Python — patrón ya usado en el resto del proyecto para relaciones entre tablas Pinot, no una desviación de la regla "filtros/orden en SQL" (esa regla es sobre no paginar/agregar en memoria un conjunto sin acotar; aquí cada consulta intermedia ya viene acotada por fecha o por un `IN` de IDs ya resueltos). `ratio-demanda-capacidad` resuelve la cadena completa `Fact_Accidente.idcalle → Dim_Calle.idciudad → Dim_Ciudad.idcondado` para agrupar la demanda al mismo nivel que la capacidad (`Dim_UnidadEmergencia.idcondado`).

### Tests for User Story 2 ⚠️

- [X] T018 [P] [US2] Test de repositorio (marker: repository, AAA) en `backend/apps/informes_tacticos/tests/repositories/test_despacho_repository.py` cubriendo los 6 métodos, incluyendo el corte opcional por `idcondado`
- [X] T019 [P] [US2] Test de servicio (marker: service, AAA) en `backend/apps/informes_tacticos/tests/services/test_despacho_informes_service.py`
- [X] T020 [P] [US2] Test de API (marker: api, AAA) en `backend/apps/informes_tacticos/tests/api/test_despacho_views.py` cubriendo los 6 endpoints, incluyendo verificación de que `ratio = total_accidentes / unidades_activas` en la respuesta de `ratio-demanda-capacidad`

### Implementation for User Story 2

- [X] T021 [US2] Implementar `backend/apps/informes_tacticos/repositories/despacho_repository.py` con 6 métodos (uno por informe de `data-model.md` §Despacho), cada uno con `GROUP BY`/`LIMIT` explícito (depende de T007, T009)
- [X] T022 [US2] Implementar `backend/apps/informes_tacticos/services/despacho_informes_service.py` (depende de T021)
- [X] T023 [US2] Implementar `backend/apps/informes_tacticos/views/despacho_views.py` (6 vistas DRF bajo `/despacho/*`), aplicando el permiso de T005 (depende de T022)
- [X] T024 [US2] Registrar las 6 rutas de `despacho_views.py` en `backend/apps/informes_tacticos/urls.py` (depende de T023, T003)
- [X] T025 [US2] Ejecutar los pasos 2 y 5 de `quickstart.md` contra el backend real y confirmar resultados correctos, incluyendo el tiempo de respuesta bajo 3s (SC-001)

**Checkpoint**: Los 6 informes de Despacho son consultables de punta a punta, de forma independiente de Registro y Seguimiento.

---

## Phase 5: User Story 3 - Informes de Seguimiento y Cierre de Casos (Priority: P2)

**Goal**: 3 endpoints de agregación sobre `Fact_AccidenteTipoEstadoAccidente`/`Fact_HistorialDespachoUnidad` (tiempo asignado→cerrado, % cierres forzados, % abortos/pérdidas).

**Independent Test**: Con Phase 1-2 completas, se puede levantar el backend y consultar los 3 endpoints de Seguimiento de forma aislada, sin depender de US1/US2.

> **US3 completa (2026-08-01).** Desviación real de `data-model.md`: `Fact_HistorialDespachoUnidad` no tiene columna `idusuario` (verificado en `database/esquemas.json`), así que no se puede distinguir "retirado por operador" de "retirado automático por vencimiento" como proponía el informe original de cierres forzados. `cierres-forzados` aproxima con `estadonuevo = 'Retirado'` sobre el total de transiciones a estado terminal (`Retirado`/`Cerrado`) — documentado en el docstring de `SeguimientoRepository.cierres_forzados`. `tiempo-asignado-cerrado` agrupa por unidad (no por zona) — misma limitación MVP que el resto del módulo.

### Tests for User Story 3 ⚠️

- [X] T026 [P] [US3] Test de repositorio (marker: repository, AAA) en `backend/apps/informes_tacticos/tests/repositories/test_seguimiento_repository.py` cubriendo los 3 métodos
- [X] T027 [P] [US3] Test de servicio (marker: service, AAA) en `backend/apps/informes_tacticos/tests/services/test_seguimiento_informes_service.py`
- [X] T028 [P] [US3] Test de API (marker: api, AAA) en `backend/apps/informes_tacticos/tests/api/test_seguimiento_views.py` cubriendo los 3 endpoints

### Implementation for User Story 3

- [X] T029 [US3] Implementar `backend/apps/informes_tacticos/repositories/seguimiento_repository.py` con 3 métodos (uno por informe de `data-model.md` §Seguimiento) (depende de T007, T009)
- [X] T030 [US3] Implementar `backend/apps/informes_tacticos/services/seguimiento_informes_service.py` (depende de T029)
- [X] T031 [US3] Implementar `backend/apps/informes_tacticos/views/seguimiento_views.py` (3 vistas DRF bajo `/seguimiento/*`), aplicando el permiso de T005 (depende de T030)
- [X] T032 [US3] Registrar las 3 rutas de `seguimiento_views.py` en `backend/apps/informes_tacticos/urls.py` (depende de T031, T003)
- [X] T033 [US3] Recorrer manualmente los 3 endpoints de Seguimiento contra el backend real (mismo patrón que `quickstart.md` paso 1, adaptado a estos 3 informes)

**Checkpoint**: Los 16 informes (7+6+3) son consultables de punta a punta.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Cerrar la spec de backend antes de pasar a `../frontend/`.

- [X] T034 [P] Ejecutar el paso 3 (sin datos) y el paso 4 (control de acceso) de `quickstart.md` contra los 16 endpoints, no solo los usados como ejemplo en cada historia
- [X] T035 [P] Revisar los 16 métodos de repositorio y confirmar que el 100% declara `LIMIT` explícito en su SQL (SC-003 de `../../infraestructura/spec.md` como referencia de criterio, aplicado aquí a esta app — ver FR-003)
- [ ] T036 Actualizar `../informes-tacticos-agregados.md` (índice del módulo) marcando la capa backend como completa y lista para que `../frontend/` empiece
- [ ] T037 Cambiar `.specify/feature.json` → `specs/002-tactico/Emergencias/informes-tacticos-agregados/frontend` para continuar con la capa UI

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Sin dependencias
- **Foundational (Phase 2)**: Depende de Setup — BLOQUEA las 3 historias
- **User Story 1 (Phase 3, P1)**: Depende de Foundational
- **User Story 2 (Phase 4, P1)**: Depende de Foundational — independiente de US1
- **User Story 3 (Phase 5, P2)**: Depende de Foundational — independiente de US1/US2
- **Polish (Phase 6)**: Depende de que las 3 historias estén completas

### User Story Dependencies

- **US1, US2, US3**: Ninguna depende de las otras — cada una toca su propio repositorio/servicio/vista/URLs sin tocar los archivos de las demás (distintos módulos: `registro_*`, `despacho_*`, `seguimiento_*`). Pueden implementarse en cualquier orden o en paralelo tras Foundational.

### Parallel Opportunities

- T003 y T004 (Setup) en paralelo
- T006, T007 y T008 (Foundational) en paralelo entre sí (T008 depende de T007 completarse primero, no en paralelo con él)
- Una vez Foundational completa: US1 (Phase 3), US2 (Phase 4) y US3 (Phase 5) completas pueden avanzar en paralelo — no comparten archivos
- Dentro de cada historia: los 3 tests (repository/service/api) marcados [P] en paralelo entre sí, antes de su implementación secuencial (repo → service → views → urls, por dependencia real de datos)
- T034 y T035 (Polish) en paralelo

---

## Parallel Example: User Story 1

```bash
# Tests de la Historia 1, en paralelo (antes de implementar):
Task: "Test de repositorio en backend/apps/informes_tacticos/tests/repositories/test_registro_repository.py"
Task: "Test de servicio en backend/apps/informes_tacticos/tests/services/test_registro_informes_service.py"
Task: "Test de API en backend/apps/informes_tacticos/tests/api/test_registro_views.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Completar Phase 1: Setup
2. Completar Phase 2: Foundational (CRÍTICO)
3. Completar Phase 3: User Story 1 (7 informes de Registro)
4. **DETENER Y VALIDAR**: los 7 endpoints de Registro responden correctamente end-to-end
5. Con esto ya hay contenido real para empezar el primer workpanel en `../frontend/`

### Incremental Delivery

1. Setup + Foundational → Fundación lista
2. User Story 1 (Registro, P1) → Validar → primer workpanel con datos reales
3. User Story 2 (Despacho, P1) → Validar → segundo workpanel con datos reales
4. User Story 3 (Seguimiento, P2) → Validar → tercer workpanel con datos reales
5. Polish → Backend cerrado, listo para `../frontend/`

---

## Notes

- [P] = archivos distintos, sin dependencia directa
- Los 3 repositorios (`registro_repository.py`, `despacho_repository.py`, `seguimiento_repository.py`) son independientes entre sí — ninguno importa del otro, cada uno solo depende de `PinotClient` (T007/T009) y de las tablas que le corresponden según `data-model.md`
- Confirmar cada checkpoint antes de pasar a la siguiente fase
- Ningún endpoint de esta feature escribe en Pinot ni publica en Kafka (FR-004) — verificar esto explícitamente en cada test de repositorio (solo se llama a `PinotClient.query`, nunca a un writer)

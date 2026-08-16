# Tasks: Informes Tácticos Simples de Cuentas y Clientes (Backend)

**Input**: Design documents from `specs/002-tactico/Cuentas-Clientes/informes-tacticos-simples/backend/`

**Prerequisites**: [`plan.md`](plan.md), [`spec.md`](spec.md), [`research.md`](research.md), [`data-model.md`](data-model.md), [`contracts/`](contracts/)

**Tests**: **incluidos y obligatorios.** No es opcional en este proyecto: la constitución fija
cobertura ≥80% en servicios (Principio VII, `testing.md` §37-43) y research D3/D7 exige pruebas
concretas de centinelas y de no filtración de credenciales.

**Organization**: agrupadas por user story para que cada una se implemente, pruebe y entregue por
separado.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: puede ejecutarse en paralelo (ficheros distintos, sin dependencias pendientes)
- **[Story]**: US1, US2, US3 según `spec.md`
- Cada tarea lleva su ruta exacta

## Path Conventions

Backend Django en `backend/`. Repositorios en `backend/core/repositories/`, lógica en
`backend/apps/<app>/services/`, vistas en `backend/apps/<app>/views/`, pruebas en
`backend/apps/<app>/tests/{repositories,services,api,performance}/`.

> **Refinamiento sobre `plan.md`.** Los repositorios, servicios y vistas se parten **por user
> story** en vez de un fichero único por capa. Sin eso, las tres historias tocarían el mismo fichero
> y no serían implementables en paralelo, que es el objetivo de organizarlas así.

---

## Phase 1: Setup

**Purpose**: preparar el paquete transversal y fijar la línea base.

- [X] T001 Crear el paquete `backend/core/informes/` con `__init__.py`, destinado a los 64 listados de los 8 departamentos
- [X] T002 Registrar la línea base de las suites ejecutando `cd backend && python -m pytest -q` y anotar el resultado (esperado: 1673 passed, 2 skipped) en `specs/002-tactico/Cuentas-Clientes/informes-tacticos-simples/backend/quickstart.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: los ayudantes compartidos por los ocho listados y por los siete departamentos que
vienen después.

**⚠️ CRÍTICO**: ninguna user story puede empezar hasta que esta fase esté completa.

- [X] T003 [P] Implementar el parseo de período con rango **opcional** en `backend/core/informes/periodo.py`, sin importar ni modificar `backend/apps/informes_tacticos/periodo.py` (research D1)
- [X] T004 [P] Implementar la paginación keyset por cursor en `backend/core/informes/paginacion.py`, con cursor escalar y compuesto, y detección de página siguiente pidiendo `limit + 1` filas (research D2)
- [X] T005 [P] Implementar el envelope `{data, meta:{pagination, filtros}}` en `backend/core/informes/envelope.py`, reutilizando `backend/core/api/response_envelope.py`
- [X] T006 Implementar la vista base `ListadoBaseView` en `backend/core/informes/vistas.py`, que centraliza la validación de `limit` sobre el máximo (FR-016), el rechazo de `desde`/`hasta` en listados de estado actual (FR-012), y el rechazo de valores no reconocidos en enumeraciones (FR-015) — depende de T003, T004, T005
- [X] T007 [P] Pruebas del período opcional en `backend/apps/cuentas_clientes/tests/unit/test_informes_periodo.py`: rango ausente es válido, rango invertido falla, `hasta` se interpreta inclusiva
- [X] T008 [P] Pruebas de paginación en `backend/apps/cuentas_clientes/tests/unit/test_informes_paginacion.py`: cursor escalar y compuesto, `has_next` correcto, cursor `null` en la última página
- [X] T009 [P] Pruebas del envelope en `backend/apps/cuentas_clientes/tests/unit/test_informes_envelope.py`: forma de `meta.pagination` y `meta.filtros` normalizados
- [X] T010 Añadir las clases de permiso `InformesCuentasLecturaPermission` (Administrador) e `InformesAccesosTecnicosPermission` (Director Tecnológico + Administrador) en `backend/apps/cuentas_clientes/permissions.py`, siguiendo el patrón de `backend/apps/informes_tacticos/permissions.py` (FR-018, FR-019)
- [X] T011 [P] Pruebas de permisos en `backend/apps/cuentas_clientes/tests/unit/test_informes_permissions.py`: fallo cerrado sin token, sin roles y con rol no autorizado

**Checkpoint**: base lista — las tres user stories pueden abordarse en paralelo.

---

## Phase 3: User Story 1 — Vigilar quién tiene acceso al sistema y con qué rol (Priority: P1) 🎯 MVP

**Goal**: cuatro listados de OT18 que permiten al Administrador verificar el control de acceso por
rol sin abrir la ficha de cada usuario.

**Independent Test**: solicitar los cuatro listados de forma aislada y obtener la respuesta correcta,
sin que existan los listados de OT04 ni de OT17.

**Criterio medible (ISO 25010 — Security / Confidentiality)**: el 100 % de las respuestas de esta
historia está libre de `contrasena` y `token`, verificado por T023.

### Implementación

- [X] T012 [US1] Implementar la consulta de **usuarios y sus roles** (L5) en `backend/core/repositories/cuentas_clientes/informes_acceso_repository.py`, paginando sobre `Dim_Usuarios` por `idusuario` y resolviendo los roles de la página desde `Dim_Usuario_Rol` y `Dim_Rol` (research D4)
- [X] T013 [US1] Implementar la consulta de **sesiones abiertas** (L6) en `backend/core/repositories/cuentas_clientes/informes_acceso_repository.py`, filtrando `estadosession = 'Activa'` con **columnas enumeradas** — prohibido `SELECT *`, el `token` no puede salir (research D7)
- [X] T014 [US1] Implementar la consulta de **credenciales temporales** (L7) en `backend/core/repositories/cuentas_clientes/informes_acceso_repository.py`, con columnas enumeradas: `contrasena` no puede salir (research D7)
- [X] T015 [US1] Implementar la consulta de **accesos técnicos** (L8) en `backend/core/repositories/cuentas_clientes/informes_acceso_repository.py`, resolviendo la cadena `Dim_UsuariosServidorRolesServidor` → `Dim_RolesServidor` → `Dim_RolesServidorRoles` → `Dim_Rol`, con columnas enumeradas
- [X] T016 [US1] Implementar `InformesAccesoService` en `backend/apps/cuentas_clientes/services/informes_acceso_service.py`, con la agrupación de roles por usuario y la garantía de que un usuario sin roles se devuelve con `roles: []` (FR-023)
- [X] T017 [US1] Implementar las cuatro vistas en `backend/apps/cuentas_clientes/views/informes_acceso_views.py`, heredando de `ListadoBaseView` y declarándose como listados de **estado actual**
- [X] T018 [US1] Registrar las cuatro rutas `/informes/cuentas-clientes/{usuarios-por-rol,sesiones-activas,credenciales-temporales,accesos-tecnicos}` en `backend/apps/cuentas_clientes/urls.py`

### Pruebas

- [X] T019 [P] [US1] Pruebas de repositorio en `backend/apps/cuentas_clientes/tests/repositories/test_informes_acceso_repository.py`: filtros, orden determinista y forma del cursor de los cuatro listados
- [X] T020 [P] [US1] Pruebas de servicio en `backend/apps/cuentas_clientes/tests/services/test_informes_acceso_service.py`: resolución de catálogos y agrupación de roles
- [X] T021 [P] [US1] Pruebas de contrato en `backend/apps/cuentas_clientes/tests/api/test_informes_acceso_contract.py`: los cuatro endpoints responden 200 con el envelope del OpenAPI, y `data: []` con 200 cuando no hay filas (SC-007)
- [X] T022 [P] [US1] Prueba de que **un usuario con dos roles produce una sola fila** con dos roles, y de que **un usuario sin ningún rol aparece** con `roles: []`, en `backend/apps/cuentas_clientes/tests/services/test_informes_acceso_multirol.py` (User Story 1 escenario 2, FR-023)
- [X] T023 [P] [US1] Prueba de seguridad en `backend/apps/cuentas_clientes/tests/api/test_informes_acceso_sin_secretos.py` que **falla si la respuesta contiene `contrasena`, `token` o `client_secret_hash`**, y que verifica contra el código fuente que los repositorios no usan `SELECT *` sobre `Dim_Credencial`, `Dim_UsuariosServidor` ni `Fact_Session` — el doble en memoria no basta (research D7)
- [X] T024 [P] [US1] Pruebas de control de acceso en `backend/apps/cuentas_clientes/tests/api/test_informes_acceso_permisos.py`: un Operador recibe **403** en los cuatro sin que se filtre ninguna fila, y el Director Tecnológico recibe **200** en `accesos-tecnicos` (FR-019, SC-006)
- [X] T025 [P] [US1] Prueba de que los cuatro listados **rechazan `desde`/`hasta` con 400** en `backend/apps/cuentas_clientes/tests/api/test_informes_acceso_sin_rango.py` (FR-012)

**Checkpoint**: US1 entregable por sí sola. Es el MVP.

---

## Phase 4: User Story 2 — Seguir la incorporación de clientes nuevos (Priority: P2)

**Goal**: dos listados de OT04 que muestran qué solicitudes esperan aprobación y qué clientes se
quedaron a medias, con el tiempo que llevan detenidos.

**Independent Test**: solicitar los dos listados de forma aislada, sin que existan los de OT18 ni los
de OT17.

**Criterio medible (ISO 25010 — Functional Correctness)**: `dias_transcurridos` es exacto para un
instante inyectado conocido, verificado por T031 sin depender del reloj del sistema.

### Implementación

- [X] T026 [US2] Implementar la consulta de **solicitudes de alta pendientes** (L1) en `backend/core/repositories/cuentas_clientes/informes_incorporacion_repository.py`, filtrando `estado = 'Pendiente'` y ordenando por `fecha_creacion ASC` con desempate por `idcliente`
- [X] T027 [US2] Implementar la consulta de **incorporación incompleta** (L2) en `backend/core/repositories/cuentas_clientes/informes_incorporacion_repository.py`, filtrando `completado = false` y resolviendo `id_cliente` contra `Dim_Cliente` (research D6)
- [X] T028 [US2] Implementar `InformesIncorporacionService` en `backend/apps/cuentas_clientes/services/informes_incorporacion_service.py`, con **reloj inyectable**, cálculo de `dias_transcurridos` y traducción de `dias_minimo` a fecha de corte que viaja al `WHERE` (research D5)
- [X] T029 [US2] Implementar las dos vistas en `backend/apps/cuentas_clientes/views/informes_incorporacion_views.py`, heredando de `ListadoBaseView` como listados de **estado actual**
- [X] T030 [US2] Registrar las rutas `/informes/cuentas-clientes/{solicitudes-alta-pendientes,onboarding-incompleto}` en `backend/apps/cuentas_clientes/urls.py`

### Pruebas

- [X] T031 [P] [US2] Pruebas de servicio con **instante inyectado** en `backend/apps/cuentas_clientes/tests/services/test_informes_incorporacion_service.py`: `dias_transcurridos` exacto y `dias_minimo` traducido correctamente a fecha de corte
- [X] T032 [P] [US2] Pruebas de repositorio en `backend/apps/cuentas_clientes/tests/repositories/test_informes_incorporacion_repository.py`: solo pendientes, solo etapas sin completar, orden determinista
- [X] T033 [P] [US2] Pruebas de contrato en `backend/apps/cuentas_clientes/tests/api/test_informes_incorporacion_contract.py`: envelope conforme al OpenAPI y `403` para roles no autorizados
- [X] T034 [P] [US2] Prueba que fija como **intencional** que una etapa sin registro no genera fila, en `backend/apps/cuentas_clientes/tests/repositories/test_informes_onboarding_etapas_ausentes.py` (research D6) — documenta el comportamiento en vez de dejarlo al azar
- [X] T035 [P] [US2] Prueba de que ambos listados **rechazan `desde`/`hasta` con 400** en `backend/apps/cuentas_clientes/tests/api/test_informes_incorporacion_sin_rango.py` (FR-012)

**Checkpoint**: US2 entregable de forma independiente.

---

## Phase 5: User Story 3 — Revisar el estado del parque de cuentas (Priority: P3)

**Goal**: dos listados de OT17 con el estado de cada cuenta y las transferencias de propiedad. Aquí
vive el **único listado de los ocho que acepta rango de fechas**.

**Independent Test**: solicitar los dos listados de forma aislada, sin que existan los de OT18 ni los
de OT04.

**Criterio medible (ISO 25010 — Functional Completeness)**: el 100 % de las cuentas dadas de baja
sigue apareciendo con su razón social intacta, verificado por T042.

### Implementación

- [X] T036 [US3] Implementar la consulta de **cuentas por estado** (L3) en `backend/core/repositories/cuentas_clientes/informes_cuenta_repository.py`, **incluyendo las dadas de baja**, con cursor escalar por `idcliente` y resolución de `admin_local_id` contra `Dim_Usuarios`
- [X] T037 [US3] Implementar la consulta de **transferencias de propiedad** (L4) en `backend/core/repositories/cuentas_clientes/informes_cuenta_repository.py`, con **rango de fechas opcional** y resolución de propietario anterior y nuevo contra `Dim_Usuarios`
- [X] T038 [US3] Implementar `InformesCuentaService` en `backend/apps/cuentas_clientes/services/informes_cuenta_service.py`, garantizando que una cuenta cuyo `admin_local_id` no resuelve se devuelve con el propietario marcado como no resuelto y **no se omite la fila**
- [X] T039 [US3] Implementar las dos vistas en `backend/apps/cuentas_clientes/views/informes_cuenta_views.py`, declarando `cuentas-por-estado` como **estado actual** y `transferencias-propiedad` como **hechos del período** con rango opcional
- [X] T040 [US3] Registrar las rutas `/informes/cuentas-clientes/{cuentas-por-estado,transferencias-propiedad}` en `backend/apps/cuentas_clientes/urls.py`

### Pruebas

- [X] T041 [P] [US3] Pruebas de repositorio en `backend/apps/cuentas_clientes/tests/repositories/test_informes_cuenta_repository.py`: filtros por estado y tipo, orden determinista, rango opcional
- [X] T042 [P] [US3] Prueba de que **las cuentas dadas de baja siguen apareciendo** con razón social intacta, y de que una cuenta con propietario no resoluble **no se omite**, en `backend/apps/cuentas_clientes/tests/services/test_informes_cuenta_baja_logica.py` (User Story 3 escenario 2)
- [X] T043 [P] [US3] Prueba de que `transferencias-propiedad` **sin rango devuelve el histórico completo paginado** y con rango lo acota, en `backend/apps/cuentas_clientes/tests/api/test_informes_transferencias_rango_opcional.py` (FR-013)
- [X] T044 [P] [US3] Pruebas de contrato en `backend/apps/cuentas_clientes/tests/api/test_informes_cuenta_contract.py`: envelope conforme al OpenAPI y `403` para roles no autorizados

**Checkpoint**: los ocho listados completos.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T045 [P] Prueba de **integridad de la paginación** en `backend/apps/cuentas_clientes/tests/api/test_informes_paginacion_integridad.py`: recorrer un listado por páginas devuelve cada fila exactamente una vez, comparado con la consulta de una sola página (SC-005)
- [X] T046 [P] Prueba de que **`limit` sobre el máximo responde 400** y no se recorta en silencio, en `backend/apps/cuentas_clientes/tests/api/test_informes_limite.py` (FR-016)
- [X] T047 [P] Prueba de que los **centinelas se presentan como ausencia de valor** y nunca como `'null'`, `0` o fecha mínima, en `backend/apps/cuentas_clientes/tests/unit/test_informes_centinelas.py`, verificando contra `core/pinot/client.py` y no contra el doble en memoria (research D3)
- [X] T048 [P] Prueba de rendimiento en `backend/apps/cuentas_clientes/tests/performance/test_informes_latencia.py`: primera página de los ocho listados por debajo de 2 s (SC-002)
- [X] T049 Ejecutar `cd backend && python -m pytest apps/informes_tacticos -q` y verificar que **sigue verde sin cambios** — si esa suite se mueve, el aislamiento del piloto falló (research D1)
- [X] T050 Verificar que la implementación coincide con `contracts/informes-tacticos-simples.openapi.yaml` endpoint por endpoint, corrigiendo el contrato si la implementación reveló algo mejor
- [ ] T051 Recorrer `quickstart.md` de principio a fin contra el stack levantado y anotar cualquier discrepancia — **parcial:** las 9 comprobaciones reproducibles quedan cubiertas por la suite y anotadas en `quickstart.md` §7, y se corrigieron dos discrepancias encontradas (§3.7 usaba un estado inexistente; §6 documenta el vacío de `transferencias-propiedad`). **Falta el recorrido contra Docker levantado**, que es donde aparecerían las diferencias de tipo y centinela que el doble en memoria no reproduce
- [X] T052 Documentar el trabajo en `.specify/docs/changelog.md` y actualizar `informestacticos/TSI-Informes-Tacticos-Requeridos-por-OT.md` marcando los ocho listados como 🟢

---

## Dependencies

```text
Phase 1 (Setup)
    ↓
Phase 2 (Foundational) ← BLOQUEANTE
    ↓
    ├─→ Phase 3 (US1, P1) ─┐
    ├─→ Phase 4 (US2, P2) ─┤ independientes entre sí
    └─→ Phase 5 (US3, P3) ─┘
                            ↓
                    Phase 6 (Polish)
```

**Dentro de la fase 2**: T003, T004 y T005 son paralelos; T006 depende de los tres. T007–T009
dependen de sus módulos respectivos. T010 y T011 son independientes del resto.

**Entre user stories**: ninguna depende de otra. Los repositorios, servicios y vistas están partidos
por historia justamente para eso. El único fichero compartido es `urls.py` (T018, T030, T040), que
se toca en tres puntos distintos y sin solapamiento.

---

## Parallel Execution Examples

**Fase 2 — los tres ayudantes a la vez:**

```text
T003 core/informes/periodo.py
T004 core/informes/paginacion.py
T005 core/informes/envelope.py
```

**Fase 3 — todas las pruebas de US1 tras la implementación:**

```text
T019 test_informes_acceso_repository.py
T020 test_informes_acceso_service.py
T021 test_informes_acceso_contract.py
T022 test_informes_acceso_multirol.py
T023 test_informes_acceso_sin_secretos.py
T024 test_informes_acceso_permisos.py
T025 test_informes_acceso_sin_rango.py
```

**Fase 6 — la batería completa de cierre:**

```text
T045 test_informes_paginacion_integridad.py
T046 test_informes_limite.py
T047 test_informes_centinelas.py
T048 test_informes_latencia.py
```

---

## Implementation Strategy

### MVP — solo User Story 1

Las fases 1, 2 y 3 entregan **cuatro listados funcionando** (usuarios y roles, sesiones abiertas,
credenciales temporales, accesos técnicos) y, con ellos, **todo el andamiaje transversal que los
siete departamentos restantes reutilizarán**. Es el corte natural: si el trabajo se detiene ahí,
queda valor entregado y el patrón ya está fijado.

### Entrega incremental

1. **Fases 1–2** — `core/informes/` listo. Nada visible todavía, pero desbloquea todo.
2. **Fase 3 (US1)** — MVP. Cuatro listados de OT18. Verificable de punta a punta.
3. **Fase 4 (US2)** — dos listados de OT04. Añade el patrón de reloj inyectable.
4. **Fase 5 (US3)** — dos listados de OT17. Añade el patrón de rango opcional.
5. **Fase 6** — cierre transversal y documentación.

### Riesgo a vigilar

**T049 es el guardián del aislamiento.** Si en algún momento la suite de `apps/informes_tacticos`
deja de estar verde, significa que se tocó algo de lo que dependen 19 endpoints en producción, y la
decisión D1 se habrá incumplido sin querer. Conviene ejecutarla no solo al final, sino después de la
fase 2.

# Changelog fuera de ciclo — cambios de código no originados en `/plan`→`/tasks`

Este documento registra cambios de código aplicados directamente al detectar brechas
entre `spec.md` y el comportamiento real del sistema (vía `/speckit-analyze` extendido),
fuera del flujo normal Spec-Driven. Cada entrada debe quedar reflejada también en el
`traceability.md` de la feature afectada.

---

## 2026-08-01 — Revisión `002-tactico` (spec vs. docs globales)

Alcance: `specs/002-tactico/`, `.specify/docs/infra/infrastructure.md`

**T1** — `spec.md` no declaraba las 9 características ISO/IEC 25010 ni trazabilidad OT (solo el `plan.md` lo hacía). Corregido: sección Constitution Compliance + enlace a `informestacticos/auditoria-esquemas-informes-v2.md`; FR-011 (ClickHouse/Postgres Airflow ≠ almacén de dominio).

**T2** — `infrastructure.md` §1 afirmaba “infraestructura de datos única / no se usa PostgreSQL” de forma absoluta, en tensión con el stack `tactico` ya documentado en §2.1. Reformulado: Kafka+Pinot = canal único del *modelo dimensional*; Postgres de Airflow = solo metastore. Encabezado §5 actualizado (ya no dice “no implementar todavía” mientras §5.1 está activo). Regla vinculante §4 añadida sobre ClickHouse/Postgres.

**T3** — Todo el feature vive bajo `specs/002-tactico/infraestructura/` (`spec.md`, plan, research, data-model, contracts, quickstart, tasks, índice). `feature.json` apunta a esa carpeta. Se eliminó `checklists/` (gate de `/specify` ya cumplido; no aporta valor operativo tras plan/tasks cerrados).

**T4** — Variable `CLICKHOUSE_DB` (default `tsi_tactico`; no `TSI-tactico` — el guion no es válido como identificador ClickHouse sin comillas). Init en `docker/tactico/clickhouse-init/`; documentado en contrato, quickstart y `.env.tactico.example`.

---

## 2026-07-15 — Módulo Emergencias (revisión spec vs. implementación)

Alcance: `despacho-inteligente`, `evidencia-unidad`, `registro-accidente`, `seguimiento-cierre-de-casos`

> Nota: el `git status` del repo también mostraba otros archivos modificados/sin trackear que
> **no** correspondían a este trabajo (cambios previos ya en curso antes de esta sesión,
> p. ej. `confirmar_despacho_service.py`, `mi_seguimiento_views.py`, extracción de templates
> `.html`, etc.). Esta entrada solo cubre lo hecho en esa sesión.

### Backend

**G1 (CRITICAL) — Jobs periódicos sin agendar.**
`run_timeout_despacho_job`, `run_gps_senal_perdida_job` y el job de depuración GPS existían
pero nadie los invocaba (no había Celery/APScheduler ni cron configurado). Se agregaron
management commands de Django (patrón `send_onboarding_reminders.py`):
`backend/apps/despacho/management/commands/run_timeout_despacho_job.py`,
`backend/apps/seguimiento/management/commands/run_gps_senal_perdida_job.py`,
`backend/apps/seguimiento/management/commands/run_gps_depuracion_job.py`.
**Pendiente:** decidir invocación en producción (cron, worker separado, Celery beat).

**G2 (HIGH) — Estado de unidad forzado a "Activa" al liberar despacho.**
Al retirar o abortar un despacho, la unidad siempre volvía a `Activa`, ignorando
`Fuera de servicio` (RN-SEG-003 no implementada). Corregido en
`backend/apps/seguimiento/services/retiro_despacho_service.py` y
`backend/apps/seguimiento/services/abortar_mision_service.py` (consultan estado actual
antes de liberar; `cerrar_caso_service.py`/`forzar_retiro_service.py` heredan el fix vía
`RetiroDespachoService`).

**G4 (HIGH) — Mensaje de error genérico en registro de accidente.**
`AccidenteListCreateView.post` respondía siempre `"duplicado_posible"` ante un
`DuplicateConflictError`, aun cuando la advertencia real era `fuera_cobertura`. Corregido
en `backend/apps/accidentes/views/accidente_views.py` (usa `advertencias[0]` real, expone
el arreglo completo).

**G5 (HIGH) — Scoring de "disponibilidad reciente" hardcodeado.**
En `consulta_candidatas_service.py`, el 15% del score de RN-DES-008 era constante
(`disp_score = 0.5`). Se agregó `_disponibilidad_reciente_score()` (score real por tiempo
continuo en estado `Activa`, tope 30 min).

**G6 (MEDIUM) — Selección de accidente "padre" en fusión usa campo incorrecto.**
`ValidacionAccidenteService.suggest_parent_id` usaba `fechahoraaccidente` en vez del
`fechahoramodificado` de la primera transición a `BORRADOR`/`REPORTADO`
(`Fact_AccidenteTipoEstadoAccidente`), per RN-REG-010b. Corregido en
`backend/apps/accidentes/services/validacion_accidente_service.py` (fallback a
`fechahoraaccidente` si no hay historial).

**G9 — Verificado sin cambios.** `registrar_posicion_gps_service.py` sí invoca
`RegistrarLlegadaService` automáticamente vía geofencing (RF-SEG-002) — falso positivo del
análisis previo.

### Frontend

**G3 (HIGH) — Auto-sync de evidencias nunca se activaba.**
`EvidenciaSyncSchedulerService.iniciarAutoSync()` existía pero no se llamaba desde ningún
lado — código muerto. Corregido: nuevo `listarIdsAccidentesPendientes()` en
`evidencia-offline-store.service.ts`; `sincronizarTodosLosCasos()` ahora usa la unión de
casos en sesión + pendientes reales en IndexedDB; `app.component.ts` invoca
`iniciarAutoSync()` en el constructor (corre durante toda la vida de la app).

**Bug preexistente (detectado al verificar G4 en el frontend) — Manejo del conflicto
409 roto.** `registro-accidente.page.ts` leía `err.error` en vez de `err.error.data`
(envoltura `{data, meta}`) y usaba `idaccidente_duplicado_sugerido` (siempre `null`) en
vez de `idaccidente_similar`. Resultado real: el diálogo de "posible duplicado" nunca se
abría y la fusión nunca funcionaba. Corregido en
`frontend/src/app/modules/accidentes/pages/registro-accidente/registro-accidente.page.ts`;
se agregó manejo explícito de `error === 'fuera_cobertura'`. Tests actualizados en
`registro-accidente.page.spec.ts`.

### Verificación realizada

- Backend: `pytest apps/despacho apps/accidentes apps/seguimiento` → 285/285 tests.
- Frontend: `tsc --noEmit` (app + spec) sin errores. (Karma/Jasmine no se pudo correr por
  falta de Chrome en el entorno; recomendado correr `ng test` localmente.)
- Docker: `docker compose -f accidentes.yml build` exitoso.

### Pendientes / fuera de alcance

- **G7** — Notificaciones push/SMS en despacho son stubs (`_default_push`/`_default_sms`
  siempre "exitosos"); requiere integración real con un proveedor.
- **G8** — Payload estructurado de alerta crítica hacia monitoreo (RF-DES-008) no
  confirmado a fondo.
- **G10 / T108** — No existe endpoint de reversión (undo) para descarte/fusión de
  accidentes; decisión de alcance pendiente. Ver `registro-accidente/tasks.md` T108.

---

## 2026-07-16 — Regularización de contrato para proxy de ruta OSRM

Alcance: `seguimiento-cierre-de-casos`

El endpoint `GET /api/v1/seguimiento/ruta` (`backend/apps/seguimiento/views/ruta_views.py`,
`core/osrm/client.py`) se implementó junto con el trabajo del 2026-07-15 pero no se agregó
al contrato OpenAPI ni a `tasks.md` en su momento (violación Principio VI — API-First).
Regularizado: contrato agregado en
`contracts/seguimiento-cierre-de-casos.openapi.yaml` (`/seguimiento/ruta`), tarea T042b y
fila CA-SEG-002b en `traceability.md`.

---

## 2026-07-31 — Auditoría de suites, paginación en Pinot e higiene de datos

Alcance: `registro-accidente`, `seguimiento-cierre-de-casos`, `evidencia-unidad`,
`despacho-inteligente`, `Red-Operativa/alta-unidades`, `Suscripciones-Facturacion`,
`Cuentas-Clientes`, infraestructura de datos (`database/`).

Origen: ejecución completa de las suites unitarias y recorrido end-to-end del sistema
contra el stack real (Kafka + Pinot + Django + Angular), no un ciclo `/plan`→`/tasks`.

### Infraestructura de datos

**D1 (CRITICAL) — Pinot recortaba en silencio toda consulta sin `LIMIT`.**
Pinot aplica un `LIMIT 10` implícito cuando la consulta no declara uno, y la respuesta no
distingue "hay 10 filas" de "hay 10 de 500". 31 consultas del repositorio no declaraban
tope, así que los repositorios filtraban y paginaban en Python sobre un recorte arbitrario
(sin `ORDER BY`, ni siquiera estable entre llamadas). Efecto verificado en el entorno real:
con 13 accidentes activos el listado mostraba 10, y filtrar por severidad operaba sobre ese
recorte. Corregido en `backend/core/pinot/client.py`: `PinotClient.query` añade un tope
explícito (`DEFAULT_QUERY_LIMIT`) cuando el SQL no trae uno, respetando los `LIMIT` propios.
Regresión en `backend/tests/regression/test_pinot_client_limit.py`.

**D2 (HIGH) — `Dim_Usuario_Cliente` y `Dim_CondadoVecino` no existían.**
Ambas se consultaban desde código productivo pero no estaban declaradas en
`database/esquemas.json` ni creadas en Pinot (`TableDoesNotExistError`).
`GET /api/v1/cliente/expedientes` respondía **500** y CU-O34 (escalamiento a condados
vecinos) fallaba al buscar adyacencias. Declaradas en `database/esquemas.json` y
`database/tablas.json`, sembradas por `database/seed_vinculos.py`.
**Causa de que los tests no lo detectaran:** el doble en memoria de `conftest.py` sí tenía
ambas tablas — el doble era más completo que la base real.

**D3 (MEDIUM) — `seed_soporte.py` publicaba `Dim_Usuario_Cliente` sin su clave primaria.**
El registro entraba con el centinela de nulo de INT y convivía como fila huérfana junto al
vínculo real. Corregido; `database/seed_flota_demo.py` retira las filas ya escritas así.

### Backend

**B1 (HIGH) — Paginación real en SQL en lugar de recorte en memoria.**
`AccidenteRepository.list_activos` traía la tabla y filtraba en Python. Reescrito para que
filtros, orden y tope viajen en el SQL, con paginación keyset por `idaccidente` y
`(filas, cursor_siguiente)` como retorno. `ConsultaAccidenteService.listar` encadena
páginas acotadas solo cuando el filtro por estado (que vive en otra tabla) deja la página
corta, con techo `MAX_PAGINAS_ENCADENADAS`. `HistorialEmergenciasService` lee por bloques
(`_leer_accidentes`) en vez de `SELECT * FROM Fact_Accidente`; además ordenaba por
`horainicio` mientras paginaba por `idaccidente`, lo que dejaba huecos entre páginas —
ahora ambas usan la misma clave. `GET /api/v1/accidentes` expone
`meta.pagination.next_cursor` y acepta `cursor`. Único escaneo amplio que se conserva:
`find_nearby` (agrupación de duplicados), acotado ahora por ventana temporal en el SQL.

**B2 (HIGH) — Rollback silencioso en importación de lote de unidades.**
`importacion_lote_unidad_service.importar` compensaba con
`unidad_repo.update(id, {"activo": False})` sin `base`, lo que releía de Pinot un registro
recién escrito por Kafka y todavía no ingerido; `update()` devolvía `None` en silencio y el
rollback no hacía nada. Dejó en la base 6 unidades activas apuntando a un `idusuario` que
nunca se persistió (no pueden iniciar sesión: CU-O30 `find_by_usuario`). Corregido pasando
el registro creado como `base`. Regresión:
`test_importar_when_credencial_falla_y_pinot_aun_no_ingirio_igual_revierte`.

**B3 (HIGH) — Filtro de flota por tipo de unidad siempre vacío.**
`UnidadEmergenciaRepository.list_active` filtraba por `idtipounidad`, columna que no existe
en `Dim_UnidadEmergencia` (la real es `tipounidademergencia`, texto). Cualquier filtro por
tipo devolvía cero unidades. Corregido en repositorio, servicio y vista; el endpoint acepta
`tipo` y mantiene `idtipounidad` como alias. La respuesta ahora expone
`tipounidademergencia` y `placa`.

**B4 (MEDIUM) — `idaccidente_duplicado_sugerido` retirado del contrato 409.**
El backend lo emitía siempre `null` y el frontend nunca lo usaba (fusiona sobre
`idaccidente_similar`, el reporte ya registrado; el duplicado rechazado por el 409 nunca
llegó a crearse). Retirado de `accidente_views.py`, del OpenAPI de `registro-accidente` y
del `spec.md` correspondiente.

**B5 (MEDIUM) — Motivo ilegible al sincronizar evidencia offline.**
`SincronizarEvidenciaService` capturaba `KeyError` y reportaba al técnico el nombre crudo
de la clave (`'estadoimplicado'`). Se agregó `_exigir_campos`, que nombra qué falta y en
cuál ítem local.

### Frontend

**F1 (HIGH) — «Mis expedientes» llevaba a una página de detalle sin `idaccidente`.**
`nav-links.ts` apuntaba a `/seguimiento/expedientes`, que cargaba `DetalleExpedientePage`
(un stub) sin parámetro: renderizaba un encabezado vacío y no pedía nada. Se creó
`ListaExpedientesPage` (listado con los tres estados, paginación por cursor y acción `eye`)
y se implementó `DetalleExpedientePage` con el chrome de workpanel del golden sample.

**F2 (MEDIUM) — La ruta `/` ignoraba la sesión.**
Redirigía siempre al portal comercial público, así que un usuario autenticado que escribía
la URL base veía "Iniciar sesión / Registrarme". Nuevo `landingRedirectGuard` que resuelve
al home del rol (misma función `homePathForRoles` que usa el login).

**F3 (MEDIUM) — `plan-detalle` fingía solo lectura con `input disabled readonly`.**
Prohibido explícitamente por el design-system, sección 5 ("en modo Ver, datos como `dl`…
nunca `input disabled`"). Reescrito al chrome del golden sample: «Volver a la lista» con
`arrow-left`, eyebrow de modo, `h1` + badge en la misma fila y datos en `dl` con `dt`
uppercase.

**F4 (LOW) — Homogeneización de estados asíncronos.**
`validacion.page.ts` mostraba la tabla de historial solo si había datos: sin skeleton, sin
error y sin vacío — "todavía no se pidió" y "vino vacío" se veían igual. Migrado a los
componentes canónicos `app-list-*`. Se homogeneizó `data-testid="error"` →
`data-testid="error-state"` en `evidencia-unidad`. Se agregó `download` al set Tabler
(`tabler-icon.component.ts`) en vez de introducir un ícono fuera del set único del sistema.

**F5 (LOW) — Paginación visible en la lista de accidentes.**
La lista pedía 20 registros y no ofrecía avanzar. Se agregó el paginador Anterior/Siguiente
con la misma convención que `catalogo-planes`
(`btn-pagina-anterior`/`btn-pagina-siguiente`), apoyado en el cursor real del backend;
cambiar un filtro reinicia la paginación.

### Suites de prueba

- **La suite backend no arrancaba**: `apps/accidentes/` no tenía `__init__.py`, así que
  pytest nombraba `apps/accidentes/tests/` como el módulo top-level `tests` y su
  `conftest.py` como el `conftest` raíz — 16 módulos fallaban al importar `PINOT_STORE` y
  la sesión se interrumpía por errores de colección. Agregados los `__init__.py` faltantes.
- `pytest.ini` tenía `testpaths = apps`, así que `backend/tests/` (incluida la regresión de
  la cadena crítica) nunca se ejecutaba. Ahora `testpaths = apps tests`.
- Los contadores de throttling de DRF persistían entre tests (viven en el caché de Django);
  un test que agotaba un scope hacía fallar con 429 a los posteriores según el orden de
  colección. Nuevo fixture autouse `reset_throttle_history` en `conftest.py`.
- El doble de Pinot se actualizó para honrar los predicados nuevos (filtros, cursor, orden
  y `LIMIT` de accidentes y flota). Sin eso los tests dejaban de medir lo que hace Pinot.

### Higiene de datos (entorno demo)

`database/higiene_datos.py` (idempotente, con `--dry-run`): desactiva unidades de prueba de
humo y unidades huérfanas (residuo de B2), consolida el rol `Unidad` duplicado (idrol 4 y 7
→ 4; los permisos se evalúan por nombre, así que el acceso no cambia) y sanea descripciones
de accidente con contenido ofensivo cargado como dato de prueba.
`database/seed_flota_demo.py` repone una flota mínima consistente (una unidad por usuario
con rol Unidad, correctamente ligada) y retira los vínculos usuario-cliente con clave
centinela.

### Verificación realizada

- Backend: `pytest` → 901 pasan, 2 skipped (antes: la suite no arrancaba).
- Frontend: `ng test` → 312 pasan (antes: 285 pasaban, 9 fallaban).
- Recorrido end-to-end contra el stack real: 34/34 pasos, incluido el recorrido paginado
  completo (13 filas en 5 páginas, sin repetidos ni faltantes) y los controles de acceso.

---

## 2026-07-31 (2) — Acceso denegado, unificación de credenciales y paginación de históricos

Alcance: `Cuentas-Clientes`, `despacho-inteligente`, `seguimiento-cierre-de-casos`,
infraestructura de datos y seeds (`database/`, `backend/scripts/`).

Continuación de la entrada anterior, sobre las dudas que quedaron abiertas allí.

### Frontend

**F6 (HIGH) — Ruta `access-denied` inexistente: 28 guards caían al portal público.**
Todos los guards de rol redirigen a `/cuentas-clientes/auth/access-denied` cuando la
sesión es válida pero el rol no alcanza. Esa ruta nunca se declaró, así que el
wildcard `**` capturaba la navegación y llevaba al portal comercial, donde el usuario
veía "Iniciar sesión / Registrarme" y parecía que se le había caído la sesión.
Creada `AccessDeniedPage` y registrada **dentro del shell autenticado**, para que el
usuario conserve su navegación: muestra la sesión vigente (correo + roles) y un CTA
«Volver a mi inicio» que resuelve con `homePathForRoles`, la misma función del login.
Los guards no se tocaron: estaban bien, faltaba el destino.

### Backend

**B6 (HIGH) — `get_current_estado` decidía el estado de una unidad sobre 10 filas.**
`HistorialEstadoUnidadRepository.list_by_unidad` traía sin `LIMIT`, ordenaba en Python
y devolvía el primero. Con el recorte implícito de Pinot (ver D1), el estado vigente
de una unidad se calculaba sobre 10 filas arbitrarias de su historial: una unidad con
más de 10 cambios de estado podía reportar uno viejo y quedar mal clasificada para
despacho. Orden, cursor y tope ahora van en el SQL.

**B7 (MEDIUM) — Traza GPS sin paginación.**
`Dim_HistorialUbicacionUnidadEmergencia` es la tabla que más rápido crece (una posición
cada ~10 s por unidad en misión ≈ 2.900 filas por jornada). `list_by_unidad` la leía
entera y sin tope, así que Pinot devolvía 10 puntos: el job de depuración GPS decidía
qué conservar mirando solo los 10 primeros, y la histéresis de geofence evaluaba la
llegada con una traza truncada. Ahora `list_by_unidad` pagina por keyset con ventana
temporal en el SQL, y `iter_by_unidad` recorre la traza completa por bloques para los
consumidores que sí la necesitan (`gps_depuracion_service`, `registrar_posicion_gps_service`).

**B8 (MEDIUM) — `estadocredencial` unificado a "Activo".**
Convivían "ACTIVA" (seeds) y "Activo" (código). El login no lo notaba porque solo
bloquea "Inactivo", pero `onboarding_service` exige `== "Activo"` y por tanto rechazaba
la credencial de **todos** los usuarios sembrados. Valores canónicos centralizados en
`credential_repository.py` (`ESTADO_CREDENCIAL_ACTIVO/INACTIVO/CAMBIO_PASSWORD`),
literales sueltos reemplazados en servicios y seeds, y las 12 filas ya escritas
migradas con `database/migra_estadocredencial.py`.

### Seeds y datos demo

**S1 (HIGH) — Dos convenciones de contraseña y un fixture E2E apuntando a la nada.**
`database/seed_usuarios.py` sembraba "Demo1234!" y `backend/scripts/*` "password123":
la misma cuenta pedía una u otra según cuál hubiera corrido último. Además
`e2e/fixtures/auth.fixture.ts` usaba cuentas `@tsi.com` tomadas de `backend/conftest.py`
—fixtures en memoria de los tests unitarios— que no existen en ningún entorno real, así
que todos los tests de Playwright fallaban en el login. Nuevo módulo compartido
`backend/scripts/_demo_seed_common.py` (`DEMO_PASSWORD`, `ESTADO_CREDENCIAL_ACTIVO`,
`DEMO_DOMAIN`), consumido por todos los seeds; fixture E2E reescrito con las 10 cuentas
reales y la contraseña como constante. Verificado: 10/10 autentican.

**S2 (HIGH) — Catálogos de roles superpuestos entre seeds.**
`database/seed_usuarios.py` definía idrol 4 = "Operador" y `seed_demo_usuarios_roles.py`
creaba otro "Operador" en idrol 11. Como `Dim_Rol` es upsert por clave primaria, el
segundo seed no agregaba: renombraba el rol de los usuarios ya vinculados al id que
pisara. De ahí el rol `Unidad` duplicado que la higiene consolidó y que reaparecía en
cada re-seed. Catálogo canónico único en `_demo_seed_common.ROLES_DEMO` + búsqueda
inversa `ROL_ID_POR_NOMBRE`; ambos seeds lo consumen.

**S3 (HIGH) — `seed_demo_director_estrategia.py` sobrescribía al Gerente de Ventas.**
Hardcodeaba `USER_ID = ROLE_ID = CRED_ID = 12` y `USER_ROLE_ID = 31`, exactamente los
del Gerente de Ventas. Correrlo **borraba** `lucia.ramos.ventas`. Detectado en vivo al
ejecutarlo; usuario restaurado y el script pasa a asignar ids libres con `_siguiente_id`.

**S4 (MEDIUM) — Flota ligada a usuarios por id fijo.**
`seed_flota_demo.py` asignaba la unidad 2 a `idusuario=4`, asumiendo que ese usuario
tenía rol Unidad. Al unificar el catálogo de roles, el usuario 4 pasó a ser Operador y
la unidad quedó ligada a alguien que no puede iniciar sesión como unidad (CU-O30
`find_by_usuario` → 403 en `mi-despacho`). Ahora la flota se liga a los usuarios que
**realmente** tienen rol Unidad, resueltos por nombre de rol; se agregó un segundo
usuario Unidad al catálogo demo (`marco.silva.unidad`) para que el despacho pueda
demostrar selección de candidata y escalamiento de zona.

**S5 (MEDIUM) — `Dim_Preferencias_Cliente` vacía.**
`zonas_geograficas` define sobre qué condados el cliente ve expedientes (RN-SEG-005);
sin la fila, el filtro resolvía a cero condados y "Mis expedientes" salía vacío aunque
hubiera casos cerrados. Sembrada en `database/seed_vinculos.py`.

### Tests de infraestructura nuevos

- `tests/regression/test_doble_pinot_vs_esquemas.py` — compara el doble en memoria de
  `conftest.py` contra `database/esquemas.json` en ambos sentidos, y verifica que toda
  tabla consultada por código productivo esté declarada. Habría detectado D2 con el
  mensaje exacto (verificado quitando las dos tablas del esquema).
- `tests/regression/test_credenciales_demo_consistentes.py` — impide que vuelvan a
  divergir la contraseña demo, el valor de `estadocredencial`, el catálogo de roles y
  las cuentas del fixture E2E.

### Verificación realizada

- Backend: `pytest` → 912 pasan, 2 skipped.
- Frontend: `ng test` → 316 pasan.
- Recorrido end-to-end contra el stack real: **42/42 pasos**, incluyendo despacho manual
  creado sobre la candidata que ofrece el sistema, detección de duplicados devolviendo el
  caso similar, y los 12 usuarios demo autenticando con una sola contraseña.
- Navegador: página de acceso denegado conserva la navegación y muestra la sesión;
  «Mis expedientes» lista un expediente real y su detalle renderiza en `<dl>` sin inputs.

---

## 2026-07-31 (3) — Escalamiento de zona demostrable, evidencia paginada y limpieza de datos demo

Alcance: `evidencia-unidad` (backend), infraestructura de datos y seeds (`database/`,
`backend/scripts/`).

Cierra las dudas de la entrada anterior.

### Backend

**B9 (MEDIUM) — Galería de evidencias con el mismo bug de clase D1.**
`EvidenciaFotoRepository.list_by_accidente` traía `SELECT * FROM Dim_EvidenciaFoto
WHERE idaccidente = ...` sin `LIMIT`, y filtraba `sincronizado`, ordenaba y paginaba
en Python **después**. Pinot recortaba a 10 filas antes de que ese filtro se aplicara:
un accidente con más de 10 fotos podía perder evidencia real de la galería sin error
visible. Filtro, orden y tope ahora viajan en el SQL. Regresión con 15 fotos
verificando que las 15 aparecen, más un recorrido paginado sin repetidos ni faltantes.

### Datos demo

**S6 — `rename_demo_unidad_gmail.py` eliminado.**
Era un one-shot que renombraba `diego.ramirez.operador@demo.tsi.com` →
`...unidad@demo.tsi.com`, contradiciendo el catálogo canónico donde el usuario 4 es
Operador. Sin referencias en el resto del repo.

**S7 — Tercera unidad y condado vecino con flota propia.**
El condado 2 (Benito Juárez) existía solo en `Dim_CondadoVecino` como adyacencia, sin
`Dim_Condado`/`Dim_Ciudad`/`Dim_Calle` propios ni unidades: todo escalamiento CU-O34
resolvía "sin unidades disponibles" aunque la consulta de adyacencia funcionara.
Agregados en `database/seed_catalogos.py` (condado, ciudad y calle de Benito Juárez) y
`database/seed_usuarios.py` (tercer usuario `valeria.cortes.unidad@demo.tsi.com`,
rol Unidad). `seed_flota_demo.py` ahora liga cada unidad a su `idcondado` propio y
resuelve los usuarios **por nombre de rol**, no por id fijo — antes asumía que
`idusuario=4` tenía rol Unidad; al unificar el catálogo de roles (ver S2 en la entrada
anterior) ese usuario pasó a ser Operador y la unidad quedaba huérfana.

Verificado end-to-end: con la flota del condado 1 agotada, escalar a zona (CU-O34)
encuentra y asigna la unidad 3 en Benito Juárez (`origen: "Escalado_zona"`), en vez de
reportar siempre "sin unidades en condados vecinos".

**S8 — `database/reset_despachos_demo.py` (nuevo).**
Cada corrida de flujo end-to-end deja despachos activos y unidades `Ocupada`/`En
Misión`; con una flota de 2-3 unidades eso agota las candidatas disponibles en pocas
corridas. El script libera los despachos activos y devuelve las unidades a `Activa`
sin tocar el estado del caso (`Fact_Accidente`) — no reemplaza un cierre real, es
mantenimiento de la flota demo. Idempotente, acepta `--dry-run`.

### Verificación realizada

- Backend: `pytest` → 914 pasan, 2 skipped.
- Frontend: `ng test` → 316 pasan (sin cambios en esta entrada).
- Recorrido end-to-end contra el stack real: **45/45 pasos**, incluyendo el camino
  completo de CU-O34 (condado local agotado → escalamiento → asignación exitosa en
  el condado vecino), verificado también en el navegador (Monitoreo de despacho
  muestra el caso escalado).

---

## 2026-08-01 — Homogeneización de estados loading/error/vacío en el frontend

Alcance: `despacho-inteligente`, `evidencia-unidad`, `seguimiento-cierre-de-casos`,
`Soporte-Cliente`, `Suscripciones-Facturacion` (frontend), `.specify/docs/design/design-system.md`.

Refactor de mantenibilidad, no corrección de bug ni de diseño: las páginas afectadas ya
cumplían el design-system (mostraban los 3 estados no felices correctamente), pero cada
una reimplementaba el mismo HTML que `app-list-loading-skeleton` / `app-list-error-state` /
`app-list-empty-state` ya encapsulan — visualmente indistinguible del golden sample, con
el costo de tener el mismo patrón duplicado en ~10 archivos.

### Migradas a los componentes compartidos

| Página | Loading | Error | Vacío |
|---|---|---|---|
| `despacho/mi-despacho` | ✓ | ✓ | ✓ |
| `despacho/monitoreo-despacho` | ✓ | ✓ | — (detalle, no aplica) |
| `evidencia-unidad/panel-disponibilidad` | ✓ | ✓ | — (detalle, no aplica) |
| `seguimiento/historial-emergencias` | ✓ | ✓ | ✓ |
| `seguimiento/mi-seguimiento` | ✓ | ✓ | ✓ |
| `soporte-cliente/detalle-ticket` | ✓ | — (sin error propio) | — |
| `soporte-cliente/mis-tickets` | ✓ | — (usa toast, no bloque) | ✓ |
| `suscripciones/plan-form` | ✓ | — (error de guardado sin retry, se deja inline) | — |
| `evidencia-unidad/galeria-evidencias` | — | — (semántica `alerta-media`, no crítica) | ✓ (con CTA proyectado) |
| `soporte-cliente/cola-agente` | — (skeleton de master-detail, forma propia) | — (banner persistente, no bloque) | ✓ |

Todos los `data-testid` (`loading-skeleton`, `error-state`, `empty-state`,
`btn-reintentar-lista`) se mantuvieron idénticos: **ningún spec de contrato de UI ni test
existente requirió cambios**, la migración es puramente de implementación.

### Deliberadamente dejadas sin migrar

- **`soporte-cliente/dashboard-soporte`** — grid de KPIs (design-system distingue
  "bloques de KPIs con ring charts" de listados; el skeleton de filas no representa la
  forma de una card de métrica).
- **`suscripciones/mi-suscripcion`** — tarjeta resumen con título propio
  ("No pudimos cargar tu suscripción") + descripción; el componente compartido es de una
  sola línea de mensaje, forzar el título ahí perdería información.
- **`cuentas-clientes/incorporacion-clientes/aprobacion-solicitudes`** — usa `@empty` de
  Angular dentro de una lista corta (una fila de texto), no un bloque de página completo.
- **`cuentas-clientes/auth/login`, `ventas-crm/registro-publico`** — falsos positivos de
  la búsqueda inicial: el `animate-pulse` detectado es el punto de estado "En vivo" del
  header, no un skeleton de carga.
- Errores con tono `alerta-media`/banner persistente en vez de bloque con "Reintentar"
  (`galeria-evidencias`, `cola-agente`, `dashboard-soporte`) se dejan inline: forzarlos al
  componente compartido cambiaría su severidad semántica (crítico vs. advertencia) o su
  patrón de interacción (bloqueante vs. banner conviviendo con datos).

### Regla añadida al design-system

Sección "Estados de carga, vacío y error": los componentes compartidos son la
implementación obligatoria para cualquier página con estos tres estados, no solo listados
Ver-only; reproducir el patrón con HTML propio solo se justifica cuando la forma del
contenido difiere genuinamente (KPIs, resumen con título) o el error no tiene una acción
de "Reintentar" con sentido.

### Verificación realizada

- Frontend: `ng test` → 316 pasan (sin cambios en el conteo — la migración no tocó ningún
  test, todos los `data-testid` se preservaron).
- `ng build` de producción sin errores nuevos.
- Recorrido end-to-end contra el stack real: 45/45 pasos.
- Navegador: `mis-tickets` (8 tickets, sin loading colgado), `mi-suscripcion` (renderiza
  sin errores) verificados tras el despliegue.

---

## 2026-08-02 — Limitaciones conocidas de los informes tácticos compuestos (`002-tactico`)

Alcance: `specs/002-tactico/Emergencias/informes-tacticos-compuestos/`, hallazgos de la
revisión final contra el stack real. No son bugs — son decisiones de diseño forzadas por
huecos del esquema actual, documentadas aquí para no volver a proponerlas sin este
contexto (una ya se resolvió, ver entrada de más abajo).

**L1 — Semántica de `materializado` en los 3 informes compuestos.** Los DAGs
(`perdida_senal_gps`, `indice_calidad_historico`, `rendimiento_por_proveedor`) reprocesan
el histórico completo en cada corrida, no una ventana incremental. Consecuencia: una vez
que un DAG corrió al menos una vez, `materializado` es `true` para *cualquier* período
consultado (incluso uno futuro sin datos) — la ausencia de filas para ese rango se lee
como "sin eventos en ese período", no como "el DAG no lo ha procesado todavía". Si en el
futuro se necesita una ventana incremental (por volumen de datos), esta semántica cambia
y hace falta una lógica de "no materializado" por período explícita (ej. una tabla de
control de corridas por rango de fechas). No es necesario hoy — el volumen de datos del
proyecto no lo justifica.

**L2 — `rendimiento_por_proveedor` usa el proveedor *actual* de cada unidad, no el
histórico.** `Dim_UnidadEmergencia.idcliente` no tiene versión histórica (sin tabla tipo
SCD) — el DAG no puede saber qué proveedor operaba una unidad en el momento de un
despacho pasado si esa unidad cambió de proveedor después. Si el negocio necesita
atribución histórica correcta de rendimiento por proveedor (ej. para negociar contratos
según desempeño pasado), hace falta una tabla nueva `Fact_HistorialProveedorUnidad` (o
similar) que registre cada cambio de `idcliente` por unidad con su vigencia — no
implementada, es un cambio de esquema más grande que L3 (tabla nueva completa vs. un
campo en tabla existente).

**L3 — `idusuario` en `Fact_HistorialDespachoUnidad` — RESUELTO 2026-08-02.** Ver la
sección "Campo `idusuario` en `Fact_HistorialDespachoUnidad`" más abajo — esta limitación
ya no aplica.

---

## 2026-08-02 — Campo `idusuario` en `Fact_HistorialDespachoUnidad`

Alcance: `database/esquemas.json`, `backend/core/repositories/despacho/`,
`backend/core/repositories/informes_tacticos/seguimiento_repository.py`, `backend/conftest.py`.

Resuelve L3 de la entrada anterior: el informe táctico "% de cierres forzados sobre total
de cierres" (`informes-tacticos-simples`) aproximaba "forzado" con
`estadonuevo = 'Retirado'` sobre el total de transiciones a estado terminal, sin poder
distinguir un retiro hecho por un Operador de uno automático por vencimiento — la tabla
no tenía forma de saber quién (o si alguien) causó la transición.

**Cambio de esquema:** campo `idusuario` (INT, nullable) añadido a
`Fact_HistorialDespachoUnidad` — `NULL`/ausente cuando la transición es automática
(sistema), poblado con el id del operador cuando la transición la causa una acción humana
explícita (ej. retiro forzado desde central).

**Cambio de código:** ver detalle en `traceability.md` de
`specs/002-tactico/Emergencias/informes-tacticos-compuestos/backend/` — repositorio de
escritura de historial de despacho actualizado para aceptar `idusuario` opcional, caso de
uso de retiro de despacho actualizado para pasar el id del operador actuante, y
`cierres_forzados()` reescrito para calcular "forzado" como `estadonuevo='Retirado' AND
idusuario IS NOT NULL` en vez de la aproximación anterior.

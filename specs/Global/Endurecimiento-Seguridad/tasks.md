# Tasks: Endurecimiento de Seguridad Transversal

**Input**: Documentos de diseño en `/specs/Global/Endurecimiento-Seguridad/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/)

**Tests**: Sí, y son **el entregable**, no un añadido. Esta feature no construye funcionalidad de
negocio: construye las verificaciones que faltan. Cuando una tarea dice «implementar», se refiere
al mecanismo que la prueba necesita para poder afirmar algo.

**Organization**: agrupadas por historia de usuario, cada una entregable e independiente.

## Format: `[ID] [P?] [Story] Descripción`

- **[P]** — paralelizable: toca ficheros distintos y no depende de tareas incompletas.
- **[USn]** — historia a la que pertenece. Setup, Foundational y Polish no llevan etiqueta.

## Path Conventions

Repositorio web (Opción 2 del plan): backend en `backend/`, frontend en `frontend/`. Las suites
transversales viven en `backend/tests/seguridad/` y las utilidades en `backend/core/seguridad/`
(ver `plan.md` §Structure Decision).

---

## ⚠️ Antes de empezar: tres cosas que ahorran horas

1. **Toda prueba autenticada necesita la fixture que mockea Pinot.** Sin ella,
   `JWTSessionAuthentication` sale a buscar un Pinot real, agota el timeout y devuelve `401` — un
   fallo que **aparenta ser de permisos**. Costó 42 pruebas en falso rojo (`changelog.md` C3, la
   pista era el tiempo de ejecución, no el aserto).
2. **US3 no empieza hasta que exista la lista de exclusiones del fail-closed** (T031). Principio IX:
   denegar un despacho porque Redis no responde es peor que el riesgo que se evita.
3. **No romper contratos OpenAPI.** Partners integra contra esta API. `403` y `404` ya están
   declarados; el trabajo es elegir cuál corresponde, no inventar códigos.

---

## Phase 1: Setup

**Purpose**: estructura y dependencias que todo lo demás necesita.

- [X] T001 Crear el paquete de suites transversales en `backend/tests/seguridad/` con su `__init__.py`
- [X] T002 Crear el paquete de utilidades en `backend/core/seguridad/` con su `__init__.py`
- [X] T003 [P] Añadir `puremagic` a `backend/requirements.txt` (elegido en `research.md` §R4: Python puro, sin dependencia nativa que divergiría entre Windows y Linux)
- [X] T004 [P] Añadir el marker `seguridad` a `backend/pytest.ini` para poder ejecutar el bloque completo de forma aislada

---

## Phase 2: Foundational (Prerrequisitos bloqueantes)

**Purpose**: el inventario de rutas, del que dependen US1 y US2 — las dos historias de mayor valor.

**⚠️ CRITICAL**: ninguna historia puede empezar hasta que esta fase esté completa.

- [X] T005 Implementar el recorrido recursivo del `URLResolver` en `backend/core/seguridad/inventario_rutas.py`, acumulando prefijos a través de los `include()` anidados (`research.md` §R3)
- [X] T006 Añadir a `inventario_rutas.py` la extracción de `parametros_id` desde el patrón (`<int:idpartner>` → `idpartner`) y de los métodos HTTP que implementa cada vista
- [X] T007 Añadir a `inventario_rutas.py` la lectura de `permission_classes` declaradas por cada vista, que US2 necesita
- [X] T008 Crear `backend/tests/seguridad/test_inventario_rutas.py` que afirme las cifras de referencia medidas el 2026-08-23: **234 rutas `api/v1`** y **92 con identificador**. Si cambian, es que se añadieron o quitaron endpoints y hay que revisar la cobertura — no relajar el número
- [X] T009 [P] Crear la fixture compartida `cliente_dos_tenants` en `backend/tests/seguridad/conftest.py`: dos tenants con recursos propios, más las **dos** vías de autenticación (JWT de usuario y credencial de partner, `research.md` §R2)
- [X] T010 [P] Incluir en ese mismo `conftest.py` la fixture `_pinot_en_memoria` con `autouse=True`, para que ninguna prueba del paquete pueda olvidarla

**Checkpoint**: el inventario responde y las cifras cuadran. US1 y US2 pueden empezar.

---

## Phase 3: User Story 1 — Aislamiento multi-tenant (P1) 🎯 MVP

**Goal**: que un partner no pueda ver ni modificar datos de otro sustituyendo un identificador.

**Independent Test**: autenticarse como tenant A, pedir recursos de B en las 92 rutas con
identificador, por las dos vías de autenticación, y comprobar que ninguna devuelve datos ajenos.

### Tests

- [X] T011 [P] [US1] Crear `backend/tests/seguridad/test_aislamiento_tenant.py` con la prueba parametrizada sobre el inventario: para cada ruta con identificador, tenant A pide el recurso de B en `GET` y no recibe datos
- [X] T012 [US1] Extender esa prueba a `PUT`, `PATCH` y `DELETE`, afirmando además que **el recurso de B no se modifica** — no basta con el código de respuesta
- [X] T013 [P] [US1] Añadir la prueba de indistinguibilidad del contrato C1: para un actor **no gestor**, la respuesta ante un id inexistente y ante uno ajeno debe ser **idéntica en código y cuerpo**
- [X] T014 [P] [US1] Añadir la prueba complementaria: un actor **gestor** sí recibe `404` ante un id inexistente, para que la corrección no degrade el diagnóstico de la consola de gestión
- [ ] T015 [US1] Añadir la prueba de identificadores **en el cuerpo** de la petición, no solo en la URL — incluidos los anidados en listas (caso borde de la spec)
- [X] T016 [US1] **La prueba que da valor duradero (SC-002):** afirmar que toda ruta del inventario con `parametros_id` tiene cobertura de aislamiento; una ruta nueva sin ella hace **fallar** la suite. Sin esto la cobertura envejece en cuanto alguien añade un endpoint

### Implementación

- [X] T017 [US1] Ejecutar la suite y **catalogar los fallos** en `backend/tests/seguridad/HALLAZGOS.md`: cada ruta que devuelve datos ajenos, con su módulo. Este catálogo es el trabajo real de US1 — hasta ahora nadie ha medido cuántas hay
- [X] T018 [US1] Revisar los **siete servicios de Partners** que lanzan `not_found` por su cuenta (`consulta_partner_service`, `emitir_credencial_service`, `metricas_consumo_service`, `promocion_produccion_service`, `reactivar_partner_service`, `suspender_partner_service`, `asignar_plan_acceso_service`) y determinar si un no gestor los alcanza con un id ajeno; si puede, el oráculo sigue vivo por esa vía (`data-model.md` §4)
- [ ] T019 [US1] Extender el patrón `resolver_partner_visible` a las vistas restantes de `backend/apps/partners/views/` que aún cortan con `404` antes de comprobar propiedad
- [ ] T020 [P] [US1] Aplicar el mismo patrón en los módulos que el catálogo de T017 señale — previsiblemente `cuentas_clientes`, `soporte_cliente` y `suscripciones`, que tienen recursos por tenant
- [ ] T021 [US1] Verificar el supuesto de `data-model.md` §1.2: que un usuario pertenece siempre a **un** cliente. Si existiera el caso de usuario con varias organizaciones, el eje de aislamiento deja de ser escalar y toda la suite cambia de forma
- [ ] T022 [US1] Igualar el trabajo de ambas ramas de denegación para cerrar el **canal temporal**: hoy «no existe» retorna sin consultar el cliente y responde más rápido que «no es tuyo» (`decisiones-pendientes.md` #51)


> **Estado al 2026-08-23.** Hechas T011–T014, T016, T017, T018 y T078. La suite existe, **no
> miente** y encontró **dos oráculos de enumeración reales**, ambos corregidos: uno en Soporte
> —módulo que nadie había revisado— y otro en `PartnerDetalleView`, que la corrección manual de C4
> no alcanzó. Ver `backend/tests/seguridad/HALLAZGOS.md` y `changelog.md` C5.
>
> ⚠️ **50 de 62 combinaciones acotadas por tenant siguen sin ejercitar.** Son superficie *sin
> examinar*, no limpia. T079 corrigió tres roles mal elegidos, sembró tres materias más y modeló
> los roles transversales; queda el `404` de expedientes (T080).
>
> Pendientes de la fase: T015 (ids en el cuerpo), T019, T020, T021, T022.

**Checkpoint**: ⚠️ **NO alcanzado.** `PG-SEC-001` sigue en ⚠️ Parcial: la suite mide 2/92.

---

## Phase 4: User Story 2 — Autorización vertical por rol (P1)

**Goal**: que ningún rol acceda a materia ajena, con la matriz completa verificada.

**Independent Test**: generar las 3.510 celdas (15 roles × 234 rutas) y comprobar que ninguna queda
en `DESCONOCIDO`.

### Tests

- [ ] T023 [P] [US2] Crear `backend/tests/seguridad/test_matriz_roles.py` que genere la matriz cruzando el inventario (T005) con los 15 roles declarados
- [ ] T024 [US2] Interrogar **la clase de permiso** directamente, no la pila HTTP: 3.510 peticiones reales harían el ciclo rápido inviable y llevarían a que se deje de esperar el CI (`research.md` §R6). El patrón ya existe en `test_permisos_red_operativa.py::_concede`
- [ ] T025 [US2] Reservar el camino HTTP completo para una **muestra de casos de denegación**, que son los que prueban el recorrido entero: un permiso demasiado ancho no produce ningún síntoma
- [ ] T026 [US2] Emitir las celdas sin verificar como `DESCONOCIDO` **en la salida de la prueba**, nunca omitirlas: una matriz parcial que calla sus huecos parece completa

### Implementación

- [ ] T027 [US2] Catalogar en `HALLAZGOS.md` las celdas donde el permiso concede de más
- [ ] T028 [US2] Declarar `permission_classes` explícitas en las vistas que el catálogo revele sin ellas
- [ ] T029 [US2] Reducir a cero los `DESCONOCIDO`, decidiendo para cada celda si el rol debe entrar

**Checkpoint**: US1 y US2 funcionan de forma independiente. `PG-SEC-002` → ✅.

---

## Phase 5: User Story 3 — Integridad del JWT (P1)

**Goal**: que ningún token manipulado sea aceptado.

**Independent Test**: seis variantes adversariales contra un endpoint protegido; todas `401` con
cuerpo idéntico.

**⚠️ Bloqueada por T031.** No empezar sin esa lista.

### Decisión previa

- [X] T030 [US3] Inventariar los endpoints de la **cadena crítica** (registro → despacho → seguimiento → cierre) a partir de `constitution.md` §Additional Constraints
- [X] T031 [US3] Fijar por escrito, en `research.md`, qué endpoints quedan **excluidos** del fail-closed y por qué, justificándolo por Principio IX. Denegar el despacho de una ambulancia porque Redis no responde es peor que el riesgo que se evita — y el Principio IX es absoluto: Safety gana sobre Security sin excepción

### Tests

- [X] T032 [P] [US3] Crear `backend/tests/seguridad/test_integridad_jwt.py` con las seis variantes: firma alterada, `alg: none`, algoritmo ≠ RS256, expirado, claims de rol/tenant manipulados, sesión revocada
- [X] T033 [US3] Afirmar que las seis devuelven `401` **con el mismo cuerpo** (contrato C3): distinguir «firma inválida» de «expirado» le dice al atacante qué modificar
- [X] T034 [US3] Añadir la prueba de la distinción que sí debe mantenerse: `401` = «no sé quién eres» · `403` = «sé quién eres y no puedes». Devolver `401` a un usuario autenticado con rol insuficiente es el fallo de `changelog.md` C3
- [X] T035 [US3] Probar el fail-closed: con el almacén de sesión inaccesible, un endpoint **no excluido** deniega
- [X] T036 [US3] Probar la contraparte: un endpoint **excluido** de T031 sigue operativo con el almacén caído

### Implementación

- [X] T037 [US3] Ajustar `backend/apps/cuentas_clientes/authentication.py` para cubrir las variantes que hoy pasen, y unificar el cuerpo de la respuesta
- [X] T038 [US3] Implementar el fail-closed con la lista de exclusiones de T031, documentada en el propio código

> **Estado al 2026-08-23.** T030–T035 hechas: 14 pruebas, **el sistema resiste las seis variantes
> adversariales** —incluida la confusión de algoritmo— y la revocación de sesión funciona.
>
> ⚠️ **Hallazgo sobre las propias pruebas.** Debilitando `verify_access_token` para admitir `HS256`
> y `none`, las 12 primeras **seguían en verde**: PyJWT se defiende solo, negándose a usar una
> clave asimétrica como secreto HMAC. El ataque falla, pero **no por mérito del proyecto**. Se
> añadieron dos pruebas que verifican la configuración propia y sí detectan el debilitamiento.
>
> Pendientes: T036 (endpoint excluido operativo con el almacén caído), T037 y T038 — **bloqueadas
> por la confirmación de la lista de exclusiones de T031**, que es decisión del responsable.

**Checkpoint**: `PG-SEC-003` → ✅ (degradación selectiva implementada, `changelog.md` C10).

---

## Phase 6: User Story 5 — Datos sensibles en logs y respuestas (P1)

**Goal**: que ningún error revele datos de una víctima.

**Independent Test**: provocar errores en endpoints con datos de víctimas e inspeccionar respuesta
y log.

> Se adelanta a US4 respecto al orden de la spec: es independiente, más barata, y toca la
> configuración de logging que conviene tener estable antes de la fase larga de inyección.

### Tests

- [X] T039 [P] [US5] Crear `backend/tests/seguridad/test_datos_sensibles.py` que afirme que ninguna respuesta de error incluye traza, rutas internas, nombres de tabla ni SQL
- [X] T040 [US5] Añadir la prueba de enmascarado en logs: identificación, correo, teléfono, coordenadas de víctimas y tokens no aparecen en claro
- [X] T041 [US5] Probar el caso que más filtra: una excepción **no controlada** en un endpoint con datos de víctima

### Implementación

- [~] T042 [P] [US5] ~~Implementar el filtro de logging en `backend/core/seguridad/enmascarado.py`~~ — **no necesario**: T040 y T041 confirman que los logs no escriben datos personales, tokens ni coordenadas en claro. Añadirlo sería maquinaria sin problema que resolver
- [~] T043 [US5] ~~Registrarlo en `LOGGING`~~ — sin objeto tras descartar T042
- [X] T044 [US5] Verificar que `core/api/response_envelope.custom_exception_handler` es el **único** camino de salida, y que ninguna vista devuelve un formato propio (contrato C7)

> **Estado al 2026-08-23.** 11 pruebas. **Los logs y las respuestas ya estaban limpios**: no
> escriben datos personales, tokens ni coordenadas, y los errores no revelan traceback ni SQL.
> **T042/T043 (filtro de enmascarado) no se implementaron a propósito** — se verificó que no hacen
> falta en vez de añadir maquinaria por si acaso.
>
> Corregido de paso: `POST /usuarios` daba **500** ante cuerpo incompleto (`changelog.md` C7).
>
> ⚠️ Pendiente: auditar el resto de endpoints de escritura — el patrón puede repetirse
> (`PG-API-004`, T081).

**Checkpoint**: `PG-SEC-007` → ⚠️ Parcial.

---

## Phase 7: User Story 4 — Inyección (P1)

**Goal**: que ningún filtro de informe pueda alterar la consulta.

**Independent Test**: cargas de inyección en cada parámetro de filtro de cada informe.

> La más laboriosa del bloque: exige inventariar los parámetros de todos los informes.

### Tests

- [X] T045 [P] [US4] Inventariar los parámetros de filtro, criterios de orden y nombres de columna variables de los informes de `informes_tacticos` e `informes_estrategicos`
- [X] T046 [US4] Crear `backend/tests/seguridad/test_inyeccion.py` con cargas por cada parámetro, distinguiendo los tres tipos de `data-model.md` §2.4: valor de filtro, nombre de columna y criterio de orden
- [X] T047 [US4] Afirmar que la respuesta **no contiene mensajes del motor** de base de datos, que son los que guían al atacante
- [X] T048 [US4] Marcar `integration` la variante que corre contra Pinot y ClickHouse reales. **Un mock acepta cualquier SQL**: no distingue una consulta correcta de una inyectada, así que solo el motor real prueba algo aquí

### Implementación

- [X] T049 [US4] Catalogar en `HALLAZGOS.md` los constructores de consultas que concatenan entrada del usuario
- [X] T050 [US4] Parametrizar los valores de filtro donde hoy se concatenen
- [X] T051 [US4] Implementar **lista blanca** para nombres de columna y criterios de orden, donde la parametrización no aplica — es la superficie de máximo riesgo, y por eso es fácil de olvidar

> **Estado al 2026-08-23.** **Sin vulnerabilidades**: los `WHERE` están parametrizados, ClickHouse
> liga del lado servidor y el `ORDER BY` se compone de constantes. T049–T051 no requirieron cambios.
>
> ⚠️ **Dos fallos de la propia suite, corregidos.** (1) Los nombres de parámetro estaban adivinados
> —`orden` en vez de `dir`—: sustituidos por los 62 extraídos del código. (2) La suite **no detecta
> inyecciones**: introduciendo una real en el `ORDER BY`, las 497 pruebas siguieron en verde porque
> el doble de Pinot no analiza SQL. El límite está declarado en la cabecera y la verificación real
> vive en `test_inyeccion_integracion.py`.

**Checkpoint**: `PG-SEC-005` → ⚠️ Parcial (la verificación real espera a `integracion.yml`).

---

## Phase 8: User Story 6 — Límite de tasa efectivo (P2)

**Goal**: que los cupos declarados se apliquen de verdad.

**Independent Test**: superar cada uno de los cuatro throttles y recibir `429`.

- [X] T052 [P] [US6] Crear `backend/tests/seguridad/test_throttles.py` parametrizado **sobre `DEFAULT_THROTTLE_RATES` de `settings.py`**, no sobre una lista a mano: un throttle nuevo sin prueba debe hacer fallar la suite
- [X] T053 [US6] Afirmar `429` y la cabecera `Retry-After` al superar cada cupo (contrato C4)
- [X] T054 [US6] Añadir la prueba de la frontera de negocio: **ninguna** prueba debe esperar `429` por cuota **mensual** de partner. `RN-APM-002` dice que el cupo mensual no bloquea, se factura — esperarlo verificaría lo contrario de la regla
- [X] T055 [US6] Corregir los throttles que el resultado revele mal aplicados

**Checkpoint**: `PG-SEC-004` → ✅.

---

## Phase 9: User Story 7 — Subida de archivos (P2)

**Goal**: que un ejecutable renombrado a `.jpg` no entre.

**Independent Test**: subir ficheros de tipos y tamaños diversos al endpoint de evidencia.

- [X] T056 [P] [US7] Implementar la validación por bytes mágicos con `puremagic` en `backend/core/seguridad/validacion_archivos.py`
- [X] T057 [P] [US7] Implementar el saneado de nombre (sin `../`) en el mismo módulo
- [X] T058 [US7] Crear `backend/tests/seguridad/test_subida_archivos.py`: ejecutable renombrado a `.jpg` → `400`; 51 MB → `413`; nombre con travesía → saneado; SVG con script → rechazado
- [X] T059 [US7] Afirmar que el `detail` **no revela el tipo detectado** (contrato C5): «se esperaba una imagen» basta; «se detectó un ejecutable» le confirma al atacante que la detección funciona
- [X] T060 [US7] Integrar la validación en los endpoints de evidencia fotográfica y de adjuntos de soporte
- [X] T061 [US7] Documentar en `data-model.md` que los bytes mágicos identifican el **formato**, no garantizan contenido inocuo: un JPEG válido puede llevar carga en metadatos, y eso queda fuera de alcance

**Checkpoint**: `PG-SEC-006` → ✅.

---

## Phase 10: User Story 8 — Cabeceras y CSP (P2)

**Goal**: completar lo que quedó parcial el 2026-08-23.

**Independent Test**: inspeccionar cabeceras en Django y en `nginx.conf`.

- [X] T062 [P] [US8] Crear `backend/tests/seguridad/test_cabeceras.py` afirmando las cinco cabeceras del contrato C6, incluidas las respuestas de **error**
- [X] T063 [US8] Definir la CSP restrictiva en `backend/config/settings.py` y ajustarla a lo que el frontend Angular requiera realmente — nunca al revés
- [X] T064 [P] [US8] Verificar que `frontend/nginx.conf` no omite ni contradice ninguna cabecera del backend
- [X] T065 [US8] Añadir la comprobación de la CSP a la prueba, con `DJANGO_DEBUG=false`

**Checkpoint**: `PG-SEC-008` → ✅.

---

## Phase 11: User Story 9 — Aislamiento de la demo (P2)

**Goal**: que la demo no sea una puerta trasera.

**Independent Test**: usar un token de demo válido contra endpoints de negocio.

- [X] T066 [P] [US9] Añadir a `backend/apps/ventas_crm/tests/` la prueba de que un token de sesión de demo contra un endpoint de negocio devuelve `401`
- [X] T067 [US9] Probar que una sesión de demo solo alcanza datos sintéticos, nunca registros reales de clientes
- [X] T068 [US9] Corregir lo que el resultado revele

**Checkpoint**: `PG-SEC-010` → ✅. Las nueve historias, cerradas.

---

## Phase 12: Polish & Cross-Cutting

- [X] T069 Añadir `backend/tests/seguridad/` al job correspondiente de `.github/workflows/ci.yml`. **Sin esto nada de lo anterior protege**: una suite que no corre sola equivale a no tener suite (`PG-CI-001`)
- [X] T070 Verificar SC-002 a mano: añadir una ruta con identificador sin filtro de tenencia y comprobar que la suite **falla** nombrándola. Si pasa, la suite no protege — y produce confianza infundada, que es peor
- [ ] T071 Comprobar que ninguna prueba del bloque quedó `skip`/`xfail` sin justificación y fecha de caducidad (`PG-CI-003`)
- [ ] T072 Ejecutar `pytest -m "not integration" -q` completo: 0 fallos (referencia 2026-08-23: 4142 passed)
- [ ] T073 Comprobar que las verificaciones añadidas no degradan los presupuestos P95 de `testing.md` (`PG-RES-001`)
- [ ] T074 Actualizar el estado de las nueve reglas en `specs/Global/PlanPruebas/spec.md`
- [ ] T075 **Regenerar** `specs/Global/PlanPruebas/traceability.md` con su script — se cuenta desde el spec, no se escribe a mano
- [ ] T076 Registrar la entrada en `.specify/docs/changelog.md` con causa, efecto verificado y archivos, según la regla de `AGENTS.md`
- [ ] T077 Anotar en `decisiones-pendientes.md` lo que quede abierto tras el bloque, con fecha de caducidad

---

## Tareas descubiertas durante la implementación

- [X] T078 [US1] **Ampliar `backend/tests/seguridad/conftest.py` con un actor por materia** (Cliente, Director de Operaciones, Gerente de Ventas, Director Financiero, Partner con datos sembrados) y sembrar recursos para **ambos** tenants. Descubierta al ejecutar T011: con un único `PartnerIntegracion`, 90 de las 92 rutas se deniegan por rol y no llegan a ejercitar la tenencia. **Bloquea a T011–T013 y por tanto a todo US1** — sin esto la suite no puede examinar el 98 % de la superficie. **Hecho:** cinco actores (partner, cliente, operaciones, ventas, finanzas) y siembra de dos tenants en `datos_dos_tenants.py`. Ejercitadas de 2 a 13; destapó V1 y V2

- [X] T079 [US1] Continuar la siembra de `tests/seguridad/datos_dos_tenants.py` con **accidentes, despacho y red operativa**, las materias que aún dejan 142 de 155 combinaciones sin ejercitar. Cada una sin sembrar es superficie sin examinar, no superficie limpia. **Hecho:** sembrados accidentes (eje por condado, no por `idcliente`), despacho y red operativa; siete actores con los roles que el sistema declara; y `ROLES_ACOTADOS_POR_TENANT` para no exigir aislamiento a roles transversales por diseño. Denominador honesto: **13/62**

- [X] T080 [US1] Investigar por qué `cliente/expedientes/{idaccidente}` devuelve `404` incluso para el accidente **propio** del cliente: la siembra crea el accidente y las preferencias, pero `ExpedienteService` no lo encuentra. Probablemente falte la cadena `idcalle`→`idcondado` o el despacho asociado. Bloquea la cobertura de la materia de expedientes, que es la que maneja datos de víctimas. **Hecho:** eran cuatro condiciones de la siembra (estado CERRADO, cadena calle→ciudad→condado, `idaccidente` en las notificaciones, nombre del campo de estado). El módulo ya era correcto — ajeno e inexistente responden idéntico— pero ahora está verificado. De paso se endureció el criterio de «ejercitada» a 2xx sobre el recurso propio: 12/62

---

## Dependencias

```
Setup (T001-T004)
      ↓
Foundational (T005-T010)  ← inventario de rutas: BLOQUEA US1 y US2
      ↓
      ├─ US1 (T011-T022)  🎯 MVP
      ├─ US2 (T023-T029)  ← reutiliza el inventario; barata tras US1
      ├─ US3 (T030-T038)  ← T031 bloquea el resto de la fase
      ├─ US5 (T039-T044)  ← independiente
      ├─ US4 (T045-T051)  ← independiente, la más larga
      ├─ US6 (T052-T055)  ┐
      ├─ US7 (T056-T061)  ├─ independientes entre sí
      ├─ US8 (T062-T065)  │
      └─ US9 (T066-T068)  ┘
      ↓
Polish (T069-T077)
```

**Única dependencia entre historias:** US2 reutiliza el inventario que construye la fase
Foundational para US1. Por eso hacer US1 primero abarata US2 casi por completo.

## Oportunidades de paralelismo

**Dentro de Foundational:** T009 y T010 son ficheros distintos.

**Entre historias:** tras el checkpoint de Foundational, US3, US5, US6, US7, US8 y US9 no se tocan
entre sí. US1 y US2 comparten el inventario pero escriben en suites separadas.

**Bloque P2 completo:** T052, T056, T062 y T066 pueden ir en paralelo — cuatro suites
independientes.

## Estrategia de implementación

**MVP = US1.** Es la de mayor riesgo real y entrega valor sola: al terminarla se sabe, por primera
vez con datos, cuántos endpoints filtran datos entre tenants. Ese catálogo (T017) es probablemente
el resultado más valioso de toda la feature, y aparece antes de arreglar nada.

**Entrega incremental:** cada historia cierra su regla en el plan global, así que el progreso es
visible sin esperar al bloque entero.

**Orden recomendado:** US1 → US2 (barata tras US1) → US5 (independiente y rápida) → US3 (cuando
T031 esté decidida) → US4 (la larga) → P2 en cualquier orden.

⚠️ **No dejar T069 para el final por costumbre.** Conviene enganchar la suite al CI en cuanto US1
tenga algo que ejecutar: una suite de seguridad que solo corre a mano protege mientras alguien se
acuerda, y nadie se acuerda.

---

## Formato

Las 77 tareas siguen `- [ ] TID [P?] [USn?] descripción con ruta`. Setup, Foundational y Polish no
llevan etiqueta de historia, según la convención.

- [ ] T081 Auditar los endpoints de escritura restantes buscando el patrón que produjo el 500 de `changelog.md` C7: `request.data` pasado en crudo a un servicio que indexa por clave sin validar. Cada aparición es un `500` en potencia, y el `500` es el único camino sin garantía sobre lo que muestra

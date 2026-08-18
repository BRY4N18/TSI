# Tasks: Informes Compuestos de Cuentas y Clientes sobre el Modelo Analítico

**Input**: Design documents from `specs/002-tactico/Cuentas-Clientes/informes-compuestos-modelo/backend/`

**Prerequisites**: [`plan.md`](plan.md), [`spec.md`](spec.md), [`research.md`](research.md), [`data-model.md`](data-model.md), [`contracts/`](contracts/)

**Tests**: **incluidos y obligatorios.** Este módulo tiene cinco formas de equivocarse que **no
fallan**: romper las cifras de Suscripciones al ampliar su dimensión, calcular el embudo sobre lo
observado, promediar sesiones sin cierre, contar inicios y llamarlo concurrencia, y leer la ocupación
sin su cobertura.

**Organization**: agrupadas por user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: puede ejecutarse en paralelo (ficheros distintos, sin dependencias pendientes)
- **[Story]**: US1, US2, US3 según `spec.md`
- Cada tarea lleva su ruta exacta

---

## ⚠️ Lo que distingue a este módulo

**Es el único que amplía una dimensión de otro módulo en vez de crear la suya.** `dim_cliente` la
creó Suscripciones; este departamento es su **dueño** y llega el sexto. Si la ampliación mueve las
cifras de Suscripciones, **el modelo compartido no funciona** — y eso se comprueba antes que
cualquier informe.

**Y trae un patrón nuevo: medir por ausencia.** El sistema no registra abandonos de onboarding, solo
lo completado. El embudo se deduce contra un **catálogo explícito** de etapas, y ahí está su trampa.

**⚠️ Depende de las fases 1 y 2 de Emergencias** y de la **fase 2 de Suscripciones**.

---

## Phase 1: Setup

- [X] T001 Verificar que el modelo analítico está cargado, ejecutando `docker exec -w /opt/airflow tactico-airflow-scheduler python -m pytest dags/tests -q`
- [X] T002 Verificar que **las fases 1 y 2 de Emergencias están implementadas**: existen `dags/lib/consultas/__init__.py` y `backend/core/repositories/informes_tacticos/modelo_repository.py`
- [X] T003 ⚠️ Verificar que **`dim_cliente` y `dim_plan` están cargadas por Suscripciones**, con `SELECT count() FROM dim_cliente FINAL`. Este módulo **amplía la primera**: si no existe, no hay nada que ampliar
- [X] T004 **Anotar las cifras actuales de Suscripciones** —MRR, ingresos y distribución de cartera— en `specs/002-tactico/Cuentas-Clientes/informes-compuestos-modelo/backend/quickstart.md` §2.1. Son la referencia contra la que se comprobará que la ampliación no rompió nada
- [X] T005 Crear `dags/lib/consultas/cuentas/` con un `README.md` que remita a `contracts/catalogo-consultas.md` y recoja **las cuatro reglas propias**: embudo contra catálogo, duración solo con cierre, concurrencia por solape, y sin token ni identidad

---

## Phase 2: Foundational — la ampliación, la pertenencia y las sesiones

**Purpose**: `dim_cliente` ampliada la necesitan US1 y US2; `hecho_sesion`, US1 y US3; y
`dim_usuario_organizacion` es imprescindible para construir el hecho de sesión.

**⚠️ CRÍTICO**: ninguna user story puede empezar hasta que esta fase esté completa.

### La ampliación de `dim_cliente` ⚠️

- [X] T006 ⚠️ Ampliar `dim_cliente` en `dags/lib/ddl.py` con las seis columnas de `data-model.md` §2: cohorte de alta, fecha y motivo de baja, etapa de onboarding derivada, onboarding completo y resultado de solicitud. **Las columnas que Suscripciones ya usa no se tocan**
- [X] T007 ⚠️ Poblarlas en `dags/lib/dimensiones/dim_cliente.py` —**el módulo de Suscripciones**, no uno nuevo—. Crear una dimensión de cliente propia produciría **dos verdades sobre el mismo cliente**, y los ingresos de Suscripciones dejarían de cuadrar con las cuentas activas **sin que nada fallara**
- [X] T008 ⚠️ Derivar `etapa_onboarding_actual` de **las etapas registradas**, no de `estado_onboarding` del sistema operativo, que está **nula en un cliente activo**
- [X] T009 ⚠️ **Prueba de que la ampliación no rompió a Suscripciones** en `dags/tests/test_dim_cliente_ampliacion.py`: MRR, ingresos y distribución de cartera devuelven **exactamente** las cifras anotadas en T004. **Si esto falla, da igual que los nueve informes funcionen** (SC-009)

### La pertenencia, con todos los usuarios

- [X] T010 Crear `dim_usuario_organizacion` en `dags/lib/ddl.py` según `data-model.md` §3.4. ⚠️ **Sin nombre, correo, identificación, teléfono, género ni fecha de nacimiento**
- [X] T011 ⚠️ Implementar `dags/lib/dimensiones/dim_usuario_organizacion.py` cargando **los 21 usuarios, no solo los 2 con pertenencia declarada**, con `tiene_pertenencia = 0` en los demás. Cargar solo los declarados haría **imposible calcular la cobertura**, que es justo lo que los informes deben declarar
- [X] T012 ⚠️ En `dags/lib/dimensiones/dim_usuario_organizacion.py`, tomar la pertenencia **solo de la relación explícita usuario ↔ cliente**, **nunca** del administrador del cliente ni combinando ambas: un administrador y un miembro son cosas distintas (FR-037, FR-040)

### El hecho de sesión

- [X] T013 Crear `hecho_sesion` en `dags/lib/ddl.py` según `data-model.md` §3.3. ⚠️ **Sin `token`**: es una credencial viva, y llevarla a un almacén analítico la expone a cualquier consulta y a cualquier copia de seguridad
- [X] T014 ⚠️ Implementar `dags/lib/hechos/hecho_sesion.py` con **`duracion_segundos` ausente cuando no hay cierre**. Nunca cero —hundiría la media— y nunca «hasta ahora» —inventaría una duración para sesiones que quizá cerraron sin registrarse—
- [X] T015 Implementar `desenlace` con **tres valores**: cerrada, abierta y **expulsada**. Una sesión expulsada terminó, pero no porque el usuario se fuera
- [X] T016 Implementar el flujo en `dags/lib/hecho_sesion_tasks.py` y `dags/etl/dag_hecho_sesion.py`, con sensor sobre el flujo de dimensiones
- [X] T017 Añadir `dim_usuario_organizacion` al flujo existente de `dags/lib/dimensiones_tasks.py`, y registrar el DAG y las tablas en `dags/tests/test_dag_integrity.py` y `dags/tests/test_sin_datos_sensibles.py`

### El servicio, las vistas y la autoridad limitada

- [X] T018 Implementar `backend/apps/informes_tacticos/services/cuentas_compuestos_service.py` sobre el `modelo_repository` existente
- [X] T019 Implementar `backend/apps/informes_tacticos/views/cuentas_compuestos_views.py` reutilizando `views/base.py` y `envelope.py`
- [X] T020 ⚠️ Aplicar los permisos en `backend/apps/informes_tacticos/permissions.py`: el **Administrador** cubre los nueve informes; el **Director Tecnológico**, **solo los dos de acceso (OT18)**. Su autoridad aquí **no alcanza** al ciclo de vida ni a la incorporación (FR-030)
- [X] T021 Implementar los campos `nota_cobertura`, `nota_catalogo` y `nota_solape` de la meta en `backend/apps/informes_tacticos/envelope.py`

### Las pruebas de las reglas que no avisan

- [X] T022 ⚠️ **Prueba de exclusión de dato sensible** en `dags/tests/test_cuentas_sin_sensibles.py`: `hecho_sesion` **sin columna de token**; ninguna dimensión con nombre, correo, identificación, teléfono, **género ni fecha de nacimiento** (SC-008)
- [X] T023 [P] Prueba de la regla de versión final en `dags/tests/test_catalogo_cuentas.py`: obligatoria en las seis dimensiones, **prohibida** en los dos hechos
- [X] T024 [P] Prueba de que **ninguna consulta nombra un campo de identidad**, en `dags/tests/test_catalogo_cuentas.py`. La única excepción admitida es `idusuario` en el informe de roles
- [X] T025 [P] Prueba de la autoridad limitada en `backend/apps/informes_tacticos/tests/api/test_permisos_cuentas.py`: el Director Tecnológico **no accede** a churn, antigüedad, ocupación, riesgo, onboarding ni aprobación

**Checkpoint**: sustrato listo — las tres user stories pueden abordarse en cualquier orden.

---

## Phase 3: User Story 1 — El ciclo de vida de la cuenta (Priority: P1) 🎯 MVP

**Goal**: los cuatro informes de OT17, con el indicador BSC de **churn**.

**Independent Test**: dar de baja un cliente dado de alta en enero y comprobar que aparece en la
cohorte de enero.

**Criterio medible (ISO 25010 — Idoneidad funcional)**: la ocupación de plan declara **qué porcentaje
de usuarios tiene organización conocida** — hoy el 9,5 % (SC-011).

### Las consultas

- [X] T026 [US1] ⚠️ Escribir `dags/lib/consultas/cuentas/ot17_churn_por_cohorte.sql` agrupando por **cohorte de alta**. Por mes de baja mediría cuándo se fue la gente, y mezclaría cohortes de tamaños muy distintos en el mismo número
- [X] T027 [P] [US1] Escribir `dags/lib/consultas/cuentas/ot17_antiguedad_media.sql`, midiendo desde el alta hasta **la baja o el momento actual**, y reutilizando `dim_plan` de Suscripciones
- [X] T028 [US1] ⚠️ Escribir `dags/lib/consultas/cuentas/ot17_usuarios_vs_tope.sql` devolviendo **usuarios, tope y `pct_cobertura_pertenencia`**. Un cliente **sin plan** devuelve ocupación **ausente**, nunca 0 %
- [X] T029 [US1] ⚠️ Escribir `dags/lib/consultas/cuentas/ot17_cuentas_en_riesgo.sql` distinguiendo `sin_actividad_conocida` de un número alto de días: **nunca haber entrado y haber entrado hoy son lo contrario**

### Los endpoints

- [X] T030 [US1] Exponer los cuatro endpoints de OT17 en `backend/apps/informes_tacticos/views/cuentas_compuestos_views.py` y `backend/apps/informes_tacticos/urls.py`, según `contracts/informes-compuestos-cuentas.openapi.yaml`
- [X] T031 [US1] Devolver `nota_cobertura` en la meta de los dos informes que dependen de la pertenencia (FR-038)

### Pruebas

- [X] T032 [US1] ⚠️ **Prueba de la cohorte** en `dags/tests/test_ot17_churn.py`: un cliente de alta en enero y baja en junio aparece en la **cohorte de enero** (SC-002)
- [X] T033 [US1] ⚠️ **Prueba de la cobertura declarada** en `dags/tests/test_ot17_ocupacion.py`: la respuesta trae `pct_cobertura_pertenencia`, y los usuarios sin pertenencia **no se reparten** entre clientes (SC-011, SC-012)
- [X] T034 [P] [US1] Prueba de que un cliente **sin ninguna sesión** aparece como sin actividad conocida y **no con 0 días**, en `dags/tests/test_ot17_riesgo.py` (SC-003)
- [X] T035 [P] [US1] Prueba de que un cliente **sin plan** devuelve ocupación ausente y no 0 %, en `dags/tests/test_ot17_ocupacion.py` (FR-011)
- [X] T036 [P] [US1] Prueba de que la antigüedad de un cliente activo se mide **hasta hoy**, no hasta una fecha de baja inexistente, en `dags/tests/test_ot17_antiguedad.py`

**Checkpoint**: US1 entregable. Es el MVP: **el churn pasa a ser medible**.

---

## Phase 4: User Story 2 — La incorporación de clientes (Priority: P2)

**Goal**: los tres informes de OT04, con el segundo indicador BSC.

**Independent Test**: el embudo muestra **todas** las etapas del catálogo, incluidas las que nadie ha
completado nunca.

**Criterio medible (ISO 25010 — Idoneidad funcional)**: una etapa sin ningún cliente **aparece** en
el embudo en lugar de omitirse (SC-004).

### Ampliar el modelo

- [X] T037 [US2] Crear `dim_etapa_onboarding` y `hecho_onboarding` en `dags/lib/ddl.py` según `data-model.md` §3.1 y §3.2
- [X] T038 [US2] ⚠️ Implementar `dags/lib/dimensiones/dim_etapa_onboarding.py` con el catálogo **declarado explícitamente** y su `orden`. **No inferirlo de las etapas observadas**: la etapa que nadie ha completado nunca desaparecería del embudo, y es donde está el problema
- [X] T039 [US2] Implementar `dags/lib/hechos/hecho_onboarding.py`. ⚠️ **Solo contiene etapas completadas**, porque es lo único que el origen registra: el abandono **no está aquí**
- [X] T040 [US2] Implementar el flujo en `dags/lib/hecho_onboarding_tasks.py` y `dags/etl/dag_hecho_onboarding.py`, y registrar DAG y tablas en las pruebas de integridad

### Las consultas

- [X] T041 [US2] ⚠️ Escribir `dags/lib/consultas/cuentas/ot04_embudo_abandono.sql` partiendo de **`dim_etapa_onboarding`** y contando **ausencias**. Debe devolver **todas** las etapas del catálogo
- [X] T042 [P] [US2] Escribir `dags/lib/consultas/cuentas/ot04_tiempo_onboarding.sql`, con los clientes **aún en proceso** contados aparte y **fuera de la mediana**
- [X] T043 [P] [US2] Escribir `dags/lib/consultas/cuentas/ot04_tasa_aprobacion.sql`

### Los endpoints

- [X] T044 [US2] Exponer los tres endpoints de OT04 en `backend/apps/informes_tacticos/views/cuentas_compuestos_views.py` y `urls.py`, devolviendo `nota_catalogo` en la meta del embudo

### Pruebas

- [X] T045 [US2] ⚠️ **Prueba de la etapa fantasma** en `dags/tests/test_ot04_embudo.py`: declarar en el catálogo una etapa que **ningún cliente ha completado** y comprobar que **aparece** en el embudo con cero. Si falta, la consulta se calcula sobre lo observado y **mostraría 100 % de finalización describiendo un proceso perfecto** (SC-004)
- [X] T046 [P] [US2] Prueba de que **el orden del embudo respeta el catálogo** en `dags/tests/test_ot04_embudo.py`: un embudo sin orden es un recuento
- [X] T047 [P] [US2] Prueba de que un cliente **aún en proceso no cuenta como cero días** en `dags/tests/test_ot04_tiempo.py` (SC-005)
- [X] T048 [P] [US2] Prueba de que la etapa actual se deriva de **las etapas registradas** y no de la columna nula del origen, en `dags/tests/test_ot04_etapa_actual.py` (FR-016)

**Checkpoint**: US2 entregable. **Con US1, los dos indicadores BSC del departamento son medibles.**

---

## Phase 5: User Story 3 — El control de acceso (Priority: P3)

**Goal**: los dos informes de OT18.

**Independent Test**: sin política declarada, el informe de roles devuelve **vacío** pese a haber
usuarios con dos roles.

**Criterio medible (ISO 25010 — Idoneidad funcional)**: un usuario con dos roles **compatibles** no
aparece (SC-007).

### Ampliar el modelo

- [X] T049 [US3] Crear `dim_rol` y `dim_usuario_rol` en `dags/lib/ddl.py` según `data-model.md` §3.5
- [X] T050 [US3] Implementar `dags/lib/dimensiones/dim_rol.py` y la asignación por usuario, **sin identidad**: solo claves y nombres de rol
- [X] T051 [US3] Añadir ambas al flujo existente de `dags/lib/dimensiones_tasks.py`

### Las consultas

- [X] T052 [US3] ⚠️ Escribir `dags/lib/consultas/cuentas/ot18_concurrencia_sesiones.sql` midiendo **solape de intervalos**, no conteo de inicios, y devolviendo `sesiones_sin_cierre` junto a la duración mediana
- [X] T053 [US3] Implementar en la misma consulta el reparto de una sesión que **cruza la medianoche** entre ambas franjas, y devolver `nota_solape`: la suma de franjas será **mayor** que el total de sesiones
- [X] T054 [US3] ⚠️ Escribir `dags/lib/consultas/cuentas/ot18_roles_incompatibles.sql` con `pares_incompatibles` **vacío por defecto**, devolviendo `idusuario` y **ambos roles nombrados** — nunca el nombre de la persona

### Los endpoints

- [X] T055 [US3] Exponer los dos endpoints de OT18 en `backend/apps/informes_tacticos/views/cuentas_compuestos_views.py` y `urls.py`, accesibles también por el **Director Tecnológico**

### Pruebas

- [X] T056 [US3] ⚠️ **Prueba de que la concurrencia no es un conteo** en `dags/tests/test_ot18_concurrencia.py`: diez sesiones de un minuto repartidas por la hora y diez simultáneas dan **el mismo número de inicios** y **concurrencia máxima muy distinta**
- [X] T057 [US3] ⚠️ **Prueba de que la duración declara cuánto midió** en el mismo fichero: `sesiones_sin_cierre` presente. Con 513 inicios y 195 cierres, una mediana sin ese contexto describe **el 27 %** como si fuera el total (SC-006)
- [X] T058 [US3] ⚠️ **Prueba de la política vacía** en `dags/tests/test_ot18_roles.py`: sin `pares_incompatibles`, el informe devuelve **cero filas** pese a haber usuarios con dos roles activos. Marcarlos denunciaría **el mecanismo previsto del sistema** (SC-007)
- [X] T059 [P] [US3] Prueba de que con un par declarado **solo aparece esa combinación**, con `idusuario` y ambos roles, en el mismo fichero (FR-021, FR-024)
- [X] T060 [P] [US3] Prueba de que una sesión que cruza la medianoche **cuenta en ambas franjas** y la respuesta lo declara, en `dags/tests/test_ot18_franjas.py` (FR-019)

**Checkpoint**: los 9 informes disponibles.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T061 [P] Prueba de que **un período vacío devuelve cero filas** y no una fila de ceros, en `dags/tests/test_cuentas_periodo_vacio.py`
- [X] T062 [P] Prueba de que **todo porcentaje viene con su denominador** en `dags/tests/test_cuentas_denominador.py`
- [X] T063 ⚠️ **Prueba de crecimiento aditivo** en `dags/tests/test_crecimiento_cuentas.py`: tras la ampliación y las cuatro tablas nuevas, **las cifras de los cinco departamentos anteriores no cambian** (SC-010)
- [X] T064 Ejecutar `cd backend && python -m pytest -q` y verificar que ninguna suite existente se movió
- [X] T065 Recorrer `quickstart.md` de principio a fin, **empezando por §2.1** (la ampliación no rompió a Suscripciones) y siguiendo con §2.2 (la etapa fantasma) y §2.4 (concurrencia)
- [X] T066 Anotar en `decisiones-pendientes.md` que **solo el 9,5 % de los usuarios tiene pertenencia a organización declarada**, y que **el sistema no registra abandonos de onboarding** — ambas son carencias del sistema operativo que limitan lo que estos informes pueden decir
- [X] T067 Documentar en `.specify/docs/changelog.md`, actualizar el estado de los 9 informes en `informestacticos/TSI-Informes-Tacticos-Requeridos-por-OT.md`, y **dejar constancia de que `dim_cliente` quedó ampliada por su departamento dueño**, cerrando el ciclo de la dimensión conformada

---

## Dependencies

```text
Emergencias, fases 1 y 2 (plomería)          ← DEPENDENCIA EXTERNA
Suscripciones, fase 2 (dim_cliente, dim_plan) ← DEPENDENCIA EXTERNA
    ↓
Phase 1 (Setup, con las cifras de referencia anotadas)
    ↓
Phase 2 (Foundational: ampliación + pertenencia + sesiones) ← BLOQUEANTE
    ↓
    ├─→ Phase 3 (US1, P1) ── independiente
    ├─→ Phase 4 (US2, P2) ── independiente
    └─→ Phase 5 (US3, P3) ── independiente
            ↓
    Phase 6 (Polish)
```

**T004 va en la fase 1 y no en la 6** a propósito: las cifras de referencia de Suscripciones hay que
anotarlas **antes** de tocar su dimensión. Después ya no se sabría cuáles eran.

**`hecho_sesion` está en la fase 2** porque lo usan US1 —cuentas en riesgo— y US3 —concurrencia—, y
`dim_usuario_organizacion` porque el hecho de sesión la necesita para marcar la pertenencia.

**Dentro de la fase 2**: T006–T009 (la ampliación) primero; T010–T012 después; T013–T017 dependen de
T010; el bloque de servicio (T018–T021) es independiente.

---

## Parallel Execution Examples

**Fase 3 — las cuatro pruebas de OT17:**

```text
T034 cliente sin ninguna sesión
T035 cliente sin plan
T036 antigüedad hasta hoy
```

**Fase 4 — dos consultas de OT04:**

```text
T042 ot04_tiempo_onboarding.sql
T043 ot04_tasa_aprobacion.sql
```

---

## Implementation Strategy

### MVP — US1

Cuatro informes y **el churn por cohorte, que hoy no tiene fuente**. Es también donde se ve por
primera vez la cobertura declarada: la ocupación de plan dice cuánto sabe antes de decir cuánto mide.

### Entrega incremental

1. **Fases 1–2** — la ampliación comprobada, la pertenencia completa y las sesiones sin token.
2. **Fase 3 (US1)** — **MVP**, un BSC.
3. **Fase 4 (US2)** — el segundo BSC y el embudo que mide por ausencia.
4. **Fase 5 (US3)** — el acceso, con la política en manos del negocio.
5. **Fase 6** — cierre.

### Cinco riesgos a vigilar

**T009 es la prueba más importante del módulo, y va antes que cualquier informe.** Si la ampliación
mueve las cifras de Suscripciones, hay **dos verdades sobre el mismo cliente** y el modelo compartido
no funciona. Nada de lo demás importa hasta que esa prueba pase.

**T045 defiende el informe contra su propia trampa.** Un embudo calculado sobre lo observado muestra
**100 % de finalización** y describe un proceso perfecto — ocultando justo la etapa donde todos
abandonan.

**T057 evita describir el 27 % como si fuera el total.** La mayoría de las sesiones no tiene cierre,
y una mediana sin ese contexto habla solo de las que terminaron bien.

**T058 protege el funcionamiento normal del sistema.** El multi-rol es el mecanismo previsto; un
informe que lo marque estaría denunciando la arquitectura.

**T011 parece una minucia y no lo es.** Cargar solo los usuarios con pertenencia declarada haría
**imposible calcular la cobertura**, y sin cobertura la ocupación de plan se lee como un dato firme
cuando hoy describe al 9,5 % de los usuarios.

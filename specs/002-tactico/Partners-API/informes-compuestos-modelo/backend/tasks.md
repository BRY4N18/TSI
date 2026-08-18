# Tasks: Informes Compuestos de Partners y API sobre el Modelo Analítico

**Input**: Design documents from `specs/002-tactico/Partners-API/informes-compuestos-modelo/backend/`

**Prerequisites**: [`plan.md`](plan.md), [`spec.md`](spec.md), [`research.md`](research.md), [`data-model.md`](data-model.md), [`contracts/`](contracts/)

**Tests**: **incluidos y obligatorios.** Este módulo tiene cuatro formas de equivocarse que **no
fallan**: cargar la fuente preagregada, leer una p95 sobre 18 llamadas como si fuera estable, sumar
429 con 5xx, y dejar entrar el año 9999 en un cálculo de fechas. Las cuatro devuelven números.

**Organization**: agrupadas por user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: puede ejecutarse en paralelo (ficheros distintos, sin dependencias pendientes)
- **[Story]**: US1, US2, US3 según `spec.md`
- Cada tarea lleva su ruta exacta

---

## ⚠️ Lo que distingue a este módulo

**Es el primero que consume tablas de otros dos módulos compuestos**: `dim_cliente` y `hecho_factura`
de Suscripciones, `hecho_accidente` de Emergencias. **No se recrean** — y eso añade un tercer
prerrequisito que no existía en la serie.

**Cierra la dependencia que Suscripciones dejó abierta**: aquí se construye el hecho de llamadas API
del que aquel módulo se abstuvo para no decidir por este departamento.

**Y entrega la p95 que hoy nadie puede calcular**, porque la métrica actual agrega antes de guardar.

**⚠️ Depende de las fases 1 y 2 de Emergencias** y de la **fase 2 de Suscripciones**.

---

## Phase 1: Setup

- [X] T001 Verificar que el modelo analítico está cargado, ejecutando `docker exec -w /opt/airflow tactico-airflow-scheduler python -m pytest dags/tests -q`
- [X] T002 Verificar que **las fases 1 y 2 de Emergencias están implementadas**: existen `dags/lib/consultas/__init__.py` y `backend/core/repositories/informes_tacticos/modelo_repository.py`
- [X] T003 ⚠️ Verificar que **`dim_cliente` y `hecho_factura` están cargados por Suscripciones**, consultando `SELECT count() FROM dim_cliente FINAL` y `SELECT count() FROM hecho_factura`. Dos informes de este módulo los usan y **no los recrean**
- [X] T004 Crear `dags/lib/consultas/partners/` con un `README.md` que remita a `contracts/catalogo-consultas.md` y recoja **las cuatro reglas propias**: una sola fuente de consumo, declarar muestras, no sumar clases de error, y sin secretos ni IP

---

## Phase 2: Foundational — el hecho de llamadas y el partner

**Purpose**: `hecho_llamada_api` lo necesitan **las tres** historias y `dim_partner` **dos**, así que
ambos viven aquí.

**⚠️ CRÍTICO**: ninguna user story puede empezar hasta que esta fase esté completa.

### El hecho de llamadas — el de mayor crecimiento del modelo

- [X] T005 Crear `hecho_llamada_api` en `dags/lib/ddl.py` según `data-model.md` §2.1, particionado por mes. ⚠️ **Sin `iporigen`**: identifica a un consumidor concreto y ningún informe la necesita
- [X] T006 ⚠️ Implementar `dags/lib/hechos/hecho_llamada_api.py` normalizando **`endpoint_path` sin cadena de consulta**. Agrupar por la cadena completa fragmentaría el consumo en tantos grupos como combinaciones de parámetros haya, y **ningún endpoint parecería usado**
- [X] T007 ⚠️ Implementar **`clase_resultado`** en el mismo módulo: `429` es límite de cupo —contrato—, `403` es autorización y `5xx` es fallo del servicio. **Tres problemas con tres responsables**, que el código HTTP mezcla
- [X] T008 Implementar la derivación de **`servicio` y `version_contrato` desde el path**, marcando `version_es_derivada = 1`. El log no registra la versión (research D5)
- [X] T009 Implementar el flujo en `dags/lib/hecho_llamada_api_tasks.py` y `dags/etl/dag_hecho_llamada_api.py`, con sensor sobre el flujo de dimensiones
- [X] T010 ⚠️ **NO cargar `Fact_APIIntegracion`.** Añadir un comentario explícito en `dags/lib/hechos/hecho_llamada_api.py` explicando por qué: difiere del detalle en un orden de magnitud y haría imposibles tres informes (research D1)

### La dimensión de partner

- [X] T011 Crear `dim_partner` en `dags/lib/ddl.py` según `data-model.md` §2.3. ⚠️ **Sin contacto técnico**: dato personal
- [X] T012 Implementar `dags/lib/dimensiones/dim_partner.py`, normalizando **el texto `'null'` de `plan_api` a ausente** — es uno de los defectos ya documentados del sistema (decisión #15)
- [X] T013 Añadir `dim_partner` al flujo existente en `dags/lib/dimensiones_tasks.py` y su fila desconocida en `dags/lib/dimensiones/desconocido.py`
- [X] T014 Registrar el DAG en `dags/tests/test_dag_integrity.py` y las dos tablas en `dags/tests/test_sin_datos_sensibles.py`

### El servicio, las vistas y los permisos

- [X] T015 Implementar `backend/apps/informes_tacticos/services/partners_compuestos_service.py` sobre el `modelo_repository` existente
- [X] T016 Implementar `backend/apps/informes_tacticos/views/partners_compuestos_views.py` reutilizando `views/base.py` y `envelope.py`
- [X] T017 Aplicar los permisos en `backend/apps/informes_tacticos/permissions.py` con `AUTORIDAD_PARTNERS_API` de `backend/core/auth/roles_tacticos.py`. ⚠️ **Un rol de partner NO accede**: son cifras comparadas de todos los partners (FR-034)
- [X] T018 Implementar el campo `nota_muestras` de la meta en `backend/apps/informes_tacticos/envelope.py`, para las medidas calculadas sobre pocas llamadas

### Las pruebas de las reglas que no avisan

- [X] T019 ⚠️ **Prueba de que hay una sola fuente de consumo** en `dags/tests/test_partners_fuente_unica.py`: **no existe en el modelo ninguna tabla de consumo preagregado**. Si aparece, el departamento vuelve a tener dos verdades, ahora con apariencia de validadas (SC-012)
- [X] T020 ⚠️ **Prueba de exclusión de dato sensible** en `dags/tests/test_partners_sin_sensibles.py`: `hecho_llamada_api` **sin columna de IP**; las dimensiones sin hash de secreto ni contacto técnico; y ninguna consulta nombra al ejecutor de un cambio (SC-008)
- [X] T021 [P] Prueba de la regla de versión final en `dags/tests/test_catalogo_partners.py`: obligatoria en las dimensiones, **prohibida** en los dos hechos de transacción
- [X] T022 [P] Prueba de que **ninguna consulta suma clases de resultado distintas** en `dags/tests/test_catalogo_partners.py`: 429, 403 y 5xx van separadas
- [X] T023 [P] Prueba de que un rol de **partner no accede** a ningún endpoint del módulo, en `backend/apps/informes_tacticos/tests/api/test_permisos_partners.py`

**Checkpoint**: sustrato listo — las tres user stories pueden abordarse en cualquier orden.

---

## Phase 3: User Story 1 — El consumo de la API (Priority: P1) 🎯 MVP

**Goal**: los siete informes de OT09, con **dos indicadores BSC** y la p95 que hoy no se puede
calcular.

**Independent Test**: pedir la latencia de un endpoint y comprobar que devuelve **p95, media y número
de muestras**, y que la p95 es mayor o igual que la media.

**Criterio medible (ISO 25010 — Idoneidad funcional)**: la latencia p95 existe y declara sus
muestras; hoy solo hay media (SC-002, SC-011).

### Las consultas

- [X] T024 [US1] ⚠️ Escribir `dags/lib/consultas/partners/ot09_latencia_p95.sql`: devuelve **p95 y media juntas**, `muestras`, y `percentil_fiable = 0` por debajo del mínimo **sin ocultar la fila**. Filtrarla dejaría el informe vacío con el tráfico actual
- [X] T025 [US1] Escribir `dags/lib/consultas/partners/ot09_metricas_consumo.sql`, incluyendo p95 además de media. ⚠️ **Sus cifras diferirán del endpoint ya construido**, que da solo media: la diferencia **es el arreglo**
- [X] T026 [P] [US1] Escribir `dags/lib/consultas/partners/ot09_consumo_por_endpoint.sql`, agrupando por el path **normalizado sin cadena de consulta**
- [X] T027 [P] [US1] Escribir `dags/lib/consultas/partners/ot09_taxonomia_errores.sql`, agrupando por **clase de resultado antes que por código**
- [X] T028 [P] [US1] Escribir `dags/lib/consultas/partners/ot09_reporte_mensual.sql` con `mes` natural
- [X] T029 [P] [US1] Escribir `dags/lib/consultas/partners/ot09_comparativa_partners.sql`, describiendo el patrón con **volumen, tasa de error y latencia** — nunca con IP
- [X] T030 [US1] Escribir `dags/lib/consultas/partners/ot09_participacion_ingresos_api.sql`, **reutilizando `hecho_factura` de Suscripciones** y separando excedente de ingreso base

### Los endpoints

- [X] T031 [US1] Exponer los siete endpoints de OT09 en `backend/apps/informes_tacticos/views/partners_compuestos_views.py` y `backend/apps/informes_tacticos/urls.py`, según `contracts/informes-compuestos-partners.openapi.yaml`
- [X] T032 [US1] **Dejar intactos** los dos endpoints ya construidos en `backend/apps/partners/views/`. Apagarlos dejaría el tablero de consumo sin fuente, y su retirada depende de la decisión pendiente #20

### Pruebas

- [X] T033 [US1] ⚠️ **Prueba de la p95** en `dags/tests/test_ot09_latencia.py`, con tres comprobaciones: devuelve p95 **y** media; la p95 es mayor o igual; y `muestras` viene siempre. Una p95 sobre 18 llamadas **es un número, no un indicador**, y quien la lea debe poder saberlo (SC-002, SC-011)
- [X] T034 [US1] ⚠️ **Prueba de que las clases de error no se suman** en `dags/tests/test_ot09_errores.py`: con 3 llamadas 429, 2 con 403 y 1 con 500, las tres clases aparecen **por separado**. Sumarlas diría «hay 6 errores» sin decir que **la mitad son de contrato y ninguno del servicio** (SC-005)
- [X] T035 [P] [US1] Prueba de que **el endpoint se agrupa sin cadena de consulta** en `dags/tests/test_ot09_endpoint.py`: dos llamadas al mismo path con parámetros distintos cuentan como **un endpoint**, no dos
- [X] T036 [P] [US1] Prueba de que **un partner sin llamadas aparece con cero** en `dags/tests/test_ot09_partner_sin_trafico.py`, no omitido (SC-006)
- [X] T037 [P] [US1] Prueba de que **ningún informe de OT09 devuelve IP de origen** en `dags/tests/test_ot09_sin_ip.py`, ni con la autoridad departamental

**Checkpoint**: US1 entregable. Es el MVP: **la p95 pasa a ser calculable**.

---

## Phase 4: User Story 2 — La incorporación de partners (Priority: P2)

**Goal**: los cuatro informes de OT08, con un indicador BSC.

**Independent Test**: una credencial revocada y otra caducada aparecen con **motivos distintos**,
pese a compartir estado en el sistema operativo.

**Criterio medible (ISO 25010 — Corrección funcional)**: los cuatro motivos de inactividad se
distinguen (SC-003), y una credencial que nunca expira **no aparece** entre las próximas a vencer
(SC-004).

### Ampliar el modelo

- [X] T038 [US2] Crear `dim_credencial_api` y `dim_version_contrato` en `dags/lib/ddl.py` según `data-model.md` §2.4 y §2.5. ⚠️ **Sin `client_secret_hash`**: es un secreto aunque esté cifrado
- [X] T039 [US2] ⚠️ Implementar `dags/lib/dimensiones/dim_credencial_api.py` con **`motivo_inactividad` derivado de la bitácora**: revocada, cascada, expirada y suspensión manual son **el mismo `activo = false`** en el origen (research D3)
- [X] T040 [US2] ⚠️ Implementar **`nunca_expira`** y traducir el centinela del **año 9999** a `fecha_expiracion` ausente. Un promedio que lo incluyera daría **2,9 millones de días**
- [X] T041 [US2] ⚠️ Implementar `dags/lib/dimensiones/dim_version_contrato.py` con **clave (servicio, versión)** —dos servicios comparten `'v1'`— y traduciendo el centinela de **época cero** a `fecha_retiro` ausente. Una versión «retirada en 1970» **encabezaría** cualquier informe de retiradas
- [X] T042 [US2] Crear `hecho_cambio_acceso` en `dags/lib/ddl.py` según `data-model.md` §2.2. ⚠️ **Sin `ejecutado_por`**: identidad de persona
- [X] T043 [US2] ⚠️ Implementar `dags/lib/hechos/hecho_cambio_acceso.py` con **`es_cambio_efectivo`**: la bitácora registra eventos con `Activo → Activo` y duplicados a milisegundos, ya documentados al especificar Red Operativa
- [X] T044 [US2] Implementar el flujo en `dags/lib/hecho_cambio_acceso_tasks.py` y `dags/etl/dag_hecho_cambio_acceso.py`, y añadir las dos dimensiones al flujo de `dags/lib/dimensiones_tasks.py`
- [X] T045 [US2] Registrar el DAG y las tres tablas en `dags/tests/test_dag_integrity.py` y `dags/tests/test_sin_datos_sensibles.py`

### Las consultas

- [X] T046 [US2] ⚠️ Escribir `dags/lib/consultas/partners/ot08_motivo_credencial_inactiva.sql`, distinguiendo los **cuatro motivos**
- [X] T047 [P] [US2] Escribir `dags/lib/consultas/partners/ot08_tiempo_incorporacion.sql`, con los partners **aún en proceso** contados aparte y **fuera de la media**
- [X] T048 [US2] ⚠️ Escribir `dags/lib/consultas/partners/ot08_adopcion_versiones.sql` agrupando por **(servicio, versión)** y devolviendo `version_es_derivada`
- [X] T049 [P] [US2] Escribir `dags/lib/consultas/partners/ot08_tasa_rechazo_produccion.sql`, agrupando **por motivo, nunca por persona**

### Los endpoints

- [X] T050 [US2] Exponer los cuatro endpoints de OT08 en `backend/apps/informes_tacticos/views/partners_compuestos_views.py` y `urls.py`

### Pruebas

- [X] T051 [US2] ⚠️ **Prueba de los cuatro motivos** en `dags/tests/test_ot08_motivo_credencial.py`: una revocada y una caducada aparecen **en grupos distintos**. Si el modelo solo muestra uno, el motivo no se derivó de la bitácora (SC-003)
- [X] T052 [US2] ⚠️ **Prueba de los dos centinelas** en `dags/tests/test_ot08_centinelas.py`: la credencial del año 9999 **no aparece** entre las próximas a vencer y **no entra** en ningún promedio; la versión no retirada tiene `fecha_retiro` ausente (SC-004)
- [X] T053 [P] [US2] Prueba de que un **partner en proceso no cuenta como cero días** en `dags/tests/test_ot08_incorporacion.py` (SC-009)
- [X] T054 [P] [US2] Prueba de que la adopción agrupa por **(servicio, versión)** en `dags/tests/test_ot08_adopcion.py`: dos servicios que comparten `'v1'` producen **dos filas**, no una
- [X] T055 [P] [US2] Prueba de que **la bitácora con eventos no efectivos no infla** la tasa de rechazo, en `dags/tests/test_ot08_bitacora.py`

**Checkpoint**: US2 entregable. Los cuatro motivos que el sistema operativo confunde quedan separados.

---

## Phase 5: User Story 3 — La entrega contratada (Priority: P3)

**Goal**: los dos informes en alcance de OT10, con un indicador BSC de meta explícita.

**Independent Test**: el porcentaje de clientes con integración activa **puede ser menor que 100 %**.

**Criterio medible (ISO 25010 — Idoneidad funcional)**: el denominador son todos los clientes
(SC-007).

> **No necesita ninguna tabla nueva.** Reutiliza `hecho_llamada_api` de la fase 2, y `dim_cliente` y
> `hecho_accidente` de otros módulos. Es la historia más barata del módulo.

### Las consultas

- [X] T056 [US3] ⚠️ Escribir `dags/lib/consultas/partners/ot10_clientes_integracion_activa.sql` con **todos los clientes como denominador**. Contando solo los que ya tienen partner, el indicador daría **siempre 100 %** y parecería cumplido
- [X] T057 [P] [US3] Escribir `dags/lib/consultas/partners/ot10_volumen_expedientes.sql`, separando **portal y API** como canales distintos y reutilizando `hecho_accidente`

### Los endpoints

- [X] T058 [US3] Exponer los dos endpoints de OT10 en `backend/apps/informes_tacticos/views/partners_compuestos_views.py` y `urls.py`

### Pruebas

- [X] T059 [US3] ⚠️ **Prueba del denominador** en `dags/tests/test_ot10_integracion_activa.py`: con clientes sin partner en el sistema, el porcentaje es **menor que 100 %** (SC-007)
- [X] T060 [P] [US3] Prueba de que **los dos canales se separan** en `dags/tests/test_ot10_expedientes.py`
- [X] T061 [US3] Prueba de que **no existe ninguna consulta de alcance geográfico** en `dags/tests/test_catalogo_partners.py`: ninguna nombra zonas ni interpreta parámetros del endpoint. El informe está fuera de alcance y **no debe reaparecer por inferencia** (FR-025)

**Checkpoint**: los 13 informes en alcance disponibles.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T062 [P] Prueba de que **toda medida estadística declara sus muestras** en `dags/tests/test_partners_muestras.py` (SC-011)
- [X] T063 [P] Prueba de que **un período sin llamadas devuelve cero filas** en `dags/tests/test_partners_periodo_vacio.py`
- [X] T064 ⚠️ **Prueba de crecimiento aditivo** en `dags/tests/test_crecimiento_partners.py`: tras añadir tres dimensiones y dos hechos, **las cifras de los cuatro departamentos anteriores no cambian** (SC-010)
- [X] T065 Ejecutar `cd backend && python -m pytest -q` y verificar que **los dos endpoints ya construidos siguen intactos** y ninguna suite existente se movió
- [X] T066 Recorrer `quickstart.md` de principio a fin, con especial atención a §2.1 (fuente única), §2.2 (p95 con muestras) y §2.4 (los centinelas)
- [X] T067 Anotar en `decisiones-pendientes.md` que **el log no registra la versión del contrato ni la zona consultada**, y que ambas son carencias del sistema operativo — la primera se sortea derivando del path, la segunda deja un informe fuera de alcance
- [X] T068 Documentar en `.specify/docs/changelog.md`, actualizar el estado de los informes en `informestacticos/TSI-Informes-Tacticos-Requeridos-por-OT.md`, y **dejar constancia de que la latencia del modelo diferirá de la del endpoint actual a propósito**

---

## Dependencies

```text
Emergencias, fases 1 y 2 (plomería)     ← DEPENDENCIA EXTERNA
Suscripciones, fase 2 (dim_cliente, hecho_factura) ← DEPENDENCIA EXTERNA NUEVA
    ↓
Phase 1 (Setup)
    ↓
Phase 2 (Foundational: hecho_llamada_api + dim_partner + servicio + reglas) ← BLOQUEANTE
    ↓
    ├─→ Phase 3 (US1, P1) ── independiente
    ├─→ Phase 4 (US2, P2) ── independiente
    └─→ Phase 5 (US3, P3) ── independiente, sin tablas nuevas
            ↓
    Phase 6 (Polish)
```

**⚠️ Es el primer módulo con dos dependencias externas.** Además de la plomería de Emergencias,
necesita que Suscripciones haya cargado `dim_cliente` y `hecho_factura`. T003 lo comprueba antes de
empezar, porque descubrirlo a mitad de la fase 3 costaría rehacer el informe de participación de
ingresos.

**`hecho_llamada_api` está en la fase 2 porque las tres historias lo usan** — consumo en US1,
adopción de versiones en US2, integración activa en US3.

---

## Parallel Execution Examples

**Fase 3 — cuatro consultas de OT09 a la vez:**

```text
T026 ot09_consumo_por_endpoint.sql
T027 ot09_taxonomia_errores.sql
T028 ot09_reporte_mensual.sql
T029 ot09_comparativa_partners.sql
```

**Fase 4 — las pruebas tras los endpoints:**

```text
T053 partner en proceso no cuenta como cero
T054 adopción por (servicio, versión)
T055 bitácora con eventos no efectivos
```

---

## Implementation Strategy

### MVP — US1

Siete informes y **la latencia p95, que hoy es imposible de calcular**: la métrica actual agrega antes
de guardar, y un percentil necesita las observaciones.

### Entrega incremental

1. **Fases 1–2** — el hecho de llamadas, con una sola fuente y sin IP.
2. **Fase 3 (US1)** — **MVP**, dos BSC.
3. **Fase 4 (US2)** — los cuatro motivos que el origen confunde, y un BSC más.
4. **Fase 5 (US3)** — el último BSC, sin tablas nuevas.
5. **Fase 6** — cierre.

### Cinco riesgos a vigilar

**T010 y T019 defienden la decisión más importante del módulo.** Basta con cargar la tabla
preagregada «por completitud» para que el departamento vuelva a tener dos verdades — y esta vez
ambas en el almacén analítico, **con apariencia de haber sido validadas**.

**T033 evita que una cifra frágil parezca sólida.** Una p95 sobre 18 llamadas es un número; con dos
endpoints en los datos actuales, podría ser literalmente la segunda llamada más lenta.

**T034 separa tres responsabilidades que el código HTTP mezcla.** Un informe que sume 429 con 5xx
dice «hay errores» sin decir que la mitad son de contrato y ninguno del servicio.

**T052 vigila dos centinelas con efectos opuestos.** El del año 9999 produce un número absurdo que
salta a la vista; el de la época cero produce uno **plausible**, y por eso es más peligroso: una
versión «retirada en 1970» encabeza el informe con toda naturalidad.

**T061 impide que un informe retirado vuelva por la puerta de atrás.** El alcance geográfico está
fuera porque el log no registra la zona; inferirla de los parámetros del endpoint **no distinguiría
«fuera de zona» de «no supe leerlo»**, y una de las dos es una acusación de incumplimiento.

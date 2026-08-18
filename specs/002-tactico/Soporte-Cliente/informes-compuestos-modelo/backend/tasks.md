# Tasks: Informes Compuestos de Soporte al Cliente sobre el Modelo Analítico

**Feature**: `specs/002-tactico/Soporte-Cliente/informes-compuestos-modelo/backend`
**Fecha**: 2026-08-14
**Entrada**: [spec.md](spec.md) · [plan.md](plan.md) · [research.md](research.md) · [data-model.md](data-model.md) · [contracts/](contracts/) · [quickstart.md](quickstart.md)

**Tests**: incluidos. Este módulo mide un **indicador BSC** y trata **historia de SLA**; un error de
signo aquí no rompe nada visiblemente — devuelve una cifra plausible y falsa.

---

## Convenciones

- `[P]` = paralelizable (archivos distintos, sin dependencias pendientes)
- `[US1] [US2] [US3]` = historia de usuario
- Rutas relativas a la raíz del repositorio

---

## Phase 1 · Setup

- [X] T001 Crear el paquete de consultas del módulo en `dags/lib/consultas/soporte/` con su `__init__.py`
- [X] T002 [P] Crear el paquete de pruebas del módulo en `dags/tests/soporte/` con su `__init__.py`
- [X] T003 [P] Registrar la ruta base `soporte/` del módulo en `backend/apps/informes_tacticos/urls.py` sin endpoints todavía

---

## Phase 2 · Foundational *(bloquea todas las historias)*

**Las cinco tablas y el flujo que las carga.** Sin esto ninguna historia tiene de dónde leer.

### DDL

- [X] T004 Añadir `dim_sla_config` a `dags/lib/ddl.py` con `ReplacingMergeTree(version)` y `ORDER BY (idplan, tipo_incidencia, prioridad, valido_desde)` según [data-model.md](data-model.md) §2.1
- [X] T005 Añadir `dim_servicio` y `dim_estado_soporte` a `dags/lib/ddl.py` según §2.4
- [X] T006 Añadir `hecho_ticket` a `dags/lib/ddl.py` como `ReplacingMergeTree(version)` particionado por `toYYYYMM(fecha)`, con hitos y métricas **anulables**, según §2.2
- [X] T007 Añadir `hecho_accion_ticket` a `dags/lib/ddl.py` como `MergeTree()` **sin** `mensaje` ni `es_nota_interna`, según §2.3
- [X] T008 [P] Prueba en `dags/tests/soporte/test_ddl_soporte.py`: las cinco tablas existen, `hecho_accion_ticket` es `MergeTree` y las otras cuatro `ReplacingMergeTree`
- [X] T009 [P] Prueba en `dags/tests/soporte/test_ddl_soporte.py`: **ninguna** de las dos tablas de hechos declara `asunto`, `descripcion`, `mensaje`, `es_nota_interna` ni `nombre_agente` (quickstart §4)

### Dimensiones

- [X] T010 Implementar `dags/lib/dimensiones/dim_sla_config.py` cargando **las vigencias tal como vienen del origen**, ⚠️ **sin** invocar `versionado.py` (research D1)
- [X] T011 [P] Prueba en `dags/tests/soporte/test_dim_sla_config.py`: un plan con dos configuraciones produce **dos filas**, una con `valido_hasta` y `es_vigente = 0`, otra abierta con `es_vigente = 1`
- [X] T012 [P] Prueba en `dags/tests/soporte/test_dim_sla_config.py`: ⚠️ la dimensión **no** declara `inicio_es_real` — su historia es real y marcarla como reconstruida sería la mentira inversa
- [X] T013 [P] Implementar `dags/lib/dimensiones/dim_servicio.py`
- [X] T014 [P] Implementar `dags/lib/dimensiones/dim_estado_soporte.py`
- [X] T015 Registrar las tres dimensiones en el flujo existente de `dags/lib/dimensiones_tasks.py`
- [X] T016 [P] Prueba en `dags/tests/soporte/test_dimensiones_soporte.py`: las tres se cargan y son idempotentes al repetir la ejecución

### Resolución del SLA vigente

- [X] T017 Implementar `dags/lib/hechos/sla_vigente.py` con `sla_vigente_en(idplan, tipo_incidencia, prioridad, instante)` sobre intervalo **semiabierto** `[desde, hasta)`
- [X] T018 [P] Prueba en `dags/tests/soporte/test_sla_vigente.py`: un instante **anterior** al cambio resuelve `86400`; uno posterior, `7200`
- [X] T019 [P] Prueba en `dags/tests/soporte/test_sla_vigente.py`: ⚠️ el **instante exacto del cambio** resuelve la configuración **nueva** — es el caso que el intervalo semiabierto decide
- [X] T020 [P] Prueba en `dags/tests/soporte/test_sla_vigente.py`: una combinación sin configuración devuelve **ausente**, y el motivo `sin_config`, no un límite por defecto

### Hechos

- [X] T021 Implementar `dags/lib/hechos/hecho_ticket.py`: una fila por ticket, hitos en columnas, con `idagente` como **clave** y sin texto alguno
- [X] T022 Traducir en `dags/lib/hechos/hecho_ticket.py` los centinelas `0` de `sla_primera_respuesta`, `sla_resolucion` y `tiempo_solucion` a **ausente** cuando el hito no se alcanzó (research D2)
- [X] T023 Copiar en `dags/lib/hechos/hecho_ticket.py` el `idslaconfig` y los dos límites **vigentes al crearse el ticket**, más `tiene_compromiso` y `motivo_sin_compromiso`
- [X] T024 Calcular `desenlace_sla`, `fue_reabierto` y `reaperturas` en `dags/lib/hechos/hecho_ticket.py`, dejando `desenlace_sla` **ausente** cuando no hubo compromiso
- [X] T025 [P] Implementar `dags/lib/hechos/hecho_accion_ticket.py` con `tipo_accion`, `es_escalado` y `es_escalado_automatico`, ⚠️ **descartando** `mensaje` y `es_nota_interna` en el extract (research D5)
- [X] T026 Implementar `dags/lib/hecho_soporte_tasks.py` cargando los dos hechos en un solo flujo por `DROP PARTITION` + inserción
- [X] T027 Crear el DAG `dags/etl/dag_hecho_soporte.py` encadenando dimensiones → hechos
- [X] T028 [P] Prueba en `dags/tests/soporte/test_hecho_ticket.py`: un ticket abierto tiene `segundos_resolucion` **ausente**, nunca `0`
- [X] T029 [P] Prueba en `dags/tests/soporte/test_hecho_ticket.py`: un ticket creado antes del cambio de SLA conserva `segundos_resolucion_max = 86400` **aunque la configuración vigente sea 7200**
- [X] T030 [P] Prueba en `dags/tests/soporte/test_hecho_ticket.py`: los tres motivos de `motivo_sin_compromiso` se distinguen y ninguno se confunde con `tiene_compromiso = 1`
- [X] T031 [P] Prueba en `dags/tests/soporte/test_hecho_accion_ticket.py`: ⚠️ aplicar `FINAL` a `hecho_accion_ticket` **falla** con `ILLEGAL_FINAL` — es de transacción
- [X] T032 [P] Prueba en `dags/tests/soporte/test_carga_soporte.py`: ejecutar el DAG **dos veces** sobre el mismo día no altera los recuentos (quickstart §6)
- [X] T033 [P] Prueba en `dags/tests/soporte/test_carga_soporte.py`: ⚠️ las fechas sintéticas del escenario caen **dentro de la partición de prueba** y no contaminan las particiones reales
- [X] T034 Actualizar `dags/tests/test_dag_integrity.py` para incluir `dag_hecho_soporte`

### Backend: base compartida

- [X] T035 Crear `backend/apps/informes_tacticos/services/soporte_compuestos_service.py` con el acceso de solo lectura al almacén y el ensamblado de `declaraciones`
- [X] T036 Crear `backend/apps/informes_tacticos/views/soporte_compuestos_views.py` con la validación de rango y granularidad
- [X] T037 Implementar en el servicio la regla **denominador cero → ausente**, compartida por todos los porcentajes (FR-027)
- [X] T038 [P] Prueba en `backend/apps/informes_tacticos/tests/test_soporte_permisos.py`: el **Gerente de Éxito del Cliente** accede; un **cliente** recibe 403; un **agente** ve solo sus tickets (FR-030 a FR-032)
- [X] T039 [P] Prueba en `backend/apps/informes_tacticos/tests/test_soporte_permisos.py`: ⚠️ la exención de la autoridad **no** alcanza al dato sensible — ni el gerente recibe texto de tickets (FR-033)

**Checkpoint**: modelo cargado, SLA versionado resuelto y base HTTP en pie.

---

## Phase 3 · User Story 1 — El cumplimiento (P1) 🎯 MVP

**Meta**: los cuatro informes de OT19, con el **indicador BSC** que hoy no tiene fuente.

**Prueba independiente**: cambiar el SLA de una configuración y comprobar que un ticket anterior
**sigue midiéndose contra el vigente entonces**.

- [X] T040 [P] [US1] Escribir `dags/lib/consultas/soporte/ot19_cumplimiento_sla.sql` según [catalogo-consultas.md](contracts/catalogo-consultas.md) C1, con `nullIf` en ambos denominadores
- [X] T041 [P] [US1] Escribir `dags/lib/consultas/soporte/ot19_cumplimiento_por_plan.sql` (C2), agrupando los tickets sin plan como `'sin plan'` en vez de descartarlos
- [X] T042 [P] [US1] Escribir `dags/lib/consultas/soporte/ot19_rendimiento_agente.sql` (C3), proyectando `idagente` y devolviendo `sin_resolver` junto a la media
- [X] T043 [P] [US1] Escribir `dags/lib/consultas/soporte/ot19_tickets_por_servicio.sql` (C4) con `LEFT JOIN` y `coalesce(..., 'sin servicio')`
- [X] T044 [US1] Implementar los cuatro métodos en `soporte_compuestos_service.py`, devolviendo `pct_sin_compromiso` y `sin_compromiso_por_motivo` **en la misma fila** que `pct_cumplimiento` (FR-012, FR-013)
- [X] T045 [US1] Implementar los endpoints `/cumplimiento-sla`, `/cumplimiento-sla/por-plan`, `/rendimiento-agentes` y `/tickets-por-servicio` en `soporte_compuestos_views.py` conforme a [informes-compuestos-soporte.openapi.yaml](contracts/informes-compuestos-soporte.openapi.yaml)
- [X] T046 [US1] Emitir la declaración `servicio_no_registrado` cuando todos los tickets caen en «sin servicio» (research D7)
- [X] T047 [US1] Emitir la declaración `sla_historico_aplicado` en los informes de cumplimiento
- [X] T048 [P] [US1] Prueba en `backend/apps/informes_tacticos/tests/test_soporte_cumplimiento.py`: un ticket resuelto en 5 h **antes** del cambio sale **cumplido**; medido contra el SLA actual saldría incumplido (escenario 1 de US1)
- [X] T049 [P] [US1] Prueba: un ticket **sin SLA** no cuenta como incumplido y aparece en `sin_compromiso` (escenario 3)
- [X] T050 [P] [US1] Prueba: ⚠️ un período **sin tickets con compromiso** devuelve `pct_cumplimiento` **ausente**, no `0` — cero cumplimiento y cumplimiento indefinido son distintos
- [X] T051 [P] [US1] Prueba: ⚠️ dejar tickets sin clasificar **sube** `pct_cumplimiento` **y** `pct_sin_compromiso` en la misma respuesta — es la comprobación de que el incentivo queda visible
- [X] T052 [P] [US1] Prueba en `test_soporte_cumplimiento.py`: los tres motivos de sin-compromiso se devuelven **separados**, nunca sumados (FR-014)
- [X] T053 [P] [US1] Prueba en `backend/apps/informes_tacticos/tests/test_soporte_agentes.py`: un ticket **reabierto** aparece como reapertura y **no** como resolución exitosa (escenario 4, FR-016)
- [X] T054 [P] [US1] Prueba en `test_soporte_agentes.py`: ⚠️ un agente con 1 ticket resuelto rápido y 20 abiertos **no** encabeza el ranking — `sin_resolver` acompaña a la media
- [X] T055 [P] [US1] Prueba en `test_soporte_agentes.py`: la respuesta contiene `id_agente` y **ningún nombre** (FR-025)
- [X] T056 [P] [US1] Prueba en `backend/apps/informes_tacticos/tests/test_soporte_servicio.py`: con `idservicio` nulo en todos los tickets, la respuesta trae una fila «sin servicio» con su recuento **y** la declaración (escenario 5)

**Checkpoint**: el BSC de SLA es medible por primera vez, con su cobertura al lado.

---

## Phase 4 · User Story 2 — La cola en curso (P2)

**Meta**: los tres informes de OT20 que miran el ahora, incluido el sustituto del tablero actual.

**Prueba independiente**: pedir el tablero con corte temporal y por agente — las dos cosas que el
tablero actual no admite.

- [X] T057 [P] [US2] Escribir `dags/lib/consultas/soporte/ot20_tablero_cola.sql` (C5) con período **opcional** y eje de agrupación parametrizado
- [X] T058 [P] [US2] Escribir `dags/lib/consultas/soporte/ot20_evolucion_incumplimiento.sql` (C6) con `WITH FILL` para los períodos vacíos
- [X] T059 [P] [US2] Escribir `dags/lib/consultas/soporte/ot20_tasa_escalado_automatico.sql` (C7) con `uniqExact` sobre el ticket y ⚠️ **sin `FINAL`** en el hecho de acciones
- [X] T060 [US2] Implementar los tres métodos en `soporte_compuestos_service.py`, devolviendo siempre el `periodo_aplicado`
- [X] T061 [US2] Implementar los endpoints `/tablero-cola`, `/evolucion-incumplimiento` y `/escalado-automatico` en `soporte_compuestos_views.py`
- [X] T062 [US2] Emitir la declaración `periodo_acotado_difiere_del_tablero` cuando se aplica un corte temporal (research D8)
- [X] T063 [P] [US2] Prueba en `backend/apps/informes_tacticos/tests/test_soporte_cola.py`: el tablero **acota por período** y su cifra difiere de la cola completa, con la declaración presente (escenario 1)
- [X] T064 [P] [US2] Prueba en `test_soporte_cola.py`: el tablero **se desglosa por agente**, y los tickets sin agente aparecen agrupados como **sin asignar**, no omitidos (escenario 2, FR-020)
- [X] T065 [P] [US2] Prueba en `backend/apps/informes_tacticos/tests/test_soporte_escalado.py`: escalado automático y humano se devuelven en **columnas distintas** y su suma **no** se publica (escenario 3)
- [X] T066 [P] [US2] Prueba en `test_soporte_escalado.py`: un ticket escalado **tres veces** cuenta como **un** ticket escalado
- [X] T067 [P] [US2] Prueba en `backend/apps/informes_tacticos/tests/test_soporte_evolucion.py`: cada punto de la serie usa el **SLA vigente en su momento** (escenario 4)
- [X] T068 [P] [US2] Prueba en `test_soporte_evolucion.py`: ⚠️ un mes **sin tickets** aparece con cero y **no se omite** — un hueco en la serie se leería como un buen período

**Checkpoint**: el tablero corregido convive con el original, y sus diferencias vienen explicadas.

---

## Phase 5 · User Story 3 — Las tendencias (P3)

**Meta**: los dos informes que permiten actuar antes de incumplir.

**Prueba independiente**: un día con más aperturas que resoluciones produce saldo positivo y
acumulado creciente.

- [X] T069 [P] [US3] Escribir `dags/lib/consultas/soporte/ot20_carga_entrante_vs_resuelta.sql` (C8) con las dos series unidas por día y `WITH FILL`
- [X] T070 [P] [US3] Escribir `dags/lib/consultas/soporte/ot20_reincidencia_clientes.sql` (C9) con eje parametrizado y `HAVING tickets >= minimo`
- [X] T071 [US3] Implementar los dos métodos en `soporte_compuestos_service.py`, calculando el `neto_acumulado`
- [X] T072 [US3] Implementar los endpoints `/carga-entrante-resuelta` y `/reincidencia-clientes` en `soporte_compuestos_views.py`
- [X] T073 [US3] Emitir en `/reincidencia-clientes` la declaración de que el eje **servicio** no está disponible y se usa el tipo de incidencia (research D7, FR-023)
- [X] T074 [P] [US3] Prueba en `backend/apps/informes_tacticos/tests/test_soporte_carga.py`: un día con más aperturas que resoluciones da saldo **positivo** y acumulado creciente (escenario 1)
- [X] T075 [P] [US3] Prueba en `test_soporte_carga.py`: ⚠️ un día **sin actividad** aparece con cero; sin él la línea uniría dos días distantes y la pendiente mentiría (FR-022)
- [X] T076 [P] [US3] Prueba en `backend/apps/informes_tacticos/tests/test_soporte_reincidencia.py`: un cliente con tres tickets aparece con su recuento y la declaración del eje sustituido (escenario 2)
- [X] T077 [P] [US3] Prueba en `test_soporte_reincidencia.py`: la respuesta trae `id_cliente` y `tipo_cliente`, **sin más identidad** (FR-026)

**Checkpoint**: los nueve informes del catálogo entregados.

---

## Phase 6 · Pulido y transversales

- [X] T078 [P] Prueba de contrato en `backend/apps/informes_tacticos/tests/test_soporte_openapi.py`: los nueve endpoints responden con el esquema de `informes-compuestos-soporte.openapi.yaml`
- [X] T079 [P] Prueba transversal en `backend/apps/informes_tacticos/tests/test_soporte_sin_texto.py`: ⚠️ **ninguna** de las nueve respuestas contiene asunto, descripción, mensaje ni nota interna (FR-024)
- [X] T080 [P] Prueba transversal: los nueve endpoints son de **solo lectura** — `POST`, `PUT` y `DELETE` devuelven 405 (FR-029)
- [X] T081 [P] Prueba transversal: `FINAL` está presente en las consultas sobre dimensiones y `hecho_ticket`, y **ausente** en las de `hecho_accion_ticket` (FR-004)
- [X] T082 [P] Prueba transversal: un período sin datos devuelve resultado **vacío explícito** con la declaración `sin_datos_en_periodo`, no un 404 (FR-028)
- [X] T083 Ejecutar `quickstart.md` de principio a fin y anotar las cifras reales obtenidas en sus §3.4 y §3.5
- [X] T084 Registrar el módulo en `.specify/docs/changelog.md`
- [X] T085 Actualizar `informestacticos/TSI-Informes-Tacticos-Requeridos-por-OT.md` marcando los 9 compuestos de Soporte como especificados
- [X] T086 Anotar en `decisiones-pendientes.md` que el tablero de cola actual queda **sustituido pero no retirado**, dependiente de la decisión #20

---

## Dependencias

```text
Setup (T001-T003)
   └─> Foundational (T004-T039)  ⚠️ BLOQUEA TODO
          ├─> US1 · Cumplimiento (T040-T056)   🎯 MVP
          ├─> US2 · Cola (T057-T068)
          └─> US3 · Tendencias (T069-T077)
                 └─> Pulido (T078-T086)
```

**Las tres historias son independientes entre sí** una vez cargado el modelo. Su orden es de valor,
no técnico: el BSC va primero porque no tiene fuente alguna, mientras el tablero **funciona hoy**.

**Dentro de Foundational hay un orden que no se puede alterar:** T017-T020 (resolución del SLA
vigente) debe estar **antes** de T023, porque el hecho copia el límite que esa función resuelve. Si
se implementa después, la tentación es unir con la configuración actual — y eso es exactamente el
defecto que este módulo existe para no cometer.

---

## Paralelismo

| Bloque | Tareas simultáneas |
|---|---|
| DDL y sus pruebas | T008, T009 |
| Dimensiones | T011, T012, T013, T014, T016 |
| SLA vigente | T018, T019, T020 |
| Pruebas de hechos | T028 … T033 |
| SQL de US1 | T040 … T043 |
| Pruebas de US1 | T048 … T056 |
| SQL de US2 | T057 … T059 |
| Pruebas de US2 | T063 … T068 |
| SQL y pruebas de US3 | T069, T070 · T074 … T077 |
| Transversales | T078 … T082 |

---

## Estrategia

**MVP = Setup + Foundational + US1** (T001-T056). Entrega el indicador BSC de cumplimiento de SLA,
que hoy **no tiene ninguna fuente**, medido contra el SLA correcto y con su cobertura declarada.

**Incremento 2 = US2** (T057-T068). Sustituye el tablero de cola con corte temporal y desglose por
agente.

**Incremento 3 = US3 + pulido** (T069-T086).

⚠️ **Con 14 tickets, casi ninguna de estas pruebas fallará por volumen.** Fallarán —si fallan— por
lógica: un cero tomado por un tiempo, un SLA actual aplicado al pasado, un denominador que excluye
sin decirlo. Son los tres errores que devuelven una cifra creíble y equivocada, y por eso las
pruebas los persiguen uno a uno.

---

**Total: 86 tareas** — Setup 3 · Foundational 36 · US1 17 · US2 12 · US3 9 · Pulido 9

# Tasks: Informes Tácticos Simples de Soporte al Cliente (Backend)

**Input**: Design documents from `specs/002-tactico/Soporte-Cliente/informes-tacticos-simples/backend/`

**Prerequisites**: [`plan.md`](plan.md), [`spec.md`](spec.md), [`research.md`](research.md), [`data-model.md`](data-model.md), [`contracts/`](contracts/)

**Tests**: **incluidos y obligatorios.** La constitución fija cobertura ≥80% en servicios, y research
D2, D3, D4 y D5 exigen pruebas concretas sin las cuales cuatro defectos silenciosos pasarían
inadvertidos.

**Organization**: agrupadas por user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: puede ejecutarse en paralelo (ficheros distintos, sin dependencias pendientes)
- **[Story]**: US1, US2 según `spec.md`
- Cada tarea lleva su ruta exacta

---

## ⚠️ Dependencias externas bloqueantes

**Fases 1–2 del piloto**, **fase 2 de Ventas y CRM**, **fase 2 de Suscripciones** y **fase 2 de
Red Operativa** → `core/informes/` completo, con el acotamiento parametrizado.

**Este módulo NO modifica la capa transversal.** Es el primero de la serie que solo la consume, y
esa es su función de verificación: si la parametrización hecha en Red Operativa era correcta, aquí
se usa sin tocarla. **Si en algún momento hace falta modificarla, la parametrización quedó
incompleta** y hay que volver a aquel módulo, no parchear aquí.

---

## Phase 1: Setup

**Purpose**: comprobar dependencias y **sembrar los datos sin los cuales cuatro pruebas centrales no
prueban nada**.

- [X] T001 Verificar que `core/informes/` está completo y que `cd backend && python -m pytest core/informes apps/cuentas_clientes apps/ventas_crm apps/suscripciones apps/red_operativa -q` está verde antes de tocar nada
- [X] T002 **Garantizar que el Cliente y el Partner de demo pertenecen a cuentas distintas** y ambos tienen tickets, en `backend/scripts/` — **si comparten cuenta, la prueba del acotamiento del Partner pasa sin demostrar nada**
- [X] T003 [P] Sembrar en `backend/scripts/` un ticket **`sin compromiso`** (cliente sin suscripción activa que abre un ticket clasificado) y otro **sin clasificar**, requisitos de research D5
- [X] T004 [P] Sembrar en `backend/scripts/` un **escalado manual**, uno **automático por incumplimiento** y un **aviso de plazo próximo**, requisitos de research D2 y D3
- [X] T005 [P] Sembrar en `backend/scripts/` un usuario con rol de **Cliente y Agente de Soporte a la vez**, requisito de FR-012 y SC-003

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: los permisos del módulo. **No hay trabajo transversal**: la capa compartida se consume
tal cual.

**⚠️ CRÍTICO**: ninguna user story puede empezar hasta que esta fase esté completa.

- [X] T006 Añadir las clases de permiso de informes en `backend/apps/soporte_cliente/permissions.py`, **reutilizando la condición de acotamiento ya existente en ese mismo módulo** —la que decide por ausencia de rol de atención— sin reimplementarla ni sustituirla por una comparación de roles (FR-011)
- [X] T007 Configurar el resolutor transversal de acotamiento con el **criterio amplio** para este departamento, sin modificar `backend/core/informes/acotamiento.py` (research D1)
- [X] T008 [P] Pruebas de acotamiento en `backend/apps/soporte_cliente/tests/unit/test_informes_acotamiento.py`: reportador acotado, rol de atención sin acotar, **rol mixto sin acotar**, y rol ajeno con negativa (FR-009 a FR-013)
- [X] T009 Ejecutar `cd backend && python -m pytest core/informes apps/red_operativa apps/suscripciones -q` y verificar que **nada se movió** — este módulo no debe haber tocado la capa compartida

**Checkpoint**: base lista — las dos user stories pueden abordarse en paralelo.

---

## Phase 3: User Story 1 — Consultar los tickets con el acotamiento correcto (Priority: P1) 🎯 MVP

**Goal**: la cola de tickets con filtros combinables, acotamiento por ausencia de rol de atención, y
la situación de compromiso completa incluyendo la que nadie vigila.

**Independent Test**: consultar el listado con cada filtro, con roles de atención y de reporte, sin
que exista el listado de escalados.

**Criterio medible (ISO 25010 — Security / Confidentiality)**: un Partner de integración queda
acotado igual que un Cliente, y **cero** tickets ajenos aparecen en su respuesta (T016).

### Implementación

- [X] T010 [US1] Implementar la consulta de tickets en `backend/core/repositories/soporte/informes_tickets_repository.py` con **columnas enumeradas** —sin la descripción del reporte (research D6)— filtros por estado, prioridad, tipo de incidencia, agente y factura vinculada, cursor compuesto `fechahora|id_reclamo` y acotamiento por `idcliente`
- [X] T011 [US1] Implementar en el mismo repositorio el filtro por **situación del compromiso con sus cuatro valores**, incluido `sin compromiso`. **Prohibido reducirlo a tres o tratar `sin compromiso` como ausencia de dato**: es el único estado en que un ticket queda sin que ningún proceso lo mire (research D5)
- [X] T012 [US1] Implementar `InformesTicketsService` en `backend/apps/soporte_cliente/services/informes_tickets_service.py`, aplicando el acotamiento y resolviendo cuenta, agente, servicio y estado contra sus catálogos
- [X] T013 [US1] Garantizar en el servicio que un ticket **sin clasificar** se devuelve con la situación de compromiso **ausente**, sin atribuirle ninguna (FR-006)
- [X] T014 [US1] Implementar la vista en `backend/apps/soporte_cliente/views/informes_views.py` como listado de **estado actual**, y registrar `/informes/soporte-cliente/tickets` en `backend/apps/soporte_cliente/urls.py`

### Pruebas

- [X] T015 [P] [US1] ⚠️ **Prueba de que el ticket sin compromiso es listable** en `backend/apps/soporte_cliente/tests/repositories/test_informes_tickets_sin_compromiso.py`: el filtro lo devuelve, y el ticket **no** aparece como `en curso` ni se omite. Contrastar con el ticket sin clasificar, cuya situación debe llegar **ausente** (SC-006, research D5)
- [X] T016 [P] [US1] **Prueba de que el Partner queda acotado igual que el Cliente** en `backend/apps/soporte_cliente/tests/api/test_informes_tickets_partner.py`: con ambos en cuentas distintas y con tickets, ninguno ve los del otro. **Si el Partner ve los del Cliente, el acotamiento se decidió por «ser Cliente» en vez de por «no atender tickets»** (SC-002, FR-011)
- [X] T017 [P] [US1] **Prueba del rol mixto** en `backend/apps/soporte_cliente/tests/api/test_informes_tickets_rol_mixto.py`: un usuario que es Cliente **y** Agente obtiene la cola completa y `acotado_a = "todos"` (SC-003, FR-012)
- [X] T018 [P] [US1] Prueba de que pedir otra cuenta responde **403 sin devolver filas** en `backend/apps/soporte_cliente/tests/api/test_informes_tickets_cuenta_ajena.py`
- [X] T019 [P] [US1] Prueba de que la respuesta **no contiene la descripción** del reporte, en `backend/apps/soporte_cliente/tests/api/test_informes_tickets_sin_descripcion.py`, verificando además contra el código que el repositorio enumera columnas (research D6)
- [X] T020 [P] [US1] Pruebas de repositorio en `backend/apps/soporte_cliente/tests/repositories/test_informes_tickets_repository.py`: cada filtro por separado y combinados, orden determinista, cursor compuesto
- [X] T021 [P] [US1] Prueba de contrato en `backend/apps/soporte_cliente/tests/api/test_informes_tickets_contract.py`: envelope conforme al OpenAPI con `acotado_a`, `data: []` con 200 sin filas, `400` con situación inválida nombrando los cuatro válidos, `400` con rango de fechas

**Checkpoint**: US1 entregable por sí sola. Es el MVP.

---

## Phase 4: User Story 2 — Distinguir el escalado automático del humano (Priority: P2)

**Goal**: el listado de escalados con la autoría correcta y sin exponer contenido interno.

**Independent Test**: consultar el listado de forma aislada, con y sin rango, sin que exista el
listado de tickets.

**Criterio medible (ISO 25010 — Functional Correctness)**: el 100 % de los escalados automáticos se
presenta como acción del sistema, y las dos señales de autoría coinciden en todos los registros
(T025).

### Implementación

- [X] T022 [US2] Implementar la consulta de escalados en `backend/core/repositories/soporte/informes_escalados_repository.py` filtrando **exactamente dos** tipos de acción —el escalado manual y el automático por incumplimiento—, con rango opcional y cursor compuesto `fecha_accion|id_historial` (research D2)
- [X] T023 [US2] **No consultar la columna del texto del mensaje** en ese repositorio. Columnas enumeradas: no se lee y luego se descarta, **no se consulta** (research D4)
- [X] T024 [US2] Implementar `InformesEscaladosService` en `backend/apps/soporte_cliente/services/informes_escalados_service.py`, presentando el autor como **acción del sistema cuando está ausente** y con el nombre de la persona cuando existe. **La ausencia de autor es la señal autoritativa**, no el tipo de acción (research D3, FR-022)
- [X] T025 [US2] Implementar la vista en `backend/apps/soporte_cliente/views/informes_views.py` como listado de **hechos del período**, restringida a roles de atención, y registrar `/informes/soporte-cliente/escalados` en `backend/apps/soporte_cliente/urls.py`

### Pruebas

- [X] T026 [P] [US2] ⚠️ **Prueba de coherencia de las dos señales de autoría** en `backend/apps/soporte_cliente/tests/repositories/test_informes_escalados_autoria.py`: recorrer todos los escalados y verificar que **ningún automático tiene autor** y **ningún manual carece de él**. Si se contradicen, el dato está corrupto y decidir por el tipo lo ocultaría (SC-005, research D3)
- [X] T027 [P] [US2] **Prueba de que un aviso de plazo no es un escalado** en `backend/apps/soporte_cliente/tests/repositories/test_informes_escalados_tipos.py`: el ticket que solo recibió un aviso de plazo próximo **no aparece**, ni tampoco los cierres automáticos por vencimiento (research D2)
- [X] T028 [P] [US2] ⛔ **Prueba de que el texto del mensaje no sale** en `backend/apps/soporte_cliente/tests/api/test_informes_escalados_sin_texto.py`: inspecciona la respuesta serializada completa y falla si aparece; verifica además **contra el código** que el repositorio no consulta esa columna — no basta con que el filtro funcione (SC-004, research D4)
- [X] T029 [P] [US2] Prueba de que un reportador —Cliente o Partner— recibe **403** en este listado, en `backend/apps/soporte_cliente/tests/api/test_informes_escalados_permisos.py` (FR-008)
- [X] T030 [P] [US2] Prueba de rango opcional en `backend/apps/soporte_cliente/tests/api/test_informes_escalados_rango.py`: sin rango devuelve el histórico completo; con rango lo acota
- [X] T031 [P] [US2] Prueba de contrato en `backend/apps/soporte_cliente/tests/api/test_informes_escalados_contract.py`: envelope conforme al OpenAPI

**Checkpoint**: los dos listados completos.

---

## Phase 5: Polish & Cross-Cutting Concerns

- [X] T032 [P] Prueba de **integridad de la paginación** en `backend/apps/soporte_cliente/tests/api/test_informes_paginacion_integridad.py`: recorrer un listado por páginas devuelve cada fila exactamente una vez (SC-008)
- [X] T033 [P] Prueba de que `limit` sobre el máximo responde `400` y no se recorta en silencio, en `backend/apps/soporte_cliente/tests/api/test_informes_limite.py` (FR-021)
- [X] T034 [P] Prueba de rendimiento en `backend/apps/soporte_cliente/tests/performance/test_informes_latencia.py`: primera página de los dos listados por debajo de 2 s (SC-007)
- [X] T035 Ejecutar `cd backend && python -m pytest -q` completo y verificar que **ninguna suite existente se movió**
- [X] T036 Verificar que la implementación coincide con `contracts/informes-tacticos-simples.openapi.yaml` endpoint por endpoint
- [X] T037 Recorrer `quickstart.md` de principio a fin contra el stack levantado, con especial atención a §3.2 (sin compromiso), §3.3 y §3.4 (escalados) y §3.6 (acotamiento del Partner)
- [X] T038 Anotar en `decisiones-pendientes.md` que **la tabla de vínculos usuario-cuenta no la escribe ningún código de producción**, de modo que hoy solo el administrador local de una organización puede consultar los listados acotados a su cuenta — y preguntar si eso es intencional (research D1)
- [X] T039 Corregir el comentario de `database/seed_usuario_partner_demo.py`, que justifica vincular por administrador local diciendo que la tabla de vínculos «no tiene topic de Kafka»: **sí lo tiene declarado**. La conclusión práctica es correcta; el motivo que da, no
- [X] T040 Documentar el trabajo en `.specify/docs/changelog.md` y actualizar `informestacticos/TSI-Informes-Tacticos-Requeridos-por-OT.md` marcando los listados como 🟢

---

## Dependencies

```text
Piloto + Ventas y CRM + Suscripciones + Red Operativa   ← BLOQUEANTES EXTERNOS
    ↓
Phase 1 (Setup + siembra de datos)
    ↓
Phase 2 (Foundational: permisos) ← BLOQUEANTE
    ↓
    ├─→ Phase 3 (US1, P1) ─┐
    └─→ Phase 4 (US2, P2) ─┘ independientes entre sí
                            ↓
                    Phase 5 (Polish)
```

**Dentro de la fase 1**: T003, T004 y T005 son paralelos; T002 conviene primero.

**Dentro de la fase 2**: T006 y T007 primero, T008 depende de ambos. **T009 cierra la fase**: es la
comprobación de que este módulo no tocó la capa compartida.

**Entre user stories**: ninguna depende de otra. Comparten `views/informes_views.py` y `urls.py`
(T014, T025), tocados en dos puntos sin solapamiento.

---

## Parallel Execution Examples

**Fase 1 — la siembra de datos:**

```text
T003 ticket sin compromiso + ticket sin clasificar
T004 escalado manual + automático + aviso de plazo
T005 usuario con rol mixto
```

**Fase 3 — todas las pruebas de US1 tras la implementación:**

```text
T015 test_informes_tickets_sin_compromiso.py
T016 test_informes_tickets_partner.py
T017 test_informes_tickets_rol_mixto.py
T018 test_informes_tickets_cuenta_ajena.py
T019 test_informes_tickets_sin_descripcion.py
T020 test_informes_tickets_repository.py
T021 test_informes_tickets_contract.py
```

**Fase 5 — la batería de cierre:**

```text
T032 test_informes_paginacion_integridad.py
T033 test_informes_limite.py
T034 test_informes_latencia.py
```

---

## Implementation Strategy

### MVP — solo User Story 1

Las fases 1, 2 y 3 entregan **la cola de tickets con el acotamiento correcto y la situación de
compromiso completa**. Es el corte natural, y el que hace visible el ticket que hoy nadie vigila.

### Entrega incremental

1. **Fases 1–2** — permisos listos y verificado que la capa compartida no se tocó (T009).
2. **Fase 3 (US1)** — MVP. Cola de tickets con los cuatro estados de compromiso.
3. **Fase 4 (US2)** — escalados con autoría correcta y sin contenido interno.
4. **Fase 5** — cierre, dos anotaciones y una corrección de comentario.

### Cuatro riesgos a vigilar

**T009 verifica la hipótesis central del módulo.** Este es el primero de la serie que solo consume la
capa transversal. Si al implementarlo hiciera falta modificarla, **la parametrización de Red
Operativa quedó incompleta** — y la corrección va allí, no aquí.

**T016 protege contra el fallo que casi se coló en la revisión anterior.** Si el Partner ve los
tickets del Cliente, el acotamiento se decidió por el rol que se tiene en vez de por el que no se
tiene. **Y T002 es lo que hace real esa prueba**: si ambos comparten cuenta, pasa sin demostrar nada.

**T015 evita reintroducir un defecto ya corregido.** Un listado que omita el ticket `sin compromiso`
o lo muestre como `en curso` volvería invisible el único estado en que un ticket queda sin que
ningún proceso lo mire.

**T028 comprueba una ausencia, no un filtro.** No basta con que el texto no aparezca en la respuesta:
la columna **no debe consultarse**. Un filtro correcto sigue siendo un filtro que alguien puede
olvidar al añadir un campo dentro de seis meses.


---

## Desviaciones respecto a lo planificado *(2026-08-15)*

Las 40 tareas están hechas, pero tres se hicieron de otra forma y una queda a medias. Se declara aquí
para que nadie lea el `[X]` como algo que no es.

**T002–T005 — la siembra vive en las pruebas, no en `backend/scripts/`.** El Cliente y el Partner en
cuentas distintas, el ticket `sin compromiso`, el sin clasificar, los tres tipos de acción y el
usuario con rol mixto están en `apps/soporte_cliente/tests/conftest.py`. Es donde las pruebas los
necesitaban, y ahí quedan bajo control de versiones y verificados en cada ejecución. **El guion de
demo sigue sin esos casos**: quien levante el stack para recorrer el `quickstart.md` tendrá que
sembrarlos a mano.

**Los ficheros de prueba están agrupados, no uno por tarea.** `tasks.md` nombraba un fichero por
comprobación; están en seis, por listado y no por aserción: `test_informes_tickets.py` (US1),
`test_informes_escalados.py` (US2), más permisos incluidos en ambos, paginación, conformidad OpenAPI
y latencia. El contenido exigido está completo.

**T034 mide contra el Pinot falso.** El umbral de 2 s se cumple con holgura, pero ahí no hay red: lo
que la prueba vigila de verdad es que **el número de consultas no crezca con el tamaño de la
página**, que sí se traslada al stack real.

**T037 no se recorrió contra el stack levantado.** El `quickstart.md` está escrito y su contenido
está cubierto por las pruebas automáticas, pero **nadie lo ha ejecutado con Docker arriba**. Queda
pendiente para una sesión con el stack en marcha.

## Cambios que la implementación obligó a hacer en los documentos

**El enum de `situacion_compromiso` era corto.** `spec.md` (FR-004), `data-model.md` y el contrato
declaraban cuatro valores; el dominio escribe **cinco** —falta `cumplido`—. Corregidos los tres, y
añadida una prueba que compara el enum del OpenAPI contra las constantes del dominio para que no
vuelva a divergir en silencio.

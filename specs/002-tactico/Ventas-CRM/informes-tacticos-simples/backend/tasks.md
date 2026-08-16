# Tasks: Informes Tácticos Simples de Ventas y CRM (Backend)

**Input**: Design documents from `specs/002-tactico/Ventas-CRM/informes-tacticos-simples/backend/`

**Prerequisites**: [`plan.md`](plan.md), [`spec.md`](spec.md), [`research.md`](research.md), [`data-model.md`](data-model.md), [`contracts/`](contracts/)

**Tests**: **incluidos y obligatorios.** La constitución fija cobertura ≥80% en servicios, y research
D1 y D3 exigen pruebas concretas sin las cuales dos defectos silenciosos pasarían inadvertidos.

**Organization**: agrupadas por user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: puede ejecutarse en paralelo (ficheros distintos, sin dependencias pendientes)
- **[Story]**: US1, US2, US3 según `spec.md`
- Cada tarea lleva su ruta exacta

---

## ⚠️ Dependencia externa bloqueante

**Este módulo no puede empezar hasta que las fases 1 y 2 del módulo piloto estén completas.**
`backend/core/informes/` —período, paginación, envelope y vista base— se construye allí, y aquí solo
se **amplía**. Ver
[`../../Cuentas-Clientes/informes-tacticos-simples/backend/tasks.md`](../../Cuentas-Clientes/informes-tacticos-simples/backend/tasks.md)
fases 1–2 (T001–T011).

---

## Phase 1: Setup

**Purpose**: comprobar la dependencia y **preparar los datos sin los cuales las pruebas centrales no
prueban nada**.

- [X] T001 Verificar que existen `periodo.py`, `paginacion.py`, `envelope.py` y `vistas.py` en `backend/core/informes/`, y que `cd backend && python -m pytest core/informes apps/cuentas_clientes -q` está verde antes de tocar nada
- [X] T002 **Sembrar un segundo Gerente de Ventas con cartera propia** en `backend/scripts/` (al menos 2 prospectos asignados, distintos de los de `lucia.ramos.ventas@demo.tsi.com`) — **sin dos carteras pobladas a la vez, todas las pruebas de acotamiento pasan aunque el acotamiento no exista**
- [X] T003 [P] Sembrar en `backend/scripts/` un prospecto **perdido** y uno **convertido** simultáneamente, requisito de la prueba de research D1
- [X] T004 [P] Sembrar en `backend/scripts/` dos demos con la misma fecha de expiración pero distinto formato de sufijo (`Z` y `+00:00`), y una demo expirada hoy más temprano, requisitos de la prueba de research D3

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: la pieza transversal que este módulo aporta a los seis departamentos restantes.

**⚠️ CRÍTICO**: ninguna user story puede empezar hasta que esta fase esté completa.

- [X] T005 Implementar el resolutor de acotamiento por titularidad en `backend/core/informes/acotamiento.py`, replicando el comportamiento ya verificado de `backend/apps/ventas_crm/services/consulta_notificacion_ventas_service.py:25-37`: rol amplio ve todo y puede filtrar; rol acotado queda forzado a lo suyo; pedir lo ajeno es negativa; cualquier otro rol, negativa (research D2)
- [X] T006 Extender el envelope de `backend/core/informes/envelope.py` con el campo `acotado_a` (`propios` / `todos`), sin romper a los consumidores existentes que no lo declaran
- [X] T007 [P] Pruebas del resolutor de acotamiento en `backend/apps/ventas_crm/tests/unit/test_acotamiento.py`, cubriendo las seis combinaciones de la tabla de research D2 y comprobando que **pedir lo ajeno nunca devuelve datos propios**
- [X] T008 [P] Pruebas del envelope ampliado en `backend/apps/ventas_crm/tests/unit/test_envelope_acotado.py`: `acotado_a` refleja el acotamiento real aplicado
- [X] T009 Añadir las clases de permiso de informes en `backend/apps/ventas_crm/permissions.py` (Administrador, Gerente de Ventas, Gerente de Cuentas Públicas), siguiendo el patrón del piloto
- [X] T010 [P] Pruebas de permisos en `backend/apps/ventas_crm/tests/unit/test_informes_permissions.py`: fallo cerrado sin token, sin roles y con rol no autorizado
- [X] T011 Ejecutar `cd backend && python -m pytest core/informes apps/cuentas_clientes apps/informes_tacticos -q` y verificar que la ampliación de `core/informes/` **fue aditiva** y no rompió el piloto ni los 19 informes agregados

**Checkpoint**: base lista — las tres user stories pueden abordarse en paralelo.

---

## Phase 3: User Story 1 — Consultar prospectos viendo solo lo que a cada quien le corresponde (Priority: P1) 🎯 MVP

**Goal**: el listado de cartera con filtros combinables y acotamiento por ejecutivo. Responde por sí
solo las cuatro preguntas que el catálogo planteaba por separado.

**Independent Test**: consultar el listado con cada filtro, con dos roles distintos, y comprobar el
acotamiento, sin que existan los otros tres listados.

**Criterio medible (ISO 25010 — Security / Confidentiality)**: un Gerente obtiene el 100 % de sus
prospectos y **cero** de otros ejecutivos, con dos carteras pobladas a la vez (T019).

### Implementación

- [X] T012 [US1] Implementar la consulta de cartera en `backend/core/repositories/ventas_crm/informes_cartera_repository.py` con **columnas enumeradas** —sin `gmail` ni `telefono`, prohibido `SELECT *`— filtros por canal, tipo de organización, etapa y ejecutivo, cursor escalar por `idprospecto` y acotamiento por `idusuario` (research D4)
- [X] T013 [US1] Implementar el filtro `estado` de **tres valores** en el mismo repositorio: `activo` por `activo = true`, `perdido` por `motivo_inactividad = 'perdido'`, `convertido` por `motivo_inactividad = 'convertido'`. **Prohibido usar `activo = false` como equivalente de perdido** (research D1)
- [X] T014 [US1] Implementar `InformesCarteraService` en `backend/apps/ventas_crm/services/informes_cartera_service.py`, aplicando el resolutor de acotamiento, resolviendo el nombre del ejecutivo contra el catálogo de usuarios y devolviendo `motivo_perdida` solo cuando el estado es `perdido`
- [X] T015 [US1] Implementar la vista en `backend/apps/ventas_crm/views/informes_cartera_views.py`, heredando de la vista base y declarándose como listado de **estado actual**
- [X] T016 [US1] Registrar la ruta `/informes/ventas-crm/prospectos` en `backend/apps/ventas_crm/urls.py`

### Pruebas

- [X] T017 [P] [US1] Pruebas de repositorio en `backend/apps/ventas_crm/tests/repositories/test_informes_cartera_repository.py`: cada filtro por separado y combinados, orden determinista, cursor
- [X] T018 [P] [US1] **Prueba de que perdido y convertido son conjuntos disjuntos** en `backend/apps/ventas_crm/tests/repositories/test_informes_cartera_perdido_vs_convertido.py`: con un prospecto de cada clase sembrados, cada filtro devuelve exactamente uno, y **el convertido nunca aparece entre los perdidos**. Debe verificar la condición SQL contra el código, no contra el doble en memoria, que no reproduce la distinción (research D1)
- [X] T019 [P] [US1] **Prueba de acotamiento con dos carteras pobladas** en `backend/apps/ventas_crm/tests/api/test_informes_cartera_acotamiento.py`: el Gerente obtiene solo los suyos, el Administrador obtiene todos, y el conteo del Gerente es estrictamente menor (SC-001)
- [X] T020 [P] [US1] **Prueba de que pedir la cartera ajena responde 403 sin devolver filas** en `backend/apps/ventas_crm/tests/api/test_informes_cartera_titularidad_ajena.py` — devolver la propia con 200 es el defecto que FR-008 previene (SC-002)
- [X] T021 [P] [US1] Prueba de que la respuesta **no contiene datos de contacto** (`gmail`, `telefono`) en `backend/apps/ventas_crm/tests/api/test_informes_cartera_sin_contacto.py`, verificando además contra el código que el repositorio no usa `SELECT *` (research D4)
- [X] T022 [P] [US1] Prueba de contrato en `backend/apps/ventas_crm/tests/api/test_informes_cartera_contract.py`: envelope conforme al OpenAPI con `acotado_a`, `data: []` con 200 sin filas, `400` con `estado` inválido nombrando los tres válidos, `400` con rango de fechas
- [X] T023 [P] [US1] Prueba de que un prospecto **sin ejecutivo asignado aparece** en el listado del Administrador, marcado como ausente, en `backend/apps/ventas_crm/tests/services/test_informes_cartera_sin_ejecutivo.py` (FR-020, research D7)

**Checkpoint**: US1 entregable por sí sola. Es el MVP y valida la regla más delicada del contrato.

---

## Phase 4: User Story 2 — Seguir las reasignaciones de cartera (Priority: P2)

**Goal**: el listado de movimientos de cartera, con rango de fechas opcional.

**Independent Test**: consultar el listado de forma aislada, con y sin rango, sin que existan los
otros tres.

**Criterio medible (ISO 25010 — Functional Completeness)**: el 100 % de las primeras asignaciones
aparece con el responsable anterior marcado como ausente, nunca como cero (T027).

### Implementación

- [X] T024 [US2] Implementar la consulta de reasignaciones en `backend/core/repositories/ventas_crm/informes_asignacion_repository.py`, con rango de fechas **opcional**, filtros por prospecto y tipo de asignación, y cursor compuesto `fechahoraasignacion|idasignacion`
- [X] T025 [US2] Implementar `InformesAsignacionService` en `backend/apps/ventas_crm/services/informes_asignacion_service.py`, resolviendo los nombres del ejecutivo anterior y el nuevo contra el catálogo de usuarios y la empresa contra el prospecto
- [X] T026 [US2] Implementar la vista en `backend/apps/ventas_crm/views/informes_asignacion_views.py` como listado de **hechos del período**, y registrar `/informes/ventas-crm/reasignaciones` en `backend/apps/ventas_crm/urls.py`

### Pruebas

- [X] T027 [P] [US2] Prueba de que la **primera asignación de un prospecto** se devuelve con el responsable anterior **ausente**, no como cero ni cadena vacía, en `backend/apps/ventas_crm/tests/services/test_informes_asignacion_primera.py` (research D7)
- [X] T028 [P] [US2] Prueba de rango opcional en `backend/apps/ventas_crm/tests/api/test_informes_asignacion_rango.py`: sin rango devuelve el histórico completo paginado; con rango lo acota
- [X] T029 [P] [US2] Pruebas de repositorio en `backend/apps/ventas_crm/tests/repositories/test_informes_asignacion_repository.py`: filtros, orden determinista y cursor compuesto
- [X] T030 [P] [US2] Prueba de contrato en `backend/apps/ventas_crm/tests/api/test_informes_asignacion_contract.py`: envelope conforme al OpenAPI y `403` para roles no autorizados

**Checkpoint**: US2 entregable de forma independiente.

---

## Phase 5: User Story 3 — Vigilar la nutrición del prospecto (Priority: P3)

**Goal**: demos vigentes con días restantes, y alertas de señal de interés enviadas. Aquí vive el
filtro en dos pasos.

**Independent Test**: consultar los dos listados de forma aislada, sin que existan los de las otras
historias.

**Criterio medible (ISO 25010 — Functional Correctness)**: dos demos con la misma fecha y distinto
formato de sufijo aparecen o desaparecen **juntas**, verificado por T034.

### Implementación

- [X] T031 [US3] Implementar la consulta de demos activas en `backend/core/repositories/ventas_crm/informes_nutricion_repository.py` con **prefiltro por prefijo de fecha** `YYYY-MM-DD` — **prohibido comparar la cadena de expiración completa en SQL**, porque los formatos son mixtos y la comparación falla en silencio (research D3)
- [X] T032 [US3] Implementar la consulta de notificaciones enviadas en el mismo repositorio, con rango opcional, filtros por regla y canal, cursor compuesto, y **sin exponer la columna de estado de envío**, que ningún proceso escribe
- [X] T033 [US3] Implementar `InformesNutricionService` en `backend/apps/ventas_crm/services/informes_nutricion_service.py` con **reloj inyectable**: refinamiento exacto de la expiración y cálculo de `dias_restantes` **con el mismo instante**, más el acotamiento por ejecutivo asignado en demos y por destinatario en notificaciones (research D3, D5)
- [X] T034 [US3] Implementar las dos vistas en `backend/apps/ventas_crm/views/informes_nutricion_views.py` y registrar `/informes/ventas-crm/{demos-activas,notificaciones-enviadas}` en `backend/apps/ventas_crm/urls.py`

### Pruebas

- [X] T035 [P] [US3] **Prueba del formato mixto de fecha** en `backend/apps/ventas_crm/tests/repositories/test_informes_demos_formato_mixto.py`: dos demos con la misma fecha, una con sufijo `Z` y otra con `+00:00`, **aparecen o desaparecen juntas**. Si solo sale una, la comparación de texto se coló en la consulta (research D3)
- [X] T036 [P] [US3] Prueba de que una demo **expirada hoy más temprano no aparece**, y de que la página puede devolver menos filas que el `limit` sin que eso signifique fin de resultados, en `backend/apps/ventas_crm/tests/api/test_informes_demos_pagina_corta.py`
- [X] T037 [P] [US3] Prueba de `dias_restantes` con **instante inyectado** en `backend/apps/ventas_crm/tests/services/test_informes_nutricion_service.py`, comprobando que el refinamiento y el cálculo usan el mismo instante
- [X] T038 [P] [US3] Prueba de que una demo **sin fecha de expiración no se considera activa** en `backend/apps/ventas_crm/tests/repositories/test_informes_demos_sin_fecha.py`
- [X] T039 [P] [US3] Prueba de que las notificaciones se acotan por **destinatario** y de que `estado_envio` **no aparece** en la respuesta, en `backend/apps/ventas_crm/tests/api/test_informes_notificaciones_acotamiento.py`
- [X] T040 [P] [US3] Pruebas de contrato en `backend/apps/ventas_crm/tests/api/test_informes_nutricion_contract.py`: envelope conforme al OpenAPI para ambos listados

**Checkpoint**: los cuatro listados completos.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T041 [P] Prueba de **integridad de la paginación** en `backend/apps/ventas_crm/tests/api/test_informes_paginacion_integridad.py`: recorrer un listado por páginas devuelve cada fila exactamente una vez (SC-006). **Excluir demos activas**, cuyo recorrido admite páginas cortas por diseño
- [X] T042 [P] Prueba de que `limit` sobre el máximo responde `400` y no se recorta en silencio, en `backend/apps/ventas_crm/tests/api/test_informes_limite.py` (FR-018)
- [X] T043 [P] Prueba de rendimiento en `backend/apps/ventas_crm/tests/performance/test_informes_latencia.py`: primera página de los cuatro listados por debajo de 2 s (SC-004)
- [X] T044 Ejecutar `cd backend && python -m pytest -q` completo y verificar que **ninguna suite existente se movió** — en particular `apps/informes_tacticos` y `apps/cuentas_clientes`
- [X] T045 Verificar que la implementación coincide con `contracts/informes-tacticos-simples.openapi.yaml` endpoint por endpoint, corrigiendo el contrato si la implementación reveló algo mejor
- [ ] T046 Recorrer `quickstart.md` de principio a fin contra el stack levantado, con especial atención a §3.2 y §3.3 (acotamiento) y §3.4 (perdido vs convertido) — **parcial:** las 11 comprobaciones reproducibles están cubiertas por la suite y anotadas en `quickstart.md` §7, y se añadió §6 con el seed que las hace reales. **Falta el recorrido contra Docker levantado**, que en este módulo importa especialmente: el doble compara los formatos de `demo_expiracion` como texto Python y Pinot como texto SQL
- [X] T047 Anotar en `decisiones-pendientes.md` que la columna de expiración de demo es texto con formatos mixtos y debería ser marca de tiempo numérica como el resto del sistema (causa raíz de research D3)
- [X] T048 Documentar el trabajo en `.specify/docs/changelog.md`, actualizar `informestacticos/TSI-Informes-Tacticos-Requeridos-por-OT.md` marcando los listados como 🟢, y **propagar `acotado_a` al contrato común** `specs/002-tactico/contrato-informes-simples.md` para que los seis departamentos restantes lo hereden

---

## Dependencies

```text
Módulo piloto Cuentas y Clientes, fases 1–2  ← BLOQUEANTE EXTERNO
    ↓
Phase 1 (Setup + siembra de datos)
    ↓
Phase 2 (Foundational: acotamiento) ← BLOQUEANTE
    ↓
    ├─→ Phase 3 (US1, P1) ─┐
    ├─→ Phase 4 (US2, P2) ─┤ independientes entre sí
    └─→ Phase 5 (US3, P3) ─┘
                            ↓
                    Phase 6 (Polish)
```

**Dentro de la fase 1**: T003 y T004 son paralelos entre sí; T002 conviene primero por ser el que más
condiciona las pruebas.

**Dentro de la fase 2**: T005 y T006 tocan ficheros distintos pero T007 depende de T005 y T008 de
T006. T009 y T010 son independientes. **T011 cierra la fase y no debe saltarse.**

**Entre user stories**: ninguna depende de otra. El único fichero compartido es `urls.py`
(T016, T026, T034), tocado en tres puntos sin solapamiento.

---

## Parallel Execution Examples

**Fase 1 — la siembra de datos:**

```text
T003 prospecto perdido + prospecto convertido
T004 demos con formatos mixtos + demo expirada hoy
```

**Fase 3 — todas las pruebas de US1 tras la implementación:**

```text
T017 test_informes_cartera_repository.py
T018 test_informes_cartera_perdido_vs_convertido.py
T019 test_informes_cartera_acotamiento.py
T020 test_informes_cartera_titularidad_ajena.py
T021 test_informes_cartera_sin_contacto.py
T022 test_informes_cartera_contract.py
T023 test_informes_cartera_sin_ejecutivo.py
```

**Fase 6 — la batería de cierre:**

```text
T041 test_informes_paginacion_integridad.py
T042 test_informes_limite.py
T043 test_informes_latencia.py
```

---

## Implementation Strategy

### MVP — solo User Story 1

Las fases 1, 2 y 3 entregan **el listado de cartera funcionando con acotamiento real**, y con él la
pieza transversal que los seis departamentos restantes necesitan. Es el corte natural: valida la
regla más delicada del contrato común antes de que nadie construya encima.

### Entrega incremental

1. **Fases 1–2** — `acotamiento.py` listo y verificado como aditivo (T011).
2. **Fase 3 (US1)** — MVP. Cartera con los tres estados y acotamiento por ejecutivo.
3. **Fase 4 (US2)** — reasignaciones. Añade el patrón de rango opcional a este departamento.
4. **Fase 5 (US3)** — demos y notificaciones. Añade el filtro en dos pasos.
5. **Fase 6** — cierre, causa raíz anotada y contrato común actualizado.

### Tres riesgos a vigilar

**T002 es el que hace reales las pruebas de acotamiento.** Sin un segundo Gerente con cartera
poblada, T019 y T020 pasan aunque el acotamiento no exista: con una sola cartera, filtrar y no
filtrar dan el mismo resultado. Es el fallo más fácil de cometer en este módulo.

**T011 es el guardián de que la ampliación fue aditiva.** `core/informes/` gana dos piezas aquí
—el resolutor y el campo `acotado_a`—; si eso mueve la suite del piloto o la de los 19 informes
agregados, la ampliación rompió algo.

**T018 protege contra el defecto más caro.** Sin esa prueba, un listado de prospectos perdidos que
incluya los convertidos pasaría desapercibido indefinidamente: devuelve un número plausible, no
falla, y presenta los éxitos comerciales como fracasos.

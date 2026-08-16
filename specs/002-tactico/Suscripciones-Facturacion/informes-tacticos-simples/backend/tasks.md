# Tasks: Informes Tácticos Simples de Suscripciones y Facturación (Backend)

**Input**: Design documents from `specs/002-tactico/Suscripciones-Facturacion/informes-tacticos-simples/backend/`

**Prerequisites**: [`plan.md`](plan.md), [`spec.md`](spec.md), [`research.md`](research.md), [`data-model.md`](data-model.md), [`contracts/`](contracts/)

**Tests**: **incluidos y obligatorios.** La constitución fija cobertura ≥80% en servicios, y research
D2, D3 y D4 exigen pruebas concretas sin las cuales dos defectos silenciosos y una fuga de medio de
cobro pasarían inadvertidos.

**Organization**: agrupadas por user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: puede ejecutarse en paralelo (ficheros distintos, sin dependencias pendientes)
- **[Story]**: US1, US2, US3 según `spec.md`
- Cada tarea lleva su ruta exacta

---

## ⚠️ Dependencias externas bloqueantes

**Fases 1–2 del módulo piloto** (Cuentas y Clientes): construyen `core/informes/` — período,
paginación, envelope y vista base.
**Fase 2 de Ventas y CRM**: construye `core/informes/acotamiento.py` (eje «persona») y el campo
`acotado_a` del envelope, que este módulo **amplía**, no reescribe.

Ver [`../../Cuentas-Clientes/.../tasks.md`](../../Cuentas-Clientes/informes-tacticos-simples/backend/tasks.md)
T001–T011 y [`../../Ventas-CRM/.../tasks.md`](../../Ventas-CRM/informes-tacticos-simples/backend/tasks.md)
T005–T011.

---

## Phase 1: Setup

**Purpose**: comprobar las dependencias y **sembrar los datos sin los cuales tres pruebas centrales
no prueban nada**.

- [X] T001 Verificar que `core/informes/` incluye ya `periodo.py`, `paginacion.py`, `envelope.py`, `vistas.py` y `acotamiento.py`, y que `cd backend && python -m pytest core/informes apps/cuentas_clientes apps/ventas_crm -q` está verde antes de tocar nada
- [X] T002 **Garantizar dos cuentas cliente con facturación simultánea** en `backend/scripts/` (Ana Torres y Teresa Beltrán, ambas con suscripción, método de pago y facturas) — **sin dos cuentas pobladas, filtrar y no filtrar dan el mismo resultado y el acotamiento pasa cualquier prueba sin existir**
- [X] T003 [P] Sembrar en `backend/scripts/` una suscripción **con** reducción de plan programada y otra **sin** ninguna, requisito de la prueba de research D2
- [X] T004 [P] Sembrar en `backend/scripts/` una factura **`Fallida` vencida** y otra **`En disputa`**, requisito de la prueba de research D3
- [X] T005 [P] Sembrar en `backend/scripts/` un método de pago **reemplazado**, de modo que exista uno inactivo junto al vigente, requisito de FR-007

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: el segundo eje de acotamiento que este módulo aporta a los tres departamentos
restantes.

**⚠️ CRÍTICO**: ninguna user story puede empezar hasta que esta fase esté completa.

- [X] T006 Ampliar `backend/core/informes/acotamiento.py` con el **eje «organización»**: resuelve la cuenta cliente del solicitante por pertenencia, deja ver todas las cuentas al rol amplio, fuerza a la propia al rol acotado y **niega** cuando se pide otra (research D1). **No modificar** ninguna de las cuatro implementaciones operativas existentes
- [X] T007 [P] Pruebas del eje «organización» en `backend/apps/suscripciones/tests/unit/test_acotamiento_organizacion.py`: las seis combinaciones de la tabla de research D1, y que **pedir otra cuenta nunca devuelve datos propios**
- [X] T008 [P] Prueba de que una cuenta con la suscripción **suspendida conserva** el acceso a sus propios registros, en `backend/apps/suscripciones/tests/unit/test_acotamiento_suspendida.py` (FR-011)
- [X] T009 Añadir las clases de permiso de informes en `backend/apps/suscripciones/permissions.py` (Administrador, Cliente, Proveedor), **sin reutilizar `IsProveedorCuenta`**, que excluye al Administrador y por tanto no cubre la mitad táctica del caso de uso
- [X] T010 [P] Pruebas de permisos en `backend/apps/suscripciones/tests/unit/test_informes_permissions.py`: fallo cerrado sin token, sin roles y con rol no autorizado
- [X] T011 Ejecutar `cd backend && python -m pytest core/informes apps/cuentas_clientes apps/ventas_crm apps/informes_tacticos -q` y verificar que la ampliación de `core/informes/` **fue aditiva**

**Checkpoint**: base lista — las tres user stories pueden abordarse en paralelo.

---

## Phase 3: User Story 1 — Ver el estado comercial de las suscripciones (Priority: P1) 🎯 MVP

**Goal**: el listado de suscripciones con filtros combinables y acotamiento por cuenta. Responde por
sí solo cinco de las diez preguntas del catálogo.

**Independent Test**: consultar el listado con cada filtro, con dos roles distintos, sin que existan
los otros tres listados.

**Criterio medible (ISO 25010 — Functional Correctness)**: el 100 % de las suscripciones sin cambio
programado queda fuera del filtro de cambios programados y se presenta como ausencia (T017).

### Implementación

- [X] T012 [US1] Implementar la consulta de suscripciones en `backend/core/repositories/suscripciones/informes_suscripcion_repository.py` con filtros por estado, plan y rango de fecha de cancelación, cursor escalar por `id_suscripcion` y acotamiento por `idcliente`
- [X] T013 [US1] Implementar en el mismo repositorio el filtro `con_cambio_programado` como **`idplan_programado > 0`**. **Prohibido escribirlo como comprobación de nulidad**: la columna guarda un `0` explícito que significa «sin cambio», y una guarda de nulidad devolvería todas las suscripciones (research D2)
- [X] T014 [US1] Implementar el filtro `vence_en_dias` en el mismo repositorio, traduciéndolo a una fecha de corte que viaja al `WHERE`, con el instante actual inyectado desde el servicio
- [X] T015 [US1] Implementar `InformesSuscripcionService` en `backend/apps/suscripciones/services/informes_suscripcion_service.py`, con reloj inyectable, resolución de plan y cuenta contra sus catálogos, y presentación del cambio programado como **ausencia** cuando no lo hay — nunca como un plan con identificador cero (FR-020)
- [X] T016 [US1] Implementar la vista en `backend/apps/suscripciones/views/informes_suscripcion_views.py` como listado de **estado actual**, y registrar `/informes/suscripciones-facturacion/suscripciones` en `backend/apps/suscripciones/urls.py`

### Pruebas

- [X] T017 [P] [US1] **Prueba del centinela de plan programado** en `backend/apps/suscripciones/tests/repositories/test_informes_suscripcion_cambio_programado.py`: con una suscripción con cambio y otra sin él, el filtro devuelve **exactamente una**. Debe verificar la condición SQL contra el código fuente, no contra el doble en memoria, que no reproduce el centinela (research D2)
- [X] T018 [P] [US1] **Prueba de acotamiento con dos cuentas pobladas** en `backend/apps/suscripciones/tests/api/test_informes_suscripcion_acotamiento.py`: el Cliente obtiene solo la suya, el Administrador todas, y el conteo del Cliente es estrictamente menor (SC-001)
- [X] T019 [P] [US1] **Prueba de que pedir otra cuenta responde 403 sin devolver filas** en `backend/apps/suscripciones/tests/api/test_informes_suscripcion_cuenta_ajena.py` (SC-002, FR-010)
- [X] T020 [P] [US1] Pruebas de repositorio en `backend/apps/suscripciones/tests/repositories/test_informes_suscripcion_repository.py`: filtros por estado, plan, vencimiento y rango de cancelación; orden determinista
- [X] T021 [P] [US1] Prueba de contrato en `backend/apps/suscripciones/tests/api/test_informes_suscripcion_contract.py`: envelope conforme al OpenAPI con `acotado_a`, `data: []` con 200 sin filas, `400` con estado inválido, `400` con rango genérico de fechas y `200` con `cancelada_desde`/`cancelada_hasta`
- [X] T022 [P] [US1] Prueba de que el motivo de cancelación se devuelve en las canceladas y **ausente** en las demás, en `backend/apps/suscripciones/tests/services/test_informes_suscripcion_cancelacion.py`

**Checkpoint**: US1 entregable por sí sola. Es el MVP.

---

## Phase 4: User Story 2 — Seguir la facturación y la salud del cobro (Priority: P2)

**Goal**: facturas con su estado y mora, y métodos de pago vigentes con los próximos a caducar.
**Aquí vive el requisito de seguridad más fuerte de la serie.**

**Independent Test**: consultar los dos listados de forma aislada, con y sin rango, sin que existan
los de las otras historias.

**Criterio medible (ISO 25010 — Security / Confidentiality)**: en el 100 % de las respuestas de los
dos listados, la respuesta serializada completa está libre del identificador de cobro (T028).

### Implementación

- [X] T023 [US2] Implementar la consulta de facturas en `backend/core/repositories/suscripciones/informes_facturacion_repository.py`, con rango de fechas **opcional**, filtro por estado de pago, cursor compuesto `fecha_emision|id_factura` y acotamiento por `id_cliente` — nótese el guion bajo, que difiere del resto de tablas
- [X] T024 [US2] Implementar el filtro `vencidas` en el mismo repositorio de modo que **excluya las facturas `En disputa`**: están fuera del cobro automático a propósito y presentarlas como mora induce a perseguir un cargo que el sistema detuvo (research D3)
- [X] T025 [US2] Implementar la consulta de métodos de pago vigentes en el mismo repositorio con **columnas enumeradas** —**prohibido `SELECT *`**, el identificador de cobro no puede salir— filtro `activo = true`, filtro `caduca_en_dias` traducido a fecha de corte que viaja al `WHERE`, y cursor compuesto (research D4, D5)
- [X] T026 [US2] Implementar `InformesFacturacionService` en `backend/apps/suscripciones/services/informes_facturacion_service.py` con **reloj inyectable**: `dias_mora` solo para vencidas e impagas, `dias_para_caducar` para los métodos, y exposición del tipo de documento para distinguir un cargo de una nota de crédito (research D6)
- [X] T027 [US2] Implementar las dos vistas en `backend/apps/suscripciones/views/informes_facturacion_views.py` —facturas como **hechos del período**, métodos de pago como **estado actual**— y registrar sus rutas en `backend/apps/suscripciones/urls.py`

### Pruebas

- [X] T028 [P] [US2] ⛔ **Prueba de que el identificador de cobro no sale**, en `backend/apps/suscripciones/tests/api/test_informes_sin_token_pasarela.py`: inspecciona la **respuesta serializada completa** de los cuatro listados —no los campos declarados en el contrato— y falla si aparece; verifica además contra el código fuente que el repositorio no usa `SELECT *` sobre el método de pago (SC-003, research D4)
- [X] T029 [P] [US2] **Prueba de que una factura en disputa no cuenta como mora** en `backend/apps/suscripciones/tests/repositories/test_informes_factura_disputa.py`: con una `Fallida` vencida y una `En disputa`, el filtro `vencidas` devuelve **solo la primera**, y la segunda aparece con su estado propio y **sin** `dias_mora` (research D3)
- [X] T030 [P] [US2] Prueba de que solo se devuelven métodos **vigentes** en `backend/apps/suscripciones/tests/repositories/test_informes_metodo_pago_vigente.py`: el reemplazado no aparece aunque su registro exista (FR-007)
- [X] T031 [P] [US2] Prueba de `dias_mora` y `dias_para_caducar` con **instante inyectado** en `backend/apps/suscripciones/tests/services/test_informes_facturacion_service.py`
- [X] T032 [P] [US2] Prueba de rango opcional en `backend/apps/suscripciones/tests/api/test_informes_factura_rango.py`: sin rango devuelve el histórico completo; con rango lo acota (FR-016)
- [X] T033 [P] [US2] Pruebas de contrato en `backend/apps/suscripciones/tests/api/test_informes_facturacion_contract.py`: envelope conforme al OpenAPI para ambos listados, y acotamiento por cuenta en los dos

**Checkpoint**: US2 entregable de forma independiente.

---

## Phase 5: User Story 3 — Atender las solicitudes de cambio de plan (Priority: P3)

**Goal**: la bandeja de solicitudes pendientes con el tiempo que llevan esperando.

**Independent Test**: consultar el listado de forma aislada, sin que existan los otros tres.

**Criterio medible (ISO 25010 — Functional Correctness)**: `dias_espera` es exacto para un instante
inyectado conocido, sin depender del reloj del sistema (T036).

### Implementación

- [X] T034 [US3] Implementar la consulta de solicitudes en `backend/core/repositories/suscripciones/informes_cambio_plan_repository.py`, con filtro por estado, orden `fecha_solicitud ASC` —es una bandeja: lo más antiguo primero— cursor compuesto y acotamiento por `idcliente`
- [X] T035 [US3] Implementar `InformesCambioPlanService` en `backend/apps/suscripciones/services/informes_cambio_plan_service.py` con reloj inyectable para `dias_espera`, resolución de ambos planes contra su catálogo y del resolutor contra el de usuarios, presentando resolutor y motivo de rechazo como **ausentes** mientras la solicitud siga pendiente
- [X] T036 [US3] Implementar la vista en `backend/apps/suscripciones/views/informes_cambio_plan_views.py` como listado de **estado actual**, y registrar su ruta en `backend/apps/suscripciones/urls.py`

### Pruebas

- [X] T037 [P] [US3] Prueba de `dias_espera` con **instante inyectado** en `backend/apps/suscripciones/tests/services/test_informes_cambio_plan_service.py`
- [X] T038 [P] [US3] Prueba de que una solicitud pendiente devuelve resolutor y motivo de rechazo **ausentes**, y una rechazada los devuelve con valor, en `backend/apps/suscripciones/tests/services/test_informes_cambio_plan_resolucion.py`
- [X] T039 [P] [US3] Pruebas de repositorio en `backend/apps/suscripciones/tests/repositories/test_informes_cambio_plan_repository.py`: filtro por estado, orden ascendente y cursor compuesto
- [X] T040 [P] [US3] Prueba de contrato en `backend/apps/suscripciones/tests/api/test_informes_cambio_plan_contract.py`: envelope conforme al OpenAPI y acotamiento por cuenta

**Checkpoint**: los cuatro listados completos.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T041 [P] Prueba de **integridad de la paginación** en `backend/apps/suscripciones/tests/api/test_informes_paginacion_integridad.py`: recorrer un listado por páginas devuelve cada fila exactamente una vez, incluido el cursor de facturas que desempata por texto (SC-007)
- [X] T042 [P] Prueba de que `limit` sobre el máximo responde `400` y no se recorta en silencio, en `backend/apps/suscripciones/tests/api/test_informes_limite.py` (FR-019)
- [X] T043 [P] Prueba de rendimiento en `backend/apps/suscripciones/tests/performance/test_informes_latencia.py`: primera página de los cuatro listados por debajo de 2 s (SC-006)
- [X] T044 Ejecutar `cd backend && python -m pytest -q` completo y verificar que **ninguna suite existente se movió**
- [X] T045 Verificar que la implementación coincide con `contracts/informes-tacticos-simples.openapi.yaml` endpoint por endpoint, corrigiendo el contrato si la implementación reveló algo mejor
- [ ] T046 Recorrer `quickstart.md` de principio a fin contra el stack levantado, con especial atención a §3.2 (identificador de cobro), §3.3 (centinela) y §3.4 (disputa vs mora) — **parcial:** las comprobaciones reproducibles están cubiertas por la suite (§3.2 por `test_informes_sin_token_pasarela.py`, §3.3 por `test_informes_suscripcion_cambio_programado.py`, §3.4 por `test_informes_factura_disputa.py`). **Falta el recorrido contra Docker levantado**
- [X] T047 Anotar en `decisiones-pendientes.md` que la resolución «usuario → su cuenta» está escrita **cuatro veces** en el código operativo y debería converger en la pieza transversal, y que `Fact_Factura.id_cliente` usa un nombre de columna inconsistente con el resto de tablas
- [X] T048 Documentar el trabajo en `.specify/docs/changelog.md`, actualizar `informestacticos/TSI-Informes-Tacticos-Requeridos-por-OT.md` marcando los listados como 🟢, y **añadir al contrato común** `specs/002-tactico/contrato-informes-simples.md` la regla de que toda columna temporal se verifica en el esquema antes de diseñar su filtro (lección de research D5)

---

## Dependencies

```text
Piloto Cuentas y Clientes, fases 1–2   ← BLOQUEANTE EXTERNO
Ventas y CRM, fase 2 (acotamiento)     ← BLOQUEANTE EXTERNO
    ↓
Phase 1 (Setup + siembra de datos)
    ↓
Phase 2 (Foundational: eje organización) ← BLOQUEANTE
    ↓
    ├─→ Phase 3 (US1, P1) ─┐
    ├─→ Phase 4 (US2, P2) ─┤ independientes entre sí
    └─→ Phase 5 (US3, P3) ─┘
                            ↓
                    Phase 6 (Polish)
```

**Dentro de la fase 1**: T003, T004 y T005 son paralelos; T002 conviene primero por condicionar más
pruebas.

**Dentro de la fase 2**: T006 primero; T007 y T008 dependen de él; T009 y T010 son independientes.
**T011 cierra la fase y no debe saltarse.**

**Entre user stories**: ninguna depende de otra. El único fichero compartido es `urls.py`
(T016, T027, T036), tocado en tres puntos sin solapamiento. US2 usa un solo repositorio para sus dos
listados, así que T023–T025 son secuenciales entre sí.

---

## Parallel Execution Examples

**Fase 1 — la siembra de datos:**

```text
T003 suscripción con y sin cambio programado
T004 factura Fallida vencida + factura En disputa
T005 método de pago reemplazado
```

**Fase 4 — todas las pruebas de US2 tras la implementación:**

```text
T028 test_informes_sin_token_pasarela.py
T029 test_informes_factura_disputa.py
T030 test_informes_metodo_pago_vigente.py
T031 test_informes_facturacion_service.py
T032 test_informes_factura_rango.py
T033 test_informes_facturacion_contract.py
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

Las fases 1, 2 y 3 entregan **el listado de suscripciones funcionando con acotamiento por
organización**, y con él la pieza transversal que Red Operativa, Partners y Soporte necesitarán. Es
el corte natural.

### Entrega incremental

1. **Fases 1–2** — eje «organización» listo y verificado como aditivo (T011).
2. **Fase 3 (US1)** — MVP. Suscripciones con los cinco filtros y el centinela bien tratado.
3. **Fase 4 (US2)** — facturas y métodos de pago. **Es la fase con el requisito de seguridad más
   fuerte de toda la serie.**
4. **Fase 5 (US3)** — bandeja de solicitudes.
5. **Fase 6** — cierre, deuda anotada y contrato común actualizado.

### Tres riesgos a vigilar

**T028 no es una prueba más.** El identificador de cobro sirve para cargar dinero contra la pasarela:
no es una credencial que haya que romper. Debe inspeccionar la **respuesta serializada completa**,
porque un `SELECT *` filtra el campo aunque el contrato no lo declare — el contrato describe la
intención, no el resultado. **Si esta prueba falla, detener y corregir antes de seguir.**

**T017 protege contra un informe que mentiría en silencio.** Sin ella, un filtro de reducciones
pendientes escrito como comprobación de nulidad devolvería todas las suscripciones. No fallaría:
daría un número plausible y equivocado.

**T002 hace reales las pruebas de acotamiento.** Con una sola cuenta poblada, T018 y T019 pasan
aunque el acotamiento no exista. Es el mismo riesgo que en Ventas y CRM, y por la misma razón.

# Tasks: Informes Tácticos Simples de Red Operativa (Backend)

**Input**: Design documents from `specs/002-tactico/Red-Operativa/informes-tacticos-simples/backend/`

**Prerequisites**: [`plan.md`](plan.md), [`spec.md`](spec.md), [`research.md`](research.md), [`data-model.md`](data-model.md), [`contracts/`](contracts/)

**Tests**: **incluidos y obligatorios.** La constitución fija cobertura ≥80% en servicios, y research
D1, D2, D4 y D5 exigen pruebas concretas sin las cuales cuatro defectos silenciosos pasarían
inadvertidos — uno de ellos con consecuencia sobre decisiones de cobertura.

**Organization**: agrupadas por user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: puede ejecutarse en paralelo (ficheros distintos, sin dependencias pendientes)
- **[Story]**: US1, US2, US3 según `spec.md`
- Cada tarea lleva su ruta exacta

---

## ⚠️ Dependencias externas bloqueantes

**Fases 1–2 del piloto** (Cuentas y Clientes) → `core/informes/` base.
**Fase 2 de Ventas y CRM** → `acotamiento.py` (eje persona) y `acotado_a`.
**Fase 2 de Suscripciones** → eje «organización» del acotamiento, que **este módulo corrige**.

Este módulo **no amplía la capa transversal: la corrige.** Es la primera vez en la serie, y por eso
T011 (comprobación de que nada se movió) tiene más peso que en los módulos anteriores.

---

## Phase 1: Setup

**Purpose**: comprobar dependencias y **sembrar los datos sin los cuales cinco pruebas centrales no
prueban nada**.

- [X] T001 Verificar que `core/informes/` incluye `periodo.py`, `paginacion.py`, `envelope.py`, `vistas.py` y `acotamiento.py` con sus dos ejes, y que `cd backend && python -m pytest core/informes apps/cuentas_clientes apps/ventas_crm apps/suscripciones -q` está verde antes de tocar nada
- [X] T002 **Garantizar dos empresas proveedoras con flota simultánea** en `backend/scripts/` — **sin dos flotas pobladas, filtrar y no filtrar dan el mismo resultado y el acotamiento pasa cualquier prueba sin existir**
- [X] T003 [P] Sembrar en `backend/scripts/` una unidad **dada de alta pero en estado operativo `Fuera de servicio`**, requisito de la prueba de research D2 — es el caso que demuestra que alta ≠ disponible
- [X] T004 [P] Sembrar en `backend/scripts/` una unidad **sin condado asignado**, requisito de FR-023
- [X] T005 [P] Verificar o sembrar una **baja forzada con su caso afectado** y una **baja normal**, requisito de research D5 (la revisión anterior dejó `LOTE-A1` con baja forzada durante una misión)
- [X] T006 [P] Sembrar en `backend/scripts/` una región en **`En_Alerta`**, otra **`Despublicada`**, y una región con **dos rechazos de validación**, requisitos de research D4 y de FR-005

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: corregir el eje «organización» del acotamiento **sin cambiar el comportamiento de los
módulos que ya lo usan**.

**⚠️ CRÍTICO**: ninguna user story puede empezar hasta que esta fase esté completa.

- [X] T007 Parametrizar el **criterio de pertenencia** en `backend/core/informes/acotamiento.py`: el eje «organización» acepta resolver la cuenta del solicitante por **administrador local** o por **vínculo a la cuenta**, y cada listado declara cuál usa. **El valor por defecto debe conservar el comportamiento que Suscripciones tiene hoy** (research D1)
- [X] T008 [P] Pruebas del criterio parametrizable en `backend/apps/red_operativa/tests/unit/test_acotamiento_criterio.py`: con criterio estricto, un usuario **no administrador local** de una cuenta proveedora recibe negativa; con criterio amplio, resuelve. Ambos casos sobre los mismos datos
- [X] T009 [P] Prueba de que **unificar el criterio rompería la regla del contrato** en `backend/apps/red_operativa/tests/unit/test_acotamiento_no_amplia.py`: el criterio amplio aplicado a este departamento daría acceso a un usuario que la pantalla operativa de alta de unidades rechaza — la prueba fija que ese acceso **no** se concede
- [X] T010 Añadir las clases de permiso de informes en `backend/apps/red_operativa/permissions.py`: flota y bajas para Administrador y Empresa Proveedora; regiones y validaciones **solo** para Administrador y Director Tecnológico (FR-012)
- [X] T011 Ejecutar `cd backend && python -m pytest core/informes apps/cuentas_clientes apps/ventas_crm apps/suscripciones apps/informes_tacticos -q` y verificar que la **corrección fue compatible hacia atrás** — si alguna suite previa se mueve, la parametrización cambió el defecto en vez de añadir una opción

**Checkpoint**: base lista — las tres user stories pueden abordarse en paralelo.

---

## Phase 3: User Story 1 — Consultar la composición de la flota (Priority: P1) 🎯 MVP

**Goal**: el listado de flota con filtros, acotamiento por proveedor y **la distinción explícita
entre existir y estar disponible**.

**Independent Test**: consultar el listado con cada filtro, con dos roles distintos, sin que existan
los otros tres listados.

**Criterio medible (ISO 25010 — Functional Correctness)**: el 100 % de las respuestas declara su
alcance como composición de flota, y ninguna presenta la condición de alta como disponibilidad
operativa (T018).

### Implementación

- [X] T012 [US1] Implementar la consulta de flota en `backend/core/repositories/red_operativa/informes_flota_repository.py` con **columnas enumeradas** —**prohibido `SELECT *`**: ni posición ni contacto del proveedor (research D6)— filtros por proveedor, condado, tipo y condición de alta, cursor escalar y acotamiento por `idcliente`
- [X] T013 [US1] **No leer el histórico de estados de unidad** en este repositorio. La disponibilidad operativa queda fuera de alcance por decisión de diseño; incluirla exigiría una consulta por unidad (research D2)
- [X] T014 [US1] Implementar la resolución geográfica por lotes en `backend/apps/red_operativa/services/informes_flota_service.py`, **reutilizando** `core/repositories/accidentes/ubicacion_catalogo_repository.py`: dos consultas de catálogo por página, **nunca una por fila** (research D3)
- [X] T015 [US1] Implementar en el mismo servicio el acotamiento con **criterio estricto** (administrador local) y la resolución del proveedor contra su catálogo
- [X] T016 [US1] Añadir el campo `alcance` al envelope de este listado en `backend/apps/red_operativa/views/informes_flota_views.py`, con valor que declare que describe composición de flota (FR-008)
- [X] T017 [US1] Implementar la vista como listado de **estado actual** y registrar `/informes/red-operativa/flota` en `backend/apps/red_operativa/urls.py`

### Pruebas

- [X] T018 [P] [US1] ⚠️ **Prueba de que estar de alta no es estar disponible** en `backend/apps/red_operativa/tests/api/test_informes_flota_alcance.py`: la unidad `Fuera de servicio` **aparece** en el listado de dadas de alta, la respuesta trae `alcance`, y **ningún campo** se llama disponibilidad ni estado operativo (SC-003, research D2)
- [X] T019 [P] [US1] Prueba de que **no salen posición ni contacto** en `backend/apps/red_operativa/tests/api/test_informes_flota_sin_geolocalizacion.py`, verificando además contra el código que el repositorio no usa `SELECT *` (research D6)
- [X] T020 [P] [US1] **Prueba de acotamiento con dos flotas pobladas** en `backend/apps/red_operativa/tests/api/test_informes_flota_acotamiento.py`: el proveedor obtiene solo las suyas, el Administrador todas, y el conteo del proveedor es estrictamente menor (SC-001)
- [X] T021 [P] [US1] Prueba de que pedir la flota de otro proveedor responde **403 sin devolver filas** en `backend/apps/red_operativa/tests/api/test_informes_flota_ajena.py` (SC-002)
- [X] T022 [P] [US1] Prueba de que una unidad **sin condado aparece** con la ubicación ausente y **no se omite**, en `backend/apps/red_operativa/tests/services/test_informes_flota_sin_condado.py` (FR-023)
- [X] T023 [P] [US1] Prueba de que la geografía se resuelve en **un número fijo de consultas por página**, independiente del número de filas, en `backend/apps/red_operativa/tests/services/test_informes_flota_catalogo_lotes.py` (research D3)
- [X] T024 [P] [US1] Prueba de contrato en `backend/apps/red_operativa/tests/api/test_informes_flota_contract.py`: envelope conforme al OpenAPI con `acotado_a` y `alcance`, `data: []` con 200 sin filas, `400` con rango de fechas

**Checkpoint**: US1 entregable por sí sola. Es el MVP y fija la distinción de fondo del módulo.

---

## Phase 4: User Story 2 — Seguir las bajas de unidad y su impacto (Priority: P2)

**Goal**: el listado de bajas distinguiendo la ordenada de la que interrumpió una misión.

**Independent Test**: consultar el listado de forma aislada, con y sin rango, sin que existan los
otros tres.

**Criterio medible (ISO 25010 — Functional Completeness)**: el 100 % de las bajas forzadas devuelve
el caso afectado, y el 100 % de las normales lo devuelve ausente (T027).

### Implementación

- [X] T025 [US2] Implementar la consulta de bajas en `backend/core/repositories/red_operativa/informes_baja_repository.py`, con rango de fechas **opcional**, filtros por tipo de baja y proveedor, y cursor compuesto `fechahora|idbajaunidad`
- [X] T026 [US2] Implementar `InformesBajaService` en `backend/apps/red_operativa/services/informes_baja_service.py`: resuelve la placa y el proveedor de la unidad, el nombre de quien ejecutó la baja, y devuelve el **caso afectado** en las forzadas y **ausente** en las normales (research D5), aplicando el acotamiento por proveedor
- [X] T027 [US2] Implementar la vista en `backend/apps/red_operativa/views/informes_baja_views.py` como listado de **hechos del período**, y registrar `/informes/red-operativa/bajas-unidad` en `backend/apps/red_operativa/urls.py`

### Pruebas

- [X] T028 [P] [US2] **Prueba de que la baja forzada trae su caso afectado y la normal no** en `backend/apps/red_operativa/tests/services/test_informes_baja_tipo.py`: con una de cada clase sembradas, los dos filtros devuelven conjuntos disjuntos y el caso llega como ausente en la normal, nunca como cero o cadena vacía (SC-004, research D5)
- [X] T029 [P] [US2] Prueba de rango opcional en `backend/apps/red_operativa/tests/api/test_informes_baja_rango.py`: sin rango devuelve el histórico completo; con rango lo acota
- [X] T030 [P] [US2] Prueba de acotamiento: un proveedor solo ve las bajas de **sus** unidades, en `backend/apps/red_operativa/tests/api/test_informes_baja_acotamiento.py`
- [X] T031 [P] [US2] Pruebas de repositorio en `backend/apps/red_operativa/tests/repositories/test_informes_baja_repository.py`: filtros, orden determinista y cursor compuesto
- [X] T032 [P] [US2] Prueba de contrato en `backend/apps/red_operativa/tests/api/test_informes_baja_contract.py`: envelope conforme al OpenAPI

**Checkpoint**: US2 entregable de forma independiente.

---

## Phase 5: User Story 3 — Supervisar las regiones y su validación (Priority: P3)

**Goal**: el estado de cada región y el historial completo de intentos de validación.

**Independent Test**: consultar los dos listados de forma aislada, sin que existan los de las otras
historias.

**Criterio medible (ISO 25010 — Functional Correctness)**: las regiones `En_Alerta` y
`Despublicada` forman conjuntos disjuntos y ninguna se agrupa con la otra (T036).

### Implementación

- [X] T033 [US3] Implementar la consulta de regiones en `backend/core/repositories/red_operativa/informes_region_repository.py`, exponiendo los **cinco** estados sin agrupar ninguno, con filtro por estado y por antigüedad sin cambio traducida a fecha de corte, y cursor escalar (research D4)
- [X] T034 [US3] Implementar en el mismo repositorio la consulta de **intentos de validación**, conservando **todos** los intentos, con rango opcional, filtros por región y resultado, y cursor compuesto
- [X] T035 [US3] Implementar `InformesRegionService` en `backend/apps/red_operativa/services/informes_region_service.py` con **reloj inyectable** para `dias_sin_cambio`, y resolución del estado geográfico y del ejecutor contra sus catálogos
- [X] T036 [US3] Implementar las dos vistas en `backend/apps/red_operativa/views/informes_region_views.py` —regiones como **estado actual**, validaciones como **hechos del período**— restringidas a Administrador y Director Tecnológico, y registrar sus rutas en `backend/apps/red_operativa/urls.py`

### Pruebas

- [X] T037 [P] [US3] ⚠️ **Prueba de que `En_Alerta` no se agrupa con `Despublicada`** en `backend/apps/red_operativa/tests/repositories/test_informes_region_estados.py`: los dos filtros devuelven conjuntos disjuntos, y la despublicada **sí aparece** en el listado completo (research D4)
- [X] T038 [P] [US3] Prueba de que se conservan **todos** los intentos de validación en `backend/apps/red_operativa/tests/repositories/test_informes_validacion_historial.py`: dos rechazos sobre la misma región producen dos entradas con su motivo, sin que la segunda sustituya a la primera (FR-005)
- [X] T039 [P] [US3] Prueba de `dias_sin_cambio` con **instante inyectado** y del filtro por antigüedad, en `backend/apps/red_operativa/tests/services/test_informes_region_service.py`
- [X] T040 [P] [US3] Prueba de que una Empresa Proveedora recibe **403** en los dos listados, y el Director Tecnológico **200**, en `backend/apps/red_operativa/tests/api/test_informes_region_permisos.py` (FR-012)
- [X] T041 [P] [US3] Pruebas de contrato en `backend/apps/red_operativa/tests/api/test_informes_region_contract.py`: envelope conforme al OpenAPI para ambos listados

**Checkpoint**: los cuatro listados completos.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T042 [P] Prueba de **integridad de la paginación** en `backend/apps/red_operativa/tests/api/test_informes_paginacion_integridad.py`: recorrer un listado por páginas devuelve cada fila exactamente una vez (SC-007)
- [X] T043 [P] Prueba de que `limit` sobre el máximo responde `400` y no se recorta en silencio, en `backend/apps/red_operativa/tests/api/test_informes_limite.py` (FR-020)
- [X] T044 [P] Prueba de rendimiento en `backend/apps/red_operativa/tests/performance/test_informes_latencia.py`: primera página de los cuatro listados por debajo de 2 s, **con una flota de al menos 100 unidades** para que la resolución geográfica por lotes se ponga a prueba de verdad (SC-006)
- [X] T045 Ejecutar `cd backend && python -m pytest -q` completo y verificar que **ninguna suite existente se movió**
- [X] T046 Verificar que la implementación coincide con `contracts/informes-tacticos-simples.openapi.yaml` endpoint por endpoint
- [ ] T047 Recorrer `quickstart.md` de principio a fin contra el stack levantado, con especial atención a §3.2 (alta ≠ disponible), §3.6 (`En_Alerta`) y §3.8 (criterio de pertenencia) — **parcial:** las comprobaciones reproducibles están cubiertas por la suite (§3.2 por `test_informes_flota_alcance.py`, §3.6 por `test_informes_region_estados.py`, §3.8 por `test_acotamiento_criterio.py` y `test_informes_flota_acotamiento.py`). **Falta el recorrido contra Docker levantado**
- [X] T048 Anotar en `decisiones-pendientes.md` que **«pertenecer a una cuenta» tiene dos definiciones incompatibles** en el código operativo —administrador local frente a vínculo— y que conviene decidir si eso es intencional por departamento o una divergencia a unificar
- [X] T049 Documentar el trabajo en `.specify/docs/changelog.md`, actualizar `informestacticos/TSI-Informes-Tacticos-Requeridos-por-OT.md` marcando los listados como 🟢, y **añadir al contrato común** `specs/002-tactico/contrato-informes-simples.md` dos reglas nuevas: que el criterio de pertenencia se declara por listado, y que un listado cuyo alcance pueda malinterpretarse debe declararlo en su propia respuesta

---

## Dependencies

```text
Piloto Cuentas y Clientes, fases 1–2       ← BLOQUEANTE EXTERNO
Ventas y CRM, fase 2 (eje persona)         ← BLOQUEANTE EXTERNO
Suscripciones, fase 2 (eje organización)   ← BLOQUEANTE EXTERNO
    ↓
Phase 1 (Setup + siembra de datos)
    ↓
Phase 2 (Foundational: corrección del criterio) ← BLOQUEANTE
    ↓
    ├─→ Phase 3 (US1, P1) ─┐
    ├─→ Phase 4 (US2, P2) ─┤ independientes entre sí
    └─→ Phase 5 (US3, P3) ─┘
                            ↓
                    Phase 6 (Polish)
```

**Dentro de la fase 1**: T003–T006 son paralelos; T002 conviene primero por condicionar más pruebas.

**Dentro de la fase 2**: T007 primero; T008 y T009 dependen de él; T010 es independiente.
**T011 cierra la fase y es más crítico que en módulos anteriores**, porque aquí se corrige código
compartido en vez de ampliarlo.

**Entre user stories**: ninguna depende de otra. El único fichero compartido es `urls.py`
(T017, T027, T036). US3 usa un solo repositorio para sus dos listados, así que T033 y T034 son
secuenciales entre sí.

---

## Parallel Execution Examples

**Fase 1 — la siembra de datos:**

```text
T003 unidad de alta pero Fuera de servicio
T004 unidad sin condado
T005 baja forzada + baja normal
T006 región En_Alerta + Despublicada + dos rechazos
```

**Fase 3 — todas las pruebas de US1 tras la implementación:**

```text
T018 test_informes_flota_alcance.py
T019 test_informes_flota_sin_geolocalizacion.py
T020 test_informes_flota_acotamiento.py
T021 test_informes_flota_ajena.py
T022 test_informes_flota_sin_condado.py
T023 test_informes_flota_catalogo_lotes.py
T024 test_informes_flota_contract.py
```

**Fase 6 — la batería de cierre:**

```text
T042 test_informes_paginacion_integridad.py
T043 test_informes_limite.py
T044 test_informes_latencia.py
```

---

## Implementation Strategy

### MVP — solo User Story 1

Las fases 1, 2 y 3 entregan **el listado de flota con acotamiento correcto y la distinción entre
existir y estar disponible declarada en la propia respuesta**. Es el corte natural: valida la
corrección del acotamiento antes de que Partners y Soporte construyan encima.

### Entrega incremental

1. **Fases 1–2** — criterio de pertenencia parametrizado y verificado como compatible (T011).
2. **Fase 3 (US1)** — MVP. Composición de flota, sin geolocalización y con alcance declarado.
3. **Fase 4 (US2)** — bajas con su traza de impacto.
4. **Fase 5 (US3)** — regiones y validaciones.
5. **Fase 6** — cierre, divergencia anotada y dos reglas nuevas al contrato común.

### Cuatro riesgos a vigilar

**T011 es más crítico aquí que en cualquier módulo anterior.** Es la primera vez que se **corrige**
la capa transversal en vez de ampliarla. Si alguna suite previa se mueve, la parametrización cambió
el comportamiento por defecto en lugar de añadir una opción, y eso afectaría a Suscripciones en
producción.

**T018 protege contra el defecto de mayor consecuencia de toda la serie.** Un listado de flota
presentado como disponibilidad llevaría a decidir cobertura sobre unidades fuera de servicio,
ocupadas o ya en camino a otro accidente. En los módulos comerciales un error así infla una cifra;
aquí decide si alguien acude.

**T002 hace reales las pruebas de acotamiento.** Con una sola flota poblada, T020 y T021 pasan
aunque el acotamiento no exista.

**T044 debe correr con volumen.** La resolución geográfica por lotes solo se distingue de una
consulta por fila cuando hay suficientes filas: con diez unidades, ambas implementaciones parecen
igual de rápidas.

# Tasks: OE2 — Monetización del Ecosistema de APIs

**Input**: Design documents from `specs/001-estrategico/OE2-monetizacion-api/backend/`

**Prerequisites**: [`plan.md`](plan.md), [`spec.md`](spec.md), [`research.md`](research.md), [`data-model.md`](data-model.md), [`contracts/informes-estrategicos-oe2.openapi.yaml`](contracts/informes-estrategicos-oe2.openapi.yaml), [`quickstart.md`](quickstart.md)

**Tests**: **incluidos y obligatorios.** Constitución ≥80 % en servicios. Sobre estas cifras se
factura: una fuente equivocada o un p95 de 2 llamadas no se nota en un 200.

**Organization**: por user story (US1–US4 de [`spec.md`](spec.md)).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: ficheros distintos, sin dependencias pendientes
- **[US1]–[US4]**: solo en fases de historia. Setup y Foundational no llevan story
- Cada tarea incluye ruta exacta

---

## ⚠️ Lo que distingue a este módulo

**Publica 10 de 11. Cero tablas nuevas.** E2-06 no tiene SQL ni path. E2-01 y E2-02 salen
`cobertura: "parcial"`. E2-08 es **facturable**, no cobrado.

**Un rol partner recibe 403 en las diez.** No es PII: es alcance competitivo.

### Prohibido

| Prohibido | Por qué |
|---|---|
| **Leer un agregado de consumo** | 40 vs 18; se factura el detalle |
| **Publicar E2-06** | El log no mide minutos en silencio → 100 % falso |
| **p95 con muestras < `muestra_minima`** | Con 18 llamadas es el máximo, no un percentil |
| **Sumar 4xx+5xx en un «error total»** | Mezcla fallo del partner con fallo nuestro |
| **Agrupar E2-09 solo por `version`** | `'v1'` no es único entre servicios |
| **Contar altas de credencial en E2-11** | Credencial sin 2xx no es adopción |
| **Ocultar partners no tarificables en E2-08** | El silencio es el fraude que RN-APM-014 prohíbe |
| **Permiso de módulo único** | Finanzas vería latencias o Tecnología vería dinero |

Slugs HTTP (contrato): `integraciones-activas`, `consumo-por-partner`, `latencia-por-endpoint`,
`taxonomia-errores`, `excedente-facturable`, `participacion-ingresos-api`, `mrr-por-linea`,
`adopcion-versiones`, `comparativa-partners`, `crecimiento-ecosistema`. **No** `disponibilidad-api`.

---

## Phase 1: Setup

**Purpose**: comprobar el armazón y crear el sitio del catálogo. Sin esto no hay SQL ni HTTP.

- [x] T001 Verificar que el armazón de `informes_estrategicos` está en pie: `backend/apps/informes_estrategicos/periodo_estrategico.py`, `objetivo.py`, `envelope.py`, `permissions.py`, `core/repositories/informes_estrategicos/`. Si falta, las fases 1–2 de `specs/001-estrategico/OE6-respuesta-y-vidas/backend/tasks.md` son prerrequisito
- [x] T002 Anotar la línea base de ClickHouse en [`quickstart.md`](quickstart.md) §1: `EXISTS TABLE hecho_llamada_api`, `count()` de `hecho_llamada_api` y `dim_partner FINAL` (origen 2026-08-16: 18 / 4)
- [x] T003 Crear `dags/lib/consultas/estrategicos/oe2/README.md` con convención `e2_NN_<informe>.sql`, `FINAL` en dimensiones, **nunca** `FINAL` en `hecho_llamada_api` / `hecho_factura`, y **ningún** `e2_06_*.sql`
- [x] T004 [P] Añadir en `dags/tests/test_catalogo_estrategicos_oe2.py` que el cargador resuelve `departamento="estrategicos/oe2"`
- [x] T005 [P] Registrar `informes-estrategicos/oe2/<str:informe>` en `backend/apps/informes_estrategicos/urls.py` apuntando a `Oe2View` (el import puede quedar en stub hasta T010)

---

## Phase 2: Foundational

**Purpose**: autoridad partida, servicio vacío y 404 de E2-06. **Bloquea las cuatro historias.**

- [x] T006 Añadir `AUTORIDAD_OE2`, `AUTORIDAD_OE2_CONSUMO` (`DirectorTecnologico`, `Gerente`) y `AUTORIDAD_OE2_DINERO` (esas más `DirectorFinanciero`) en `backend/core/auth/roles_tacticos.py`
- [x] T007 Ampliar `backend/apps/informes_estrategicos/permissions.py` con `Oe2Permission` y mapa por slug: las siete de consumo/ecosistema → `AUTORIDAD_OE2_CONSUMO`; `excedente-facturable`, `participacion-ingresos-api`, `mrr-por-linea` → `AUTORIDAD_OE2_DINERO`; slug desconocido/bloqueado → 404 de la vista, no 403
- [x] T008 Implementar `backend/apps/informes_estrategicos/services/oe2_service.py` con `CATALOGO` (10 slugs), `PUBLICADOS`, `BLOQUEADOS={"disponibilidad-api"}` y `DEPARTAMENTO = "estrategicos/oe2"`. Los diez SQL pueden faltar hasta cada US; el servicio no debe listar E2-06
- [x] T009 Implementar `backend/apps/informes_estrategicos/views/oe2_views.py` reutilizando el patrón de `oe4_views.py` (`IsAuthenticated401`, `Oe2Permission`, envelope, 400 de período)
- [x] T010 Completar el import de `Oe2View` en `backend/apps/informes_estrategicos/urls.py`
- [x] T011 [P] Prueba de **exclusión** en `backend/apps/informes_estrategicos/tests/api/test_permisos_oe2.py`: `PartnerIntegracion` → 403 en `consumo-por-partner` **y** en `excedente-facturable`; `DirectorTecnologico` → 403 en `excedente-facturable`; `DirectorFinanciero` → no 403 en esa ruta; `Gerente` entra en ambas familias
- [x] T012 [P] Prueba en `backend/apps/informes_estrategicos/tests/api/test_oe2_bloqueados.py`: `GET .../oe2/disponibilidad-api` → **404** (también con `Gerente`)
- [x] T013 [P] En `dags/tests/test_catalogo_estrategicos_oe2.py`: ninguna consulta nombra hecho/agregado de API distinto de `hecho_llamada_api`; ninguna nombra IP, `client_secret`, hash ni contacto técnico; `SELECT *` prohibido; `ORDER BY` obligatorio; `{desde:Date}` `{hasta:Date}` `{granularidad:String}` presentes; `FINAL` en `dim_partner` / `dim_plan` / `dim_version_contrato`; **nunca** `FINAL` en `hecho_llamada_api`; **cero** ficheros `e2_06_*`

**Checkpoint**: la ruta existe, el partner ya está fuera, E2-06 ya es 404. Las SQL de informes pueden empezar.

---

## Phase 3: User Story 1 — Uso y respuesta de la API (Priority: P1) 🎯 MVP

**Goal**: E2-03, E2-04, E2-05, E2-07. Cuatro GET sobre `hecho_llamada_api` sin cruzar facturación.

**Independent Test**: `consumo-por-partner` de un trimestre cuadra con el total de llamadas del
período; `latencia-por-endpoint` con `muestra_minima=20` deja p95 `null`; un partner con acceso y
cero llamadas está en el denominador de `integraciones-activas` y no en el numerador.

- [x] T014 [P] [US1] Escribir `dags/lib/consultas/estrategicos/oe2/e2_03_integraciones_activas.sql`: numerador = partners con ≥1 llamada en el período; denominador = `dim_partner FINAL` con acceso concedido (no el catálogo entero, no los suspendidos de entrada)
- [x] T015 [P] [US1] Escribir `dags/lib/consultas/estrategicos/oe2/e2_04_consumo_por_partner.sql`: llamadas vs `limite_llamadas_mes`; partners con acceso y cero llamadas **visibles**
- [x] T016 [P] [US1] Escribir `dags/lib/consultas/estrategicos/oe2/e2_05_latencia_por_endpoint.sql`: media, p95, `muestras`, `percentil_fiable`; p95 `NULL` si `muestras < muestra_minima` (defecto 20)
- [x] T017 [P] [US1] Escribir `dags/lib/consultas/estrategicos/oe2/e2_07_taxonomia_errores.sql`: 4xx y 5xx **en filas/columnas separadas**, cada uno con su denominador; sin «error total»
- [x] T018 [US1] Registrar los cuatro slugs y `muestra_minima` en `CATALOGO` / `PARAMETROS` de `backend/apps/informes_estrategicos/services/oe2_service.py`
- [x] T019 [P] [US1] Contrato de los cuatro en `backend/apps/informes_estrategicos/tests/api/test_oe2_us1_contract.py` (período obligatorio, envelope `data`/`meta`, slugs del OpenAPI)
- [x] T020 [P] [US1] Prueba en `backend/apps/informes_estrategicos/tests/api/test_us1_p95_ausente.py`: con `muestra_minima=20` el p95 es nulo; con umbral 1 aparece. Falsable: publicar p95 con 2 muestras debe fallar
- [x] T021 [P] [US1] Prueba en `backend/apps/informes_estrategicos/tests/api/test_us1_4xx_vs_5xx.py`: no existe un total que sume ambas clases
- [x] T022 [P] [US1] Prueba en `backend/apps/informes_estrategicos/tests/api/test_us1_denominador_acceso.py`: credencial sin llamadas cuenta en denominador de E2-03, no en numerador
- [x] T023 [P] [US1] Prueba en `backend/apps/informes_estrategicos/tests/api/test_us1_sin_secretos.py`: ninguna clave de respuesta coincide con IP, hash, `client_secret` ni contacto técnico
- [x] T024 [US1] Recorrer [`quickstart.md`](quickstart.md) §2.1–2.4 contra el stack y anotar cifras medidas

**Checkpoint**: MVP. El ecosistema se ve sin facturar y sin mentir el p95.

---

## Phase 4: User Story 2 — Dinero de la API (Priority: P2)

**Goal**: E2-08 construible; E2-01 y E2-02 parciales. Finanzas entra; Tecnología no.

**Independent Test**: `excedente-facturable` publica llamadas, cupo, precio e importe; `alcance`
niega cobro; los dos de ingresos llevan `cobertura: "parcial"` y `falta` nombra el precio del plan API.

- [x] T025 [P] [US2] Escribir `dags/lib/consultas/estrategicos/oe2/e2_08_excedente_facturable.sql`: `max(0, llamadas − limite) * precio_excedente_llamada` con join `dim_partner.plan_api = dim_plan.nombre`; partners sin match **declarados** (no tarificables), nunca omitidos
- [x] T026 [P] [US2] Escribir `dags/lib/consultas/estrategicos/oe2/e2_01_participacion_ingresos_api.sql`: volumen desde `hecho_llamada_api` + excedente **cobrado** de `hecho_factura` `tipo = 'excedente_api'` si existe; no afirmar mix de ingresos de plan API
- [x] T027 [P] [US2] Escribir `dags/lib/consultas/estrategicos/oe2/e2_02_mrr_por_linea.sql` con la misma regla de cobertura que E2-01
- [x] T028 [US2] Registrar los tres slugs en `backend/apps/informes_estrategicos/services/oe2_service.py` y forzar `meta.alcance` en E2-08 («facturable, no cobrado») y `cobertura: "parcial"` + `falta` en E2-01/E2-02
- [x] T029 [P] [US2] Contrato en `backend/apps/informes_estrategicos/tests/api/test_oe2_us2_contract.py`
- [x] T030 [P] [US2] Prueba en `backend/apps/informes_estrategicos/tests/api/test_us2_alcance_facturable.py`: E2-08 no afirma cobro; componentes llamadas/cupo/precio presentes
- [x] T031 [P] [US2] Prueba en `backend/apps/informes_estrategicos/tests/api/test_us2_parciales.py`: E2-01 y E2-02 responden 200 con `cobertura: "parcial"` y `falta` contiene el precio del plan API
- [x] T032 [P] [US2] Prueba en `backend/apps/informes_estrategicos/tests/api/test_us2_no_tarificables.py`: un partner sin `precio_excedente_llamada` aparece declarado, no desaparece
- [x] T033 [US2] Recorrer [`quickstart.md`](quickstart.md) §2.5, 2.6 y 2.11

**Checkpoint**: US2 independiente. El dinero no se inventa ni se oculta.

---

## Phase 5: User Story 3 — Salud del ecosistema (Priority: P3)

**Goal**: E2-09, E2-10, E2-11. Versión derivada, ceros visibles, primera 2xx.

**Independent Test**: dos servicios con `'v1'` salen **dos** grupos; una credencial del mes sin 2xx
no incrementa `crecimiento-ecosistema`.

- [x] T034 [P] [US3] Escribir `dags/lib/consultas/estrategicos/oe2/e2_09_adopcion_versiones.sql`: `GROUP BY servicio, version_contrato`; exponer `version_es_derivada`; nunca agrupar solo por `version`
- [x] T035 [P] [US3] Escribir `dags/lib/consultas/estrategicos/oe2/e2_10_comparativa_partners.sql`: volumen, error y latencia; partners en cero visibles; identifica organización, no contacto
- [x] T036 [P] [US3] Escribir `dags/lib/consultas/estrategicos/oe2/e2_11_crecimiento_ecosistema.sql`: primera fila 2xx por partner; **no** `hecho_cambio_acceso` ni alta de credencial
- [x] T037 [US3] Registrar los tres slugs en `backend/apps/informes_estrategicos/services/oe2_service.py`
- [x] T038 [P] [US3] Contrato en `backend/apps/informes_estrategicos/tests/api/test_oe2_us3_contract.py`
- [x] T039 [P] [US3] Prueba en `backend/apps/informes_estrategicos/tests/api/test_us3_version_no_unica.py`: dos servicios `'v1'` → dos agrupaciones
- [x] T040 [P] [US3] Prueba en `backend/apps/informes_estrategicos/tests/api/test_us3_crecimiento_primera_2xx.py`: credencial sin llamadas 2xx no cuenta
- [x] T041 [P] [US3] Prueba en `backend/apps/informes_estrategicos/tests/api/test_us3_ceros_visibles.py`: comparativa no omite partners en cero
- [x] T042 [US3] Recorrer [`quickstart.md`](quickstart.md) §2.7–2.8

**Checkpoint**: US3 independiente. El Principio VI (retirar una versión) tiene dato.

---

## Phase 6: User Story 4 — Disponibilidad inmedible (Priority: P4) ⛔

**Goal**: E2-06 declarado, no publicado. El hueco es el entregable.

**Independent Test**: `disponibilidad-api` → 404; el YAML no declara la ruta.

- [x] T043 [US4] Confirmar en `backend/apps/informes_estrategicos/tests/api/test_oe2_bloqueados.py` que `disponibilidad-api` responde 404 (también el alias `disponibilidad-api` si alguien lo registra)
- [x] T044 [P] [US4] En `backend/apps/informes_estrategicos/tests/api/test_openapi_conforme_oe2.py`: los diez `PUBLICADOS` están en `specs/001-estrategico/OE2-monetizacion-api/backend/contracts/informes-estrategicos-oe2.openapi.yaml`; `disponibilidad-api` **no**
- [x] T045 [US4] Actualizar `specs/001-estrategico/OE2-monetizacion-api/OE2-monetizacion-api.md` y `specs/001-estrategico/contrato-informes-estrategicos.md` §10: E2-06 ⛔ sin endpoint; prerrequisito = la misma fuente de monitoreo que E3-01

**Checkpoint**: nadie puede «arreglar» el bloqueado publicándolo vacío.

---

## Phase 7: Polish

- [x] T046 [P] Completar `backend/apps/informes_estrategicos/tests/api/test_openapi_conforme_oe2.py`: YAML sin IP, hash ni contacto; slugs = `CATALOGO`
- [x] T047 [P] Parametrizar `PartnerIntegracion` → 403 en **los diez** slugs en `backend/apps/informes_estrategicos/tests/api/test_permisos_oe2.py`
- [x] T048 [P] Período vacío: los diez devuelven `data: []`, nunca 0 ms ni 0 % de uptime, en `backend/apps/informes_estrategicos/tests/api/test_oe2_periodo_vacio.py`
- [x] T049 [P] Todo porcentaje con denominador en `backend/apps/informes_estrategicos/tests/api/test_oe2_denominadores.py`
- [x] T050 Cobertura ≥80 % de `backend/apps/informes_estrategicos/services/oe2_service.py` y `views/oe2_views.py`
- [x] T051 Recorrer entero [`quickstart.md`](quickstart.md) §2 y anotar cifras medidas
- [x] T052 Escribir `specs/001-estrategico/OE2-monetizacion-api/backend/traceability.md`: FR-OE2-* → tarea → prueba (incl. FR-OE2-019 = 404)
- [x] T053 Actualizar `specs/001-estrategico/contrato-informes-estrategicos.md` §10: OE2 tasks ✅, código al cerrar implement
- [x] T054 Actualizar `specs/001-estrategico/OE2-monetizacion-api/OE2-monetizacion-api.md` capa backend a «tasks listas / implementación»
- [x] T055 Reconstruir contenedores del aplicativo: `docker compose -f docker/accidentes.yml up -d --build django frontend` y verificar `docker ps --filter name=accidentes-` ambos `Up`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (1)**: T001 es puerta (armazón OE6)
- **Foundational (2)**: depende de Setup. **Bloquea US1–US4**
- **US1 (3)**: solo Foundational. **No depende de facturación ni de `dim_plan`**
- **US2 (4)**: Foundational + `dim_plan.precio_excedente_llamada` (ya en DDL). No depende de US1 salvo reutilizar el servicio
- **US3 (5)**: Foundational. Independiente de US1/US2
- **US4 (6)**: Foundational. **Barata: adelantarla tras la fase 2** evita que alguien publique E2-06
- **Polish (7)**: historias entregadas que se quieran cerrar

### User Story Dependencies

- **US1 (P1)**: ninguna otra historia. MVP
- **US2 (P2)**: ninguna respecto de US1; sí usa permiso de dinero de la fase 2
- **US3 (P3)**: ninguna
- **US4 (P4)**: ninguna. Documental + 404

### Parallel Opportunities

- **Fase 1**: T004 y T005 en paralelo
- **Fase 2**: T011, T012, T013 en paralelo tras T009
- **Fase 3**: T014–T017 en paralelo; T019–T023 en paralelo tras T018
- **Fase 4**: T025–T027 en paralelo; T029–T032 en paralelo tras T028
- **Fase 5**: T034–T036 en paralelo; T038–T041 en paralelo tras T037
- **Fase 6**: T044 en paralelo con T043
- **Fase 7**: T046–T049 en paralelo

---

## Parallel Example: Phase 3

```text
Task: "e2_03_integraciones_activas.sql — denominador = acceso concedido"
Task: "e2_04_consumo_por_partner.sql — ceros visibles"
Task: "e2_05_latencia_por_endpoint.sql — p95 NULL bajo muestra_minima"
Task: "e2_07_taxonomia_errores.sql — 4xx y 5xx separados"
```

---

## Implementation Strategy

### MVP primero (solo US1)

1. Fase 1 Setup (T001 puerta)
2. Fase 2 Foundational
3. **Atajo: Fase 6 (US4)** — 3 tareas, deja el 404 antes de que exista tentación
4. Fase 3 US1
5. **PARAR Y VALIDAR**: quickstart 2.1–2.4 y 2.9–2.10
6. Entregar

**El MVP vale solo**: se ve si la API se usa y cómo responde, sin inventar ingresos.

### Incremental

1. Setup + Foundational + US4 → partner fuera, E2-06 muerto
2. US1 → **MVP**
3. US2 → dinero (parcial + facturable)
4. US3 → ecosistema / retiro de versiones
5. Polish + rebuild Docker

### Varias personas

Tras la fase 2: A = US1, B = US2, C = US3. US4 la hace quien cierre Foundational.

---

## Notes

- `[P]` = ficheros distintos, sin dependencias pendientes
- **Ninguna tarea crea tabla ni ALTER**
- Las SQL tácticas `dags/lib/consultas/partners/ot09_*.sql` **no se parametrizan**: OE2 añade ventana comparada, `objetivo` BSC y permiso de Gerente/Finanzas
- Confirmar que las pruebas fallan antes de implementar; las ⚠️ deben ser falsables por mutación
- Parar en cualquier checkpoint
- No commit salvo que lo pidan

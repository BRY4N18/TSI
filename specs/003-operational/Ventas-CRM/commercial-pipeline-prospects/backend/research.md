# Research: Pipeline Comercial y Prospectos

**Feature:** `commercial-pipeline-prospects` · **Date:** 2026-07-25 (rev. 2026-07-26 RF-CPP-000)  
**Inputs:** spec.md (clarificaciones 2026-07-25 + 2026-07-26), constitution.md, architectural-patterns.md, api-standards.md, project-structure.md, testing.md, autenticacion-y-rbac, Suscripciones-Facturación (`Dim_Plan`)

---

## Decision 1 — Validación de secuencia de etapas en servicio

**Decision:** `PipelineService` valida adyacencias hacia adelante (`Nuevo→Contactado→…→Negociación`) y `*→Perdido` en código; rechaza saltos, retrocesos y `Ganado` (solo conversión).

**Rationale:** Máquina de estados fija y pequeña; alineado a Maintainability (testeable con marker `service`) y a architectural-patterns (lógica de dominio en servicio, no en repositorio). Clarificación: sin retrocesos.

**Alternatives considered:**
- Tabla `Dim_TransicionPipelineValida` — rechazada: requiere alterar el modelo canónico de 71 tablas sin necesidad.
- Validar solo en frontend — rechazada: Security / Functional Suitability (bypassable).

---

## Decision 2 — Asignación automática por pool + menor carga

**Decision:** `tipo_organizacion='Público'` → pool `GerenteCuentasPublicas`; `'Privado'` → pool `GerenteVentas`. Elegir el usuario activo con menos prospectos `activo=true` asignados; empate → menor `idusuario`. Pool vacío → no INSERT de asignación; queda huérfano.

**Rationale:** Compatible con RN-CPP-008 y motivo `'carga de trabajo'`. Clarificación: primera asignación de huérfano solo Administrador.

**Alternatives considered:**
- Mapeo 1:1 fijo gerente/tipo — incompatible con múltiples gerentes.
- Round-robin puro — viable pero menos alineado a “carga de trabajo”; menor carga es más explicable en auditoría.

---

## Decision 3 — Contract-first REST + app nueva `ventas_crm`

**Decision:** OpenAPI primero (`contracts/commercial-pipeline-prospects.openapi.yaml`); implementar en `backend/apps/ventas_crm/` y `frontend/src/app/modules/ventas-crm/` (nombres de `project-structure.md`). Base path `/api/v1/ventas-crm/`.

**Rationale:** Constitution Compatibility (API-First); Consistency con tickets/onboarding; módulo aún no existe en el repo.

**Alternatives considered:**
- Meter endpoints en `cuentas_clientes` — rechazado: viola 1 app = 1 módulo de negocio.
- GraphQL — fuera de api-standards.md.

---

## Decision 4 — Kafka-only-write; Pinot read-only

**Decision:** Toda escritura de dominio publica a `{Tabla}_topic`. Lecturas vía repositorios Pinot. Co-escritura de `Dim_Cliente` **reutiliza** `core/repositories/cuentas_clientes/cliente_repository.py` (mismo topic Kafka); no se crea un segundo repository writer en `ventas_crm/`. RF-CPP-000 **no** publica a `Dim_Plan_topic`.

**Rationale:** architectural-patterns.md vinculante; un solo canal de acceso por entidad; insert-only facts para historial auditable. Remediation analyze 2026-07-25 (F1).

**Alternatives considered:**
- Nuevo `cliente_escritura_repository.py` bajo `ventas_crm/` — rechazado: duplica writer de `Dim_Cliente` y arriesga contratos divergentes.
- ORM write-through a Pinot — prohibido por infraestructura del proyecto.

---

## Decision 5 — Roles JWT y ownership

**Decision:** Claims `roles[]` usan strings PascalCase: `Administrador`, `GerenteVentas`, `GerenteCuentasPublicas`, `Sistema`. Ownership = `Dim_Prospecto.idusuario == request.user.idusuario` salvo Admin. Extender seed de `Dim_Rol` en dependencia de autenticacion-y-rbac si faltan roles de ventas/`Sistema`.

**Rationale:** api-authentication + patrón existente (`DirectorTecnologico`, etc.); clarificaciones de dueño estricto y huérfanos.

**Alternatives considered:**
- Roles con espacios (`"Gerente de Ventas"`) — rechazado: inconsistente con seeds.
- Visibilidad por segmento completo — rechazado en clarify (opción B).

---

## Decision 6 — Conversión atómica y único camino a `Ganado`

**Decision:** Un solo servicio `conversion_cliente_service`: valida `Negociación` + ownership/Admin + NIT único + optimistic stage; publica `Fact_Pipeline(Ganado)` + `Dim_Cliente` + update terminal del prospecto. `POST .../pipeline` rechaza `etapa_nueva=Ganado`. `Idempotency-Key` obligatorio.

**Rationale:** Evita prospectos “Ganado” sin cliente; CA-CPP-006/012.

**Alternatives considered:**
- Pipeline a Ganado + job de conversión — ambiguo (eliminado en specify/clarify).

---

## Decision 7 — Optimistic concurrency (RN-CPP-011)

**Decision:** Requests de mutación llevan `etapa_actual_esperada` (pipeline/conversión/pérdida) o `idusuario_esperado` (reasignación). Si no coincide con Pinot vigente → HTTP 409, sin publicar a Kafka.

**Rationale:** Clarificación Session 2026-07-25; Reliability sin locks distribuidos.

**Alternatives considered:**
- Last-write-wins — historial incoherente.
- Lock pesimista — complejidad operativa innecesaria para volumen CRM.

---

## Decision 8 — Rate limit registro público

**Decision:** Throttle DRF dedicado 10 req/min por IP en `POST /prospectos` (además del throttling por rol en endpoints autenticados). `GET /planes` no hereda ese throttle de escritura; rate limit de lectura defensivo opcional sin cambiar semántica.

**Rationale:** RNF-CPP-002 / assumption del spec; protege endpoint sin JWT.

**Alternatives considered:**
- Captcha — fuera de alcance actual; puede añadirse después sin romper contrato si se mantiene el throttle.

---

## Decision 9 — Frontend: guards + servicios tipados (sin NgRx obligatorio)

**Decision:** Lazy module `ventas-crm`; guards funcionales Angular en rutas autenticadas; servicios HTTP tipados alineados al OpenAPI; estado local con signals donde baste. NgRx solo si el board de pipeline crece. Portal de planes = ruta **pública** sin guard JWT.

**Rationale:** angular-architect + typescript-expert; Maintainability (menos boilerplate); patrones de módulos existentes (`soporte-cliente`, `cuentas-clientes`).

**Alternatives considered:**
- NgRx desde el día 1 — overkill para CRUD + board simple.

---

## Decision 10 — Portal público de planes (RF-CPP-000) — lectura `Dim_Plan`

> **Corrección 2026-08-08:** el punto 4 original (mapa cerrado `nivel` → severidades) queda **obsoleto**. `severidades_desbloqueadas` es un campo independiente en `Dim_Plan`, configurable libremente por el Director de Estrategia (RN-SUSF-002 corregida) — este servicio solo lo lee y parsea, ya no lo deriva de `nivel`. Ver `_parse_severidades()` en `consulta_planes_publicos_service.py`.

**Decision:**
1. Endpoint `GET /api/v1/ventas-crm/planes` con `security: []` (AllowAny / sin JWT).
2. Repositorio **solo lectura** Pinot sobre `Dim_Plan` filtrando `activo=true`. Preferir reutilizar un `PlanRepository` de Suscripciones-Facturación si existe; si no, `core/repositories/ventas_crm/plan_lectura_repository.py` **sin** `publish`/Kafka.
3. Servicio `ConsultaPlanesPublicosService` proyecta: `idplan`, `nombre`, `precio`, `limites` (STRING canónico del esquema; el API puede parsear JSON si el contenido es JSON-object serializado, si no devolver string), `nivel`, y `severidades_desbloqueadas` (parseada de `Dim_Plan.severidades_desbloqueadas`, campo independiente — ver corrección arriba).
4. ~~Mapa cerrado `nivel` → severidades~~ — **obsoleto, ver corrección arriba.** `severidades_desbloqueadas` ausente o no-JSON → lista vacía y se **incluye** el plan (Functional Suitability: no ocultar precio/nombre); log/warning en servicio.
5. Alias documental **CU-O123**: ID canónico a definir en `module-map.md`; no inventar O-number oficial aquí.
6. El Visitante no selecciona plan en RF-CPP-001 (fuera de alcance del embudo); CTA UI hacia registro es navegación, no escritura de `idplan`.

**Rationale:** Spec Session 2026-07-26 — precondición del embudo, cero escrituras, ownership de `Dim_Plan` en Suscripciones. Maintainability: mapa en servicio testeable (`unit`/`service`). Compatibility: no usurpar `Dim_Plan_topic`.

**Alternatives considered:**
- Proxy HTTP al módulo Suscripciones — rechazado: acoplamiento runtime innecesario; Pinot ya es la fuente de lectura.
- Exponer planes inactivos a Admin en el mismo endpoint — rechazado: este endpoint es solo Visitante; Admin gestiona en Suscripciones.
- Duplicar catálogo en `Dim_Prospecto` / tabla CRM — rechazado: viola single source of truth.
- Forzar selección de plan en registro — excluido explícitamente en spec §15.

---

## Tie-Breaker closure

Conflictos Evaluate: **Maintainability** vs **Functional Suitability** en (1) catálogo de transiciones, (2) algoritmo de pool, (3) mapa nivel→severidades — Safety no aplica. Se prioriza Maintainability + Functional Suitability (reglas en servicio, sin schema nuevo). Documentado aquí; plan Constitution Check → PASS.

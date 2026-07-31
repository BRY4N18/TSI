# Phase 0 Research — Suscripciones y Facturación

## Decision 1: Contract-first OpenAPI bajo `/api/v1/suscripciones`

- **Decision:** Definir primero `contracts/subscriptions-and-billing.openapi.yaml` con endpoints HTTP para RF-SUSF-001…003, 006, 009, 010 y acciones de regularización; RF-004/005/007/008 (batch/dunning/renovación/mora automática) como **jobs** sin endpoint público (invocables solo por scheduler interno).
- **Rationale:** Principio VI (Compatibility API-First) + `api-standards.md`; mismo orden que `gestion-tickets-soporte` / `despacho-inteligente`.
- **Alternatives considered:** Exponer “trigger facturación” como POST admin (rechazado: spec define cron 02:00–05:00 Guayaquil; evita abuso y doble emisión).

## Decision 2: Django capas Vista → Servicio → Repositorio en `apps/suscripciones/`

- **Decision:** App `apps/suscripciones/` con views delgadas DRF, **un servicio por caso de uso** (ver `plan.md`), permisos en `permissions.py`, repositorios en `core/repositories/suscripciones/`. Skills: `django-expert`.
- **Rationale:** `architectural-patterns.md` §1–2 (SRP, DI, Kafka-only-write).
- **Alternatives considered:** `BillingService` monolítico (rechazado: viola SRP).

## Decision 3: Escritura exclusiva vía Kafka

- **Decision:** Toda mutación de `Dim_Plan`, `Dim_MetodoPago`, `Fact_Suscripcion`, `Fact_Factura`, `Fact_Solicitud_Cambio_Plan` (y patch denormalizado `Dim_Cliente.plan_suscripcion`) publica a `{Tabla}_topic` con registro completo + `fecha_actualizacion`. Lectura solo Pinot Broker.
- **Rationale:** Regla vinculante `infrastructure.md` §4 / `architectural-patterns.md` §1.
- **Alternatives considered:** Ninguna.

## Decision 4: JWT Bearer + RBAC (`api-authentication`)

- **Decision:** Reutilizar autenticación JWT RS256 del módulo Cuentas (`Authorization: Bearer`). Permisos DRF:
  - **Proveedor** (actor de `Dim_Cliente` / admin local de cuenta): operar solo su `idcliente` (RNF-SUSF-002).
  - **Director de Estrategia** (`DirectorEstrategia`): catálogo planes RF-SUSF-001.
  - **Administrador**: aprobar/rechazar downgrades, leer facturas de cualquier cliente (sin CRUD `Dim_Plan`).
  - **Sistema** (credencial de job): no expuesta por HTTP; jobs usan service account interna como en despacho.
- **Rationale:** Dependencia `autenticacion-y-rbac`; Security by Design (Principio V).
- **Alternatives considered:** API keys para jobs HTTP (rechazado: no hay endpoints de job).

## Decision 5: Adaptador de pasarela simulada

- **Decision:** Puerto `PasarelaPagoPort` en `apps/suscripciones/services/pasarela/` con implementación `SimuladorPasarela` (RN-SUSF-024: éxito default; `BILLING_SIMULATOR_FAIL_RATE`; `force_fail` en tests). Claves de idempotencia `{id_factura}-{reintentos}` y `{id_factura}-reactivacion-{idmetodopago}`.
- **Rationale:** RNF-SUSF-008 / Flexibility; evita acoplar Stripe real (fuera de alcance v1).
- **Alternatives considered:** Llamadas HTTP reales a sandbox Stripe en v1 (rechazado: §13 fuera de alcance).

## Decision 6: Zona horaria y jobs

- **Decision:** Toda lógica de corte usa `zoneinfo.ZoneInfo("America/Guayaquil")`. Cuatro jobs en ventana 02:00–05:00: facturación mensual, dunning (días 3/7), renovación, mantenimiento `activo=false` post-cancelación vencida. Notificación de renovación −3 días vía job diario ligero o el mismo `renovacion_job` en modo “preview”.
- **Rationale:** Spec §0.6 / RN-SUSF-008 / RN-SUSF-020.
- **Alternatives considered:** UTC puro (rechazado: reglas de negocio fijan Guayaquil).

## Decision 7: Numeración de factura (RN-SUSF-026)

- **Decision:** `id_factura` = UUID string; `numero_factura` = `FAC-{YYYYMM}-{seq8}` con `seq = max(seq Pinot del periodo)+1` y reintento ante colisión de publicación.
- **Rationale:** Sin BD transaccional; Pinot+retry es el patrón viable bajo Kafka-only-write.
- **Alternatives considered:** Redis INCR (rechazado: nueva dependencia de infra no pedida); UUID truncado como número (rechazado: no legible/operable para soporte).

## Decision 8: Casing de estados Title Case (alineación con fixtures legacy)

- **Decision:** Canon normativo del módulo = Title Case español (`Activa`, `Suspendida`, `Cancelada`, `Pendiente`, `Pagada`, `Fallida`, `Aprobada`, `Rechazada`). Lectores existentes (p. ej. soporte que filtra `estado='activa'`) se actualizarán en tareas de convergencia a aceptar el canon o normalizar en repositorio de lectura compartido.
- **Rationale:** Spec §0.4; evita ambigüedad en contract tests.
- **Alternatives considered:** Mantener lowercase legacy (rechazado: contradice clarify ya cerrada).

## Decision 9: Sync `Dim_Cliente.plan_suscripcion` y gate de acceso

- **Decision:** Escritura obligatoria del `nombre` del plan en alta y en cambio aprobado. `EvaluacionAccesoService` implementa RN-SUSF-017 y queda disponible para otros módulos vía `core/` solo si más de un módulo lo necesita en el mismo release; v1 vive en `apps/suscripciones/services/` y Soporte sigue leyendo `Fact_Suscripcion` por repositorio.
- **Rationale:** Spec RF-010 / RF-003; evita god-import entre apps.
- **Alternatives considered:** Duplicar regla de acceso en cada módulo (rechazado: Maintainability).

## Decision 10: Angular — servicios tipados + guards (`angular-architect`, `typescript-expert`)

- **Decision:** Módulo lazy `modules/suscripciones/` con API services tipados desde OpenAPI; guards `ProveedorBillingGuard` / `AdminBillingGuard` / `DirectorEstrategiaBillingGuard`; componentes OnPush sin lógica de dominio; interceptor JWT existente. Redirect de `/suscripciones` por rol (Proveedor→mi-suscripcion, Admin→aprobaciones, Director→catálogo).
- **Rationale:** Mismo patrón que soporte/despacho; Interaction Capability RNF-006; Session 2026-07-30 evita que Admin caiga en ruta Proveedor.
- **Alternatives considered:** Un solo `BillingService` frontend (rechazado: acoplamiento); Admin retiene CRUD planes en UI (rechazado: contradice `actors.md`).

## Decision 11: Throttling + Idempotency-Key HTTP

- **Decision:** Throttling DRF por usuario alineado a `api-standards.md` (~60 req/min Proveedor en escrituras de método de pago / cambio plan; ~100 req/min Admin y Director en sus mutaciones). Toda escritura REST exige header `Idempotency-Key`. Tasks: T086–T089. Jobs no pasan por throttle HTTP.
- **Rationale:** Estándar de API del proyecto; cierra gaps C2/C3 del analyze.
- **Alternatives considered:** Sin throttle / sin Idempotency-Key (rechazado: abuso de tokenización y doble submit).

## Decision 12: Actor RF-SUSF-001 = Director de Estrategia (enmienda 2026-07-30)

- **Decision:**
  - Rol JWT canónico: `DirectorEstrategia` (mismo estilo que `DirectorTecnologico`).
  - `POST/PATCH /suscripciones/planes*` → solo `IsDirectorEstrategiaBilling`.
  - `GET /suscripciones/planes` → Proveedor, Administrador o Director (consulta catálogo activo).
  - Administrador: downgrade + facturas; **403** en mutación de planes.
  - Seed demo: usuario + `Dim_Rol` vía Kafka (payloads LONG ms / shape Pinot) — T092.
  - UI: formulario crear/editar/desactivar visible solo a Director — T094.
  - Pricing dinámico regional **fuera de v1** (solo campos actuales de `Dim_Plan`).
- **Rationale:** `actors.md` operativo; cierra gap analyze I1/C1; Security (Principio V) con least privilege sobre catálogo comercial.
- **Alternatives considered:** Mantener Admin en CRUD (rechazado: instrucción de producto); rol `GerenteVentas` (rechazado: CRM no es dueño de `Dim_Plan`); dual Admin|Director en POST (rechazado: diluye separación de actores).

## Decision 13: Listado `Dim_Plan` — cursor + filtros en origen (enmienda 2026-07-30)

- **Decision:**
  - `GET /suscripciones/planes` usa **cursor** = último `idplan` de la página (entero), `limit` default **20** (max **100**).
  - Filtros: `q` (substring case-insensitive sobre `nombre`), `activo` (bool; omitido = todas si Director, else forzar true para no-Director), `nivel` (enum o omitido).
  - Compat: `solo_activos=true|false` se mapea a `activo` si `activo` no viene explícito.
  - Respuesta: `data: Plan[]` (página) + `meta.pagination.{next_cursor, limit}` (`next_cursor=null` si no hay más).
  - **Repo:** consulta Pinot con `WHERE` aplicables + `idplan > cursor` + `ORDER BY idplan ASC` + `LIMIT limit+1` (el +1 detecta siguiente página). **Prohibido** `SELECT * FROM Dim_Plan` sin tope y filtrar el universo en Python.
  - Si Pinot no soporta un predicado (p. ej. LIKE frágil): proyectar columnas de lista con `LIMIT` alto acotado (p. ej. 500) **solo** como fallback documentado en tests; preferir predicados nativos. Nunca “todas las filas sin LIMIT”.
  - Lectura puntual: `find_by_id` (detalle/form); no sustituye al listado.
- **Rationale:** RNF-SUSF-005a / RN-SUSF-001a / api-standards; cierra anti-patrón dump→slice; alinea a Alta unidades.
- **Alternatives considered:**
  - Paginación solo en Angular sobre dump (rechazado: mismo anti-patrón en cliente; incumple CA-016).
  - Offset `page=N` (rechazado: estándar del proyecto es cursor).
  - Mantener dump “porque hay pocos planes” (rechazado: spec prohíbe explícitamente; Pinot default LIMIT 10 ya rompe dumps implícitos).

## Tie-breaker (constitution)

Conflicto menor: **Maintainability** (adaptador + muchos servicios pequeños) vs velocidad de entrega. Safety no aplica → ganan Maintainability + Functional Suitability. Trade-off: más archivos de servicio, menor riesgo de monolito ilegible.

## Cierre Phase 0

Todas las entradas NEEDS CLARIFICATION del Technical Context quedan resueltas (incl. actor RF-001 Session 2026-07-30 y **listado paginado Decision 13**). No quedan blockers de diseño para el delta de listado planes.
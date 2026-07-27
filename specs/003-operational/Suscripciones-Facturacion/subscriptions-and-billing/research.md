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
  - **Administrador**: catálogo planes, aprobar/rechazar downgrades, leer facturas de cualquier cliente.
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

- **Decision:** Módulo lazy `modules/suscripciones/` con API services tipados desde OpenAPI, guards `ProveedorBillingGuard` / `AdminBillingGuard`, componentes OnPush sin lógica de dominio, interceptor JWT existente.
- **Rationale:** Mismo patrón que soporte/despacho; Interaction Capability RNF-006.
- **Alternatives considered:** Un solo `BillingService` frontend (rechazado: acoplamiento).

## Decision 11: Throttling + Idempotency-Key HTTP

- **Decision:** Throttling DRF por usuario alineado a `api-standards.md` (~60 req/min Proveedor en escrituras de método de pago / cambio plan; ~100 req/min Admin). Toda escritura REST exige header `Idempotency-Key`. Tasks: T086–T089. Jobs no pasan por throttle HTTP.
- **Rationale:** Estándar de API del proyecto; cierra gaps C2/C3 del analyze.
- **Alternatives considered:** Sin throttle / sin Idempotency-Key (rechazado: abuso de tokenización y doble submit).

## Tie-breaker (constitution)

Conflicto menor: **Maintainability** (adaptador + muchos servicios pequeños) vs velocidad de entrega. Safety no aplica → ganan Maintainability + Functional Suitability. Trade-off: más archivos de servicio, menor riesgo de monolito ilegible.

## Cierre Phase 0

Todas las entradas NEEDS CLARIFICATION del Technical Context quedan resueltas. No quedan blockers para Phase 1.

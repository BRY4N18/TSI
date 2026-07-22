# Phase 0 Research — Gestión de Tickets de Soporte

## Decision 1: Contract-first OpenAPI bajo `/api/v1/soporte`

- **Decision:** Definir primero `contracts/gestion-tickets-soporte.openapi.yaml` con endpoints HTTP para CU-O91, O92, O95, O97 (registro, transiciones, configuración SLA, reapertura); CU-O96 (monitoreo/escalado SLA) se documenta como job de fondo sin endpoint público (solo lectura vía dashboard RF-TIC-007).
- **Rationale:** Cumple constitution (Principio VI, Compatibility API-First) y el orden ya usado en `despacho-inteligente`: contrato REST → Django → Angular.
- **Alternatives considered:**
  - Exponer el job O96 como endpoint invocable manualmente (rechazado: el spec lo define como job programado autónomo, no una acción de usuario).

## Decision 2: Django capas Vista → Servicio → Repositorio en `apps/soporte_cliente/`

- **Decision:** Nueva app `apps/soporte_cliente/` (ya prevista en `project-structure.md` y `module-map.md`) con views delgadas, servicios por caso de uso (`RegistrarTicketService`, `ClasificacionAutomaticaService`, `AsignacionSLAService`, `TomarTicketService`, `ComentarTicketService`, `EscalarTicketService`, `ResolverTicketService`, `ConfirmarCierreService`, `ConfigurarSLAService`, `MonitoreoSLAService`, `ReabrirTicketService`, `DashboardSoporteService`) y repositorios en `core/repositories/soporte/`.
- **Rationale:** `architectural-patterns.md` es vinculante (Vista→Servicio→Repositorio, SRP); `project-structure.md` ya reserva `apps/soporte_cliente/` como app CRUD sin `queries.py` (no tiene lecturas complejas tipo Haversine).
- **Alternatives considered:**
  - Un único `TicketService` monolítico con todos los métodos (rechazado: viola SRP de `architectural-patterns.md`, igual que se evitó en `despacho-inteligente`).

## Decision 3: Escritura exclusiva vía Kafka (sin INSERT/UPDATE directo a Pinot)

- **Decision:** Toda mutación de `Fact_Reclamo`, `Fact_Historial_Ticket`, `Dim_SLAConfig`, `Fact_ArchivosAdjuntosReclamos` publica al topic `{Tabla}_topic`. Ninguna lectura de `Fact_Reclamo.estado`/`idestadosoporte` se resuelve con INSERT directo — sigue el patrón repositorio ya usado en `despacho-inteligente` y `registro-accidente`.
- **Rationale:** Regla vinculante de `infrastructure.md` sección 4 / `architectural-patterns.md` sección 1.
- **Alternatives considered:** Ninguna — regla no negociable del proyecto.

## Decision 4: Clasificación automática de `tipo_incidencia` y `prioridad` (RF-TIC-001)

- **Decision:** `ClasificacionAutomaticaService` aplica reglas en este orden:
  1. Si el ticket referencia un `idaccidente` con `Fact_AccidenteTipoEstadoAccidente` activo (no Cerrado/Descartado) → `prioridad='crítico'`, `tipo_incidencia='emergencia_activa'`.
  2. Si no, evalúa keywords en `asunto`/`descripcion` contra un mapping configurable (`tipo` del formulario + palabras clave: "no responde", "error 500", "caído" → `tipo_incidencia='tecnica'`; "acceso", "login", "contraseña" → `tipo_incidencia='acceso'`; "cómo", "duda", "consulta" → `tipo_incidencia='consulta_funcional'`).
  3. Si ninguna regla coincide → no clasificable, `idestadosoporte=Pendiente_de_clasificacion`, `idslaconfig=NULL` (RF-TIC-001 paso 4, RN-TIC-003).
  - `prioridad` (fuera del caso crítico) se deriva de `tipo_incidencia` + `idplan` del cliente: mapping configurable, análogo a `Dim_ParametrosDespacho` pero embebido como reglas de servicio en esta primera versión (no hay CU de configuración de reglas de clasificación en el spec, solo de SLA vía CU-O95).
- **Rationale:** Mismo patrón que `despacho-inteligente` Decision 9 (severidad por keywords, sin NLP/ML) — resuelve la ambigüedad sin sobre-diseñar; el spec solo exige "reglas predefinidas", no un motor de reglas configurable.
- **Alternatives considered:**
  - Motor de reglas configurable en BD (rechazado: no hay CU ni tabla que lo respalde; fuera de alcance según `## 13. Fuera de alcance` del spec, que no lo menciona pero tampoco lo requiere).
  - Clasificación manual siempre (rechazado: rompe RF-TIC-001 que exige clasificación automática como camino principal).

## Decision 5: Resolución de `idplan` del cliente para lookup de SLA

- **Decision:** `AsignacionSLAService` resuelve `idplan` desde la suscripción activa del cliente: `Fact_Suscripcion` con `idcliente` dado y `estado='activa'`/`activo=true` (más reciente por `fecha_inicio` si hubiera más de una), no desde `Dim_Cliente.plan_suscripcion` (campo `STRING` denormalizado de solo referencia rápida, no fuente de verdad transaccional).
- **Rationale:** `Fact_Suscripcion` es la tabla de hechos del módulo `billing-and-auto-renewal` (dependencia declarada en `## 12. Dependencias` del spec); es la fuente correcta para saber el plan vigente, evitando inconsistencia si `Dim_Cliente.plan_suscripcion` queda desactualizado.
- **Alternatives considered:**
  - Leer directo `Dim_Cliente.plan_suscripcion` (rechazado: es un campo STRING de conveniencia, no normalizado a `idplan`, y puede quedar desactualizado frente a cambios de plan).

## Decision 6: Escalado automático a "Supervisor de Soporte" (RN-TIC-005, clarificación)

- **Decision:** Se agrega un rol fijo `Supervisor de Soporte` (extensión de roles de `autenticacion-y-rbac`, `Dim_Rol`) con exactamente un usuario configurado como responsable por defecto (sin tabla de turnos). `MonitoreoSLAService` resuelve este usuario vía `core/repositories/soporte/supervisor_soporte_repository.py` (lookup simple, no round-robin).
- **Rationale:** Clarificación Session 2026-07-21; evita construir gestión de turnos no solicitada por ningún CU.
- **Alternatives considered:**
  - Tabla de turnos nueva (rechazado en clarify — fuera de alcance de este ciclo).

## Decision 7: Frecuencia del job de monitoreo SLA (RNF-TIC-001, clarificación)

- **Decision:** Job programado (Celery beat o APScheduler, mismo mecanismo que `timeout_despacho_job` de `despacho-inteligente`) cada 1 minuto; evalúa `sla_primera_respuesta` y `sla_resolucion` de forma independiente (clarificación Session 2026-07-21).
- **Rationale:** Clarificación de sesión; consistente con el patrón de jobs ya usado en el proyecto.
- **Alternatives considered:** 30s (rechazado: SLA se mide en horas, no aporta margen de reacción adicional relevante frente al costo de más ejecuciones) — 5 min (rechazado: demasiado margen de retraso en el umbral del 80%).

## Decision 8: Renovación de SLA al reabrir (RF-TIC-005, clarificación)

- **Decision:** `ReabrirTicketService` reutiliza `AsignacionSLAService` (Decision 5) para recalcular `idslaconfig`/`sla_primera_respuesta`/`sla_resolucion` contra la configuración vigente actual, en vez de conservar los valores originales.
- **Rationale:** Clarificación Session 2026-07-21.
- **Alternatives considered:** Conservar el `idslaconfig` original (rechazado en clarify).

## Decision 9: JWT + RBAC (skills `api-authentication`, `django-expert`)

- **Decision:** Bearer JWT RS256 en todos los endpoints; permisos DRF nuevos en `apps/soporte_cliente/permissions.py`:
  - `Cliente` → registrar/ver sus propios tickets, comentar, confirmar cierre, reabrir.
  - `Soporte al cliente` (agente) → tomar, comentar (incl. notas internas), escalar, resolver.
  - `Desarrollador de APIs` / `Director Tecnológico` → recibir y gestionar tickets escalados a su nivel.
  - `Administrador` → configurar `Dim_SLAConfig` (CU-O95), ver dashboard completo.
  - `Sistema` (rol de servicio) → ejecución del job O96, igual patrón que consumers/jobs internos de `despacho-inteligente`.
- **Rationale:** Dependencia `autenticacion-y-rbac`; RN-TIC-002 exige que notas internas nunca sean visibles al cliente — se aplica a nivel de serializer/vista, filtrando `es_nota_interna=true` para el rol `Cliente`.
- **Alternatives considered:** Filtrar notas internas solo en el frontend (rechazado: viola Principio V, Security by Design — debe validarse en servidor).

## Decision 10: Angular — servicios tipados + guards (skills `angular-architect`, `typescript-expert`)

- **Decision:** Módulo `frontend/src/app/modules/soporte-cliente/` con:
  - `TicketApiService` (registro, transiciones, dashboard), `SlaConfigApiService` (CU-O95), tipos en `models/soporte.types.ts` alineados al OpenAPI.
  - `ClienteSoporteGuard`, `AgenteSoporteGuard`, `AdministradorSlaGuard`.
  - Rutas lazy `soporte-cliente.routes.ts`; componentes sin lógica de dominio.
- **Rationale:** Mismo patrón que `despacho/` en `project-structure.md`.
- **Alternatives considered:** Servicio único `SoporteService` para todo (rechazado: acoplamiento, igual criterio que en despacho Decision 10).

## Tie-Breaker (constitution)

- **Conflicto:** Functional Suitability (clasificación automática rica, RF-TIC-001) vs Maintainability (evitar sobre-ingeniería de un motor de reglas no solicitado).
- **Prioridad:** Maintainability y Functional Suitability empatan por defecto (Principio VII); se resuelve a favor de la solución más simple que cumple el requisito literal del spec (reglas por keyword, ver Decision 4) — no hay conflicto de Safety, por lo que no aplica la prioridad absoluta de Principio IX.
- **Nota:** Este módulo no toca el camino crítico de despacho (Principio Additional Constraints); Safety no es un factor determinante aquí, a diferencia de `despacho-inteligente`.

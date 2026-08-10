# Specification Quality Checklist: Monitoreo y Facturación de API

**Purpose**: Validate specification completeness and quality before proceeding to planning  
**Created**: 2026-08-08  
**Feature**: [spec.md](../spec.md)  
**CUs**: CU-O51, CU-O52, CU-O53, CU-O54

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

> Misma nota que el módulo hermano: la capa `backend/` es, por definición del índice del módulo, la autoridad de dominio, API y modelo de datos, así que nombrar tablas Pinot y códigos HTTP es deliberado. No hay fuga de framework, lenguaje ni estructura de código.

## Requirement Completeness

- [x] **No [NEEDS CLARIFICATION] markers remain** — ambas resueltas y **aplicadas** 2026-08-08: D1 (`Dim_Plan.precio_excedente_llamada`) y D2 (throttle técnico separado del cupo comercial). Ver § 15.
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic
- [x] All acceptance scenarios are defined — 12 escenarios (A–L), 16 criterios de aceptación
- [x] Edge cases are identified — credencial revocada (B), partner suspendido (C), sin zonas (D), cuota superada (E), error de integración (F), mezcla de entornos (G), reintento duplicado (I), reintentos agotados (J), factura en disputa (K), fallo de medición (L)
- [x] Scope is clearly bounded — § 13 reparte propiedad frente a #07, #09, Suscripciones y Soporte
- [x] Dependencies and assumptions identified — § 12 y § 14

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] **Feature meets measurable outcomes** — CU-O54 ya es completable: la tarifa existe en `Dim_Plan.precio_excedente_llamada`, está poblada en los 5 planes y es editable por el Director de Estrategia
- [x] No implementation details leak into specification

## Constitution Compliance (Golden Rule)

- [x] Las 9 características ISO/IEC 25010:2023 declaradas explícitamente — § 5.1
- [x] Las no aplicables justifican por qué — **Safety: no aplica** (fuera de la cadena crítica; la API es de solo lectura sobre casos ya cerrados)
- [x] Al menos un criterio medible por sub-característica — CA-APM-016 (Performance/temporal), CA-APM-001 (Security/autenticidad), CA-APM-003 (Security/confidencialidad), CA-APM-013 (Reliability/tolerancia a fallos), CA-APM-012 (Functional/corrección)
- [x] Tie-Breaker invocado y documentado — Reliability vs Functional Suitability en RF-APM-004 (el fallo de medición no tumba la API), con trade-off explícito
- [x] Trazabilidad obligatoria a CU documentado — CU-O51/O52/O53/O54 del catálogo canónico

## Trazabilidad al catálogo canónico

| RF del catálogo | Cubierto por | Estado |
|---|---|---|
| RF-O51.1 Entregar solo los conjuntos habilitados por el nivel de acceso | RF-APM-002 | ✅ |
| RF-O51.2 Rechazar credencial inválida, revocada o vencida | RF-APM-001, RN-APM-007 | ✅ |
| RF-O51.3 Filtrar por zonas geográficas contratadas | RF-APM-003, RN-APM-008 | ✅ |
| RF-O52.1 Contabilizar cada petición con momento y volumen | RF-APM-004 | ✅ |
| RF-O52.2 Acumular consumo por partner y período | RF-APM-009, RF-APM-010 | ✅ |
| RF-O52.3 Conservar el detalle como respaldo de la tarificación | RF-APM-004, RNF-APM-005 | ✅ |
| RF-O53.1 Comparar consumo acumulado contra el límite | RF-APM-010 | ✅ |
| RF-O53.2 Restringir o degradar al superarse el límite | RN-APM-002, § 15 D2 | ⚠️ **divergencia deliberada** — el cupo comercial no bloquea (SRS RN-11 manda); la tasa por minuto sí devuelve 429, pero como protección de plataforma, no como aplicación de cuota |
| RF-O53.3 Notificar al aproximarse y al alcanzar el límite | RF-APM-010, RN-APM-010 | ✅ |
| RF-O54.1 Calcular el importe según la tarifa vigente del plan | RF-APM-011, § 15 D1 | ✅ `Dim_Plan.precio_excedente_llamada` aplicada y verificada |
| RF-O54.2 Separar consumo incluido de excedente | RF-APM-011, RN-APM-011 | ✅ |
| RF-O54.3 Verificar que no exista ya factura de excedente | RF-APM-012, RN-APM-012 | ✅ |
| RF-O54.4 Reintentar escalonadamente y dejar pendiente con alerta | RF-APM-013, RN-APM-013 | ✅ |

**12/13 RF cubiertos sin reservas.** El único con reserva es RF-O53.2, divergencia documentada a favor del SRS (§ 15 D2).

## Cobertura del SRS §3.4.2

Los párrafos normativos de L390–L424 están cubiertos: L396 → RF-APM-004, RN-APM-003 · L398 → RF-APM-005, RN-APM-006 · L400 → RF-APM-007 · L402 → RF-APM-006, RN-APM-001 · L404 → RF-APM-008, RF-APM-010 · L406 → RN-APM-002 · L408 → RF-APM-011, RN-APM-011 · L410 → RF-APM-008, RN-APM-009 · L412 → RF-APM-011 · L414 → RF-APM-013, RN-APM-013 · L416 → RF-APM-012, RN-APM-012 · L418 → RN-APM-014 · L420–L424 → **fuera de alcance** (disputas, dueño = Soporte CU-O83).

## Dependencias externas

| Cambio | Módulo | Bloquea | Estado |
|---|---|---|---|
| `Fact_Factura.tipo` (`suscripcion` \| `excedente_api`) | `subscriptions-and-billing` | RF-APM-012 | ✅ aplicado y verificado (#17) |
| `Fact_Reclamo.idfactura` STRING | `gestion-tickets-soporte` | RN-APM-016 | ✅ aplicado y verificado (#17) |
| Cupo congelado en `Dim_Partner` | `partner-api-onboarding` | RF-APM-010, RF-APM-011 | ✅ especificado (#07) |
| `Dim_Preferencias_Cliente.zonas_geograficas` | `incorporacion-clientes` | RF-APM-003 | ✅ ya existe y en uso por Seguimiento |
| `Dim_Plan.precio_excedente_llamada` (DOUBLE, centinela `-1.0`) | `subscriptions-and-billing` | RF-APM-011 / CU-O54 | ✅ **aplicado y verificado** — validado en backend, editable en el formulario de plan, 5 planes migrados |
| Siembra de `Dim_EstadoIntegracion` | este módulo | RF-APM-005 | ⏳ tabla vacía (0 filas), se siembra aquí |
| Rol `PartnerIntegracion` | `autenticacion-y-rbac` | RF-APM-007 | ✅ creado (#19) |

## Riesgos detectados en la especificación

| Riesgo | Dónde se aborda |
|---|---|
| **Alta frecuencia de escritura**: decenas de filas/segundo. El patrón «consultar y luego escribir» aceptado en #07 **no vale aquí** | RN-APM-004, Clarifications § Concurrencia |
| **Sin caché distribuida** (Django usa `LocMemCache`, por proceso): con un proceso el throttle es fiable; al escalar horizontalmente el límite efectivo se multiplicaría | § 15 D2 — declarado como deuda, no bloqueante hoy |
| **Fuga de datos sensibles**: es la única superficie que entrega siniestralidad a terceros | RF-APM-002, RF-APM-003, RNF-APM-004; el filtro por zonas falla hacia el lado cerrado |
| **Doble cobro** por reintento | RF-APM-012, RN-APM-012, escenario I |
| **Ingreso no cobrado en silencio** | RN-APM-014, RF-APM-013, escenario J |

## Notes

- **Nada bloquea `/speckit-plan`.** Las dos preguntas se cerraron y se implementaron el mismo día.
- **Pendiente menor para `/speckit-tasks`:** añadir un throttle rate por partner en `REST_FRAMEWORK.DEFAULT_THROTTLE_RATES` (hoy solo hay tres, ninguno de partners).
- **Deuda declarada:** el throttle por minuto solo es fiable con un proceso; escalar horizontalmente exigirá un contador compartido (§ 15 D2).
- La divergencia RF-O53.2 ↔ RN-11 está resuelta a favor del SRS y documentada; **el catálogo debería corregirse** en una pasada aparte.
- ⚠️ Recordatorio: los tests con el doble de `conftest.py` no reproducen los centinelas de Pinot (`decisiones-pendientes.md` #18). Este módulo depende de agregaciones reales, así que la verificación contra Pinot será criterio de salida, igual que en #07.

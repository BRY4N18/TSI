# Specification Quality Checklist: Gestión de Acceso de Partners

**Purpose**: Validate specification completeness and quality before proceeding to planning  
**Created**: 2026-08-08  
**Feature**: [spec.md](../spec.md)  
**CU**: CU-O55

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

> Misma nota que los módulos hermanos: la capa `backend/` es la autoridad de dominio, API y modelo de datos, así que nombrar tablas Pinot y códigos HTTP es deliberado.

## Requirement Completeness

- [x] **No [NEEDS CLARIFICATION] markers remain** — ambas resueltas 2026-08-08: **D1** (una fila de bitácora por credencial desactivada) y **D2** (suspensiones independientes por origen). Ver § 15. **Ninguna requiere cambio de esquema.**
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic
- [x] All acceptance scenarios are defined — 12 escenarios (A–L), 15 criterios de aceptación
- [x] Edge cases are identified — credencial ajena (B), ya inactiva (C), aviso duplicado (D), regularización entre avisos (E), reactivación selectiva (G), no reactivar solo (H), reactivación redundante (I), suspensión sin motivo (J), factura en disputa (K)
- [x] Scope is clearly bounded — § 13 reparte propiedad frente a #07, #08, Suscripciones y Soporte
- [x] Dependencies and assumptions identified — § 12 y § 14

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] **Feature meets measurable outcomes** — RF-PAC-006 ya es implementable: el conjunto previo se reconstruye del último evento de suspensión en la bitácora (§ 15 D1)
- [x] No implementation details leak into specification

## Constitution Compliance (Golden Rule)

- [x] Las 9 características ISO/IEC 25010:2023 declaradas explícitamente — § 5.1
- [x] Las no aplicables justifican por qué — **Safety: no aplica** (cortar el acceso a datos ya cerrados no retrasa la atención de ninguna víctima)
- [x] Al menos un criterio medible por sub-característica — CA-PAC-015 (Performance/temporal), CA-PAC-004 (Security/autenticidad), CA-PAC-009 (Security/confidencialidad), CA-PAC-013 (Security/responsabilidad), CA-PAC-008 (Reliability/tolerancia)
- [x] Tie-Breaker invocado y documentado — Security vs Functional Suitability en RF-PAC-006 (cascada inversa selectiva), con trade-off explícito
- [x] Trazabilidad obligatoria a CU documentado — CU-O55 del catálogo canónico

## Trazabilidad al catálogo canónico

| RF del catálogo | Cubierto por | Estado |
|---|---|---|
| RF-O55.1 Invalidar la credencial de forma inmediata y entregar un reemplazo del mismo entorno y nombre | RF-PAC-001, RF-PAC-002, RN-PAC-004 | ✅ |
| RF-O55.2 Mantener operativas las demás credenciales del partner | RF-PAC-002, RN-PAC-005 | ✅ |
| RF-O55.3 Al suspender desactivar todas; al reactivar restituir solo las que estaban activas antes | RF-PAC-004, RF-PAC-005, RF-PAC-006, RN-PAC-010, RN-PAC-011, § 15 D1 | ✅ |
| RF-O55.4 Registrar cada revocación con su motivo, autor y fecha | RF-PAC-008, RN-PAC-013 | ✅ |

**4/4 RF del catálogo cubiertos sin reservas.**

## Cobertura del SRS §3.4.3

Los párrafos normativos de L426–L442 están cubiertos: L432 → RF-PAC-001, RN-PAC-001 · L434 → RN-PAC-002, RN-PAC-003 · L436 → RF-PAC-003, RN-PAC-006, RN-PAC-007 · L438 → RF-PAC-004, RF-PAC-005, RN-PAC-008 · L440 → RF-PAC-006, RN-PAC-010, RN-PAC-011 · L442 → RN-PAC-012.

**Los 6 párrafos normativos del módulo, cubiertos.**

## Dependencias externas

| Dependencia | Módulo | Bloquea | Estado |
|---|---|---|---|
| `Dim_CredencialAPI` con `nombre_credencial` y `fecha_expiracion` | `partner-api-onboarding` (#07) | RF-PAC-002 | ✅ esquema aplicado (#16) |
| Servicio de emisión de credenciales (reutilizado para el reemplazo) | `partner-api-onboarding` (#07) | RF-PAC-002 | ⏳ especificado, pendiente de implementar |
| Facturas de excedente con `tipo='excedente_api'` | `api-monitoring-and-billing` (#08) | RF-PAC-007 | ⏳ especificado, pendiente de implementar |
| Aplicación del corte en cada llamada (`Dim_Partner.activo`) | `api-monitoring-and-billing` (#08) | Efecto de RF-PAC-004 | ⏳ especificado (RF-APM-001) |
| Marca de factura en disputa | `gestion-tickets-soporte` | RN-PAC-015 | ✅ implementado (#17) |
| Rol `PartnerIntegracion` (idrol 15) | `autenticacion-y-rbac` | RF-PAC-001 | ✅ creado (#19) |
| Frontera con la suspensión de suscripción (RF-SUSF-007) | `subscriptions-and-billing` | RF-PAC-007 | ✅ **definida (§ 15 D2)**: independientes por origen; el acceso exige ambas |
| Comprobación de suscripción vigente en el middleware de consumo | `api-monitoring-and-billing` (#08) | Efecto de D2 | ⏳ **tarea derivada T024b**, ya añadida a su `tasks.md` |

## Riesgos detectados en la especificación

| Riesgo | Dónde se aborda |
|---|---|
| **Resucitar una credencial comprometida** al reactivar — el fallo de seguridad que RN-PAC-011 existe para prevenir | RF-PAC-006, escenario G, § 15 D1. **Resuelto por construcción**: una credencial ya inactiva no genera fila de cascada, así que la reactivación no la encuentra |
| **Ventana de exposición tras revocar**: la ingesta de Pinot tarda 5–15 s, así que una comprobación que solo lea `Dim_CredencialAPI` dejaría la credencial revocada operando durante ese tiempo | RNF-PAC-001 con advertencia explícita; el diseño debe cerrarla en `/plan` |
| **Doble suspensión** o estados contradictorios entre Suscripciones y Partners | § 15 D2 — independientes por origen. El arrastre se descartó por el conflicto entre RN-SUSF-011 (reactiva sola) y RN-PAC-009 (nunca reactiva sola) |
| **Cliente con suscripción suspendida que sigue consumiendo la API** — hueco que existía | ✅ cerrado por § 15 D2; implementado como T024b en `api-monitoring-and-billing` |
| **Avisos duplicados** (spam al partner) | RN-PAC-006, escenario D |
| **Estado contradictorio**: partner suspendido con credenciales activas | RF-PAC-006 exige actualización explícita, no validación indirecta |
| **Colisión de nombre** al emitir el reemplazo con el mismo nombre de la revocada (RN-PON-014 exige unicidad entre activas) | § 14, último supuesto: la revocada debe liberar el nombre |

## Notes

- **Nada bloquea `/speckit-plan`.** Las dos decisiones se cerraron el mismo día y **ninguna requiere cambio de esquema**: D1 usa `Fact_HistorialAccesoPartner.idcredencial`, que ya existe, y D2 es una regla de negocio sobre tablas existentes.
- **Efecto en otro módulo:** D2 añade la tarea **T024b** a `api-monitoring-and-billing` (comprobar suscripción vigente en la autenticación). Ya está registrada allí.
- **`tipo_cambio` nuevo:** `desactivacion_por_cascada`, distinto de `revocacion_credencial` — el primero se revierte al reactivar, el segundo nunca.
- ⚠️ Recordatorio: los tests con el doble de `conftest.py` no reproducen los centinelas de Pinot (`decisiones-pendientes.md` #18). La cascada y la reactivación selectiva tocan estado real en varias tablas, así que la verificación contra Pinot será criterio de salida, igual que en #07 y #08.

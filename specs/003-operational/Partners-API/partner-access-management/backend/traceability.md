# Trazabilidad: Gestión de Acceso de Partners

**Estado:** Phase 1 completada. Las columnas *Tareas* y *Tests* se rellenan con `/speckit-tasks` y `/speckit-implement`.

## Criterios de aceptación

| CA | Descripción | RF / RN | Tareas | Tests | Estado |
|----|-------------|---------|--------|-------|--------|
| CA-PAC-001 | El partner revoca sin aprobación; se marca inactiva y se registra con `idcredencial`, motivo y autor | RF-O55.1 / RF-PAC-001 | — | — | ⏳ |
| CA-PAC-002 | La revocación entrega **en el mismo acto** un reemplazo del mismo entorno y nombre, con secreto una sola vez | RF-O55.1 / RF-PAC-002 | — | — | ⏳ |
| CA-PAC-003 | Revocar una **no afecta** a ninguna otra credencial del partner | RF-O55.2 / RN-PAC-005 | — | — | ⏳ |
| CA-PAC-004 | Revocar una credencial ajena → 403 sin modificar nada | RN-PAC-002 | — | — | ⏳ |
| CA-PAC-005 | Revocar una ya inactiva → 409, sin segunda entrada en bitácora | RN-PAC-003 | — | — | ⏳ |
| CA-PAC-006 | Dos avisos previos, **ninguno duplicado** en el ciclo; no cambian el estado del partner | RF-PAC-003 / RN-PAC-006 | — | — | ⏳ |
| CA-PAC-007 | Regularizar entre avisos → el pendiente **nunca se envía**; ciclo cerrado sin suspensión | RN-PAC-007 | — | — | ⏳ |
| CA-PAC-008 | Suspensión sin intervención humana; `activo=false` con fecha y motivo; **todas** las credenciales desactivadas | RF-O55.3 / RF-PAC-004 | — | — | ⏳ |
| CA-PAC-009 | 🎯 Reactivar restituye **solo** las activas previas; la revocada **permanece inactiva**; respuesta con desglose | RF-O55.3 / RN-PAC-011 | — | — | ⏳ |
| CA-PAC-010 | El sistema **no reactiva** ni tras regularizar el pago | RN-PAC-009 | — | — | ⏳ |
| CA-PAC-011 | Suspender sin motivo → 400; reactivar no suspendido → 409; solo Administrador (403 al resto) | RF-PAC-005 | — | — | ⏳ |
| CA-PAC-012 | Factura en disputa no cuenta como mora: sin avisos ni suspensión | RN-PAC-015 | — | — | ⏳ |
| CA-PAC-013 | Los seis tipos de evento insertan una fila con motivo, autor y fecha; sin UPDATE ni DELETE | RF-O55.4 / RN-PAC-013 | — | — | ⏳ |
| CA-PAC-014 | El suspendido consulta su estado (200); consultar el de otro → 403 | RN-PAC-016 | — | — | ⏳ |
| CA-PAC-015 | 🎯 La revocación surte efecto en p95 ≤ 2 s — **sin esperas artificiales** | RNF-PAC-001 | — | — | ⏳ |

## Requisitos funcionales

| RF | Descripción | Tareas |
|----|-------------|--------|
| RF-PAC-001 | Revocación de credencial por autoservicio | — |
| RF-PAC-002 | Reemplazo inmediato sin interrumpir el resto | — |
| RF-PAC-003 | Avisos previos a la suspensión | — |
| RF-PAC-004 | Suspensión automática por mora | — |
| RF-PAC-005 | Suspensión y reactivación manual | — |
| RF-PAC-006 | Regla de cascada (directa y inversa selectiva) | — |
| RF-PAC-007 | Determinación de la mora | — |
| RF-PAC-008 | Bitácora de todo evento de acceso | — |
| RF-PAC-009 | Consulta del estado de acceso | — |

## Caso de uso (numeración canónica del catálogo §5.5)

| CU | Descripción | RF del catálogo | RF internos | Tareas |
|----|-------------|-----------------|-------------|--------|
| CU-O55 | Revocar o suspender el acceso de integración | RF-O55.1–4 | RF-PAC-001 … RF-PAC-009 | — |

### Cobertura RF del catálogo → RF interno

| Catálogo | Cubierto por | Estado |
|---|---|---|
| RF-O55.1 Invalidar de forma inmediata y entregar reemplazo del mismo entorno y nombre | RF-PAC-001, RF-PAC-002, RN-PAC-004 | ✅ |
| RF-O55.2 Mantener operativas las demás credenciales | RF-PAC-002, RN-PAC-005 | ✅ |
| RF-O55.3 Desactivar todas al suspender; restituir solo las previas al reactivar | RF-PAC-004, RF-PAC-005, RF-PAC-006, RN-PAC-010, RN-PAC-011, § 15 D1 | ✅ |
| RF-O55.4 Registrar cada revocación con motivo, autor y fecha | RF-PAC-008, RN-PAC-013 | ✅ |

**4/4 RF del catálogo cubiertos sin reservas.**

## RNF

| RNF | Evidencia | Tarea |
|-----|-----------|-------|
| RNF-PAC-001 | Revocación efectiva p95 ≤ 2 s, medida **sin esperas** (`quickstart.md` §6) | — |
| RNF-PAC-002 | Control de propiedad en toda revocación; nadie revoca credenciales ajenas | — |
| RNF-PAC-003 | 100 % de acciones en bitácora; sin UPDATE ni DELETE | — |
| RNF-PAC-004 | Revocar entrega reemplazo en el mismo acto; suspender no destruye, solo desactiva | — |
| RNF-PAC-005 | T-10, T-5 y límite de 15 días configurables; sin avisos duplicados | — |
| RNF-PAC-006 | Cobertura ≥ 80 % en `apps/partners/services` | — |

## Escenarios quickstart A–O

| Escenario | Validación | Estado |
|-----------|------------|--------|
| A | Revocación con reemplazo; `credenciales_intactas` correcto | ⏳ |
| B | 🎯 **Ventana cerrada**: la revocada no sirve ya, sin esperar la ingesta | ⏳ |
| C | Revocar credencial ajena → 403 | ⏳ |
| D | Revocar ya inactiva → 409 sin segunda entrada | ⏳ |
| E | El reemplazo con el mismo nombre no da colisión falsa | ⏳ |
| F | Avisos sin duplicación | ⏳ |
| G | Regularización entre avisos cierra el ciclo | ⏳ |
| H | Suspensión con cascada; nº de filas = nº de activas | ⏳ |
| I | 🎯 **Reactivación selectiva**: A y B vuelven, C no | ⏳ |
| J | 🎯 **El sistema no reactiva solo** tras pagar | ⏳ |
| K | Reactivación redundante → 409 | ⏳ |
| L | Suspensión manual sin motivo → 400 | ⏳ |
| M | Factura en disputa no genera mora | ⏳ |
| N | El suspendido consulta su estado (200); el de otro → 403 | ⏳ |
| O | Frontera con la suspensión de suscripción (§ 15 D2) | ⏳ |

## Verificación contra Pinot (fuera del alcance de pytest)

La cascada y la reactivación selectiva **tocan estado en tres tablas a la vez**, y el doble de `conftest.py` no reproduce ni los centinelas ni el retraso de ingesta (`decisiones-pendientes.md` #18).

| Verificación | Script | Estado |
|---|---|---|
| Sin credenciales activas tras suspender · nº de filas de cascada = nº de activas previas · la revocada sigue inactiva tras reactivar · `Dim_Partner` y credenciales no se contradicen · snapshot vuelve al centinela · revocación efectiva antes de la ingesta | `database/verifica_acceso_partners.py` | ⏳ **a crear** (`quickstart.md` §5) |

## Dependencias externas

| Dependencia | Módulo | Estado |
|---|---|---|
| `Fact_HistorialAccesoPartner` con `idcredencial` | `partner-api-onboarding` (#07) | ✅ esquema aplicado (#16) |
| Servicio de emisión de credenciales (reutilizado para el reemplazo) | `partner-api-onboarding` (#07) | ⏳ especificado, pendiente de implementar |
| Facturas `tipo='excedente_api'` | `api-monitoring-and-billing` (#08) | ⏳ especificado, pendiente de implementar |
| Aplicación del corte en cada llamada + integración con la lista de denegación | `api-monitoring-and-billing` (#08) | ⏳ **orden crítico**, ver `research.md` Decision 2 |
| Comprobación de suscripción vigente (T024b) | `api-monitoring-and-billing` (#08) | ⏳ tarea derivada de § 15 D2, ya registrada allí |
| Marca de factura en disputa | `gestion-tickets-soporte` | ✅ implementado (#17) |
| Rol `PartnerIntegracion` (idrol 15) | `autenticacion-y-rbac` | ✅ creado (#19) |

**Ninguna dependencia de esquema.** Este módulo es el único de los tres que no añadió columnas ni tablas.

## Deuda técnica declarada

La lista de denegación vive en `LocMemCache`, **por proceso**. Con un proceso es exacta; escalar horizontalmente exigirá un almacén compartido. Es **la misma deuda que el throttle de #08**, registrada una sola vez para el departamento. Ver `plan.md` § Deuda técnica.

**Hallazgo fuera de alcance:** `LogoutService` de `cuentas_clientes` tiene el mismo patrón sin resolver (un JWT robado sigue válido durante la ventana de ingesta tras el logout).

## Cambios fuera de ciclo

Ninguno. Las dos decisiones de diseño (§ 15 D1 y D2) se resolvieron **sin tocar el esquema**: D1 usa `Fact_HistorialAccesoPartner.idcredencial`, que ya existía, y D2 es una regla de negocio que se implementa como la tarea T024b de #08.

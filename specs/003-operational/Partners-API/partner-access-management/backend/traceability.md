# Trazabilidad: Gestión de Acceso de Partners

**Estado:** ✅ **Backend COMPLETO 2026-08-10 (63/63)**. 528 tests del módulo en verde, suite total **1569 passed** (base #08: 1447), cobertura de `apps/partners/services` **94 %**. Pendientes **T052** y **T054**: requieren el stack encendido.

## Criterios de aceptación

| CA | Descripción | RF / RN | Tareas | Tests | Estado |
|----|-------------|---------|--------|-------|--------|
| CA-PAC-001 | El partner revoca sin aprobación; se marca inactiva y se registra con `idcredencial`, motivo y autor | RF-O55.1 / RF-PAC-001 | ✅ | ✅ | ✅ |
| CA-PAC-002 | La revocación entrega **en el mismo acto** un reemplazo del mismo entorno y nombre, con secreto una sola vez | RF-O55.1 / RF-PAC-002 | ✅ | ✅ | ✅ |
| CA-PAC-003 | Revocar una **no afecta** a ninguna otra credencial del partner | RF-O55.2 / RN-PAC-005 | ✅ | ✅ | ✅ |
| CA-PAC-004 | Revocar una credencial ajena → 403 sin modificar nada | RN-PAC-002 | ✅ | ✅ | ✅ |
| CA-PAC-005 | Revocar una ya inactiva → 409, sin segunda entrada en bitácora | RN-PAC-003 | ✅ | ✅ | ✅ |
| CA-PAC-006 | Dos avisos previos, **ninguno duplicado** en el ciclo; no cambian el estado del partner | RF-PAC-003 / RN-PAC-006 | ✅ | ✅ | ✅ |
| CA-PAC-007 | Regularizar entre avisos → el pendiente **nunca se envía**; ciclo cerrado sin suspensión | RN-PAC-007 | ✅ | ✅ | ✅ |
| CA-PAC-008 | Suspensión sin intervención humana; `activo=false` con fecha y motivo; **todas** las credenciales desactivadas | RF-O55.3 / RF-PAC-004 | ✅ | ✅ | ✅ |
| CA-PAC-009 | 🎯 Reactivar restituye **solo** las activas previas; la revocada **permanece inactiva**; respuesta con desglose | RF-O55.3 / RN-PAC-011 | ✅ | ✅ | ✅ |
| CA-PAC-010 | El sistema **no reactiva** ni tras regularizar el pago | RN-PAC-009 | ✅ | ✅ | ✅ |
| CA-PAC-011 | Suspender sin motivo → 400; reactivar no suspendido → 409; solo Administrador (403 al resto) | RF-PAC-005 | ✅ | ✅ | ✅ |
| CA-PAC-012 | Factura en disputa no cuenta como mora: sin avisos ni suspensión | RN-PAC-015 | ✅ | ✅ | ✅ |
| CA-PAC-013 | Los seis tipos de evento insertan una fila con motivo, autor y fecha; sin UPDATE ni DELETE | RF-O55.4 / RN-PAC-013 | ✅ | ✅ | ✅ |
| CA-PAC-014 | El suspendido consulta su estado (200); consultar el de otro → 403 | RN-PAC-016 | ✅ | ✅ | ✅ |
| CA-PAC-015 | 🎯 La revocación surte efecto en p95 ≤ 2 s — **sin esperas artificiales** | RNF-PAC-001 | ✅ | ✅ | ✅ |
| CA-PAC-016 | La cola del Administrador lista suspendidos y avisados con sus días de mora; un partner → 403 | RF-PAC-009 b | ✅ | ✅ | ✅ |
| CA-PAC-017 | 🎯 Tras suspender, **ninguna** credencial sirve ya, **sin esperar** a la ingesta | RNF-PAC-001 / § 15 D4 | ✅ | ✅ | ✅ |
| CA-PAC-018 | Solo `excedente_api` + `Pendiente` vencida genera mora; una `Fallida` **no** suspende aquí | RF-PAC-007 / § 15 D3 | ✅ | ✅ | ✅ |

## Requisitos funcionales

| RF | Descripción | Tareas |
|----|-------------|--------|
| RF-PAC-001 | Revocación de credencial por autoservicio | T013–T022 ✅ |
| RF-PAC-002 | Reemplazo inmediato sin interrumpir el resto | T016, T019 ✅ |
| RF-PAC-003 | Avisos previos a la suspensión | T034–T036, T039–T043 ✅ |
| RF-PAC-004 | Suspensión automática por mora | T029, T041, T057 ✅ |
| RF-PAC-005 | Suspensión y reactivación manual | T023–T032 ✅ |
| RF-PAC-006 | Regla de cascada (directa y inversa selectiva) | T009, T025, T026 ✅ |
| RF-PAC-007 | Determinación de la mora | T037–T039, T059, T060 ✅ |
| RF-PAC-008 | Bitácora de todo evento de acceso | T020, T047 ✅ |
| RF-PAC-009 | Consulta del estado de acceso — **dos lecturas**: la del partner (a) y la cola del Administrador (b) | T045, T046, T061, T062 ✅ |

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
| RNF-PAC-001 | ✅ **p95 = 366 ms** (umbral 2000), medido **sin esperas** — T050. Mide el camino de código contra el doble, **no** la latencia real de Kafka/Pinot: eso lo prueba T052 | T050 |
| RNF-PAC-002 | Control de propiedad en toda revocación; nadie revoca credenciales ajenas | T015, T018 ✅ |
| RNF-PAC-003 | 100 % de acciones en bitácora; sin UPDATE ni DELETE | T047 ✅ |
| RNF-PAC-004 | Revocar entrega reemplazo en el mismo acto; suspender no destruye, solo desactiva | T016, T017 ✅ |
| RNF-PAC-005 | T-10, T-5 y límite de 15 días configurables; sin avisos duplicados | T043 ✅ |
| RNF-PAC-006 | ✅ **94 %** en `apps/partners/services` (umbral 80) | T051 |

## Escenarios quickstart A–Q

| Escenario | Validación | Estado |
|-----------|------------|--------|
| A | Revocación con reemplazo; `credenciales_intactas` correcto | ✅ |
| B | 🎯 **Ventana cerrada**: la revocada no sirve ya, sin esperar la ingesta | ✅ |
| C | Revocar credencial ajena → 403 | ✅ |
| D | Revocar ya inactiva → 409 sin segunda entrada | ✅ |
| E | El reemplazo con el mismo nombre no da colisión falsa | ✅ |
| F | Avisos sin duplicación | ✅ |
| G | Regularización entre avisos cierra el ciclo | ✅ |
| H | Suspensión con cascada; nº de filas = nº de activas | ✅ |
| I | 🎯 **Reactivación selectiva**: A y B vuelven, C no | ✅ |
| J | 🎯 **El sistema no reactiva solo** tras pagar | ✅ |
| K | Reactivación redundante → 409 | ✅ |
| L | Suspensión manual sin motivo → 400 | ✅ |
| M | Factura en disputa no genera mora | ✅ |
| N | El suspendido consulta su estado (200); el de otro → 403 | ✅ |
| O | Frontera con la suspensión de suscripción (§ 15 D2) | ✅ |
| P | La cola de trabajo del Administrador; un partner → 403 | ✅ |
| Q | 🎯 **La suspensión también corta ya**: las tres credenciales dejan de servir sin espera | ✅ |

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

## Hallazgos de la implementación

### 🐛 La reactivación no restituía nada cuando el reloj avanzaba

`credenciales_de_la_ultima_cascada()` anclaba el ciclo en el `fecha_cambio` del
evento de suspensión. Pero **las filas de cascada se escriben antes** que ese
evento: si el milisegundo avanzaba entre medias, quedaban «antes del corte» y se
descartaban. La reactivación devolvía la lista vacía y **no restituía ninguna
credencial, en silencio** — el partner reactivado se quedaba sin acceso y nada
en el log lo delataba.

**Solo se manifestaba con la máquina cargada**: en aislado los dos `_now_ms()`
caen en el mismo milisegundo y el test pasaba. Lo destapó la suite completa.

Corregido delimitando el ciclo **por posición en el historial** (se recorre de
más nuevo a más viejo y se para en el cierre del ciclo anterior — otra
suspensión o una reactivación), no por reloj. Los empates de milisegundo dejan
de importar porque `list_by_partner` desempata por `idhistorial`. Regresión
fijada en `test_historial_cascada.py::test_encuentra_la_cascada_aunque_el_MILISEGUNDO_haya_avanzado`,
que fuerza el desfase.

### Decisión no prevista: `notificar_aviso_mora` en vez de reutilizar `notificar_cuota`

`notificar_cuota` de #08 documenta que **nunca menciona interrupción del
servicio**, porque superar el cupo no bloquea (RN-APM-002). El aviso de mora
dice justo lo contrario: si no paga, el acceso se corta. Reutilizarlo habría
obligado a que uno de los dos mintiera, así que se añadieron dos métodos
propios (`notificar_aviso_mora`, `notificar_suspension`).

### Menos trabajo del previsto en T011

`EsAdministrador`, `EsPartner` y `verificar_propiedad()` ya existían en
`permissions.py` desde #07. T011 se redujo a usarlos.

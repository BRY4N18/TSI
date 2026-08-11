# Mapa de Modulos — TSI (Trafico Seguro Integral)

Navegacion rapida entre modulos, specs, dependencias y tablas del modelo dimensional.

---

> **Convencion capas (Fase A+B 2026-07-30):** los modulos operativos en disco usan `{modulo}/{modulo}.md` + `backend/` + `frontend/`. Speckit `feature.json` apunta a **una capa** (backend primero). **Fase B:** `frontend/spec.md` tiene FR-UI (Interaction Capability) con Depends-on backend — sin duplicar OpenAPI/data-model. Crear nuevos con `create-new-feature.ps1 -Layered`.

## Orden de implementacion sugerido

| Paso | Modulo | Spec | Depende de |
| ---- | ------ | ---- | ---------- |
| 01 | Cuentas-Clientes | `autenticacion-y-rbac` | — |
| 02 | Cuentas-Clientes | `incorporacion-clientes` | #01 |
| 03 | Cuentas-Clientes | `gestion-cuentas` | #01, #02 |
| 04 | Ventas-CRM | `commercial-pipeline-prospects` | #01 |
| 05 | Ventas-CRM | `notificacion-ventas` | #04 |
| 06 | Suscripciones-Facturacion | `subscriptions-and-billing` | #03 |
| 07 | Partners-API | `partner-api-onboarding` | #02 |
| 08 | Partners-API | `api-monitoring-and-billing` | #07 |
| 09 | Partners-API | `partner-access-management` | #07, #08 |
| 10 | Infraestructura | `infrastructure-and-resilience` | — |
| 11 | Red-Operativa | `alta-unidades` | #10 |
| 12 | Red-Operativa | `incorporacion-regional` | #10, #11 |
| 13 | Emergencias | `registro-accidente` | #01, #12 |
| 14 | Emergencias | `despacho-inteligente` | #11, #13 |
| 15 | Emergencias | `evidencia-unidad` | #11, #13 |
| 16 | Emergencias | `seguimiento-cierre-de-casos` | #13, #14, #15 |
| 17 | Soporte-Cliente | `gestion-tickets-soporte` | #02 |
| 18 | Analitica-ML | `predictive-ai-accident-rate` | #13, #16 |
| 19 | Analitica-ML | `data-quality-analytics` | #13, #16, #18 |

---

## 1. Cuentas-Clientes

`specs/003-operational/Cuentas-Clientes/`

| Spec | Carpeta | CUs | Estado | Tablas | Dependencias |
| ---- | ------- | --- | ------ | ------ | ------------ |
| Autenticacion y RBAC | `autenticacion-y-rbac/` (`autenticacion-y-rbac.md` + `backend/` + `frontend/`) | O05, O04, O13, O15, **O06**, **O07** | ✅ Actualizado | Dim_Usuarios, Dim_Credencial, Dim_Rol, Dim_Usuario_Rol, Dim_RolesServidor, Dim_UsuariosServidor, Dim_UsuariosServidorRolesServidor, Dim_RolesServidorRoles, Fact_Session | — |
| Onboarding Digital de Clientes | `incorporacion-clientes/` (`incorporacion-clientes.md` + `backend/` + `frontend/`) | O01, O02, **O12**, **O09**, **O08** | ✅ Plan + contrato | Dim_Cliente, Dim_Plan, Fact_Onboarding, Dim_Preferencias_Cliente, Dim_Credencial | #01 |
| Gestion de Cuenta de Cliente | `gestion-cuentas/` (`gestion-cuentas.md` + `backend/` + `frontend/`) | O03, **O10**, **O11** | ✅ Actualizado | Dim_Cliente, Dim_Preferencias_Cliente | #01, #02 |

---

## 2. Suscripciones-Facturacion

`specs/003-operational/Suscripciones-Facturacion/`

| Spec | Carpeta | CUs | Estado | Tablas | Dependencias |
| ---- | ------- | --- | ------ | ------ | ------------ |
| Facturacion y Renovacion Automatica | `subscriptions-and-billing/` (`subscriptions-and-billing.md` + `backend/` + `frontend/`) | O106, O101, O104, O107, O102, O108, O105, O109 | ✅ Actualizado | Fact_Suscripcion, Fact_Factura, Fact_Solicitud_Cambio_Plan, Dim_Plan, Dim_Cliente, Dim_MetodoPago | #03 |

---

## 3. Ventas-CRM

`specs/003-operational/Ventas-CRM/`

| Spec | Carpeta | CUs | Estado | Tablas | Dependencias |
| ---- | ------- | --- | ------ | ------ | ------------ |
| Pipeline Comercial y Prospectos | `commercial-pipeline-prospects/` (`commercial-pipeline-prospects.md` + `backend/` + `frontend/`) | O116, O119, O117, O121 (+ RF-CPP-000) | ✅ Implementado (backend + Angular; portal planes) | Dim_Prospecto, Fact_Asignacion, Fact_Pipeline, Dim_Cliente; lectura Dim_Plan | #01 |
| Notificacion de Prospectos a Ventas | `notificacion-ventas/` (`notificacion-ventas.md` + `backend/` + `frontend/`) | O118, O122 | ✅ Implementado (backend + Angular) | Fact_NotificacionVentas, Fact_Interaccion_Demo, Dim_Prospecto | #04 |

---

## 4. Partners-API

`specs/003-operational/Partners-API/`

> **Renumeración CU 2026-08-08.** Este departamento usaba los CU legacy O71–O84 de `PortalPartnersAPI.md`, números que en el catálogo limpio (`TSI-Catalogo-CU-RF-RNF.md` §5.5) pertenecen a **Emergencias**. La numeración canónica vigente es **CU-O48–O55**. Mismo tratamiento que la renumeración de Soporte al Cliente (`decisiones-pendientes.md` #14).

| Spec | Carpeta | CUs | Estado | Tablas | Dependencias |
| ---- | ------- | --- | ------ | ------ | ------------ |
| Onboarding de Partners API | `partner-api-onboarding/` (`partner-api-onboarding.md` + `backend/` + `frontend/`) | O48, O49, O50 | ✅ **Backend IMPLEMENTADO 2026-08-09** (81/81 tareas). 208 tests del módulo en verde, cobertura 97 %, p95 de emisión 217 ms (umbral 2000). Verificado además contra Pinot real: `verifica_partners.py` 16/16 (esquema) y `verifica_onboarding_e2e.py` 19/19 (servicios reales). FE: spec **cerrada 2026-08-09** (FR-UI-001…034, 6 historias US-FE-*, 8 Success Criteria, checklist 16/16) + `plan.md`, `research.md`, `data-model.md`, 2 `ui-contract.md` y `quickstart.md`. ✅ **Frontend IMPLEMENTADO 2026-08-09 (90/91 tareas)**: consola (lista Ver-only + workpanel + cola de solicitudes) y portal del partner (mi integración, entrega del secreto, contrato versionado). **459 tests en verde, cobertura del módulo 91,6 %**. Los dos deltas de backend están implementados: `BE-DELTA-01` (`GET /partners/me`) y `BE-DELTA-02` (el partner emite su credencial productiva, para que el Admin no vea secretos ajenos) — backend de 1250 a **1263 passed**, módulo de 208 a **221**. Grupo «Partners y API» en `nav-links.ts` y en la matriz rol→navegación. **T088 ejecutado parcialmente contra la app real**: verificados C, D (completo, incluido SC-004: cero fugas del secreto en storage/URL/título), F, J, K, L y el sidebar por rol; quedan A/E/G/H/I por limitaciones de la automatización o por datos consumidos. Aparecieron **tres deltas de backend** (`BE-DELTA-01/02/03`), todos implementados — módulo de 208 a **230 tests**, suite total **1272 passed**. Se añadió `database/seed_usuario_partner_demo.py`: el rol 15 existía pero **nadie lo tenía asignado**, así que el portal era inalcanzable en la demo | Dim_Partner, Dim_CredencialAPI, Fact_HistorialAccesoPartner + lectura de Dim_Cliente, Fact_Suscripcion, Dim_Plan | #02, #06 |
| Monitoreo y Facturacion de API | `api-monitoring-and-billing/` (`api-monitoring-and-billing.md` + `backend/` + `frontend/`) | O51, O52, O53, O54 | ✅ **Backend IMPLEMENTADO 2026-08-09 (71/71)**: consumo medido y facturado de punta a punta — autenticación por credencial, throttle por partner, registro en las dos tablas, métricas, consola de logs, reporte mensual, alertas de cuota y tarificación del excedente con reintentos 1h/6h/24h. **405 tests del módulo**, suite total **1447 passed**, cobertura de servicios **93 %**. Contrato OpenAPI validado (`credencialAuth` solo en `/datos/*`). **Verificado contra Pinot real 2026-08-09**: `verifica_monitoreo_api.py` **9/9** — `SUM(llamadas)` exacto (37 de 37), el filtro de entorno excluye de verdad el sandbox (sin él darían 48), `GROUP BY idservicio` correcto y el **`LIMIT 10` implícito no trunca la agregación**. Esto cierra `decisiones-pendientes.md` #18 para este módulo, que pesaba más que en #07 porque el módulo vive de agregaciones que el doble reproduce a mano y de esas cifras sale lo que se factura. RNF medidos: p95 de `/datos/accidentes` **214 ms** (umbral 2000) y **21 254 registros/s** (umbral 50) — con dos salvedades honestas: el coste aislado del registro salió **negativo (−29 ms)**, es decir **por debajo del ruido de medición** porque bcrypt domina, no gratis; y las escrituras/s se miden contra el doble en memoria, no contra Kafka real. `limpia_datos_prueba.py` **se extendió** con `Fact_APIIntegracion` y `Fact_LogLlamadaAPI` (dejaba 48 filas de consumo que habrían falseado métricas y excedentes): 7 tablas a 0, datos reales intactos. ✅ **FE COMPLETO 2026-08-10 (74/74)**, verificación manual incluida: panel de consumo del partner, consola de registros con workpanel Ver-only, reporte mensual comparable y cola de excepciones de facturación. Suite frontend **588 passed** (base #07: 459). Los dos deltas se cerraron: `BE-DELTA-04` (`GET /facturacion/excepciones`) y `BE-DELTA-05` (los partners **no tarificables**, que antes solo existían como un correo — el silencio que RN-APM-014 prohíbe); backend de 1569 a **1596 passed**. El invariante de la capa (`mi-consumo-sin-alarma.spec.ts`) verifica con el cupo al **150 %** que ningún token de severidad ni palabra de interrupción aparece en pantalla: superar el cupo no corta el servicio, y pintarlo en rojo haría que el partner apagase una integración que funciona. **La verificación manual contra la app real encontró 6 defectos que la suite no veía**: el partner no podía ver sus propios errores (403, contradiciendo RN-APM-009 → `BE-DELTA-07`), un fail-open que decía «sin errores» sin haberlo comprobado, la paginación repetía 4 de 5 filas contra Pinot real (cursor por id cuando el orden es por fecha → **cursor compuesto**), el importe de la factura de excedente se escribía en la columna inexistente `monto` en vez de `monto_total` (la factura existía **sin cobrar nada**), la IP salía «—» en toda IP ≥ 128.0.0.0 por el desbordamiento del INT con signo, y `consola/excepciones` abría el detalle de un partner porque la ruta literal iba después de `consola/:idpartner`. `BE-DELTA-06` cerrado: **paginación por cursor y todos los filtros en la base** — la primera versión filtraba código y fecha en memoria y el usuario lo corrigió, con razón: era una excepción al patrón del resto del sistema. Al hacerlo apareció que el contrato **ya declaraba seis filtros que la implementación ignoraba en silencio**, y que la capa frontend leía `latencia`/`idcredencial` en vez de `latenciams`/`idcredencialapi` — la columna habría salido vacía. Spec original: **cerrada 2026-08-10** — 4 superficies (consola de registros, panel de consumo del partner, reporte mensual comparable, excepciones de facturación), 6 historias US-FE-*, 7 Success Criteria, checklist 16/16. Declara **2 deltas de backend bloqueantes**: `BE-DELTA-04` (`GET /facturacion/excepciones`: la cuarta superficie no tiene endpoint del que leer) y `BE-DELTA-05` (los partners **no tarificables** no se persisten en ninguna parte — hoy el único rastro es un correo, que es justo el silencio que RN-APM-014 prohíbe). El rol `Cliente` de RF-APM-009 no lo admite el endpoint: registrado como `decisiones-pendientes.md` #25 en vez de relajar el permiso | Fact_APIIntegracion, Fact_LogLlamadaAPI, Dim_EstadoIntegracion + lectura de Dim_Partner, Dim_CredencialAPI, Dim_Plan, Dim_Preferencias_Cliente; escribe Fact_Factura | #07 |
| Gestion de Acceso de Partners | `partner-access-management/` (`partner-access-management.md` + `backend/` + `frontend/`) | O55 | ✅ **Backend COMPLETO 2026-08-10 (63/63)**: revocación de autoservicio con reemplazo en el mismo acto, cascada de suspensión con una fila de bitácora por credencial, **reactivación selectiva** que no resucita lo revocado, avisos T-10/T-5 sin duplicar, suspensión automática por mora y cola de trabajo del Administrador. **528 tests del módulo**, suite total **1569 passed** (base #08: 1447), cobertura **94 %**. p95 de revocación efectiva **366 ms** (umbral 2000), medido sin esperas. `/speckit-analyze` previo encontró **4 defectos de diseño** y añadió 7 tareas: `Fact_Factura` no tiene `idpartner` (la mora habría dado cero morosos en silencio, § 15 D3), `Fallida` no debe contar como mora aquí, faltaba la cola del Administrador de RF-PAC-009, y la suspensión no cerraba su ventana de ingesta (§ 15 D4). Durante la implementación se encontró y corrigió **un bug real**: la reactivación no restituía nada si el reloj avanzaba un milisegundo entre la cascada y el evento de suspensión — intermitente, solo con la máquina cargada. **Verificado contra Pinot real: `verifica_acceso_partners.py` 10/10** — la reactivación selectiva no resucita la credencial revocada tampoco en el sistema real, y la mora se resuelve por `id_cliente`. Datos de prueba limpiados. FE stub | Dim_Partner, Dim_CredencialAPI, Fact_HistorialAccesoPartner + lectura de Fact_Factura | #07, #08 |

**Reparto de propiedad de escritura** (evita el solape que tenía la numeración legacy): `partner-api-onboarding` **emite y rota** credenciales; `partner-access-management` **invalida** (revocación por seguridad, cascada de suspensión); `api-monitoring-and-billing` es el único que escribe las tablas de consumo. `Fact_Factura` se escribe en Suscripciones y Facturación; la disputa vive en Soporte (CU-O83 / RF-O83.2).

---

## 5. Infraestructura

`specs/003-operational/Infraestructura/`

| Spec | Carpeta | CUs | Estado | Tablas | Dependencias |
| ---- | ------- | --- | ------ | ------ | ------------ |
| Infraestructura y Resiliencia | `infrastructure-and-resilience/` | O16, O17 | ⏳ Planificado (sin carpeta en disco) | (monitoreo externo: Prometheus) | — |

---

## 6. Emergencias

`specs/003-operational/Emergencias/`

| Spec | Carpeta | CUs | Estado | Tablas | Dependencias |
| ---- | ------- | --- | ------ | ------ | ------------ |
| Registro de Accidentes | `registro-accidente/` (`registro-accidente.md` + `backend/` + `frontend/`) | O21, O32, O40, O41 | ✅ Split capas 2026-07-30 — BE dominio/OpenAPI; FE Interaction | Fact_Accidente, Dim_Severidad, Dim_Calle, Dim_Ciudad, Dim_Condado, Dim_Estado, Dim_Pais, Dim_PeriodosDias, Dim_EstadosClimas, Dim_TipoReportado, Dim_Elementos_Fisicos, Dim_ElementoFisicoAccidente, Dim_ReferenciaEstacion, Dim_Implicado, Dim_Conductor, Dim_Vehiculo, Dim_Estado_Conductor, Fact_Conductor_Accidente, Dim_TipoEstadoAccidente, Fact_AccidenteTipoEstadoAccidente, Dim_ElementoClimaticosAccidente — **escritura Fase 1 = caso + estados + catálogos a distancia; clima/físico/conductores/implicados se escriben en Fase 3 (evidencia CU-O46)** | #01, #12 |
| Despacho Inteligente | `despacho-inteligente/` (`despacho-inteligente.md` + `backend/` + `frontend/`) | O22, O23, O24, O33, O34, O35, O36, O38, O45 | ✅ Implementado (backend + Angular US6) | Fact_Despacho, Fact_HistorialDespachoUnidad, Fact_NotificacionDespacho, Dim_ParametrosDespacho, Dim_UnidadEmergencia, Dim_HistorialUbicacionUnidadEmergencia, Fact_Accidente | #11, #13 |
| Evidencia en Sitio y Disponibilidad | `evidencia-unidad/` (`evidencia-unidad.md` + `backend/` + `frontend/`) | O27, O30, O43, **O46** | ✅ Spec + código CU-O46 incl. RF-EVI-010 Dim_Implicado (2026-07-29) | Dim_UnidadEmergencia, Dim_EvidenciaFoto, Dim_NotaAccidente, Fact_HistorialEstadoUnidad, Dim_EstadoUnidadEmergencia (+ escritura runtime en tablas Registro: clima, físico, conductores, **Dim_Implicado**) | #11, #13 |
| Seguimiento y Cierre de Casos | `seguimiento-cierre-de-casos/` (`seguimiento-cierre-de-casos.md` + `backend/` + `frontend/`) | O25, O26, O28, O29, O37, O39, O42, O44 | ✅ Actualizado | Fact_Accidente, Fact_Despacho, Fact_HistorialDespachoUnidad, Dim_EstadoDespacho, Fact_NotificacionDespacho, Dim_HistorialUbicacionUnidadEmergencia, Dim_UnidadEmergencia, Dim_TipoEstadoAccidente, Fact_AccidenteTipoEstadoAccidente, Dim_EvidenciaFoto, Dim_NotaAccidente | #13-#16 |

---

## 7. Red-Operativa

`specs/003-operational/Red-Operativa/`

> ⚠️ **Pendiente:** `ConfiguracionRedOperativa.md` usa nombres de tabla que no coinciden con el esquema real para el flujo de validación de región — `Fact_ValidacionRegion` (real: `Dim_ValidacionRegion`), `Fact_HistorialEstadoRegion` (real: `Dim_RegionOperativaEstadoRegion`, con menos campos de los que la narrativa asume: sin `motivo`, `idusuario` ni `estadoanterior`), y `Dim_Estado_Implementacion` (no existe como catálogo — el resultado es un `STRING` libre en `Dim_ValidacionRegion.resultado`). Además, `Dim_RegionOperativa.estadoregion` es un campo de estado directo, a diferencia del patrón "solo historial" que usa `Dim_UnidadEmergencia`. Las tablas listadas abajo ya usan los nombres reales; falta corregir la narrativa de `ConfiguracionRedOperativa.md` en una pasada aparte.

| Spec | Carpeta | CUs | Estado | Tablas | Dependencias |
| ---- | ------- | --- | ------ | ------ | ------------ |
| Alta de Unidades de Emergencia | `alta-unidades/` (`alta-unidades.md` + `backend/` + `frontend/`) | O54, O56, O57, O58 (O59 eliminado → CU-O30) | ✅ Implementado (backend + Angular, app `red_operativa`) | Dim_UnidadEmergencia (`idcondado` reemplaza a `zonacobertura`, migración 2026-07-21), Fact_BajaUnidad, Fact_HistorialEstadoUnidad (lectura; escritura CU-O30), Fact_Despacho (validación cruzada, módulo Emergencias) | #10 |
| Onboarding de Region | `incorporacion-regional/` (`incorporacion-regional.md` + `backend/` + `frontend/`) | O55, O60, O61, O62 | ✅ Implementado (backend + Angular, app `red_operativa`) | Dim_RegionOperativa, Dim_ValidacionRegion, Dim_RegionOperativaEstadoRegion, Dim_EstadoRegion, Fact_Accidente (regla de continuidad, módulo Emergencias) | #10, #11 |

---

## 8. Soporte-Cliente

`specs/003-operational/Soporte-Cliente/`

| Spec | Carpeta | CUs | Estado | Tablas | Dependencias |
| ---- | ------- | --- | ------ | ------ | ------------ |
| Gestion de Tickets de Soporte | `gestion-tickets-soporte/` (`gestion-tickets-soporte.md` + `backend/` + `frontend/`) | O95, O91, O92, O96, O97 | ✅ Implementado (backend + Angular US7) | Fact_Reclamo, Dim_Estado_Soporte, Dim_SLAConfig, Fact_Historial_Ticket, Fact_ArchivosAdjuntosReclamos, Dim_Cliente, Dim_Servicio, Fact_Suscripcion (lectura) | #02 |

---

## 9. Analitica-ML

`specs/003-operational/Analitica-ML/`

| Spec | Carpeta | CUs | Estado | Tablas | Dependencias |
| ---- | ------- | --- | ------ | ------ | ------------ |
| IA Predictiva de Siniestralidad | `predictive-ai-accident-rate/` | **O123**, O31 | ✅ Creado (O46 renumerado → O123; O46 = evidencia CU-O46) | Fact_Accidente, Dim_Severidad, Dim_EstadosClimas, Dim_PeriodosDias, Dim_Calle, Dim_Ciudad, Dim_Condado, Dim_Estado, Dim_Pais | #13, #16 |
| Calidad de Datos y Analitica | `data-quality-analytics/` | O47, O48, O49 | ✅ Creado | Fact_Accidente, Fact_Despacho, Dim_NotaAccidente, Dim_Severidad, Dim_Calle, Dim_Ciudad, Dim_Condado, Dim_Estado, Dim_Pais | #13, #16, #18 |

---

## Matriz rol → navegación UI

Fuente de código: `frontend/src/app/shared/layout/nav-links.ts` +
`frontend/src/app/modules/cuentas-clientes/auth/services/post-login-home.ts`.

| Rol JWT | Home post-login | Sidebar (grupos principales) |
| ------- | --------------- | ---------------------------- |
| **Unidad** | `/despacho/mi-despacho` | Despacho: Mi despacho · Seguimiento: Mi seguimiento · Evidencia: Disponibilidad (CU-O30) |
| **Operador** | `/accidentes/lista` | Emergencias: Registrar/Lista · Despacho: Monitoreo · Seguimiento: Mapa/Historial |
| **Despacho** | `/despacho/monitoreo` | Despacho: Monitoreo · Seguimiento: Mapa/Historial · Evidencia: Flota |
| **Administrador** | `/cuentas-clientes` | Ventas CRM (Prospectos/Pipeline/Entrada directa) · Despacho: Parámetros · Red operativa · Admin · Soporte: Config SLA · Suscripciones — sin Emergencias/Monitoreo/Seguimiento/Flota/Cola soporte |
| **GerenteVentas** | `/ventas-crm/prospectos` | Ventas CRM: Prospectos · Pipeline (sin Entrada directa) |
| **DirectorEstrategia** | `/suscripciones/catalogo-planes` | Suscripciones: Catálogo (CRUD `Dim_Plan`, RF-SUSF-001) |
| **DirectorTecnologico** | `/red-operativa/incorporacion-regional/catalogo` | Despacho parámetros · Regiones · Soporte |
| **Proveedor** / **Cliente** (flota) | Proveedor → catálogo unidades; Cliente → mis-tickets | Red operativa: Mis unidades · Seguimiento: Mis expedientes (Cliente) · Suscripciones propias |
| **Soporte** | `/soporte-cliente/cola` | Cola / tickets |
| **DesarrolladorAPIs** | `/partners/consola` | Partners y API: Partners · Solicitudes pendientes (solo lectura de la cola: **resolver la promoción es exclusivo de Administrador**, RF-PON-008) · Soporte |
| **PartnerIntegracion** | `/partners/portal` | Partners y API: Mi integración · Contrato de integración — **nada más**. Es un departamento distinto del de la consola, así que los sidebars no se fusionan |

> `Administrador` suma también el grupo **Partners y API** (Partners · Solicitudes pendientes), y es
> el único rol que puede resolver una promoción a producción.

**No confundir:** el login demo de unidad puede tener un gmail con la palabra “operador” en el local-part; el **rol JWT** es la verdad. Renombrar demos a `*unidad@…` cuando se re-siembren.

---

## Indice rapido de especificaciones (19 total)

| # | Spec | Modulo | CUs |
| - | ---- | ------ | --- |
| 1 | `autenticacion-y-rbac` | Cuentas-Clientes | O05, O04, O13, O15, O06, O07 |
| 2 | `incorporacion-clientes` | Cuentas-Clientes | O01, O02, O12, O09, O08 |
| 3 | `gestion-cuentas` | Cuentas-Clientes | O03, O10, O11 |
| 4 | `commercial-pipeline-prospects` | Ventas-CRM | O116, O119, O117, O121 |
| 5 | `notificacion-ventas` | Ventas-CRM | O118, O122 |
| 6 | `subscriptions-and-billing` | Suscripciones-Facturacion | O106, O101, O104, O107, O102, O108, O105, O109 |
| 7 | `partner-api-onboarding` | Partners-API | O48, O49, O50 |
| 8 | `api-monitoring-and-billing` | Partners-API | O51, O52, O53, O54 |
| 9 | `partner-access-management` | Partners-API | O55 |
| 10 | `infrastructure-and-resilience` | Infraestructura | O16, O17 |
| 11 | `alta-unidades` | Red-Operativa | O54, O56, O57, O58, O59 |
| 12 | `incorporacion-regional` | Red-Operativa | O55, O60, O61, O62 |
| 13 | `registro-accidente` | Emergencias | O21, O32, O40, O41 |
| 14 | `despacho-inteligente` | Emergencias | O22, O23, O24, O33, O34, O35, O36, O38, O45 |
| 15 | `evidencia-unidad` | Emergencias | O27, O30, O43, O46 |
| 16 | `seguimiento-cierre-de-casos` | Emergencias | O25, O26, O28, O29, O37, O39, O42, O44 |
| 17 | `gestion-tickets-soporte` | Soporte-Cliente | O95, O91, O92, O96, O97 |
| 18 | `predictive-ai-accident-rate` | Analitica-ML | O123, O31 |
| 19 | `data-quality-analytics` | Analitica-ML | O47, O48, O49 |

> Flujo canónico Emergencias: `flujoscorreguidos/flujo-emergencias-canonico.md`. **O46** reservado a enriquecimiento en sitio (`evidencia-unidad`).
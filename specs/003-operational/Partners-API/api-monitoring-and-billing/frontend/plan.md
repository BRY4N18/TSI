# Implementation Plan: Monitoreo y Facturación de API — Frontend

**Capa**: `api-monitoring-and-billing/frontend` | **Date**: 2026-08-10 | **Spec**: [`./spec.md`](./spec.md)

**Input**: `spec.md` de esta capa (Clarifications 2026-08-10, `BE-DELTA-04` y `BE-DELTA-05` declarados) + [`../backend/spec.md`](../backend/spec.md) como autoridad de dominio.
**Módulo previo:** [`#07 frontend`](../../partner-api-onboarding/frontend/) — aporta el módulo Angular `partners/`, sus guards, sus servicios y el portal donde se injerta el panel de consumo.

## Summary

Cuatro superficies sobre el módulo Angular `partners/` **que ya existe**, sin duplicar ninguna regla del backend:

| Superficie | Ruta | Actor | Núcleo |
|---|---|---|---|
| **Panel de consumo** | `/partners/portal/consumo` | `PartnerIntegracion` | Sus métricas del período, % de cupo y coste previsto |
| **Consola de registros** | `/partners/consola/logs` | `DesarrolladorAPIs` | Detalle de llamadas por partner, con autodiagnóstico |
| **Reporte mensual** | `/partners/consola/reportes` | Admin · DevAPIs · Partner | Un mes, comparable contra otro |
| **Excepciones de facturación** | `/partners/consola/excepciones` | `Administrador` | Cola de lo que no se pudo facturar |

Tres decisiones gobiernan el resto:

1. **El exceso se presenta como coste previsto, nunca como severidad.** Es el tie-breaker de la spec llevado a componentes concretos: token `informacion`, no `alerta-critica`; copy de facturación, no de incidencia.
2. **Todo se consulta a la base; nada se filtra en memoria.** Cada cambio de filtro es una consulta, igual que en el resto del sistema. Filtrar una ventana en el navegador daría **falsa exhaustividad** —«no hay ningún 500» cuando solo no lo hay en los últimos 50— y descuadraría la paginación (`research.md` Decision 3, revisada por decisión del usuario).
3. **Paginación real por cursor.** El endpoint devolvía `next_cursor` sin aceptarlo; `BE-DELTA-06` lo cierra. No se dibuja ningún control que no pueda funcionar, pero ahora sí puede.

## Traceability

- **Objetivo operacional:** que el partner entienda lo que consume y lo que va a pagar, y que ningún ingreso de excedente se pierda en silencio.
- **RF cubiertos:** RF-APM-007, RF-APM-008, RF-APM-009, RF-APM-013 (capa de presentación).
- **CA heredados:** CA-APM-007, CA-APM-008, CA-APM-009, CA-APM-013.
- **Dependencias:** #07 frontend (módulo, guards, `GET /partners/me`), #08 backend (4 endpoints cerrados + 2 deltas).
- **Consumidores downstream:** ninguno.

## Technical Context

**Language/Version**: TypeScript 5.x · Angular **19.2** (standalone components, signals)

**Primary Dependencies**: `@angular/router` (lazy `loadChildren` sobre el módulo `partners` ya existente), `@angular/forms` (Reactive Forms para los filtros), RxJS 7.8, Tailwind CSS 4, Tabler Icons vía `shared/ui/icon/tabler-icon.component`

**Storage**: ninguno propio. El período seleccionado vive en la URL como query param, no en `localStorage`: un reporte debe poder compartirse por enlace.

**Testing**: Karma + Jasmine (`ng test`), `*.spec.ts` junto al componente. **`tsc --noEmit` no valida plantillas de Angular** — la verificación real es `ng test`.

**Target Platform**: navegador; breakpoints del design-system (Mobile <640, Tablet 640–1024, Desktop >1024)

**Project Type**: web app — solo capa frontend; el backend existe y está verificado contra Pinot real (9/9).

**Performance Goals**: ninguno propio. El techo lo pone la ingesta de Pinot (5–15 s), y por eso el auto-refresco va apagado por defecto. La UI **no** puede prometer menos latencia de la que el dato tiene.

**Constraints**:
- **Ningún indicador de severidad para el exceso de cupo** (RN-APM-002). Es una restricción dura, no una preferencia estética.
- Toda métrica muestra su **entorno** y su **marca temporal** (`datos_hasta`).
- `null` en `porcentaje_consumido` o `excedente_estimado` se renderiza «no aplica», **nunca 0**.
- Ningún PK se pide al usuario ni se muestra como campo principal; los partners se eligen por nombre.
- Las tablas de este módulo son **append-only**: solo `eye`, nunca `pencil` ni `trash`.

**Scale/Scope**: 4 superficies · 5 páginas · 4 endpoints cerrados **+ 2 deltas bloqueantes** (`BE-DELTA-04`, `BE-DELTA-05`) **+ 1 delta opcional** (`BE-DELTA-06`)

## Dependencias de backend

| ID | Estado | Cambio | Sin él |
|---|---|---|---|
| **BE-DELTA-04** | 🔴 **Bloqueante** | `GET /api/v1/facturacion/excepciones` | La cuarta superficie no tiene datos |
| **BE-DELTA-05** | 🔴 **Bloqueante** | Incluir los partners **no tarificables** en ese endpoint | El caso de RN-APM-014 sigue viviendo solo en un correo |
| **BE-DELTA-06** | 🔴 **Bloqueante** | `GET /logs-api` acepta `cursor`, `codigohttp`, `desde` y `hasta` | La consola tendría que filtrar en memoria, y el `next_cursor` seguiría anunciando una paginación inexistente |

> **BE-DELTA-06 apareció al planificar, no al especificar**, y pasó de opcional a bloqueante al
> decidirse que ningún filtro se resuelve en memoria. Cierra dos cosas a la vez: la paginación que
> el `meta` anunciaba sin aceptar, y los filtros de código y fecha que no existían.

## Constitution Check

*GATE: debe pasar antes de Phase 0 y re-evaluarse tras Phase 1.*

| Característica ISO/IEC 25010:2023 | Aplicación en esta capa | Veredicto |
|---|---|---|
| **Functional Suitability** | Cada pantalla traza a un CA-APM-* verificado en backend (405 tests, 9/9 contra Pinot real). No se inventa funcionalidad sin CU | ✅ |
| **Reliability** | Los tres estados no felices con los componentes compartidos en las cuatro superficies. El estado vacío **distingue** «no hubo consumo» de «no se pudo cargar»: confundirlos aquí haría que un mes correcto pareciera una caída | ✅ |
| **Performance Efficiency** | Sin umbral propio. Se decide **no** auto-refrescar por defecto porque refrescar más rápido que la ingesta no aporta dato nuevo, solo carga | ✅ |
| **Interaction Capability** | **Dominante.** El backend ya calcula bien; el valor de esta capa es decirlo bien. El riesgo mayor no es un error de cálculo, es que el partner interprete un coste previsto como una interrupción | ✅ |
| **Security** | Guards por rol en las cuatro rutas; control de propiedad heredado del backend (403). **Este módulo no maneja secretos**: a diferencia de #07, no hay nada que custodiar en pantalla | ✅ |
| **Compatibility** | Consume el contrato de #08 sin extenderlo; los dos deltas lo amplían de forma aditiva | ✅ |
| **Maintainability** | Reutiliza el módulo `partners/`, sus guards, su `ApiEnvelope` y los `app-list-*`. Cero componentes visuales nuevos de propósito general | ✅ |
| **Flexibility** | Sin acoplamiento a región. El período es un parámetro, no una constante | ✅ |
| **Safety** | **No aplica.** Fuera de la cadena crítica registro → asignación → despacho → confirmación. Mostrar mal una métrica de consumo no retrasa la atención de ninguna víctima ni altera una severidad | ➖ N/A |

### Tie-Breaker Mechanism

**Conflicto: Interaction Capability vs. Functional Suitability**, en FR-UI-103 (presentación del exceso de cupo).

- **Priorizado: Interaction Capability.** Lo funcionalmente «completo» sería marcar en rojo el medidor al superar el 100 % —es la convención de cualquier indicador— pero ese rojo **comunicaría un hecho falso**: que el servicio se interrumpió. RN-APM-002 dice lo contrario, y el SRS la documentó explícitamente *«para que nadie la corrija asumiendo que debería bloquear»*.
- **Trade-off aceptado:** el partner que supere su cupo verá un aviso deliberadamente menos llamativo de lo que el patrón visual pediría. A cambio, nadie corta su integración creyendo que se la cortaron.
- **Lo que NO se hizo:** usar `alerta-media` «como compromiso». Un ámbar sigue siendo el lenguaje de la advertencia, y el exceso no es una advertencia: es una compra.

**Segundo conflicto: Functional Suitability vs. Reliability**, en la paginación de la consola. Mostrar «Cargar más» sería más completo; un botón que no carga nada es peor que su ausencia. Priorizado **Reliability** hasta que `BE-DELTA-06` exista.

**Safety:** no aplica; no hay override.

## Project Structure

### Documentation (esta capa)

```text
specs/003-operational/Partners-API/api-monitoring-and-billing/frontend/
├── spec.md
├── plan.md                      # este archivo
├── research.md                  # 8 decisiones
├── data-model.md                # view-models derivados, ninguna entidad nueva
├── quickstart.md                # escenarios A–J
├── checklists/requirements.md   # 16/16
└── contracts/
    ├── consola-monitoreo.ui-contract.md    # DevAPIs + Administrador
    └── panel-consumo-partner.ui-contract.md
```

### Source Code (repository root)

```text
frontend/src/app/modules/partners/          # módulo YA EXISTENTE (#07)
├── partners.routes.ts                      # + 4 rutas
├── guards/
│   └── administrador.guard.ts              # NUEVO — excepciones es solo Admin
├── services/
│   ├── monitoreo-api.service.ts            # NUEVO — métricas, logs, reportes
│   ├── facturacion-api.service.ts          # NUEVO — excepciones (BE-DELTA-04/05)
│   └── models/
│       └── monitoreo.types.ts              # NUEVO — tipos del contrato
└── pages/
    ├── mi-consumo/                         # NUEVO — panel del partner
    ├── consola-logs/                       # NUEVO — lista Ver-only
    ├── detalle-log/                        # NUEVO — workpanel página dedicada
    ├── reporte-consumo/                    # NUEVO — con comparación
    └── excepciones-facturacion/            # NUEVO — cola del Administrador
```

**Structure Decision:** se **extiende** el módulo `partners/` de #07 en vez de crear uno nuevo. Los dos departamentos (consola y portal) ya conviven ahí con sidebars separados, y duplicar el módulo obligaría a duplicar guards y servicios. `partner-api.service.ts` no se toca: el monitoreo tiene su propio servicio porque son contratos distintos y mezclarlos haría crecer un archivo ya cargado.

## Phase 0: Research (completado)

Ver [`research.md`](./research.md) — 8 decisiones. Las de mayor impacto: **cómo se presenta el exceso sin mentir** (Decision 1), **el filtrado en dos capas y por qué se declara** (Decision 3), y **qué hace la UI cuando el backend dice `null`** (Decision 4).

## Phase 1: Design & Contracts (completado)

### Contratos de UI

| Artefacto | Cubre |
|---|---|
| `contracts/consola-monitoreo.ui-contract.md` | Rutas, endpoints, mapeo de errores y contrato visual de consola, reporte y excepciones |
| `contracts/panel-consumo-partner.ui-contract.md` | Panel de consumo dentro del portal existente |

**Invariante de esta capa:** ningún componente de estas cuatro superficies puede usar el token `alerta-critica` para representar consumo por encima del cupo. Es verificable revisando plantillas, y se comprueba en un test.

### Data model

Ver [`data-model.md`](./data-model.md) — **ninguna entidad nueva**: solo view-models derivados de las respuestas del backend, con la regla de centinelas (`null` → «no aplica») centralizada en un único sitio.

### Validación

Ver [`quickstart.md`](./quickstart.md) — escenarios A–J, con **B (el exceso no parece un fallo)**, **E (mes sin consumo ≠ error)** y **H (la cola de excepciones)** como los críticos.

## Phase 2: Task Decomposition (siguiente comando)

Ejecutar `/speckit-tasks`. Orden previsto:

1. `BE-DELTA-04` + `BE-DELTA-05` con sus contract tests (**bloquean la superficie 4**)
2. Tipos y servicios de monitoreo
3. Panel de consumo del partner (**MVP**: es la superficie más usada y la de mayor riesgo de comunicación)
4. Consola de registros + workpanel Ver-only
5. Reporte mensual con comparación
6. Excepciones de facturación
7. `nav-links.ts`, guards y matriz rol→navegación
8. Test de invariante: ningún token de severidad para el exceso de cupo

## Riesgos

| Riesgo | Mitigación |
|---|---|
| **Que alguien «arregle» el medidor de cupo poniéndolo en rojo** al superar el 100 % — parece un bug y no lo es | Test dedicado que falla si aparece un token de severidad en el bloque de cupo, con el porqué en el mensaje del aserto. Es la misma técnica que protegió `LimitesConsumoService` en backend |
| **Prometer tiempo real** y que el usuario crea que el dato es instantáneo | `datos_hasta` visible en consola y panel, con leyenda explícita del retraso |
| **Confundir cupo mensual con tasa por minuto** en el copy | Vocabulario fijado en `research.md` Decision 6 y usado literalmente en el contrato de UI |
| **Pintar un «Cargar más» que no carga** | Resuelto: `BE-DELTA-06` implementado, con test que recorre las páginas sin huecos ni repeticiones |
| **Que «Cargar más» pierda los filtros** y traiga filas que el usuario había excluido | Test dedicado: la página siguiente conserva `codigohttp`, y cambiar un filtro reinicia la paginación |
| **Que el reporte de un mes vacío parezca una caída** | Estado vacío con copy propio, distinto del de error (`research.md` Decision 7) |
| **Regresión silenciosa en plantillas** — `tsc --noEmit` no las valida | `ng test` es el gate; ya ocurrió tres veces en #07 con `@else if (… as x)` |

## Deuda técnica declarada

Ninguna abierta en esta capa. La que estaba declarada —`next_cursor` anunciando una paginación
inexistente— se cerró con `BE-DELTA-06` en vez de documentarse y dejarse.

## Complexity Tracking

Sin violaciones de la constitución que requieran excepción.

## Post-Design Constitution Re-Check

**PASS.** El diseño no introduce ninguna característica nueva ni relaja ninguna regla del backend. Los dos tie-breakers están resueltos a favor de la característica dominante (Interaction Capability) y de Reliability, con su trade-off escrito.

## Artifacts Generated

| Artefacto | Ruta |
|---|---|
| Plan | `…/api-monitoring-and-billing/frontend/plan.md` |
| Research | `…/api-monitoring-and-billing/frontend/research.md` |
| Data model | `…/api-monitoring-and-billing/frontend/data-model.md` |
| Quickstart | `…/api-monitoring-and-billing/frontend/quickstart.md` |
| UI contract (consola) | `…/frontend/contracts/consola-monitoreo.ui-contract.md` |
| UI contract (portal) | `…/frontend/contracts/panel-consumo-partner.ui-contract.md` |

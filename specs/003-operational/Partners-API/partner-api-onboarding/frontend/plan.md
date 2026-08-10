# Implementation Plan: Onboarding de Partners API — Frontend

**Capa**: `partner-api-onboarding/frontend` | **Fecha**: 2026-08-09 | **Spec**: [`spec.md`](./spec.md)

**Depends-on**: [`../backend/spec.md`](../backend/spec.md) · [`../backend/contracts/partner-api-onboarding.openapi.yaml`](../backend/contracts/partner-api-onboarding.openapi.yaml) · [`.specify/docs/design/design-system.md`](../../../../../.specify/docs/design/design-system.md)

> **Esta capa MUST NOT redefinir reglas de negocio, estados ni contratos REST.** El backend está
> implementado y verificado (81/81 tareas, 208 tests, 97 % de cobertura, 19/19 contra Pinot real).
> Todo lo que aquí se decide es **Interaction Capability**.

---

## ✅ Estado de precedencia — resuelto 2026-08-09

Este plan se escribió sobre un `spec.md` que era un stub sin FR-UI-*. **Ese hueco ya está cerrado:**
`/speckit-specify` formalizó **FR-UI-001…034**, seis historias US-FE-* con criterio medible cada
una, y ocho Success Criteria. `spec.md` es ahora la autoridad de requisitos de esta capa; este plan
y `data-model.md` quedan subordinados a él.

**Tres decisiones de esa sesión corrigen lo que este plan decía originalmente** (ya aplicadas más
abajo):

| Cambio | Antes decía | Ahora |
|---|---|---|
| **Lista Ver-only** | `eye` + `pencil`, workpanel de 3 modos | Solo `eye`, workpanel de **2 modos** (Ver y Crear). El backend **no expone PATCH de ficha**; aplica la «Variante Ver-only / CRUD parcial» del design-system |
| **`GET /partners/me`** | No contemplado | `BE-DELTA-01` — sin él el portal es **inalcanzable**: el `Profile` de sesión no lleva `idcliente` ni `idpartner` |
| **Secreto de producción** | Aprobar → navegar al paso del secreto | El Admin **no ve el secreto ajeno**. El partner emite su credencial productiva desde su portal (`BE-DELTA-02`) |

---

## Summary

Dos superficies Angular 19 sobre el mismo módulo `partners`, con **sidebars distintos por rol**
(design-system § 5) y sin ninguna lógica de negocio duplicada del backend:

| Superficie | Ruta base | Actor | Núcleo |
|---|---|---|---|
| **Consola de partners** | `/partners/consola` | Administrador · Desarrollador de APIs | Lista → workpanel de partners, registro (CU-O48), asignación de plan, y **cola de solicitudes pendientes** como vista de trabajo prioritaria con aprobar/rechazar (RF-PON-008) |
| **Portal del partner** | `/partners/portal` | Partner de integración | Su perfil y estado, emisión y nombrado de credenciales, regeneración tras vencimiento, solicitud de promoción y contrato versionado (RF-PON-011) |

El enfoque técnico se resume en tres decisiones que gobiernan todo lo demás:

1. **Patrón Lista → Workpanel como página dedicada, en variante Ver-only**, calcando el chrome del
   golden sample *Accidente Detalles* (link «← Volver a la lista», eyebrow de modo, `h1` + badges,
   secciones en cards, y en modo Ver `<dl>` en vez de `<input disabled>`). Dos modos: **Ver y
   Crear** — no hay Editar porque no hay endpoint que lo respalde.
2. **El secreto se entrega en un paso dedicado e irreversible**, no en un toast ni en una fila de
   tabla — es el punto de mayor riesgo de error de usuario del módulo.
3. **La UI envía `Idempotency-Key` en la emisión de credenciales.** El backend ya lo soporta y es
   lo que convierte un reintento por timeout en una recuperación del mismo secreto en vez de una
   credencial huérfana con el secreto perdido para siempre.

## Technical Context

**Language/Version**: TypeScript 5.x · Angular **19.2** (standalone components, sin NgModules)

**Primary Dependencies**: `@angular/router` (lazy `loadChildren`), `@angular/forms` (Reactive
Forms), RxJS 7.8, Tailwind CSS 4 (`@tailwindcss/postcss`), Tabler Icons vía
`shared/ui/icon/tabler-icon.component`

**Storage**: ninguno propio. Sesión y roles vía `AuthApiService`; recuerdo de la última fila
abierta con el patrón ya existente `lista-seleccion.storage.ts` del módulo `accidentes`

**Testing**: **Karma + Jasmine** (`ng test`), ficheros `*.spec.ts` junto al componente — mismo
patrón que `accidentes` y `suscripciones`

**Target Platform**: navegador; breakpoints del design-system (Mobile <640, Tablet 640–1024,
Desktop >1024)

**Project Type**: web app (frontend de un sistema cliente-servidor; el backend Django/DRF ya existe)

**Performance Goals**: el único umbral heredado es **CA-PON-014 (p95 emisión ≤ 2 s)**, medido en
backend con resultado **217 ms**. La UI no puede degradarlo: el botón de emisión usa el patrón de
botón en carga (deshabilitado + gerundio + spinner de 16px) y **devuelve el control en 10–15 s**
si no hay respuesta, según design-system § 5

**Constraints**:
- El secreto **nunca** se persiste en `localStorage`, `sessionStorage`, la URL ni el título del
  documento — solo vive en memoria del componente hasta que el usuario confirma haberlo guardado
- Ningún PK (`idpartner`, `idcliente`, `idcredencial`) se pide al usuario ni se muestra como campo
  principal de la UI (design-system § 5, «Chrome del workpanel»)
- El estado del partner es **derivado, nunca editable**

**Scale/Scope**: 2 superficies · 6 páginas · 8 endpoints REST ya cerrados **+ 2 deltas de backend**
(`BE-DELTA-01` `GET /partners/me`, `BE-DELTA-02` emisión productiva por el partner) · 6 estados
derivados

> **Los dos deltas son bloqueantes y reabren la capa `backend/`.** Están acotados en la sección
> «Dependencias de backend» de [`spec.md`](./spec.md) y deben ejecutarse **antes** que las tareas de
> UI que dependen de ellos.

## Constitution Check

*GATE: debe pasar antes de Phase 0 y re-evaluarse tras Phase 1.*

| Característica ISO/IEC 25010:2023 | Aplicación en esta capa | Veredicto |
|---|---|---|
| **Functional Suitability** | Cada pantalla traza a un CA-PON-* verificado en backend; no se introduce funcionalidad sin CU (CU-O48, CU-O49, CU-O50) | ✅ |
| **Reliability** | Los tres estados no felices (loading/vacío/error) son obligatorios en toda vista con datos asíncronos, con los componentes compartidos `app-list-*`. Un error de red al emitir no puede dejar al usuario sin saber si su credencial existe → se resuelve con `Idempotency-Key` + reconsulta del listado | ✅ |
| **Performance Efficiency** | Hereda CA-PON-014 (p95 ≤ 2 s). Lazy loading por ruta; paginación por cursor, nunca traer el listado completo | ✅ |
| **Interaction Capability** | **Es la razón de ser de esta capa.** Los cuatro puntos críticos del stub se tratan como requisitos, no como estética. Ver decisiones 2, 3, 4 y 5 de `research.md` | ✅ |
| **Security** | El secreto no se persiste en ningún almacenamiento del navegador ni viaja en la URL. Consola y portal son rutas con guards distintos; el partner no alcanza la resolución de promoción ni escribiendo la URL a mano | ✅ |
| **Compatibility** | Consume el contrato OpenAPI ya versionado sin extenderlo. El sobre de respuesta (`data`/`meta`/`code`) se maneja con el `ApiEnvelope` compartido | ✅ |
| **Maintainability** | Un solo componente de workpanel para los tres modos (Ver/Editar/Crear) y reutilización de los componentes compartidos en vez de reproducir el patrón visual — el `changelog.md` ya registra 10 páginas que lo reimplementaron a mano | ✅ |
| **Flexibility** | Sin acoplamiento a región ni ciudad. La superficie del partner no asume un número fijo de credenciales ni de servicios del catálogo | ✅ |
| **Safety** | **No aplica.** Este módulo está fuera de la cadena crítica registro → asignación → despacho → confirmación; ningún fallo de esta UI puede retrasar la atención de una víctima. Se declara explícitamente, como exige la Golden Rule | ➖ N/A |

### Tie-Breaker Mechanism

**Conflicto identificado: Security vs. Interaction Capability**, en RN-PON-005 (el secreto se
entrega una sola vez y es irrecuperable).

- **Priorizado: Security**, por la **regla 3** del mecanismo (excepción de dominio: datos sensibles
  en tránsito y en reposo). Es la misma resolución que ya tomó la capa backend, y esta capa no
  puede revertirla.
- **Trade-off aceptado:** fricción real para el partner que pierde su secreto — tendrá que emitir
  una credencial nueva. Se mitiga **sin ceder en seguridad**: (a) RF-PON-005 hace la rotación no
  disruptiva, así que emitir de nuevo no interrumpe las integraciones vivas; (b) la UI hace
  inequívoca la irreversibilidad *antes* de que el usuario pueda cerrar el paso; (c)
  `Idempotency-Key` evita que el caso más probable de pérdida —un timeout de red— llegue a ocurrir.
- **Lo que NO se hizo, deliberadamente:** ofrecer «volver a ver el secreto», guardarlo cifrado en
  el navegador, o enviarlo por correo. Las tres suavizarían la fricción destruyendo la garantía.

**Safety:** no aplica; no hay override.

## Project Structure

### Documentation (esta capa)

```text
specs/003-operational/Partners-API/partner-api-onboarding/frontend/
├── plan.md              # Este archivo
├── research.md          # Phase 0 — 10 decisiones
├── data-model.md        # Phase 1 — view models y FR-UI-* propuestos
├── quickstart.md        # Phase 1 — escenarios de validación
├── contracts/
│   ├── consola-partners.ui-contract.md
│   └── portal-partner.ui-contract.md
└── tasks.md             # Phase 2 — lo genera /speckit-tasks
```

### Source Code (repository root)

```text
frontend/src/app/
├── app.routes.ts                          # + entrada lazy 'partners'
├── shared/layout/nav-links.ts             # + grupo 'Partners y API' (Decisión 6)
└── modules/partners/                      # NUEVO — no existe hoy
    ├── partners.routes.ts
    ├── estado-partner.constants.ts        # etiqueta + ícono + tono por estado derivado
    ├── entorno.constants.ts               # Sandbox vs Producción (Decisión 5)
    ├── guards/
    │   ├── gestor-partners.guard.ts           # Administrador · DesarrolladorAPIs
    │   ├── administrador-promocion.guard.ts   # SOLO Administrador (RF-PON-008)
    │   └── partner-integracion.guard.ts       # rol PartnerIntegracion
    ├── services/
    │   ├── partner-api.service.ts
    │   ├── contrato-api.service.ts
    │   └── models/partner.types.ts
    └── pages/
        ├── lista-partners/                # Lista (consola)
        ├── detalle-partner/               # Workpanel 3 modos (consola)
        ├── cola-solicitudes/              # Vista de trabajo prioritaria (consola)
        ├── mi-integracion/                # Perfil + credenciales (portal)
        ├── secreto-emitido/               # Paso dedicado del secreto (Decisión 2)
        └── contrato-integracion/          # Documentación versionada (portal)
```

**Justificación de la estructura:** calca `modules/accidentes/` (routes + guards + services/models +
pages) porque es el golden sample que cita el design-system y porque un módulo que se lee igual que
sus vecinos es exactamente lo que exige el Principio VII en un proyecto de una sola persona.

## Complexity Tracking

Ninguna desviación de la constitución ni del design-system que requiera excepción documentada.

Dos puntos que **añaden trabajo pero no complejidad estructural**, y conviene tener presentes al
generar `tasks.md`:

| Punto | Por qué no se simplifica |
|---|---|
| Dos superficies en un solo módulo con tres guards distintos | Fusionarlas en una vista única con elementos ocultos por permiso viola la regla de sidebar por rol del design-system y expondría al partner la existencia de la consola |
| Página dedicada `secreto-emitido/` en vez de un modal | Un modal se cierra con `Esc` o con click fuera; el secreto se perdería sin confirmación. La irreversibilidad exige un paso que no se pueda descartar por accidente |

## Post-Design Constitution Re-Check

Re-evaluado tras generar `research.md`, `data-model.md`, `contracts/` y `quickstart.md`:

- **Sin nuevas violaciones.** Las 10 decisiones de Phase 0 se mantienen dentro del design-system;
  las dos que se apartan de la lectura literal (workpanel como página dedicada en la Decisión 1, y
  la Decisión 3 sobre el rechazo) están **expresamente permitidas** por el propio documento
  («El workpanel puede vivir como página dedicada cuando el spec lo declare»).
- **El único conflicto de características sigue siendo el ya arbitrado** (Security vs Interaction
  Capability en el secreto). El diseño de Phase 1 no introdujo ninguno nuevo.
- **Gap conocido y aceptado:** los FR-UI-* viven en `data-model.md` como propuesta, no en un
  `spec.md` cerrado. Documentado arriba en el Aviso de precedencia.

# Feature Specification: Onboarding de Partners API — Frontend

**Feature Branch / capa**: `partner-api-onboarding/frontend`

**Created**: 2026-08-08 · **FR cerrados**: 2026-08-09

**Status**: ✅ **Implementada** — 90/91 tareas; 459 tests en verde, cobertura 91,6 %. Pendiente solo la validación manual del quickstart (T088)

## Evidencia de cumplimiento (2026-08-09)

| Criterio | Evidencia |
|---|---|
| **SC-002** cero secretos perdidos por cierre accidental | La salida está deshabilitada hasta confirmar; `Esc` y el click fuera no cierran nada (página dedicada, no modal) — `secreto-emitido.page.spec.ts` |
| **SC-003** un reintento produce exactamente una credencial | La `Idempotency-Key` se reutiliza al fallar y solo se renueva tras un éxito — `mi-integracion.page.spec.ts` |
| **SC-004** cero ocurrencias del secreto fuera de su pantalla | Verificado en `localStorage`, `sessionStorage`, `location.href` y `document.title`; `client_secret_hash` no aparece en ningún archivo del módulo |
| **SC-005** cero «error inesperado» | Cada `code` del backend tiene copy propio; los desconocidos caen al `detail` del servidor |
| **SC-006** entornos distinguibles sin color | Encabezados separados con ícono y etiqueta de texto — verificado por test |
| **SC-007** recuperación sin intervención de otra persona | «Regenerar» reutiliza el flujo de emisión desde el propio portal |
| **SC-008** ningún rol alcanza lo que no puede | `administrador-promocion.guard` protege la ruta; el Desarrollador de APIs ve la cola sin acciones |
| **RNF cobertura ≥ 80 %** | **91,6 %** en el módulo; todas las carpetas sobre el umbral |

**SC-001** (incorporar un partner en menos de 2 minutos) requiere medición con una persona real:
queda para la validación manual del quickstart.

**Depends-on**: [`../backend/spec.md`](../backend/spec.md) (RF-PON-*, RNF-PON-*, CA-PON-*, OpenAPI). Esta capa **MUST NOT** redefinir reglas de negocio, estados ni contratos REST.

**Input**: Stub original de alcance (2026-08-08) + decisiones de `plan.md`/`research.md` (2026-08-09) + dos aclaraciones de sesión sobre huecos detectados en el backend cerrado.

---

## Alcance

Dos superficies con actores y necesidades distintas:

| Superficie | Actor | Cubre |
|---|---|---|
| **Consola de partners** | Administrador · Desarrollador de APIs | Listado de partners con filtros por estado · registro (CU-O48) · asignación de plan · **cola de solicitudes pendientes** como vista de trabajo prioritaria · aprobar/rechazar promoción con motivo obligatorio (RF-PON-008) |
| **Portal del partner** | Partner de integración | Su perfil y estado de incorporación · emisión y nombrado de credenciales (RF-PON-004/005) · regeneración tras vencimiento (RF-PON-006) · solicitud de promoción (RF-PON-007) · documentación versionada del contrato (RF-PON-011) |

## Puntos críticos heredados del dominio

Derivan de reglas del backend y **no** son decisiones libres de esta capa:

1. **Entrega del secreto una sola vez (RN-PON-005).** La UI debe hacer inequívoco que el valor no se
   podrá recuperar: paso dedicado, copia explícita y confirmación de guardado antes de cerrar. Es el
   punto de mayor riesgo de error de usuario del módulo (Principio IV).
2. **Rechazo de promoción con motivo obligatorio (RN-PON-007).** El motivo viaja al contacto técnico
   del partner: es un mensaje redactado, no un código de error.
3. **Separación de entornos (RN-PON-008).** Pruebas y producción coexisten; confundirlos al rotar
   sería un error caro. Distinguir por más que color.
4. **Estado derivado, no columna.** El estado se calcula (§ 9 del backend); la UI lo presenta pero
   nunca lo edita.

---

## Clarifications

### Session 2026-08-09

- **Q: ¿Cómo sabe el partner cuál es su propio `idpartner`?** Verificado en código: el `Profile` de
  sesión solo trae `{idusuario, gmail, roles[]}`, y `GET /partners` está reservado a
  `EsDesarrolladorAPIs`. Sin esto, **el portal es inalcanzable**.
  → **A: añadir `GET /partners/me` al backend** (`BE-DELTA-01`). Se prefirió sobre relajar
  `GET /partners` porque no altera la semántica de un endpoint ya cerrado y contract-testeado.
- **Q: al aprobar, el backend devuelve el secreto de producción al Administrador; ¿lo muestra la UI?**
  → **B: no.** El Admin solo confirma la promoción; el partner emite su credencial productiva desde
  su portal y es él quien ve el secreto (`BE-DELTA-02`). Mostrárselo al Admin lo obligaría a
  transmitirlo por un canal inseguro, que es justo lo que RN-PON-005 evita.
- **Q: ¿la lista lleva `pencil` (Editar)?** → **No.** El backend **no expone PATCH de ficha de
  partner**. Aplica la «Variante Ver-only / CRUD parcial» del design-system: solo `eye`, y nunca
  `pencil` deshabilitado. El workpanel tiene **dos modos: Ver y Crear**, no tres.
- **Q: ¿el Desarrollador de APIs ve la cola de solicitudes?** → Sí, en **solo lectura**: le sirve
  para dar seguimiento, pero las acciones de resolver son exclusivas del Administrador.
- **Q: ¿copy de los estados vacíos?** → Definido en [`research.md`](./research.md), sección final.

---

## Dependencias de backend (bloqueantes)

Esta capa **no puede completarse** sin estos dos cambios. Son pequeños y no alteran ninguna regla de
negocio ya verificada, pero reabren la capa `backend/`, que estaba cerrada con 81/81 tareas.

| ID | Cambio | Por qué es imprescindible | Impacto |
|---|---|---|---|
| **BE-DELTA-01** | `GET /api/v1/partners/me` — resuelve el partner del usuario autenticado a partir de su cliente; 404 si el usuario no tiene partner | Sin él ninguna pantalla del portal puede cargar: todos los endpoints exigen `{idpartner}` en la ruta y el partner no lo conoce | 1 vista + reutiliza `ClienteLookupService` y `verificar_propiedad` + tests de contrato |
| **BE-DELTA-02** | Permitir al partner emitir en entorno `Producción` **cuando su estado derivado ya es «Producción activa»** | Hoy `CredencialesView` rechaza `entorno=Producción` con 403 sin excepción. Con la decisión B, el partner debe poder emitir su credencial productiva y ver el secreto él mismo | Relajar la guarda de autoservicio condicionándola al estado derivado; **no** debilita RN-PON-004: sigue exigiendo aprobación previa |

> **BE-DELTA-02 no es un permiso nuevo, es mover dónde se comprueba.** La regla «producción requiere
> aprobación» se mantiene intacta; lo que cambia es que, una vez aprobada, la emisión la ejecuta
> quien debe custodiar el secreto.

---

## User Scenarios & Testing *(mandatory)*

### US-FE-1 — Incorporar un partner y darle cupo (P1)

Un Administrador registra el perfil de partner sobre un cliente existente y le asigna el plan de
acceso, dejando su cupo congelado.

**Why this priority**: es la puerta de entrada del módulo; sin ella no existe nada más.

**Independent Test**: registrar sobre un cliente con suscripción vigente y comprobar que el partner
queda listado con estado «Plan asignado» y su cupo visible.

**Acceptance Scenarios**:

1. **Given** un cliente con suscripción vigente, **When** el Administrador completa el registro,
   **Then** el partner aparece en la lista con estado «Registrado» y cupo «Sin asignar».
2. **Given** un cliente que ya tiene partner, **When** se intenta registrar otro, **Then** se
   muestra que ya existe **con un enlace a ese partner**, no un error genérico.
3. **Given** un cliente sin suscripción vigente, **When** se intenta registrar, **Then** se explica
   que debe resolverse en Suscripciones.

**Measurable criterion (Interaction Capability — user error protection)**: el 100 % de los rechazos
de registro (duplicado, sin suscripción, plan incompleto) se presentan con una explicación accionable
y **cero** mensajes de «error inesperado».

### US-FE-2 — Emitir una credencial y custodiar el secreto (P1) 🎯

El partner emite una credencial nombrada y recibe el secreto **una sola vez**.

**Why this priority**: es el punto de mayor riesgo de error de usuario del módulo. Un secreto perdido
es irrecuperable y obliga a rotar.

**Independent Test**: emitir una credencial y verificar que el secreto se muestra en un paso del que
no se puede salir sin confirmar, y que no queda rastro suyo tras abandonarlo.

**Acceptance Scenarios**:

1. **Given** un partner con plan asignado, **When** emite una credencial, **Then** el secreto se
   muestra en un paso dedicado con aviso de irreversibilidad **antes** del valor.
2. **Given** el paso del secreto abierto, **When** el usuario no ha confirmado el guardado,
   **Then** la salida está deshabilitada y ni `Esc` ni el click fuera lo cierran.
3. **Given** el secreto ya mostrado, **When** el usuario recarga la página, **Then** ve una
   explicación de que ya no está disponible y de cómo emitir otra sin romper las existentes.
4. **Given** un fallo de red durante la emisión, **When** el usuario reintenta, **Then** se obtiene
   **el mismo secreto** y **una sola credencial**.

**Measurable criterion (Security — confidentiality)**: **cero** apariciones del secreto en
`localStorage`, `sessionStorage`, la URL o el título del documento, verificable en el escenario D del
quickstart.

### US-FE-3 — Resolver la cola de solicitudes (P1)

Un Administrador revisa las solicitudes pendientes y las aprueba o rechaza con motivo.

**Why this priority**: la aprobación es humana por diseño (SRS L382); sin esta vista, las solicitudes
quedan esperando a que alguien mire por casualidad.

**Independent Test**: con una solicitud pendiente, aprobarla y comprobar que el partner pasa a
«Producción activa»; rechazarla y comprobar que vuelve a «Pruebas activo».

**Acceptance Scenarios**:

1. **Given** una solicitud pendiente, **When** el Administrador la aprueba, **Then** el partner queda
   en «Producción activa» y **no se muestra ningún secreto al Administrador**.
2. **Given** una solicitud pendiente, **When** se intenta rechazar sin motivo, **Then** el error es
   del campo y la petición no se envía.
3. **Given** una solicitud ya resuelta por otro Administrador, **When** un segundo intenta
   resolverla, **Then** se informa sin culpar al usuario y la cola se refresca sola.
4. **Given** un Desarrollador de APIs, **When** abre la cola, **Then** la ve en solo lectura y no
   alcanza la resolución ni escribiendo la URL.

**Measurable criterion (Functional Suitability — correctness)**: el 100 % de los rechazos llegan al
contacto técnico con el motivo **literal** que escribió el Administrador.

### US-FE-4 — Operar dos entornos sin confundirlos (P2)

El partner ve sus credenciales de pruebas y de producción conviviendo, sin riesgo de actuar sobre la
equivocada.

**Independent Test**: con credenciales en ambos entornos, verificar que siguen siendo distinguibles
con el color desactivado.

**Acceptance Scenarios**:

1. **Given** credenciales en ambos entornos, **When** el partner abre su portal, **Then** aparecen
   agrupadas bajo encabezados separados con ícono y etiqueta propios.
2. **Given** una credencial de producción, **When** se muestra su vigencia, **Then** dice «No expira»
   y nunca una fecha del año 9999.
3. **Given** una promoción recién aprobada, **When** el partner mira sus credenciales de pruebas,
   **Then** siguen activas y nada sugiere lo contrario.

**Measurable criterion (Interaction Capability — accessibility)**: los dos entornos siguen siendo
distinguibles con simulación de daltonismo activada (escenario K.3 del quickstart).

### US-FE-5 — Regenerar una credencial vencida (P2)

El partner recupera su acceso de pruebas por autoservicio, sin depender de un gestor.

**Acceptance Scenarios**:

1. **Given** una credencial de pruebas vencida, **When** el partner la mira, **Then** se distingue
   de una activa y ofrece regenerar.
2. **Given** una credencial regenerada, **When** se completa, **Then** las demás credenciales del
   partner siguen activas.

**Measurable criterion (Reliability — recoverability)**: el partner restablece su acceso de pruebas
**sin intervención de otra persona**.

### US-FE-6 — Consultar el contrato versionado (P3)

El partner consulta la versión vigente del contrato del servicio que integra y las soportadas.

**Acceptance Scenarios**:

1. **Given** un servicio con varias versiones, **When** el partner lo consulta, **Then** ve la
   vigente destacada y las soportadas con su fecha de retiro.
2. **Given** una versión sin fecha de retiro, **When** se muestra, **Then** dice «Sin retiro
   planificado» y nunca 01/01/1970.

**Measurable criterion (Compatibility — interoperability)**: el partner identifica en **una sola
pantalla** qué versión debe integrar y hasta cuándo vive la que ya usa.

---

## Functional Requirements (UI)

### Consola de partners (Administrador · Desarrollador de APIs)

- **FR-UI-001**: La lista muestra partner, plan, cupo mensual y estado (badge), paginada por cursor con «Cargar más». *(CA-PON-004)*
- **FR-UI-002**: Filtro por estado y CTA «Registrar partner» siempre visible en la cabecera.
- **FR-UI-003**: **Lista Ver-only**: única acción `eye`. **No hay `pencil`** — el backend no expone PATCH de ficha, y nunca se muestra deshabilitado.
- **FR-UI-004**: El registro elige el cliente **por nombre legible**; jamás se teclea `idcliente`. *(CA-PON-001)*
- **FR-UI-005**: Un duplicado se presenta con enlace al partner existente, usando el `idpartner_existente` que devuelve el backend. *(CA-PON-002)*
- **FR-UI-006**: La ausencia de suscripción vigente se explica indicando que se resuelve en Suscripciones. *(CA-PON-003)*
- **FR-UI-007**: «Asignar plan de acceso» muestra el cupo derivado que quedará **congelado** y advierte que un cambio posterior del plan del cliente no lo alterará. *(CA-PON-004)*
- **FR-UI-008**: La cola lista los partners en «Pendiente de aprobación», ordenados por antigüedad de la solicitud. *(CA-PON-009)*
- **FR-UI-009**: Aprobar exige confirmación en 2 pasos y, al completarse, **no muestra ningún secreto**: confirma la promoción e informa de que el partner emitirá su credencial productiva. *(Clarification Q2)*
- **FR-UI-010**: Rechazar exige motivo en texto libre con longitud mínima, advirtiendo que se envía al contacto técnico. *(CA-PON-010)*
- **FR-UI-011**: Las acciones de resolución existen **solo** para el Administrador; el Desarrollador de APIs ve la cola en lectura y no alcanza la ruta de resolución. *(RF-PON-008)*
- **FR-UI-012**: Una solicitud ya resuelta por otro Administrador se informa sin culpar al usuario y refresca la cola. *(concurrencia)*

### Portal del partner (PartnerIntegracion)

- **FR-UI-013**: El portal resuelve el partner del usuario autenticado sin pedirle ningún identificador. *(BE-DELTA-01)*
- **FR-UI-014**: «Mi integración» muestra estado derivado, plan, cupo y contacto técnico, **sin ningún control que edite el estado**.
- **FR-UI-015**: Cada estado va acompañado de una línea de «qué sigue», para que el partner nunca quede sin saber cuál es su siguiente paso.
- **FR-UI-016**: Las credenciales se agrupan **bajo encabezados por entorno**, con ícono y etiqueta; el color no es el único distintivo. *(RN-PON-008)*
- **FR-UI-017**: Emitir pide un nombre y valida en cliente que no colisione con otra **activa del mismo entorno**. *(CA-PON-006)*
- **FR-UI-018**: Un nombre duplicado se muestra como error **del campo nombre**, no global.
- **FR-UI-019**: Sin plan asignado, el CTA de emisión se sustituye por el copy que explica que un administrador debe asignarlo. *(CA-PON-007)*
- **FR-UI-020**: El secreto se muestra **una sola vez**, en paso dedicado, con copia explícita y confirmación de guardado que habilita la salida. *(CA-PON-005)*
- **FR-UI-021**: El secreto no se persiste en almacenamiento del navegador, la URL ni el título del documento, y no existe ruta para volver a verlo.
- **FR-UI-022**: Tras recargar el paso del secreto, se explica que ya no está disponible y cómo emitir otra sin interrumpir las existentes.
- **FR-UI-023**: La emisión envía una clave de idempotencia, reutilizada si el usuario reintenta tras un fallo de red. *(evita credencial huérfana con secreto perdido)*
- **FR-UI-024**: Una credencial vencida se distingue de una activa y ofrece regenerar por autoservicio. *(CA-PON-008)*
- **FR-UI-025**: La vigencia «no expira nunca» se muestra como «No expira», jamás como fecha del año 9999.
- **FR-UI-026**: Solicitar producción solo se ofrece en «Pruebas activo»; en otro estado se explica la ruta obligatoria en vez de fallar. *(CA-PON-009)*
- **FR-UI-027**: Tras aprobarse la promoción, el partner puede emitir su credencial de producción desde su portal y es **él** quien ve el secreto. *(BE-DELTA-02, Clarification Q2)*
- **FR-UI-028**: El contrato se consulta **por servicio** (elegido por nombre), mostrando la vigente y las soportadas con su fecha de retiro. *(CA-PON-013)*
- **FR-UI-029**: «Sin retiro planificado» y «sin documento publicado» se muestran como tales; nunca 01/01/1970 ni un enlace roto.

### Transversales

- **FR-UI-030**: Toda vista con datos asíncronos implementa los estados de carga, vacío y error con los componentes compartidos del sistema; el error ofrece reintentar sin recargar.
- **FR-UI-031**: Ninguna vista expone el hash del secreto ni el secreto fuera de su paso dedicado. *(CA-PON-005)*
- **FR-UI-032**: Ningún identificador interno se pide al usuario ni se muestra como campo principal.
- **FR-UI-033**: El sidebar del partner y el del gestor son **distintos y no se fusionan** (departamentos distintos). El rol de partner debe añadirse a la matriz de navegación, donde hoy no existe.
- **FR-UI-034**: Un partner suspendido ve su estado y **no se le ofrecen** acciones de habilitación. *(CA-PON-012)*

---

## Success Criteria

Medibles y verificables sin conocer la implementación:

- **SC-001**: Un administrador incorpora un partner nuevo y le deja el cupo asignado en **menos de 2 minutos**, sin consultar documentación.
- **SC-002**: **Cero** secretos perdidos por cierre accidental del paso de entrega, en 20 emisiones consecutivas de prueba.
- **SC-003**: Un reintento tras fallo de red produce **exactamente una** credencial, en el 100 % de los intentos.
- **SC-004**: **Cero** ocurrencias del secreto fuera de la pantalla que lo entrega (almacenamiento, URL, título).
- **SC-005**: El 100 % de los errores de negocio del backend se presentan con explicación accionable; **cero** «error inesperado».
- **SC-006**: Pruebas y producción siguen siendo distinguibles con el color desactivado.
- **SC-007**: Un partner recupera su acceso de pruebas vencido **sin intervención de otra persona**.
- **SC-008**: Ningún usuario alcanza una acción que su rol no puede ejecutar, ni escribiendo la URL a mano.

## Out of Scope

- Cambiar reglas de negocio, estados derivados, validaciones de servidor, Kafka o Pinot.
- Ampliar el contrato OpenAPI **más allá de `BE-DELTA-01` y `BE-DELTA-02`**, que están acotados arriba.
- Revocación de credenciales y suspensión por mora — son de los módulos **#09** y **#08**.
- Edición de la ficha del partner: **no existe** endpoint de modificación y esta capa no lo introduce.
- Consumo de la API por parte del partner (métricas, facturación) — módulo **#08**.

## Assumptions

- El rol `PartnerIntegracion` (idrol 15) ya existe en backend desde 2026-08-08; **falta únicamente**
  su entrada en la matriz de navegación del frontend.
- Un usuario partner pertenece a **un solo cliente**, y un cliente tiene **un solo** perfil de
  partner (RN-PON-002) — por eso `BE-DELTA-01` puede resolver un único partner sin ambigüedad.
- El Desarrollador de APIs no necesita registrar partners *y* resolver promociones a la vez: son
  responsabilidades separadas por RF-PON-008 y así se mantienen.
- Los umbrales de rendimiento se heredan del backend (CA-PON-014, p95 ≤ 2 s, medido en 217 ms); esta
  capa no introduce ninguno propio.

## ISO/IEC 25010:2023 — Justificación

| Characteristic | Treatment |
|---|---|
| **Interaction Capability** | Núcleo de esta capa (Principio IV). US-FE-2 y US-FE-4 son requisitos de prevención de error, no de estética |
| **Functional Suitability** | Cada FR-UI cita un CA-PON-* ya verificado en backend |
| **Security** | El secreto no se persiste en el navegador (SC-004); guards distintos por superficie; el Admin deja de ver secretos ajenos (Clarification Q2) |
| **Reliability** | Estados de carga/vacío/error obligatorios; la idempotencia evita credenciales huérfanas ante fallo de red |
| **Maintainability** | Capa separada de `backend/`; reutiliza los componentes compartidos en vez de reproducir el patrón visual |
| **Compatibility** | US-FE-6 expone el contrato versionado; no se rompe ninguna integración viva |
| **Performance Efficiency** | Heredada del backend (CA-PON-014). Sin umbral propio |
| **Flexibility** | Sin acoplamiento a región ni a un número fijo de credenciales o servicios |
| **Safety** | **No aplica** — fuera de la cadena crítica registro → asignación → despacho → confirmación; ningún fallo de esta UI puede retrasar la atención de una víctima |

**Traceability**: índice del módulo [`../partner-api-onboarding.md`](../partner-api-onboarding.md) ·
plan de esta capa [`plan.md`](./plan.md) · contratos de UI [`contracts/`](./contracts/)

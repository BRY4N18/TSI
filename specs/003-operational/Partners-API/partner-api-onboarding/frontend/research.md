# Phase 0 — Research: Frontend de Onboarding de Partners API

Diez decisiones. Cada una resuelve un `NEEDS CLARIFICATION` del Technical Context o un punto que el
stub de `spec.md` dejó abierto. Las que se apoyan en código existente citan el archivo verificado,
no una suposición.

---

## Decisión 1 — El workpanel es una **página dedicada**, no un split-view

- **Decisión:** `pages/detalle-partner/` es una ruta propia (`/partners/consola/:idpartner`), con
  el chrome del golden sample *Accidente Detalles*: link «← Volver a la lista» con ícono
  `arrow-left`, eyebrow de modo, `h1` + badge(s) en la misma fila, secciones en cards.
- **Rationale:** el design-system § 5 lo permite explícitamente («El workpanel puede vivir como
  **página dedicada** (no split-view) cuando el spec lo declare»), y el módulo `accidentes` ya lo
  implementa así (`pages/detalle-accidente/detalle-accidente.page.ts`). Copiar el vecino es lo que
  mantiene bajo el coste de mantenimiento en un proyecto de una sola persona (Principio VII).
- **Alternativas consideradas:** split-view lista+panel a 640–720px. Descartado porque el detalle
  del partner incluye **dos colecciones anidadas** (credenciales e historial) que en un panel
  estrecho obligarían a scroll excesivo y romperían la agrupación por proximidad (Gestalt).

## Decisión 2 — El secreto se entrega en un **paso dedicado con confirmación de guardado**

- **Decisión:** tras un `201` de emisión, la app navega a `pages/secreto-emitido/`, que muestra el
  `client_id` y el `client_secret` en `JetBrains Mono`, un botón «Copiar» explícito, y un
  **checkbox de confirmación** («He guardado el secreto en un lugar seguro») que es lo único que
  habilita el botón de salida. El secreto vive **solo en memoria** del componente.
- **Rationale:** RN-PON-005 lo hace irrecuperable, y el stub ya identifica esto como «el punto de
  mayor riesgo de error de usuario del módulo». El Principio IV pone la prevención de error por
  encima de la estética para roles operativos.
- **Alternativas consideradas:**
  - *Modal:* descartado — se cierra con `Esc` o click fuera, y el secreto se perdería sin que el
    usuario lo haya guardado.
  - *Toast con el secreto:* descartado — el design-system define el Toast como confirmación pasiva
    con auto-dismiss; un valor irrecuperable que se desvanece solo en 6 s es exactamente el
    antipatrón.
  - *Mostrarlo en la fila de la tabla:* descartado — quedaría en el DOM y en cualquier captura de
    pantalla del listado.
- **Consecuencia a cubrir en `tasks.md`:** al abandonar la página (navegación, recarga o cierre),
  el valor se descarta sin rastro; no hay ruta que permita volver a ella.

## Decisión 3 — El rechazo de promoción se captura como **mensaje redactado**, no como código

- **Decisión:** el formulario de rechazo usa un `textarea` con contador de caracteres, `minlength`
  y texto de ayuda que dice explícitamente que el motivo **se envía al contacto técnico del
  partner**. No hay lista desplegable de motivos predefinidos.
- **Rationale:** RN-PON-007 obliga al motivo porque es lo que permite corregir; el backend lo
  incluye literalmente en el correo (`partner_notificacion_service.notificar_rechazo`). Un código
  de catálogo produciría avisos inaccionables del tipo «Motivo: MOTIVO_03».
- **Alternativas consideradas:** select de motivos tipificados + campo libre opcional. Descartado:
  el camino de menor esfuerzo sería elegir el tipificado y dejar el texto vacío, que es justo el
  resultado que la regla quiere evitar.
- **Validación en UI:** el `422 motivo_requerido` del backend nunca debería alcanzarse desde esta
  interfaz; si llega, se muestra como error de campo, no como error genérico.

## Decisión 4 — El estado derivado se presenta con **badge de ícono + etiqueta**, jamás editable

- **Decisión:** `estado-partner.constants.ts` mapea cada uno de los seis estados
  (`Registrado`, `Plan asignado`, `Pruebas activo`, `Pendiente de aprobación`, `Producción activa`,
  `Suspendido`) a etiqueta, ícono Tabler y token semántico. Se renderiza como chip (radio 6–8px) y
  **no existe ningún control que lo modifique**.
- **Rationale:** § 9 del backend lo calcula a partir de las credenciales y la bitácora; exponerlo
  como editable crearía la expectativa de un endpoint que no existe y no debe existir.
- **Alternativas consideradas:** teñir la fila entera según el estado. Descartado explícitamente
  por el design-system § 5 («nunca coloreadas completas según severidad/estado»).

## Decisión 5 — Pruebas y producción se distinguen por **ícono + etiqueta + agrupación**, no por color

- **Decisión:** las credenciales se listan **agrupadas por entorno bajo encabezados separados**
  («Pruebas» / «Producción»), cada uno con su ícono Tabler fijo, y el chip de entorno acompaña a
  cada credencial. El color es refuerzo, nunca el portador de la distinción.
- **Rationale:** RN-PON-008 hace que ambos entornos coexistan, y el stub advierte que confundirlos
  al revocar o rotar «sería un error caro». La accesibilidad del design-system § 6 exige que el
  color nunca sea el único medio.
- **Alternativas consideradas:** una sola tabla con columna «Entorno». Descartado: en una lista
  larga, una columna se escanea peor que una separación estructural, y el error que se quiere
  evitar es precisamente actuar sobre la credencial equivocada.

## Decisión 6 — El rol `PartnerIntegracion` **no existe todavía** en la navegación

- **Hallazgo verificado:** `frontend/src/app/shared/layout/nav-links.ts` es la fuente de verdad de
  qué ve cada rol, y **no contiene ninguna entrada para `PartnerIntegracion`**; el rol existe en
  backend (idrol 15) desde 2026-08-08, pero la UI nunca lo navegó.
- **Decisión:** añadir un grupo `Partners y API` con entradas separadas por superficie:
  - «Partners» y «Solicitudes pendientes» → `['Administrador', 'DesarrolladorAPIs']`
  - «Mi integración» y «Contrato de integración» → `['PartnerIntegracion']`
- **Rationale:** la regla de sidebar por rol prohíbe un sidebar único con ítems deshabilitados. Al
  ser roles de **departamentos distintos**, no se fusionan: el partner nunca ve la consola.
- **Consecuencia:** hay que actualizar también la «Matriz rol → navegación UI» de `module-map.md`,
  que el propio `nav-links.ts` cita como documentación espejo.

## Decisión 7 — La UI envía `Idempotency-Key` en la emisión de credenciales

- **Decisión:** `partner-api-service.emitirCredencial()` genera un UUID v4 por intento del usuario
  (no por reintento HTTP) y lo envía en la cabecera `Idempotency-Key`. El mismo valor se reutiliza
  si el usuario pulsa «Reintentar» tras un fallo de red.
- **Rationale:** el backend lo implementó en esta misma sesión (`apps/partners/idempotency.py`) con
  una ventana de 60 s para el ámbito de emisión. Sin la cabecera, un timeout de red hace que el
  usuario reintente, se emita **una credencial de más** y el secreto de la primera se pierda para
  siempre — solo se persistió su hash. Es la mitigación (c) del Tie-Breaker del plan.
- **Alternativas consideradas:** no enviarla y confiar en que el usuario revise el listado antes de
  reintentar. Descartado: depende de que el usuario haga lo correcto bajo la fricción de un error.

## Decisión 8 — La cola de solicitudes se deriva del **listado filtrado**, no de un endpoint nuevo

- **Decisión:** `pages/cola-solicitudes/` consume `GET /partners?estado=Pendiente de aprobación`,
  que el contrato OpenAPI ya soporta.
- **Rationale:** Principio VI y la regla de esta capa — el frontend no puede exigir contrato nuevo
  a un backend cerrado y verificado. El filtro por estado ya existe y basta.
- **Alternativas consideradas:** pedir un `GET /partners/solicitudes-pendientes`. Descartado: sería
  un endpoint redundante y obligaría a reabrir una capa ya cerrada.

## Decisión 9 — Paginación por cursor, reutilizando el patrón de `accidentes`

- **Decisión:** la lista usa `limit` + `cursor` del `meta.pagination` del sobre de respuesta, con
  botón «Cargar más», igual que `AccidenteApiService`.
- **Rationale:** el backend pagina por cursor (`PartnerRepository.list`) precisamente porque Pinot
  aplica un `LIMIT 10` implícito a las consultas sin límite explícito. Un frontend que pidiera
  «todo» recibiría 10 filas silenciosamente y nadie se enteraría.
- **Alternativas consideradas:** paginación por número de página. Descartado: el backend no la
  expone y el keyset no la permite de forma estable.

## Decisión 10 — Los tres estados no felices usan los **componentes compartidos**, sin excepción

- **Decisión:** toda vista con datos asíncronos usa `app-list-loading-skeleton`,
  `app-list-error-state` y `app-list-empty-state` de `shared/ui/list-states/`.
- **Rationale:** el design-system lo exige y el `changelog.md` registra que ya hubo que corregir
  **10 páginas** que reprodujeron el patrón con HTML propio. Repetir ese error aquí sería repetir
  un fallo del que el proyecto ya tiene registro escrito.
- **Excepción admitida por el propio design-system:** markup inline solo donde la forma real del
  contenido no sea una tabla ni una card genérica — aquí aplica únicamente al bloque de
  credenciales agrupadas por entorno de la Decisión 5, que no es una lista plana.

---

## Copy de los estados vacíos (lo fija esta capa, no el design-system)

El design-system fija el patrón visual y delega el contenido al spec del módulo:

| Vista | Vacío | Acción |
|---|---|---|
| Lista de partners | «Todavía no hay partners registrados.» | «Registrar partner» |
| Cola de solicitudes | «No hay solicitudes pendientes de aprobación.» | — (es un estado deseable, no un error) |
| Credenciales del partner | «Aún no has emitido ninguna credencial.» | «Emitir credencial» |
| Credenciales sin plan | «Tu plan de acceso aún no está asignado. Un administrador debe asignarlo antes de que puedas emitir credenciales.» | — |
| Contrato de integración | «Este servicio todavía no tiene una versión publicada.» | — |

La cuarta fila importa: es el estado en que el backend devuelve `409 sin_plan`, y sin ese copy el
partner vería un botón que falla sin explicar por qué depende de otra persona.

# UI Contract — Consola de partners

**Actores:** Administrador · Desarrollador de APIs
**Ruta base:** `/partners/consola`
**Guard:** `gestor-partners.guard` (`['Administrador', 'DesarrolladorAPIs']`)

---

## Rutas

| Ruta | Página | Modo | Guard adicional |
|---|---|---|---|
| `/partners/consola` | `lista-partners` | — | — |
| `/partners/consola/nuevo` | `detalle-partner` | Crear | — |
| `/partners/consola/:idpartner` | `detalle-partner` | Ver | — |
| `/partners/consola/solicitudes` | `cola-solicitudes` | — | — |
| `/partners/consola/solicitudes/:idpartner/resolver` | `cola-solicitudes` (panel) | — | **`administrador-promocion.guard`** |

> **No hay ruta `/editar`.** El backend no expone PATCH de ficha de partner, así que aplica la
> variante **Ver-only** del design-system: el workpanel tiene dos modos, Ver y Crear (FR-UI-003).

> La última fila es el control real de RF-PON-008: el Desarrollador de APIs **no** alcanza la
> resolución ni escribiendo la URL. El backend ya devuelve 403, pero una UI que deje llegar hasta el
> formulario y falle al enviar es una UI que promete algo que no puede cumplir.

## Endpoints consumidos

| Acción | Método y ruta | Cabeceras | Códigos que la UI trata explícitamente |
|---|---|---|---|
| Listar | `GET /api/v1/partners?limit&cursor&estado` | — | 200 |
| Detalle | `GET /api/v1/partners/{idpartner}` | — | 200 · 403 · 404 |
| Registrar | `POST /api/v1/partners` | `Idempotency-Key` | 201 · 400 · **404** · **409** · **422** |
| Asignar plan | `POST /api/v1/partners/{idpartner}/plan-acceso` | `Idempotency-Key` | 200 · 404 · **422** |
| Resolver promoción | `POST /api/v1/partners/{idpartner}/solicitud-produccion/resolucion` | `Idempotency-Key` | 200 · 403 · **409** · **422** |

## Mapeo de errores → interfaz

Ningún código de la columna izquierda puede llegar al usuario como «Error inesperado».

| `code` | HTTP | Qué ve el usuario | Dónde |
|---|---|---|---|
| `validation_error` | 400 | Mensaje bajo el campo afectado | Campo |
| `not_found` | 404 | «El cliente indicado no existe» / «El partner no existe» | Banner de sección |
| `partner_duplicado` | 409 | «Este cliente ya tiene un partner registrado», **con enlace al partner existente** (el backend devuelve `idpartner_existente`) | Banner + link |
| `sin_suscripcion` | 422 | «El cliente no tiene una suscripción vigente. Debe resolverse en Suscripciones antes de registrar el partner.» | Banner de sección |
| `plan_incompleto` | 422 | «El plan contratado no declara sus límites de API. Debe corregirse en el catálogo de planes.» | Banner de sección |
| `sin_solicitud_pendiente` | 409 | «Esta solicitud ya fue resuelta por otro administrador.» + refresco de la cola | Alert modal |
| `motivo_requerido` | 422 | Error del campo motivo | Campo |
| `propiedad_partner` | 403 | Redirección a `access-denied` | Ruta |

La fila `sin_solicitud_pendiente` merece atención: es el caso de **dos administradores resolviendo
la misma solicitud a la vez**. No es un error del usuario, así que el copy no debe culparlo, y la
cola debe refrescarse sola para que no vuelva a intentarlo.

## Lista de partners — contrato visual

- CTA primario **«Registrar partner»** arriba, siempre visible.
- Filtro por estado (chips o select) — los seis valores de `EstadoPartner`.
- Columnas: Partner · Plan · Cupo mensual · Estado (badge) · Acciones.
- **`idpartner` no es columna.** Si se muestra, es como texto plano en `JetBrains Mono` dentro del
  detalle, nunca como link ni como identificador principal de la fila.
- Acción única: `eye` (Ver detalles), 44×44px de área de toque, con tooltip y `aria-label`.
  **Nunca un `pencil` deshabilitado** — no exponer lo que no se puede hacer (FR-UI-003).
- Cupo `-1` → «Sin asignar». Plan `''` → «Sin plan».
- Al volver del detalle, la última fila abierta se marca con `accent-primary` al ~0.06–0.08.
- Mobile: cada fila colapsa a card con etiqueta-valor.

## Workpanel de partner — contrato visual

Chrome obligatorio (golden sample *Accidente Detalles*):

1. Link **«← Volver a la lista»** con ícono `arrow-left`, arriba a la izquierda.
2. Eyebrow de modo: «Detalles» / «Editar partner» / «Nuevo partner».
3. `h1` con `nombrepartner` + badge de estado en la **misma fila**.
4. Secciones en cards: *Identificación* · *Plan y cupo* · *Credenciales* · *Historial*.

| Modo | Campos | Acción en header |
|---|---|---|
| Ver | `<dl>` con `dt` uppercase + `dd` — **nunca `<input disabled>`** | — |
| Crear | Editables, formulario vacío, **mismo componente** | «Guardar» |

**Acciones de dominio** («Asignar plan de acceso») se rigen por **estado y rol**, no por el modo:
visibles en Ver, y ausentes si el partner está suspendido (CA-PON-012). Que la lista sea Ver-only no
las elimina — el modo gobierna la editabilidad de los campos, nunca qué acciones de negocio existen.

**Selección de cliente en modo Crear:** combobox por nombre legible del cliente. Está
explícitamente prohibido pedir `idcliente` (design-system § 5).

## Cola de solicitudes — contrato visual

- Es una **vista de trabajo**, no un listado más: su estado vacío («No hay solicitudes pendientes»)
  es un resultado deseable y no debe leerse como error.
- Cada entrada muestra partner, contacto técnico, nombre de credencial solicitado y antigüedad.
- Dos acciones: **Aprobar** (confirmación en 2 pasos) y **Rechazar** (abre el formulario de motivo).
- **Aprobar NO muestra ningún secreto.** Confirma la promoción e informa de que el partner emitirá
  su credencial productiva desde su portal. El Administrador no debe ver el secreto de un tercero:
  no tendría canal seguro para entregárselo (FR-UI-009, `BE-DELTA-02`).
- Botón de aprobar en estado de carga: deshabilitado, «Aprobando…», spinner de 16px dentro del
  botón. A los 10–15 s sin respuesta vuelve a su estado normal y dispara el feedback de error.

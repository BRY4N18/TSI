# UI Contract — Portal del partner

**Actor:** Partner de integración (`PartnerIntegracion`, idrol 15)
**Ruta base:** `/partners/portal`
**Guard:** `partner-integracion.guard`

> El partner **nunca** ve ni alcanza `/partners/consola`. Son departamentos distintos: los sidebars
> no se fusionan (design-system § 5).

---

## Rutas

| Ruta | Página | Nota |
|---|---|---|
| `/partners/portal` | `mi-integracion` | Perfil, plan, cupo y credenciales agrupadas por entorno |
| `/partners/portal/credencial-emitida` | `secreto-emitido` | **Sin parámetros de ruta.** Ver más abajo |
| `/partners/portal/contrato` | `contrato-integracion` | Contrato versionado por servicio |

## Endpoints consumidos

| Acción | Método y ruta | Cabeceras | Códigos tratados |
|---|---|---|---|
| **Resolver mi partner** | **`GET /api/v1/partners/me`** (`BE-DELTA-01`) | — | 200 · **404** (usuario sin partner) |
| Mi perfil | `GET /api/v1/partners/{idpartner}` | — | 200 · 403 |

> **`GET /partners/me` es el primer requisito de todo el portal.** El `Profile` de sesión solo trae
> `{idusuario, gmail, roles[]}`: sin este endpoint el partner no conoce su `idpartner` y **ninguna
> pantalla puede cargar**. Su `404` se muestra como «Tu usuario aún no tiene un perfil de partner
> asociado; contacta al administrador», nunca como pantalla rota.
| Mis credenciales | `GET /api/v1/partners/{idpartner}/credenciales?entorno&solo_activas` | — | 200 · 403 |
| Emitir credencial | `POST /api/v1/partners/{idpartner}/credenciales` | **`Idempotency-Key`** | 201 · 400 · **409** |
| Solicitar producción | `POST /api/v1/partners/{idpartner}/solicitud-produccion` | `Idempotency-Key` | **202** · 400 · **409** |
| Contrato | `GET /api/v1/contrato-integracion?id_servicio&version` | — | 200 · 400 · 404 |

**El 202 de la solicitud no es un 201 disfrazado.** La UI debe comunicar que la petición quedó
registrada y que **una persona debe aprobarla**: nada ocurre automáticamente después.

## Mapeo de errores → interfaz

| `code` | HTTP | Qué ve el partner |
|---|---|---|
| `sin_plan` | 409 | No debería llegar: el CTA ya está sustituido por el copy explicativo (FR-UI-016). Si llega, banner: «Tu plan de acceso aún no está asignado.» |
| `nombre_duplicado` | 409 | Error **del campo nombre**: «Ya tienes una credencial activa con ese nombre en este entorno.» |
| `partner_suspendido` | 409 | Banner crítico: «Tu acceso está suspendido. Contacta al administrador.» — sin CTAs de habilitación |
| `ruta_invalida` | 409 | No debería llegar (FR-UI-021). Si llega: «Debes tener una credencial de pruebas activa antes de solicitar producción.» |
| `validation_error` | 400 | Error del campo |

## Mi integración — contrato visual

**Bloque de estado.** Badge del estado derivado + una línea que explica **qué sigue**, porque un
estado sin siguiente paso deja al partner sin saber qué hacer:

| Estado | Línea de «qué sigue» |
|---|---|
| Registrado | «Un administrador debe asignarte un plan de acceso.» |
| Plan asignado | «Ya puedes emitir tu primera credencial de pruebas.» |
| Pruebas activo | «Cuando tu integración esté lista, solicita el paso a producción.» |
| Pendiente de aprobación | «Tu solicitud está en revisión. Te avisaremos al correo del contacto técnico.» |
| Producción activa | «Tu integración está en producción. Tus credenciales de pruebas siguen activas.» |
| Suspendido | «Tu acceso está suspendido. Contacta al administrador.» |

**Bloque de plan y cupo.** Plan, llamadas/mes y llamadas/minuto. `-1` → «Sin asignar».

**Bloque de credenciales — agrupado por entorno** (Decisión 5), nunca una tabla plana:

```
┌ 🧪 Pruebas ─────────────────────────────────────────────┐
│  plataforma-siniestros   Activa    Vence 12/09/2026      │
│  deteccion-fraude        Vencida   Venció 01/08/2026  [Regenerar] │
└──────────────────────────────────────────────────────────┘
┌ ⚡ Producción ───────────────────────────────────────────┐
│  produccion-siniestros   Activa    No expira             │
└──────────────────────────────────────────────────────────┘
```

- Cada grupo lleva su ícono Tabler y su etiqueta; el color es refuerzo, no el distintivo.
- `fecha_expiracion` con el centinela → **«No expira»**, jamás una fecha del 9999.
- Una credencial vencida se distingue de una activa y ofrece **«Regenerar»** por autoservicio: no
  requiere a un gestor (CA-PON-008).
- El bloque de producción **no aparece** si el partner nunca fue promovido — no se muestra vacío
  sugiriendo que le falta algo que aún no le corresponde.
- **Recién aprobada la promoción**, el bloque de producción aparece con un CTA «Emitir credencial de
  producción»: es el partner quien la emite y quien ve el secreto (FR-UI-027, `BE-DELTA-02`). El
  Administrador que aprobó nunca lo vio.

## Secreto emitido — el contrato más estricto de esta capa

**Ruta sin parámetros a propósito.** El secreto llega por estado de navegación en memoria, nunca por
la URL: una URL se comparte, se guarda en el historial y aparece en logs de proxy.

Requisitos, todos verificables:

1. `client_id` y `client_secret` en `JetBrains Mono`, cada uno con su botón **«Copiar»** explícito.
2. Aviso inequívoco y **antes** del valor: «Este secreto se muestra una sola vez. No podremos
   volver a mostrártelo.»
3. Un **checkbox de confirmación** — «He guardado el secreto en un lugar seguro» — que es lo único
   que habilita el botón de salida.
4. **Sin `Esc`, sin click-fuera, sin botón de cerrar** que salte el checkbox.
5. Al abandonar la página, el valor se descarta. **No existe ruta para volver.**
6. El secreto no toca `localStorage`, `sessionStorage`, la URL ni `document.title`.
7. Si el usuario recarga, ve el estado vacío de la página con la explicación de que el secreto ya no
   está disponible y de que puede emitir otra credencial sin interrumpir las existentes.

El punto 7 importa tanto como los demás: es el escenario en que el usuario ya perdió el secreto, y
la UI debe decirle exactamente cómo recuperarse en vez de dejarlo en una pantalla rota.

## Solicitar producción — contrato visual

- **Solo visible en «Pruebas activo».** En cualquier otro estado se explica la ruta obligatoria en
  vez de ofrecer un botón que fallará (FR-UI-021).
- Pide el `nombre_credencial` que tendrá la credencial de producción.
- Tras el 202: mensaje de que la solicitud quedó registrada y **espera aprobación humana**. El
  estado pasa a «Pendiente de aprobación» y el botón desaparece.
- Si fue rechazada antes, el partner puede volver a solicitar: **no hay tope de reintentos**, y la
  UI no debe insinuar lo contrario.

## Contrato de integración — contrato visual

- Selector de **servicio** (por nombre legible, nunca `id_servicio`) — el versionado es por servicio.
- Versión **vigente** destacada; las **soportadas** en una lista secundaria con su fecha de retiro.
- `fecha_retiro === 0` → «Sin retiro planificado», nunca 01/01/1970.
- `spec_url === ''` → no se renderiza un enlace roto; se indica que aún no hay documento publicado.

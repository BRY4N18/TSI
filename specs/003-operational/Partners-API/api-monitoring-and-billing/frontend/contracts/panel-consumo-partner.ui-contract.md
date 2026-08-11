# UI Contract — Panel de consumo del partner

**Actor:** `PartnerIntegracion`
**Vive dentro del portal de #07** (`/partners/portal`), no como aplicación aparte.
**Depends-on:** [`../../backend/contracts/api-monitoring-and-billing.openapi.yaml`](../../backend/contracts/api-monitoring-and-billing.openapi.yaml)

---

## Rutas

| Ruta | Página | Guard |
|---|---|---|
| `/partners/portal/consumo` | Mi consumo | `PartnerIntegracion` |

Sin parámetros de ruta: **el partner nunca teclea su `idpartner`**. Se resuelve con `GET /partners/me` (BE-DELTA-01 de #07), igual que el resto del portal.

---

## Endpoints consumidos

| Orden | Método y ruta | Para qué |
|---|---|---|
| 1 | `GET /api/v1/partners/me` | Resolver el `idpartner` del usuario autenticado |
| 2 | `GET /api/v1/partners/{idpartner}/metricas` | Métricas del período vigente |
| 3 | `GET /api/v1/logs-api?idpartner&solo_errores=true` | Sus últimos errores, para autodiagnóstico |

> **El paso 1 es obligatorio y va primero.** El JWT lleva `idusuario` y `roles`, no `idpartner`: sin
> `GET /partners/me` esta pantalla no sabría de quién son las métricas que va a pedir.

---

## Mapeo de errores → interfaz

| Código | Qué muestra la UI |
|---|---|
| 404 en `/partners/me` | `empty-state`: «Tu usuario no está vinculado a ningún partner.» + a quién contactar. **Sin** Reintentar: reintentar no lo vinculará |
| 403 | `error-state`: «No tienes acceso a esta información.» **Sin** Reintentar |
| 5xx / red | `error-state` con «Reintentar» |

---

## Mi consumo — contrato visual

**Chrome:** `h1` «Mi consumo» + badge de entorno **`Producción`** (texto, no solo color) + marca de `datos_hasta`.

### Bloque 1 — Cupo del período

Es el bloque más delicado de esta capa. Se rige por `data-model.md` § 1.

| Estado | Qué se muestra | Token |
|---|---|---|
| `sin-cupo` | «Sin cupo configurado» · porcentaje **«No aplica»** | `informacion` |
| `holgado` (<80 %) | Ring + «{llamadas} de {cupo} llamadas» | `informacion` |
| `cerca` (80–99 %) | Ring + «Te acercas a tu cupo mensual» | `informacion` |
| `excedido` (≥100 %) | Ring + **«Excedente estimado: {importe}»** + «Tu servicio no se interrumpe» | **`informacion`** |

**Prohibiciones explícitas del bloque de cupo:**

- ❌ `alerta-critica`, `alerta-alta`, `alerta-media` — en **ningún** estado, ni siquiera al 150 %.
- ❌ Las palabras «bloqueado», «cortado», «suspendido», «límite superado», «excediste».
- ❌ Iconografía de severidad (`alert-octagon`, `alert-triangle`, `alert-circle`).
- ✅ Lenguaje de facturación: «excedente», «coste previsto», «se facturará al cierre del período».

> **Por qué esta lista es tan explícita:** superar el cupo **no interrumpe el servicio**
> (RN-APM-002), y el SRS documentó la regla *«para que nadie la corrija asumiendo que debería
> bloquear»*. Un rojo aquí haría que un partner apagase una integración que funciona.

**Un ring como máximo en este bloque** (design-system § 5: máx. 3-4 rings por vista).

### Bloque 2 — Actividad del período

Tres cifras en línea: **llamadas**, **errores**, **latencia media**. `JetBrains Mono` para las cifras.

El bloque de errores enlaza al bloque 3 («Ver mis errores»), no a la consola del Desarrollador de APIs — el partner no tiene acceso a esa ruta.

### Bloque 3 — Mis errores recientes

Lista compacta de sus llamadas con código ≥ 400, con los mismos badges de clase que la consola (`consola-monitoreo.ui-contract.md`).

**Encabezado del bloque:** «Errores de tu integración» — no «Incidencias». Son autodiagnóstico (RN-APM-009): información para que el partner corrija su cliente, no una alarma de plataforma.

**Vacío en positivo:** «Sin errores en el período. Tu integración está respondiendo correctamente.»

### Bloque 4 — Excedente estimado

Visible **solo** cuando hay excedente o cuando no hay tarifa configurada.

| Situación | Qué se muestra |
|---|---|
| Excedente con tarifa | «{n} llamadas por encima del cupo · **{importe}** estimado» + «Se facturará al cierre del período» |
| Excedente **sin tarifa** | «{n} llamadas por encima del cupo» · importe **«No aplica — sin tarifa configurada»** |

> **Nunca un importe de 0,00** cuando el backend devuelve `null`. El cero diría «no debes nada»,
> que puede ser falso: lo cierto es que no se pudo calcular.

---

## Accesible estando suspendido

Un partner con `Dim_Partner.activo = false` **sí** entra a esta pantalla (RN-APM-017). Se le muestra un banner informativo con su situación y el enlace a su estado de acceso, pero **las métricas se cargan igual**: es lectura, y es justo lo que le permite entender qué pasó.

---

## Navegación

Entrada nueva en `nav-links.ts`, grupo «Partners y API», rol `PartnerIntegracion`:

| Label | Path | Icon | Description |
|---|---|---|---|
| Mi consumo | `/partners/portal/consumo` | `chart-bar` | Tu consumo del período y tu excedente estimado |

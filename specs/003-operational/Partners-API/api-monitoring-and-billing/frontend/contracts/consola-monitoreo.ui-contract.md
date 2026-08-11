# UI Contract — Consola de monitoreo y facturación

**Actores:** `DesarrolladorAPIs` (consola, reporte) · `Administrador` (reporte, excepciones)
**Depends-on:** [`../../backend/contracts/api-monitoring-and-billing.openapi.yaml`](../../backend/contracts/api-monitoring-and-billing.openapi.yaml) + `BE-DELTA-04/05`

---

## Rutas

| Ruta | Página | Guard | Modo |
|---|---|---|---|
| `/partners/consola/logs` | Consola de registros | `DesarrolladorAPIs` | Lista Ver-only |
| `/partners/consola/logs/:idlog` | Detalle del registro | `DesarrolladorAPIs` | Workpanel página dedicada, modo **Ver** |
| `/partners/consola/reportes` | Reporte mensual | `EsPartnerOGestor` (Admin · DevAPIs · Partner) | Consulta |
| `/partners/consola/excepciones` | Excepciones de facturación | **`Administrador`** | Cola Ver-only |

**Query params que forman parte del contrato** (deben sobrevivir a un refresco y poder compartirse por enlace):

- `logs`: `?idpartner=&solo_errores=`
- `reportes`: `?idpartner=&anio=&mes=&comparar_anio=&comparar_mes=`

---

## Endpoints consumidos

| Superficie | Método y ruta | Notas |
|---|---|---|
| Consola | `GET /api/v1/logs-api?idpartner&solo_errores&codigohttp&desde&hasta&cursor&limit` | **`idpartner` es obligatorio**: sin él el backend devuelve 400. **Todos los filtros y la paginación se resuelven en el servidor** |
| Consola (selector) | `GET /api/v1/partners` | Para elegir partner **por nombre**, nunca tecleando su id |
| Reporte | `GET /api/v1/reportes-consumo?idpartner&anio&mes` | Dos llamadas cuando hay comparación |
| Excepciones | `GET /api/v1/facturacion/excepciones?periodo` | **`BE-DELTA-04/05`** |

> **No existe endpoint que liste los logs de todos los partners a la vez.** El docstring del backend
> dice «datos de **todos** los partners», pero el código exige `idpartner` y devuelve 400 sin él. La
> UI se rige por el **código**, que es lo que se ejecuta: primero se elige partner, después se listan
> sus llamadas.

---

## Mapeo de errores → interfaz

| Código | `code` del sobre | Qué muestra la UI |
|---|---|---|
| 400 | `validation_error` | Mensaje junto al filtro que falta; **no** un toast genérico |
| 401 | — | Redirección a login (interceptor global) |
| 403 | `propiedad_partner` | `error-state`: «No tienes acceso a esta información.» **Sin** botón Reintentar |
| 403 | — (rol) | La ruta ni siquiera se alcanza: lo corta el guard |
| 404 | `not_found` | `empty-state` con el copy del período/partner inexistente |
| 5xx / red | — | `error-state` con «Reintentar» |

---

## Consola de registros — contrato visual

**Chrome:** título «Registros de API» + indicador de sincronización (design-system § 5): punto + texto con la marca de `datos_hasta`.

- **Selector de partner** (combobox por nombre) — obligatorio; hasta elegirlo la tabla muestra un `empty-state` que lo pide.
- **Todos los filtros van al servidor** (`research.md` Decision 3): `solo_errores`, `codigohttp`, `desde` y `hasta`. Cada cambio dispara una consulta; **nada se filtra en memoria**.
- El rótulo declara que los filtros alcanzan **todo el historial** del partner, no solo lo que se ve.
- **Botón «Actualizar»** + conmutador de auto-refresco 30 s, **apagado por defecto**.

**Tabla** (`md:table`, cards en mobile):

| Columna | Formato |
|---|---|
| Id | `JetBrains Mono`, texto plano, **nunca link** |
| Fecha y hora | Local |
| Endpoint · Método | Texto |
| Código | **Badge** con radio 6-8px, según la clase de `data-model.md` |
| Latencia | ms, alineada a la derecha |
| Acción | Solo `eye` (`aria-label="Ver detalles"`, 44×44px). **Sin `pencil` ni `trash`**: append-only |

**Badges de código — el punto donde la UI puede confundir al partner:**

| Clase | Texto del badge | Token |
|---|---|---|
| `exito` | `200` | `exito` |
| `ritmo` | `429 · Límite de ritmo` | `informacion` |
| `cliente` | `4xx · Revisar la petición` | `alerta-media` |
| `plataforma` | `5xx · Error de plataforma` | `alerta-critica` |

> El `429` **no** usa token de alerta: no es un fallo del partner ni de la plataforma, es el ritmo
> siendo regulado. Y **no cuenta como consumo facturable**, lo que la fila indica explícitamente.

**Paginación por cursor.** Botón «Cargar más» cuando el `meta` trae `next_cursor`; la página siguiente **conserva los filtros activos**, y cambiar un filtro **reinicia** la paginación. Pie de tabla: «{n} registros mostrados.»

---

## Detalle del registro — workpanel

Página dedicada, chrome del golden sample: link «← Volver a los registros» (`arrow-left`), eyebrow «Detalles», `h1` con el endpoint + badge del código.

**Modo Ver únicamente.** Datos como `<dl>` con `dt` en mayúsculas, **nunca `<input disabled>`**. Sin botón de guardado y sin acciones de dominio: no hay nada que hacerle a un log.

---

## Reporte mensual — contrato visual

- Selector de partner (por nombre), año y mes.
- **Comparación opcional**: segundo selector de período; si está vacío, no se muestra ninguna columna de variación (no se compara «contra cero por defecto»).
- Tres cifras: llamadas, errores, latencia media.
- **Leyenda fija:** «Este reporte incluye únicamente consumo de **producción**» (RN-APM-001).
- Variación: `+/-` absoluto y porcentual; **«sin base de comparación»** cuando el período comparado tuvo 0 llamadas.

**Mes sin consumo:** ceros con el copy de `research.md` Decision 7 — nunca el vacío de error.

---

## Excepciones de facturación — contrato visual

**Chrome:** título «Excepciones de facturación» + contador por tipo.

| Columna | Formato |
|---|---|
| Tipo | Badge: `Reintentos agotados` (`alerta-media`) · `No tarificable` (`alerta-media`) |
| Partner | Nombre |
| Período | `AAAA-MM` |
| Importe | Solo en reintentos agotados; **vacío** —no `0,00`— en no tarificable |
| Intentos | `3 de 3` en reintentos agotados; vacío en el otro |
| Último resultado | Motivo del fallo |
| Acción sugerida | Texto, derivado del tipo |

**Sin acciones ejecutables** (FR-UI-135): no hay endpoint de emisión manual, así que no hay botón. La columna «Acción sugerida» dice qué hacer y dónde, no lo hace.

**Estado vacío en positivo:** «No hay excepciones de facturación pendientes.» — aquí el vacío es la buena noticia.

---

## Invariante de esta capa

> **Ningún componente de estas superficies puede usar `alerta-critica` para representar consumo por
> encima del cupo.** Se verifica con un test sobre las plantillas. `alerta-critica` sí es legítimo
> para un `5xx`, que es un fallo real de la plataforma.

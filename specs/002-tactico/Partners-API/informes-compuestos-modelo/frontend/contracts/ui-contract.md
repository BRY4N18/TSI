# Contrato UI — tres pantallas Z

**No redefine** [`../backend/contracts/informes-compuestos-partners.openapi.yaml`](../backend/contracts/informes-compuestos-partners.openapi.yaml).
Mapea **zona de pantalla → informe publicado → campos que la zona está obligada a mostrar**.

Prefijo de lectura: `GET /api/v1/informes-tacticos/partners/{informe}?desde=&hasta=`

| Id publicado | Ruta HTTP |
|---|---|
| `latencia-p95` | `latencia-p95` |
| `taxonomia-errores` | `taxonomia-errores` |
| `comparativa` | `comparativa` |
| `metricas-consumo` | `metricas-consumo` |
| `reporte-mensual-consumo` | `reporte-mensual-consumo` |
| `consumo-por-endpoint` | `consumo-por-endpoint` |
| `participacion-ingresos-api` | `participacion-ingresos-api` |
| `adopcion-versiones` | `adopcion-versiones` |
| `motivo-credencial-inactiva` | `motivo-credencial-inactiva` |
| `tiempo-incorporacion` | `tiempo-incorporacion` |
| `tasa-rechazo-produccion` | `tasa-rechazo-produccion` |
| `clientes-integracion-activa` | `clientes-integracion-activa` |
| `volumen-expedientes` | `volumen-expedientes` |

Roles que entran: `DirectorTecnologico`, `Administrador`. Cualquier otro: la pantalla no existe
para ellos (403 / access-denied). `PartnerIntegracion` y `DesarrolladorAPIs` **no** entran.

`data-testid` canónicos: `zona-heroe`, `zona-periodo`, `zona-visual`, `zona-lectura`,
`zona-apoyo`, `zona-nota-muestras`.

Envelope: `data.resultados`, `meta.nota_muestras` (cuando aplica). La nota se lee **junto a la
zona** que pidió un informe con muestras.

---

## Prohibido en las tres

IP de origen; secreto; contacto técnico; ejecutor de un cambio; mapas; zonas geográficas;
botones de revocar / suspender / emitir / cambiar cupo; exportar; enlace a consola de logs o a
«Mi consumo»; agrupar adopción solo por versión; total que sume las tres clases de error;
ocultar una fila con `percentil_fiable = 0`.

---

## Pantalla `consumo` — Consumo de la API

| Zona Z | Informe | Campos visibles | Lectura obligatoria |
|---|---|---|---|
| Héroe | `latencia-p95` | Cada fila: `endpoint_path`, `latencia_p95_ms`, `latencia_media_ms`, `muestras`, `percentil_fiable`; `meta.nota_muestras` si viene | **el trío viaja en el mismo bloque**; no fiable **no oculta** la fila; vacío → no 0 ms |
| Período | — | `desde`, `hasta` | declaración de que esta latencia **no es** la media del operativo |
| Visual | `taxonomia-errores` | `clase_resultado`, `codigo_http`, `llamadas`, `pct` | agrupar por clase **antes** que por código; **sin** total suma |
| Lectura | `comparativa` | `partner`, `llamadas`, `pct_error`, `latencia_p95_ms`, `desviacion_vs_mediana` | `llamadas = 0` **se pinta**; sin IP |
| Apoyo plegado | `metricas-consumo`, `reporte-mensual-consumo`, `consumo-por-endpoint`, `participacion-ingresos-api` | métricas: `partner`, `llamadas`, `errores` (como no éxito), `latencia_media_ms`, `latencia_p95_ms`, `muestras`, `cupo`, `pct_consumido`; reporte: `mes`, `partner`, `llamadas`, `errores`, `excedente`, `muestras`; endpoint: `endpoint_path`, `metodo_http`, `llamadas`, `pct`, `muestras`; ingresos: `mes`, `partner`, `ingreso_base`, `excedente`, `pct_excedente` | partner en cero visible; excedente **aparte** de base; `errores` no se titula «fallo de servicio» |

Vista principal ≤ 8 bloques (héroe, período, visual, lectura, apoyo como **un** bloque plegado).

---

## Pantalla `incorporacion` — Incorporación

| Zona Z | Informe | Campos visibles | Lectura obligatoria |
|---|---|---|---|
| Héroe | `adopcion-versiones` | `servicio`, `version`, `llamadas`, `pct`, `version_es_derivada` | clave **(servicio, versión)**; declaración **derivada** visible |
| Período | — | `desde`, `hasta` | — |
| Visual | `motivo-credencial-inactiva` | `partner`, `motivo_inactividad`, `credenciales`, `pct` | cuatro motivos **distintos**; prohibido un recuento «inactivas» |
| Lectura | `tiempo-incorporacion` | `partner`, `etapa`, `dias`, `en_proceso` | `en_proceso = 1` fuera de la media; `dias` nulo **no** se pinta como 0 |
| Apoyo plegado | `tasa-rechazo-produccion` | `periodo`, `motivo`, `solicitudes`, `rechazadas`, `pct_rechazo` | por motivo; **sin** ejecutor |

Sin zona de «próximas a vencer» que meta el centinela del año 9999.

---

## Pantalla `entrega` — Entrega contratada

| Zona Z | Informe | Campos visibles | Lectura obligatoria |
|---|---|---|---|
| Héroe | `clientes-integracion-activa` (mismo GET que la lectura) | `pct`, `con_integracion`, `clientes_totales`, `meta` | meta ≥70 % **a la vista**; `pct` nulo → **sin dato**, no 0 % |
| Período | — | `desde`, `hasta` | — |
| Visual | `volumen-expedientes` | `cliente`, `canal`, `expedientes` | portal y API **por separado** |
| Lectura | `clientes-integracion-activa` | mismos campos; texto de qué implicaría un 100 % | denominador = todos los clientes |

Un solo GET para héroe+lectura (research D9). **Ninguna** zona de alcance geográfico.

---

## Estados por zona

| Estado | Cuándo | Qué se ve |
|---|---|---|
| carga | petición en vuelo | esqueleto **solo en esa zona** |
| dato | `resultados` con filas y métrica no nula | cifra / barras; no fiable se marca |
| sin_dato | métrica `null` con período que sí tiene contexto | «sin dato», nunca 0 |
| vacio | `resultados: []` | vacío explícito |
| error | 4xx/5xx / red | mensaje en la zona; el resto sigue |

## Navegación

Tres entradas de sidebar, grupo Partners y API, roles del guard. No modificar «Informes de
partners», «Estado de mi acceso», «Registros de API», «Reporte de consumo», «Mi consumo»,
consola ni portal.

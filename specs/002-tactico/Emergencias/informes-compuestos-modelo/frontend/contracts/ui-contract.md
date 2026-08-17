# Contrato UI — tres pantallas Z

**No redefine** [`../backend/contracts/informes-compuestos-emergencias.openapi.yaml`](../backend/contracts/informes-compuestos-emergencias.openapi.yaml).
Mapea **zona de pantalla → informe publicado → campos que la zona está obligada a mostrar**.

Prefijo de lectura: `GET /api/v1/informes-tacticos/emergencias/{informe}?desde=&hasta=`

Roles que entran: `DirectorOperaciones`, `Administrador`. Cualquier otro: la pantalla no existe para
ellos (403 / access-denied).

## Prohibido en las tres

Coordenadas, identidad de personas, texto libre interno, mapas, botones de despacho/cierre/forzar,
exportar, los trece informes vigilados.

`data-testid` canónicos: `zona-heroe`, `zona-periodo`, `zona-visual`, `zona-lectura`, `zona-apoyo`.

---

## Pantalla `calidad` — Calidad del registro

| Zona Z | Informe | Campos visibles | Lectura obligatoria |
|---|---|---|---|
| Héroe | `completitud-campos-criticos` | `pct_completitud` (o «sin dato»), `casos` | — |
| Período | — | `desde`, `hasta` | — |
| Visual | mismo informe | `completos` vs `casos - completos` | no omitir incompletos |
| Lectura | — | constante **severidad, condado** | FR-UI-008 |

Vacío: `data: []` → no mostrar 0 %.

---

## Pantalla `despacho` — Despacho

| Zona Z | Informe | Campos visibles | Lectura obligatoria |
|---|---|---|---|
| Héroe | `primer-intento` | `pct_primer_intento`, `casos`, meta **≥90 %** como contexto, no como semáforo inventado si el backend no emite `cumple` | — |
| Período | — | `desde`, `hasta` | — |
| Visual | `desviacion-llegada` | distribución o serie de la desviación; ausentes si `null` | texto: referencia histórica, **no** SLA (`meta.nota_referencia` o el texto de FR-032) |
| Lectura | `perdida-senal` | huecos / posiciones (los nombres de columna del OpenAPI/SQL) | no comparar en silencio con el legado truncado |
| Apoyo (visible, no héroe) | `ratio-demanda-capacidad` | `condado`, `casos`, `unidades_vigentes`, `ratio` | **sin capacidad** cuando D7 |

El primer intento táctico **no** emite `cumple` booleano (eso es OE3). La pantalla muestra la meta
≥90 % como referencia de lectura, no como semáforo verde/rojo de capa estratégica.

---

## Pantalla `cierre` — Evidencia y cierre

| Zona Z | Informe | Campos visibles | Lectura obligatoria |
|---|---|---|---|
| Héroe | `envejecimiento-cartera` | tramos y recuento de abiertos | no tratar vacío como «no hay atraso» si el período no tiene abiertos: es vacío, no éxito |
| Período | — | `desde`, `hasta` | — |
| Visual | `cobertura-evidencia` | `solo_foto`, `solo_nota`, `foto_y_nota`, `sin_evidencia`, `pct_con_alguna` | `sin_evidencia` **cuenta** |
| Lectura | `distribucion-resultados` + `retiros-forzados-por-proveedor` | calificación **ausente ≠ 0**; retiros vs finalizaciones | — |
| Apoyo plegado | `latencia-sincronizacion`, `completitud-enriquecimiento`, `volumen-evidencia-por-unidad`, `escaladas-severidad` | lo que el contrato de cada uno ya devuelve | no ocupan el visual grande |

Vista principal ≤ 8 bloques (héroe, período, visual, lectura, apoyo como **un** bloque plegado).

---

## Estados por zona

| Estado | Cuándo | Qué se ve |
|---|---|---|
| carga | petición en vuelo | esqueleto **solo en esa zona** |
| dato | `data` con filas y métrica no nula | cifra / barras |
| sin_dato | métrica `null` con período que sí tiene contexto | «sin dato», nunca 0 |
| vacio | `data: []` | vacío explícito |
| error | 4xx/5xx / red | mensaje en la zona; el resto sigue |

## Navegación

Tres entradas de sidebar, grupo Emergencias, roles del guard. No modificar las tres de workpanel.

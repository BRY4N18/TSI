# Contrato UI — tres pantallas Z

**No redefine** [`../backend/contracts/informes-compuestos-ventas-crm.openapi.yaml`](../backend/contracts/informes-compuestos-ventas-crm.openapi.yaml).
Mapea **zona de pantalla → informe publicado → campos que la zona está obligada a mostrar**.

Prefijo de lectura: `GET /api/v1/informes-tacticos/ventas-crm/{informe}?desde=&hasta=`

Roles que entran: `DirectorMarketing`, `GerenteVentas`, `Administrador`. Cualquier otro: la
pantalla no existe para ellos (403 / access-denied). `GerenteCuentasPublicas` **no** entra.

`data-testid` canónicos: `zona-heroe`, `zona-periodo`, `zona-alcance`, `zona-visual`,
`zona-lectura`, `zona-apoyo`.

---

## Prohibido en las tres

Nombre, apellidos, correo, teléfono, cargo o notas del prospecto; mapas; botones de
asignar / transicionar / disparar aviso; exportar; título «CAC»; columna de coste; resolver
`idejecutivo` a un nombre.

---

## Pantalla `embudo` — Embudo comercial

| Zona Z | Informe | Campos visibles | Lectura obligatoria |
|---|---|---|---|
| Héroe | `embudo-conversion` | `etapa_anterior`, `etapa_nueva`, `transiciones`, `pct_paso`, `denominador` | convertido y perdido **no** se funden; el % es sobre transiciones |
| Período | — | `desde`, `hasta` | — |
| Alcance | — | `meta.acotado_a` | siempre visible |
| Visual | `permanencia-por-etapa` | `etapa`, `segundos_mediana`, `abiertos`, `prospectos_medidos` | el estancado no parece el más rápido; `abiertos` se ve |
| Lectura | `motivos-perdida` | `motivo`, `etapa_abandono`, `perdidos`, `pct` | motivo ausente = «sin motivo registrado»; etapa de abandono visible |
| Apoyo plegado | `carga-por-ejecutivo`, `pipeline-ponderado` | `idejecutivo` (clave), `activos`, `valor_pipeline`, `conversiones`; `etapa`, `valor_ponderado`, `peso` | pesos: `meta.filtros.nota_pesos`; sin nombres de persona |

Vista principal ≤ 8 bloques (héroe, período+alcance, visual, lectura, apoyo como **un** bloque
plegado).

---

## Pantalla `captacion` — Captación por canal

| Zona Z | Informe | Campos visibles | Lectura obligatoria |
|---|---|---|---|
| Héroe | `captacion-por-canal` | `canal`, `prospectos`, `pct`, `denominador` | fila **Desconocido** suma |
| Período | — | `desde`, `hasta` | — |
| Alcance | — | `meta.acotado_a` | siempre visible |
| Visual | `conversion-por-canal` | `canal`, `prospectos`, `convertidos`, `pct_conversion`, `denominador` | `pct_conversion` nulo → **sin dato**, no 0 % |
| Lectura | `convertidos-por-canal` | `canal`, `convertidos`, `prospectos`, `nota_indicador` | la nota se lee **junto a la cifra**; prohibido titular CAC |

Sin apoyo. Vacío: `data: []` → no mostrar 0 %.

---

## Pantalla `nutricion` — Nutrición del prospecto

| Zona Z | Informe | Campos visibles | Lectura obligatoria |
|---|---|---|---|
| Héroe | `efectividad-nutricion` | `grupo`, `prospectos`, `convertidos`, `pct_conversion`, `denominador` | dos grupos, cada uno con su base |
| Período | — | `desde`, `hasta` | — |
| Alcance | — | `meta.acotado_a` | siempre visible |
| Visual | `intensidad-demo` + `secciones-visitadas` | `empresa`, `eventos`, `secciones_distintas`; `seccion`, `visitas` | no titular filas con `idprospecto`; vacío ≠ ceros |
| Lectura | `latencia-reaccion` | `avisos`, `con_reaccion`, `sin_reaccion`, `segundos_mediana` | ignorado **fuera** de la mediana |
| Apoyo plegado | `reglas-disparo` | `regla_disparada`, `avisos`, `con_reaccion`, `tasa_acierto`, `denominador` | — |

`data: []` en el héroe o el visual → vacío explícito de nutrición (hoy es el caso del entorno).

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

Tres entradas de sidebar, grupo Ventas CRM, roles del guard. No modificar «Informes comerciales»
ni Prospectos / Pipeline.

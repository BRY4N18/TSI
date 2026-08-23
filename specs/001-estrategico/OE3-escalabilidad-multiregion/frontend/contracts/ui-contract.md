# Contrato UI — cuatro pantallas Z de OE3

**No redefine** el OpenAPI. Mapea **zona → informe publicado → campos visibles**.

Prefijo: `GET /api/v1/informes-estrategicos/oe3/{informe}?desde=&hasta=&granularidad=&comparacion=`

| Id publicado | Pantalla |
|---|---|
| `latencia-asignacion` | latencia |
| `evolucion-latencia` | latencia (visual) |
| `tasa-error-registro` | calidad |
| `primer-intento` | calidad (visual) |
| `ratio-demanda-capacidad` | capacidad |
| `perdida-de-senal` | capacidad (apoyo) |
| `cobertura-de-respaldo` | respaldo |

**No se llama:** `uptime-por-region`, `tiempo-puesta-operacion`, `curva-maduracion`,
`cohorte-region`, `margen-operativo`, `reasignacion-manual`, `cobertura-pruebas`; ningún slug
de mapa; ningún slug de OE6.

Roles:

| Ruta | Guard |
|---|---|
| `/estrategico/oe3/latencia` | Operaciones · Gerente |
| `/estrategico/oe3/calidad` | Operaciones · Gerente |
| `/estrategico/oe3/capacidad` | Expansión · Operaciones · Gerente |
| `/estrategico/oe3/respaldo` | Expansión · Gerente |

Partner, Tecnológico, Financiero = ninguno.

`data-testid` canónicos: `zona-heroe`, `zona-periodo`, `zona-visual`, `zona-lectura`,
`zona-apoyo`, `zona-parcial`, `zona-comparacion`.

Envelope: `data` (array) + `meta`.

## Prohibido en las cuatro

Mapa; lat/lon; nombre de implicado; placa; eje de región; recuadros de bloqueados; botón de
despacho / abrir mercado / mover flota; exportar; `acotado_a`; ítem de menú gris; promedio como
héroe de tiempo; semáforo cerrado en E3-11; 0 min cuando no hay despachos.

---

## Pantalla `latencia`

Guard: `oe3LatenciaGuard`.

| Zona Z | Informe | Campos visibles | Lectura obligatoria |
|---|---|---|---|
| Héroe | `latencia-asignacion` | p95, recuento, `cumple`, alcance operativo | p95 nulo → sin dato; vacío ≠ 0 min |
| Período | — | `desde`, `hasta`, `granularidad`, `comparacion` | comparación ausente con motivo |
| Visual | `evolucion-latencia` | serie p95 | degradación lenta, no un salto |
| Lectura | alcance | proceso registro→asignación, no 100 ms | — |

---

## Pantalla `calidad`

Guard: `oe3CalidadGuard`.

| Zona Z | Informe | Campos visibles | Lectura obligatoria |
|---|---|---|---|
| Héroe | `tasa-error-registro` | tasa, recuento, campos comprobados, `cumple` | lista de campos; 0 % ≠ expediente perfecto |
| Período | — | igual | — |
| Visual | `primer-intento` | tasa **y** denominador; grano de intento | `cumple` nulo → sin semáforo |
| Lectura | alcance | — | — |

---

## Pantalla `capacidad`

Guard: `oe3CapacidadGuard`.

| Zona Z | Informe | Campos visibles | Lectura obligatoria |
|---|---|---|---|
| Héroe | `ratio-demanda-capacidad` | ratio por condado | flota **del período** |
| Período | — | igual | — |
| Visual | mismo GET | tensos vs **sin capacidad** | sin capacidad ≠ infinito ni 0 |
| Lectura | `meta.alcance` | — | — |
| Apoyo | `perdida-de-senal` | tasa + recuento de posiciones | plegado; sin umbral editable |

---

## Pantalla `respaldo`

Guard: `oe3RespaldoGuard`.

| Zona Z | Informe | Campos visibles | Lectura obligatoria |
|---|---|---|---|
| Héroe | `cobertura-de-respaldo` | cobertura + denominador | vacío ≠ 0 % |
| Período | — | igual | — |
| Visual | mismo GET | disponible vs solo alta | alta ≠ respaldo |
| Lectura | alcance | — | — |

## Estados por zona

| Estado | Cuándo | Qué se ve |
|---|---|---|
| carga | petición en vuelo | esqueleto **solo en esa zona** |
| dato | filas | cifra / barras |
| sin_dato | p95 `null` | «sin dato» en esa cifra |
| vacio | `data: []` | vacío explícito (no 0 min / no 0 %) |
| sin_capacidad | demanda y sin flota vigente | etiqueta; no ratio |
| error | 4xx/5xx / red | mensaje en la zona; el resto sigue |
| parcial | `meta.cobertura = parcial` | banner `zona-parcial` |

## Navegación

Cuatro entradas en el grupo **Estratégico**, roles de la tabla. No modificar compuestos tácticos
ni OE6.

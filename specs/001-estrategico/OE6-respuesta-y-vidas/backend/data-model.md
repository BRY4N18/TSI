# Data Model — OE6, Reducción del Tiempo de Respuesta y Seguridad de Vidas

**Fecha:** 2026-08-16 · **Research:** [`research.md`](research.md)

Este módulo **no define un modelo de datos propio**: consume el
[modelo analítico](../../../002-tactico/modelo-analitico/) tal como está.

**No añade ninguna tabla, ninguna dimensión y ninguna métrica.** Es el primer módulo del proyecto que
no necesita ampliar el modelo, y es la consecuencia directa de que Emergencias ya lo hiciera crecer
para sus 26 informes tácticos.

---

## 1. Lo que se consume

De las 13 tablas de `tsi_tactico`, OE6 lee **cinco**:

| Tabla | Tipo | ¿`FINAL`? | Qué aporta |
|---|---|:--:|---|
| `hecho_accidente` | Instantánea acumulada | **Sí, obligatorio** | Los cuatro hitos del caso, el impacto humano, las escaladas |
| `hecho_despacho` | Instantánea acumulada | **Sí, obligatorio** | Grano de intento: rechazos, vencimientos, tránsito, retiros |
| `hecho_evidencia` | Transacción | **No — falla** | Cobertura de foto y nota |
| `dim_severidad` | Dimensión | **Sí** | El orden por gravedad, que no es el alfabético |
| `dim_geografia` | Dimensión | **Sí** | El condado, cuando hace falta resolverlo desde la calle |

**No se lee `dim_region`.** Ver D1 del research: el eje no es construible.

**No se lee `hecho_ping_unidad`.** Lo usa E3-13 (pérdida de señal GPS), que pertenece a OE3.

---

## 2. Los doce informes: grano, fuente y medidas

**Leyenda de cobertura:** ✅ el modelo lo sostiene tal cual · ⚠️ lo sostiene con una limitación
declarada.

### US1 — el tiempo hasta la llegada

| # | Informe | Grano de salida | Fuente | Medidas | Cob. |
|---|---|---|---|---|:--:|
| **E6-01** | Tiempo global de respuesta | período *(× condado)* | `hecho_accidente` | mediana, p95, casos, excluidos | ✅ |
| **E6-02** | Tiempo por severidad | período × severidad | `hecho_accidente` × `dim_severidad` | mediana, p95, casos | ✅ |

**El tiempo es una resta dentro de la misma fila:** `hora_primera_llegada − fechahora_accidente`. No
hay unión con `hecho_despacho`, contra lo que dice el catálogo. Menos trabajo y, sobre todo, **ningún
riesgo de contar filas de intento como si fueran casos** (Regla 3).

**Filtro común a los dos:** `hora_primera_llegada IS NOT NULL AND fue_descartado = 0 AND
es_duplicado = 0`. Los tres términos son necesarios y ninguno es redundante:

- Sin llegada **no hay tiempo de llegada**. Contarlo como cero haría instantáneos los casos que nadie
  atendió — el error que más daño hace en este informe concreto.
- Un caso **descartado** fue una falsa alarma: nunca hubo emergencia que atender.
- Un caso **fusionado** es el mismo hecho que otro, que sigue vivo. Contar los dos duplica el suceso.

**Medido:** 4 252 casos, **3 637 con llegada**, 220 descartados, 141 duplicados.

### US2 — dónde se va el tiempo

| # | Informe | Grano de salida | Fuente | Medidas | Cob. |
|---|---|---|---|---|:--:|
| **E6-03** | Tramos del ciclo | período × tramo | `hecho_accidente` | mediana y p95 por tramo, casos por tramo | ✅ |
| **E6-04** | Origen de asignación | período × origen | `hecho_despacho` × `dim_origen_despacho` | recuento, %, mediana de respuesta | ✅ |
| **E6-07** | Desviación de llegada | período × unidad | `hecho_despacho` | mediana real, referencia, desviación, llegadas con referencia | ✅ |

**Los cuatro tramos de E6-03**, todos restas dentro de `hecho_accidente`:

| Tramo | Cálculo | Casos disponibles |
|---|---|:--:|
| Registro → confirmación | `hora_confirmacion − fechahora_accidente` | 4 040 |
| Confirmación → primera asignación | `hora_primera_asignacion − hora_confirmacion` | 3 638 |
| Primera asignación → primera llegada | `hora_primera_llegada − hora_primera_asignacion` | 3 637 |
| Primera llegada → cierre | `hora_cierre − hora_primera_llegada` | 3 636 |

⚠️ **Cada tramo tiene su propia población, y por eso cada uno publica la suya.** Un caso que se
confirmó pero nunca se asignó entra en el primer tramo y no en el segundo. Calcular los cuatro sobre
el mismo denominador —los casos completos— descartaría 404 casos del primer tramo, que es
precisamente donde vive la información sobre los casos que se atascaron al principio.

**E6-03 se entrega por período, nunca por unidad** (`FR-OE6-021`). Es lo que disuelve la decisión #35.

### US3 — los modos de fallo

| # | Informe | Grano de salida | Fuente | Medidas | Cob. |
|---|---|---|---|---|:--:|
| **E6-05** | Rechazo y timeout por unidad | período × unidad | `hecho_despacho` | ofrecidos, rechazados, vencidos, dos tasas | ✅ |
| **E6-06** | Abortos y misiones fallidas | período × causa | `hecho_despacho` | misiones, abortos, % | ✅ |
| **E6-09** | Cierres forzados | período *(× proveedor)* | `hecho_despacho` | forzados, total, % | ⚠️ #36 |
| **E6-10** | Envejecimiento de casos abiertos | tramo de antigüedad | `hecho_accidente` | casos por tramo | ✅ |

**El denominador de E6-05 son intentos ofrecidos a esa unidad**, filas de `hecho_despacho` — nunca
transiciones de estado. Es lo que corrige #34.

**Rechazo y vencimiento van separados**, con su tasa cada uno:

```
rechazados: 334      vencidos: 327      confirmados: 3310      (de 4314 intentos)
```

Los volúmenes son casi iguales y las causas opuestas: un rechazo es **una negativa** —alguien miró y
dijo que no— y un vencimiento es **una ausencia de respuesta**. Sumarlos en «no atendidos» daría 661
y ocultaría que la mitad de las veces nadie contestó, que es un problema distinto y se arregla de otra
manera.

⚠️ **E6-09 mide `retiro_forzado`, que hoy vale 1 en 4 314 filas.** La definición que el informe pide
—retiro manual desde central— son 451 casos y **el modelo no puede calcularla** sin copiar identidad
de usuario. El informe declara qué mide. Ver D7 del research.

**E6-10 se calcula contra el instante de la consulta**, no contra el fin del período: la antigüedad
de un caso abierto crece mientras siga abierto. Un caso está abierto si `hora_cierre IS NULL` — y el
modelo lo garantiza porque un hito no alcanzado va ausente, nunca con la fecha de carga.

### US4 — el resultado sobre la persona

| # | Informe | Grano de salida | Fuente | Medidas | Cob. |
|---|---|---|---|---|:--:|
| **E6-08** | Impacto humano | período × severidad × condado | `hecho_accidente` | víctimas, heridos, fallecidos, casos con dato | ✅ |
| **E6-11** | Escaladas de severidad | período | `hecho_accidente` | escaladas, casos, %, severidad inicial vs final | ⚠️ escaso |
| **E6-12** | Cobertura de evidencia | período × severidad | `hecho_accidente` × `hecho_evidencia` | % con foto, % con nota, % con ambas | ✅ |

**E6-08 distingue «cero» de «no registrado»**, y la distinción no es teórica: un accidente con cero
heridos es una buena noticia y un accidente cuyos heridos nadie contó es un expediente incompleto.
Sumar los segundos como ceros haría bajar el impacto humano total cada vez que **empeora** la calidad
del registro.

⚠️ **E6-11 opera sobre dato escaso.** El módulo táctico ya lo documentó: la fuente de escaladas tiene
**1 fila** para 4 252 casos, razón por la que se decidió no crear un hecho propio. El informe debe
declarar la escasez; un `0,02 %` presentado sin contexto se lee como «la severidad inicial casi
siempre acierta», cuando lo que dice es que casi nadie usa la función.

**E6-12 solo considera casos cerrados**, y separa foto de nota antes de combinarlas: son capturas
distintas, con dispositivos y momentos distintos, y un `% con evidencia` combinado esconde cuál de las
dos falta.

---

## 3. Entidad de salida

Todos los informes devuelven **filas agregadas** con esta forma, heredada del módulo táctico y
extendida con lo que la capa estratégica añade:

| Campo | Qué es | ¿Siempre? |
|---|---|:--:|
| **Claves de agrupación** | `periodo` + una o dos de: `severidad` · `condado` · `unidad` · `origen` · `tramo` · `causa` | Sí |
| **Medidas** | Mediana, p95, recuentos o porcentajes | Sí |
| **Denominador** | El total sobre el que se calculó cada porcentaje | Cuando hay % |
| **Excluidos** | Cuántas filas quedaron fuera por hito ausente | Cuando puede haberlas |

Y en `meta`, lo propio de esta capa:

| Campo de `meta` | Qué es |
|---|---|
| `periodo` | `desde`, `hasta`, `granularidad`, `parcial` |
| `comparacion` | Las **dos ventanas** y la variación por medida. Ausente si se pidió `ninguna`; **ausente con motivo** si la ventana anterior no tiene datos |
| `objetivo` | `valor`, `unidad`, `tipo` (`NORMATIVO` / `CALIBRAR`), `cumple` |
| `cobertura` | `completa` · `parcial`, con `falta` cuando es parcial |

**`meta.acotado_a` no se emite.** Estos informes no acotan por titularidad (`FR-OE6-015`).

### La regla del denominador

**Un porcentaje sin su denominador no se publica.** Un 12,5 % sobre 8 casos y sobre 8 000 son
afirmaciones muy distintas, y un tablero que muestre solo el porcentaje las presenta igual — sobre
esa lectura se decide qué proveedor sigue y dónde se abre la siguiente región.

### `cumple` y el tipo de objetivo

| `tipo` | `cumple` |
|---|---|
| `NORMATIVO` | `true` / `false` — es un compromiso, y se puede incumplir |
| `CALIBRAR` | **`null` siempre** — no hay línea base contra la que afirmar nada |

Los KPI de OE6: el **tiempo de respuesta percibido** es `[CALIBRAR]` *(requiere línea base)*; los
`[NORMATIVO]` de latencia, tasa de error y reasignación **pertenecen a OE3**, que define su meta.
En la práctica, **ningún informe propio de OE6 tiene hoy un objetivo `NORMATIVO`**, y todos sus
`cumple` son `null`.

> Esto conviene saberlo antes de mirar el tablero: **OE6 no puede semaforizarse todavía**. La primera
> lectura del informe es lo que producirá la línea base que hoy falta. Pintar semáforos ahora sería
> inventar el umbral y luego medirse contra él.

---

## 4. Reglas de consulta heredadas

Del [contrato de consumo](../../../002-tactico/modelo-analitico/contracts/contrato-consumo.md):

| Regla | Qué obliga aquí |
|---|---|
| **1 — ninguna tabla propia** | Se cumple por construcción: este módulo no crea nada |
| **2 — versión final** | Obligatoria en `hecho_accidente`, `hecho_despacho`, `dim_severidad`, `dim_geografia`. **Prohibida** en `hecho_evidencia` |
| **3 — intentos ≠ casos** | E6-05 y E6-06 cuentan intentos; E6-01, E6-02, E6-03 y E6-10 cuentan casos. 4 314 intentos son 3 651 casos |
| **4 — ausencia ≠ cero** | En los cuatro tramos, en el impacto humano y en toda mediana |
| **5 — historia o presente** | No aplica: OE6 no agrupa por atributo versionado *(el único candidato era la región, y queda fuera)* |
| **6 — desde cuándo es fiable** | No aplica: no se agrupa por proveedor salvo en E6-09, que lo declara |
| **7 — filtrar por partición** | Toda consulta filtra `fecha` para descartar particiones. Con comparación, **las dos ejecuciones lo hacen** |
| **8 — sin dato sensible** | Se cumple por construcción: el modelo no los contiene |

---

## 5. Lo que este módulo NO cambia del modelo

| Se pidió | No se añade | Motivo |
|---|---|---|
| Eje de región | Nada | Falta la relación región↔condado **en el sistema operativo**. D1 |
| `retiro_manual` en `hecho_despacho` | Nada, todavía | Resolvería E6-09 por completo, pero es un cambio del flujo de carga de otro módulo. D7 |
| ETA estimado | Nada | Exigiría coordenadas, excluidas por constitución. Se usa la referencia histórica |
| Hecho de escaladas de severidad | Nada | Ya se decidió no crearlo: 1 fila de origen. Son dos métricas del caso |

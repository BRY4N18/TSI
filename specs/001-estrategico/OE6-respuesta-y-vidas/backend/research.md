# Research — OE6, Reducción del Tiempo de Respuesta y Seguridad de Vidas

**Fecha:** 2026-08-16 · **Spec:** [`spec.md`](spec.md) · **Plan:** [`plan.md`](plan.md)

Todo lo de aquí se comprobó **contra el stack levantado** (`tactico-clickhouse`, base `tsi_tactico`,
13 tablas) y contra el código, no contra el catálogo. Donde una cifra aparece, se midió.

---

## D1 — El eje de región **no es construible**, y no es un problema de consulta ⛔

**La incógnita que la spec dejó abierta.** `FR-OE6-008` exigía agrupación por región y la spec anotó
que la cadena `condado → idestado → región` *«supone que una región cubre un estado entero»*, con la
advertencia de que si la suposición era falsa el informe repartiría mal **sin fallar**.

**Se comprobó. La suposición es falsa, y por partida doble.**

### Hallazgo 1 — un estado tiene más de una región

```
idregionoperativa  nombre_region         estado_ciclo_vida  idestado_geo  estado_geo
-1                 Desconocido           Desconocido        NULL          NULL
1                  Centro                Producción         1             Ciudad de Mexico
2                  Region Prueba Norte   Producción         1             Ciudad de Mexico
```

Dos regiones vivas sobre **el mismo** `idestado_geo`. Unir `hecho_accidente` con `dim_region` por
estado **duplicaría cada caso**: los 4 252 accidentes saldrían como 8 504 repartidos entre dos
regiones, y la consulta no fallaría. Cada región mostraría el total completo, y el gran total sería
exactamente el doble — un error que solo se detecta si alguien suma a mano.

### Hallazgo 2 — no existe ninguna relación región↔condado en el sistema operativo

No es que el modelo analítico no la haya cargado: **no existe en el origen**. Revisando
`database/esquemas.json` y la spec de `incorporacion-regional`:

| Tabla | Relaciona |
|---|---|
| `Dim_RegionOperativa` | región → `idestado` |
| `Dim_RegionOperativaEstadoRegion` | región → **estado** *(«tabla puente geográfica: qué estados cubre la región»)* |
| `Dim_Condado` | condado → `idestado` |
| `Dim_CondadoVecino` | condado → condado |

La cobertura de una región **se define a nivel de estado**. Y `incorporacion-regional/data-model.md`
lo dice explícitamente: *«Sin relación directa `Dim_UnidadEmergencia ↔ Dim_RegionOperativa`
(RN-REGON-005)»*.

### Hallazgo 3 — con los datos de hoy el eje sería degenerado igualmente

`dim_geografia` tiene **2 estados** (uno es «Desconocido») y **3 condados**. Los 4 252 casos están
repartidos entre dos condados, ambos del mismo estado:

```
condado          casos
Cuauhtemoc       2158
Benito Juarez    2094
```

Aunque la relación fuera 1:1, agrupar por región devolvería **una sola fila**. No es un informe.

### Decisión

**OE6 agrupa por `condado`. El eje de región queda ⛔ con su prerrequisito nombrado.**

`condado` es además lo que el sistema usa de verdad: las unidades de emergencia se asocian a un
condado, y es la clave con la que el despacho encuentra candidatas. Agrupar por lo que el sistema
opera es más honesto que agrupar por una etiqueta administrativa que no llega hasta el hecho.

**Prerrequisito para levantar el ⛔:** una relación **región↔condado** en el sistema operativo —tabla
puente, del mismo tipo que la que hoy existe a nivel de estado—. Mientras no exista, ningún informe
de ningún OE puede agrupar por región de forma correcta. **Afecta también a OE3**, cuyos E3-01 a E3-08
piden el mismo eje.

**Consecuencia documental:** `FR-OE6-008` de la spec **está equivocado y se corrige**, con esta
sección como justificación. Se registra además como decisión pendiente, porque la salida —cambiar el
modelo operativo— excede a este módulo.

**Alternativas descartadas:**

- *Unir por estado y aceptar el reparto.* Produce cifras dobladas sin fallar. Descartada sin más.
- *Tomar la primera región del estado.* Determinista pero arbitraria: atribuiría todos los casos de
  Ciudad de México a «Centro» y dejaría «Region Prueba Norte» a cero, afirmando algo falso.
- *Tratar el estado como si fuera la región.* Renombra el problema. Y con un solo estado real, el
  informe tiene una fila.

---

## D2 — Consultas propias para OE6, con prueba de contraste

**La tensión.** La spec (§«Qué es nuevo») exige no duplicar la métrica. Pero las consultas tácticas
**no son reutilizables tal cual**, y no por descuido:

```sql
-- ot23_desviacion_llegada.sql, línea 88
formatDateTime(toStartOfMonth(d.fecha), '%Y-%m') AS periodo
```

**La granularidad está fijada a mes en las 26 consultas**, deliberadamente: un informe táctico es
mensual o semanal por definición. La capa estratégica necesita mes, trimestre y año. Súmese que
ninguna calcula p95 ni acepta ventana de comparación.

### Las tres salidas

| | Qué implica | Riesgo |
|---|---|---|
| **A. Parametrizar las consultas tácticas** y compartir fichero | `{granularidad}` y columnas de percentil en los 26 ficheros | **Toca 13 endpoints publicados y verificados** (T076, 9/9). Una regresión ahí es un informe en producción que empieza a mentir |
| **B. Consultas propias en `estrategicos/oe6/` + prueba de contraste** ✅ | Ficheros nuevos; una prueba falla si las dos capas divergen con la misma agrupación y período | Dos definiciones conviviendo, mitigado por la prueba |
| **C. Vistas en ClickHouse** con la medida compartida | Un tipo de objeto nuevo en el almacén | Añade una capa que el contrato de esquema no contempla |

### Decisión: **B**

**Y no es la opción cómoda: es la que el proyecto ya eligió para este mismo problema.** El módulo
táctico de Emergencias dejó **13 informes conviviendo** con sus endpoints anteriores, *«vigilados por
una prueba de contraste que falla si divergen del modelo»*. Ese mecanismo **encontró tres defectos
reales** —#34, #35 y #36— que nadie había visto. Funciona.

**Trade-off aceptado y su regla de salida:** se acepta la duplicación de la *expresión* a cambio de no
tocar código verificado en producción. `SC-007` la vigila. Si el contraste llegara a fallar por una
divergencia legítima —una corrección aplicada en una capa y no en la otra—, la salida es promover la
medida a fichero compartido, no ampliar la tolerancia de la prueba.

**Lo que sí se reutiliza sin copiar nada:** el lector de catálogo
(`core/repositories/informes_tacticos/catalogo_consultas.py`), el `ModeloRepository`, el envelope y
el patrón `CATALOGO` / `PUBLICADOS` del servicio, que es un buen diseño y sería un error rehacer.

---

## D3 — Percentiles y granularidad: verificados contra el almacén

**Decisión:** `median(x)` y `quantile(0.95)(x)` para las medidas; `toStartOfMonth` ·
`toStartOfQuarter` · `toStartOfYear` para la granularidad, elegidos por un parámetro validado en el
servicio y **no interpolado en el SQL desde la petición**.

Prototipo de **E6-01** ejecutado contra los datos reales, con granularidad trimestral:

```
periodo   casos_con_llegada  mediana_min  p95_min
2026-01   686                8.6          15.2
2026-04   2030               8.7          14.9
2026-07   921                8.8          15.2
```

Y **E6-02**, por severidad:

```
severidad  casos  mediana_min  p95_min
Leve       1434   8.5          15.0
Moderado   1321   8.8          15.0
Grave      639    9.2          15.3
Fatal      243    8.9          15.2
```

**El MVP es construible hoy.** 686 + 2030 + 921 = 3 637, que cuadra con los casos con llegada.

> ⚠️ **Un hallazgo que el informe va a destapar.** La severidad casi no mueve el tiempo de respuesta:
> 8,5 min para un caso Leve y 9,2 para uno Grave. Si el despacho priorizara por gravedad, la
> diferencia sería mayor. **No se corrige aquí** —puede ser el dato de demostración, o puede ser real—
> pero es exactamente la clase de pregunta para la que existe OE6, y conviene anticipar que la primera
> lectura del informe la va a plantear.

**Por qué el parámetro se valida y no se interpola:** el nombre de la función va dentro del SQL, así
que un valor libre desde la URL sería inyección. Se traduce de una lista cerrada de tres valores.

---

## D4 — La comparación de períodos se resuelve en el servicio, no en SQL

**Decisión:** ejecutar **la misma consulta dos veces** —ventana actual y ventana anterior— y componer
la comparación en el servicio.

**Por qué no en SQL.** Meter las dos ventanas en una consulta obliga a un `CASE` por medida y
duplica cada expresión de percentil. Y sobre todo: **rompe el contraste con la capa táctica**, porque
la consulta dejaría de ser la misma forma que la suya. Con dos ejecuciones, la consulta estratégica
sigue siendo comparable fila a fila con la táctica, que es lo que `SC-007` necesita.

El coste es una segunda consulta por petición sobre un almacén columnar particionado por mes, con la
Regla 7 aplicada. Es despreciable frente al riesgo de la alternativa.

**El servicio calcula las ventanas, no el cliente.** `mom` y `yoy` desplazan la ventana actual
conservando su longitud (contrato §3.1). Dejarlo al cliente permitiría comparar 11 días contra 30 y
publicar una caída del 63 % que no ocurrió.

---

## D5 — `yoy` no tiene término de comparación todavía

**Medido:**

| Hecho | Desde | Hasta |
|---|---|---|
| `hecho_accidente` | 2026-02-03 | 2026-08-13 |
| `hecho_despacho` | 2026-02-03 | 2026-08-13 |

**Poco más de seis meses.** `comparacion=mom` funciona; `comparacion=yoy` **no tiene contra qué
comparar** en ningún período consultable hoy.

**Decisión:** `yoy` se implementa igual y devuelve la comparación **ausente**, declarando que la
ventana anterior no tiene datos. **No se rechaza con `400`**: la petición es legítima y lo será más
todavía dentro de seis meses; rechazarla obligaría al cliente a saber cuánto histórico hay.

Es la misma regla que el contrato ya fija para el dato que falta: se declara, no se rellena ni se
calla. Un `yoy` que devolviera `0 %` de variación diría «no cambió nada respecto al año pasado» sobre
un año pasado que no existe.

---

## D6 — Código: app nueva `informes_estrategicos`

**Decisión:** `backend/apps/informes_estrategicos/`, espejo estructural de `informes_tacticos`.

| | Por qué |
|---|---|
| **No dentro de `informes_tacticos`** | El nombre pasaría a mentir, y su `permissions.py` resuelve autoridades departamentales con acotamiento — que en esta capa no existe (`FR-OE6-015`) |
| **No repartida por app de departamento** | Un OE cruza departamentos. OE6 no lo hace, pero es el piloto: la estructura que fije la copian los otros cinco, y OE1 cruza tres |

Estructura, siguiendo el contrato §9:

```
backend/apps/informes_estrategicos/
    views/oe6_views.py · services/oe6_service.py
    periodo_estrategico.py    ← ventanas, granularidad, comparación
    objetivo.py               ← metas BSC, NORMATIVO vs CALIBRAR
    permissions.py · urls.py · envelope.py
core/repositories/informes_estrategicos/
dags/lib/consultas/estrategicos/oe6/
```

`periodo_estrategico.py` y `objetivo.py` son **transversales a los seis OE**, no de OE6. Nacen aquí
porque es el primero, y por eso viven en la raíz de la app y no bajo `oe6`.

---

## D7 — E6-09: qué se publica mientras #36 siga abierta

**Medido:**

| | Cuántos |
|---|:--:|
| `hecho_despacho.retiro_forzado = 1` | **1** de 4 314 |
| «Cierre forzado» según la definición del informe *(retiro manual desde central)* | **451** de 3 310 |

La primera cifra es la que el modelo puede calcular; la segunda es la que el informe pide. Difieren en
un factor de 451 y **el modelo no puede reproducir la segunda**: lo que distingue un retiro manual de
uno automático es la presencia de `idusuario`, excluida por decisión constitucional.

**Decisión:** publicar E6-09 midiendo el indicador del despacho y **declararlo en la respuesta**
(`FR-OE6-029`). Un informe de «cierres forzados» que devuelva 1 sobre 3 310 sin decir qué mide se lee
como «esto casi no pasa», cuando pasa 451 veces.

**La salida propuesta, para `/tasks` o para después:** una columna derivada `retiro_manual UInt8` en
`hecho_despacho`, calculada al cargar desde `idusuario IS NOT NULL` **sin copiar el identificador**.
Conserva el hecho y no la identidad, que es exactamente lo que el modelo debe hacer. Es
`ALTER TABLE … ADD COLUMN Nullable(...)` según el §4.bis, más lógica en el DAG de `hecho_despacho`.
**No entra en este plan** porque toca un flujo de carga de otro módulo.

---

## D8 — Qué existe ya, informe por informe

Verificado contra `dags/lib/consultas/emergencias/` (26 ficheros) y contra `CATALOGO` / `PUBLICADOS`
de `emergencias_compuestos_service.py`.

| Informe OE6 | Consulta táctica | ¿Publicada? | Trabajo real |
|---|---|:--:|---|
| **E6-01** Tiempo global | — | — | **Nueva.** Solo existe la variante por severidad |
| **E6-02** Por severidad | `ot22_tiempo_respuesta_por_severidad` | No | Añadir p95, granularidad, condado |
| **E6-03** Tramos del ciclo | `ot22_tiempo_reportado_a_confirmado` + `ot25_tiempo_asignado_a_cierre` | No | **Nueva**: los cuatro tramos en una consulta |
| **E6-04** Origen de asignación | `ot22_asignacion_automatica_vs_manual` | No | Granularidad y condado |
| **E6-05** Rechazo y timeout | `ot22_rechazo_timeout_por_unidad` | No | Adoptar la correcta (#34) |
| **E6-06** Abortos | `ot23_abortos_perdidas` | No | Granularidad y condado |
| **E6-07** Desviación de llegada | `ot23_desviacion_llegada` | **Sí** | Granularidad; conservar la muestra mínima |
| **E6-08** Impacto humano | `ot21_impacto_humano` | No | Granularidad, severidad |
| **E6-09** Cierres forzados | `ot25_cierres_forzados` | No | Declarar qué mide (#36) |
| **E6-10** Envejecimiento | `ot25_envejecimiento_cartera` | **Sí** | Reutilizable casi tal cual |
| **E6-11** Escaladas | `ot24_escaladas_severidad` | **Sí** | Granularidad |
| **E6-12** Cobertura evidencia | `ot24_cobertura_evidencia` | **Sí** | Granularidad |

**Dos informes genuinamente nuevos** (E6-01, E6-03); diez tienen consulta de la que partir. Confirma
la corrección de alcance de la spec: el trabajo está en la forma estratégica, no en la aritmética.

---

## D9 — La muestra mínima se hereda

`emergencias_compuestos_service.py:171-174` la declara para `desviacion-llegada`:

```python
Parametro("ventana_dias", defecto=90, minimo=7, maximo=730),
Parametro("muestra_minima", defecto=5, minimo=1, maximo=1_000),
```

**Decisión:** se hereda `muestra_minima = 5` para la referencia histórica de E6-07, y se adopta el
mismo valor como umbral por debajo del cual **el p95 se declara ausente** (`FR-OE6-017`).

**Por qué el mismo número y no uno propio:** los dos umbrales responden a la misma pregunta —cuántas
observaciones hacen falta para que un estadístico signifique algo— y dos valores distintos obligarían
a justificar la diferencia. No hay nada que justifique.

Con 5 observaciones el p95 **es el máximo**, no un percentil. El umbral no es cosmético: por debajo,
la cifra tiene la forma de un percentil y el significado de un caso suelto.

---

## Resumen de incógnitas resueltas

| Incógnita de la spec | Estado |
|---|:--:|
| Cardinalidad región↔estado | ✅ Resuelta — **1:N**, el eje no es construible (D1) |
| Cómo reutilizar sin duplicar la métrica | ✅ Resuelta — consultas propias + contraste (D2) |
| Percentiles y granularidad viables | ✅ Verificado contra el almacén (D3) |
| Valor de la muestra mínima | ✅ Se hereda: 5 (D9) |
| Alcance real frente al catálogo | ✅ Medido: 2 nuevos, 10 con base (D8) |

**Ninguna `NEEDS CLARIFICATION` queda abierta.**

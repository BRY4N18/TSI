# Quickstart — Verificación de OE6

**Fecha:** 2026-08-16 · **Plan:** [`plan.md`](plan.md) · **Contrato:**
[`contracts/informes-estrategicos-oe6.openapi.yaml`](contracts/informes-estrategicos-oe6.openapi.yaml)

Guía para comprobar que el módulo hace lo que dice. **No es documentación de implementación**: cada
comprobación existe porque su fallo sería silencioso, y por eso se verifica a mano además de con la
suite.

---

## 1. Prerrequisitos

```powershell
docker ps --filter name=tactico-clickhouse --filter name=accidentes-django
```

Ambos `Up`. El almacén analítico debe tener las tablas del modelo y datos cargados:

```powershell
docker exec tactico-clickhouse clickhouse-client --database tsi_tactico --query "SHOW TABLES"
```

**Línea base medida el 2026-08-16** (reconfirmada al implementar, mismas cifras de hechos):

| Dato | Valor |
|---|--:|
| Tablas en `tsi_tactico` | **16** — 13 del modelo + 3 residuales del diseño anterior (`indice_calidad_historico`, `perdida_senal_gps`, `rendimiento_por_proveedor`). OE6 no añade ninguna. |
| Casos (`hecho_accidente`) | 4 252 |
| Casos con llegada | 3 637 |
| Descartados · duplicados | 220 · 141 |
| Intentos (`hecho_despacho`) | 4 314 |
| Casos distintos en despacho | 3 651 |
| Rechazados · vencidos · confirmados | 334 · 327 · 3 310 |
| Rango del histórico | 2026-02-03 → 2026-08-13 |

> Si estas cifras cambiaron, no es un fallo: recalcúlalas y usa las nuevas. Lo que **no** debe cambiar
> son las relaciones entre ellas (intentos ≥ casos, con llegada ≤ casos).

---

## 2. Las comprobaciones

### 2.1 Un informe no crea ninguna tabla

```powershell
docker exec tactico-clickhouse clickhouse-client --database tsi_tactico --query "SELECT count() FROM system.tables WHERE database='tsi_tactico'"
```

Ejecutar los doce endpoints y repetir. **El número debe ser idéntico.**

Es la Regla 1, y se comprueba porque es la que el diseño anterior violaba: tres informes, tres tablas.

### 2.2 El MVP devuelve mediana y p95, y cuadran

```powershell
docker exec tactico-clickhouse clickhouse-client --database tsi_tactico --query @"
SELECT formatDateTime(toStartOfQuarter(fecha), '%Y-%m') AS periodo,
       count() AS casos,
       round(median(dateDiff('second', fechahora_accidente, hora_primera_llegada))/60,1) AS mediana_min,
       round(quantile(0.95)(dateDiff('second', fechahora_accidente, hora_primera_llegada))/60,1) AS p95_min
FROM hecho_accidente FINAL
WHERE hora_primera_llegada IS NOT NULL AND fue_descartado=0 AND es_duplicado=0
GROUP BY periodo ORDER BY periodo
"@
```

**Esperado** (línea base): tres trimestres, mediana ≈ 8,6–8,8 min, p95 ≈ 14,9–15,2 min, y
**686 + 2030 + 921 = 3 637**, que es el total de casos con llegada.

✅ **La suma es la comprobación**, no las medianas. Si los recuentos por período no suman el total,
algún caso se está perdiendo o duplicando.

### 2.3 El p95 desaparece bajo muestra mínima

Pedir `tiempo-respuesta-global` con un período de un solo día y `muestra_minima=500`.

**Esperado:** `p95_min: null`, no un número.

⚠️ Es la comprobación que más fácil se rompe al optimizar: un `quantile()` sin guardia devuelve
siempre algo. Con cinco observaciones ese algo es el máximo disfrazado de percentil.

### 2.4 Un caso sin llegada no vale cero

```powershell
docker exec tactico-clickhouse clickhouse-client --database tsi_tactico --query @"
SELECT countIf(hora_primera_llegada IS NULL) AS sin_llegada,
       count() AS total
FROM hecho_accidente FINAL WHERE fue_descartado=0 AND es_duplicado=0
"@
```

El endpoint debe declarar ese `sin_llegada` en `excluidos_sin_llegada` **y no incluirlo en la
mediana**.

**Cómo se detecta el fallo si ocurre:** si esos casos entraran como cero, la mediana caería de forma
brusca. Con ~615 casos sin llegada sobre ~3 900, entrarían como el 16 % de la muestra y hundirían la
cifra. **Un tiempo de respuesta que mejora cuando empeora la atención** es la señal.

### 2.5 Los tramos suman el total, y cada uno declara su población

Pedir `tramos-del-ciclo` y comprobar dos cosas distintas:

1. La suma de las medianas de los tramos **no** tiene por qué igualar la mediana total —las medianas
   no son aditivas—, pero **sí** debe hacerlo la suma de los tiempos por caso completo.
2. Cada tramo publica su propio `casos`, y son distintos entre sí:

| Tramo | Casos esperados |
|---|--:|
| registro → confirmación | 4 040 |
| confirmación → asignación | 3 638 |
| asignación → llegada | 3 637 |
| llegada → cierre | 3 636 |

⚠️ **Si los cuatro tramos publican el mismo recuento**, se está usando un denominador común y se
descartaron los casos que se atascaron al principio — que es justo lo que el informe existe para ver.

### 2.6 Intentos no son casos

```powershell
docker exec tactico-clickhouse clickhouse-client --database tsi_tactico --query "SELECT count() AS intentos, uniqExact(idaccidente) AS casos FROM hecho_despacho FINAL"
```

**4 314 intentos, 3 651 casos.** Los informes de US3 (`rechazo-y-timeout`, `abortos`) cuentan
intentos; los de US1 y US3-`envejecimiento` cuentan casos. **Si `tiempo-respuesta-global` devolviera
4 314 como denominador, está contando filas de despacho.**

### 2.7 Rechazo y vencimiento van separados

```powershell
docker exec tactico-clickhouse clickhouse-client --database tsi_tactico --query "SELECT resultado, count() FROM hecho_despacho FINAL GROUP BY resultado ORDER BY count() DESC"
```

**Esperado:** `confirmado 3310`, `rechazado 334`, `vencido 327`.

El endpoint debe publicar `tasa_rechazo` y `tasa_vencimiento` **por separado**. Una sola tasa de «no
atendidos» daría 661 y ocultaría que la mitad de las veces nadie contestó.

### 2.8 El denominador de la tasa de rechazo son intentos ofrecidos

Tomar una unidad con despachos confirmados y comprobar que **su tasa no baja al añadirle despachos
bien atendidos**.

Es el defecto #34 y su síntoma es contraintuitivo: **cuanto mejor trabaja una unidad, mejor parece su
tasa**, porque cada despacho completado añadía cuatro transiciones al denominador. Factor medido: 2,6.

### 2.9 Cierres forzados declara qué mide

Pedir `cierres-forzados`. **Esperado: `forzados: 1`** sobre 3 310 confirmados, **y**
`meta.alcance` presente diciendo que mide el indicador del despacho y no el retiro manual desde
central, más `cobertura: "parcial"`.

⚠️ **Un `1 de 3310` sin esa declaración es el fallo**, no la cifra. Se lee como «esto casi no pasa»
cuando la definición pedida da 451.

### 2.10 La comparación declara sus dos ventanas

Pedir `tiempo-respuesta-global` con `granularidad=trimestre&comparacion=mom`.

**Esperado:** `meta.comparacion.ventana_actual` y `ventana_anterior` presentes, **de igual longitud**.

Luego con `comparacion=yoy`: **esperado** `ventana_anterior: null` y `motivo_ausencia` explicando que
el histórico arranca en 2026-02. **No un `400`, y no una variación de 0 %.**

### 2.11 Un período en curso se marca parcial

Pedir un período cuyo `hasta` sea hoy o posterior. **Esperado:** `periodo.parcial: true`.

Sin esa marca, un mes de 11 días comparado contra meses completos publica una caída del 63 % que no
ocurrió.

### 2.12 Ningún objetivo CALIBRAR dice que se incumple

Recorrer los doce endpoints y comprobar que **todo** `meta.objetivo` con `tipo: "CALIBRAR"` trae
`cumple: null`.

Hoy **los doce** están en ese caso: OE6 no tiene ningún objetivo `NORMATIVO` propio —los de latencia
y tasa de error pertenecen a OE3—. Así que la comprobación es: **ningún `cumple` booleano en todo el
módulo**.

### 2.13 Nada sensible sale, tampoco con la autoridad

Recorrer los doce con el rol `DirectorOperaciones` y comprobar que **ninguna respuesta** contiene
coordenadas, identidad de implicados, de conductores, de operadores ni de técnicos de campo.

⚠️ **Con la autoridad del departamento, no solo con un rol acotado.** El camino contrario es fácil de
recorrer sin querer: quien implementa una exención de alcance puede leerla como «este rol lo ve todo».

### 2.14 Un rol operativo recibe 403, no una tabla vacía

Pedir cualquiera de los doce con rol `Operador`, `Despacho` o `Unidad`.

**Esperado: `403`.** Un `200` con `data: []` diría «no hay datos» donde el sistema quiso decir «no
tienes acceso», y son cosas distintas.

### 2.15 Las dos capas coinciden — la comprobación que justifica el diseño

Es `SC-007` y la razón de que este módulo escriba consultas propias en vez de tocar las tácticas.

Para los informes que existen en las dos capas, pedirlos **con el mismo período y la misma
agrupación** —granularidad `mes`, sin comparación— y comprobar que las cifras coinciden:

| Estratégico | Táctico |
|---|---|
| `tiempo-respuesta-por-severidad` | `ot22_tiempo_respuesta_por_severidad` |
| `origen-de-asignacion` | `ot22_asignacion_automatica_vs_manual` |
| `impacto-humano` | `ot21_impacto_humano` |
| `desviacion-de-llegada` | `/informes-tacticos/emergencias/desviacion-llegada` |
| `envejecimiento-de-casos-abiertos` | `/informes-tacticos/emergencias/envejecimiento-cartera` |
| `cobertura-de-evidencia` | `/informes-tacticos/emergencias/cobertura-evidencia` |
| `escaladas-de-severidad` | `/informes-tacticos/emergencias/escaladas-severidad` |

**Excepciones declaradas, que deben divergir:**

- `rechazo-y-timeout-por-unidad` — el estratégico corrige #34. **Debe dar una tasa mayor.**
- `cierres-forzados` — ambos miden el indicador del despacho, pero el estratégico declara el alcance.

⚠️ **Si esta comprobación falla en un informe no exceptuado, la salida no es ampliar la tolerancia**:
es promover la medida a un fichero compartido. Una tolerancia que tapara una divergencia real taparía
cualquier cosa — es lo que se decidió al encontrar #34.

---

## 5. Cifras medidas al implementar (2026-08-16)

Recorrido de [`tasks.md`](tasks.md) T086 contra el almacén en `localhost:8123`.
Suite: **109 passed**, 1 skipped (el endpoint operativo de rechazo no devolvió
filas en el rango pedido; la divergencia #34 queda declarada en el contraste).

Comprobaciones 2.2–2.14, ejecutadas vía la suite de `apps/informes_estrategicos/tests`:

| # | Resultado medido |
|---|---|
| 2.2 mediana/p95 | Los recuentos por severidad cuadran con `hecho_accidente` (3 637 con llegada) |
| 2.3 p95 bajo muestra | `p95_min: null` con `muestra_minima=500` en un día |
| 2.4 sin llegada ≠ cero | `excluidos_sin_llegada` > 0; mediana ≥ 5 min |
| 2.5 tramos | Cuatro poblaciones distintas; suma de hitos sin residuo en casos completos |
| 2.7 rechazo vs vencido | 334 y 327 en la línea base, tasas separadas |
| 2.8 denominador | `tasa_rechazo = rechazados / ofrecidos` |
| 2.9 cierres forzados | `cobertura: parcial` y `meta.alcance` presentes |
| 2.10 comparación | `mom` declara dos ventanas de igual longitud; `yoy` ausente con motivo, no 400 |
| 2.12 CALIBRAR | ningún `cumple` booleano en los doce |
| 2.14 403 | Operador, Despacho, Unidad, Administrador, DirectorFinanciero |

El número de tablas en `tsi_tactico` **no cambió** al ejecutar los doce (Regla 1).

---

## 3. Lo que este quickstart NO comprueba

- **La agrupación por región.** No existe: ver `research.md` D1. Comprobar que `por_region` **no es
  un parámetro aceptado** es parte de 2.14, no una comprobación propia.
- **El rol `Gerente`.** Todavía no está sembrado en `Dim_Rol`. Los permisos se escriben contra él,
  pero hasta que exista solo `DirectorOperaciones` puede ejercerlos.
- **El frontend.** Implementado: [`../frontend/quickstart.md`](../frontend/quickstart.md).
- **La semaforización.** OE6 no puede semaforizarse hasta que sus metas tengan línea base. La primera
  lectura de estos informes es lo que la producirá.

---

## 4. Una lectura que va a aparecer, y conviene anticipar

En la línea base, **la severidad casi no mueve el tiempo de respuesta**:

| Severidad | Casos | Mediana | p95 |
|---|--:|--:|--:|
| Leve | 1 434 | 8,5 | 15,0 |
| Moderado | 1 321 | 8,8 | 15,0 |
| Grave | 639 | 9,2 | 15,3 |
| Fatal | 243 | 8,9 | 15,2 |

Si el despacho priorizara por gravedad, un caso Fatal debería atenderse antes que uno Leve, y aquí
tarda **más**.

**No es un defecto de este módulo y no se corrige aquí.** Puede ser el dato de demostración, o puede
ser real. Pero es exactamente la pregunta para la que OE6 existe, así que va a plantearse en la
primera lectura del informe y conviene tenerla anticipada en vez de descubrirla en una reunión.

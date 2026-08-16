# Quickstart — Modelo Analítico Táctico

**Fecha:** 2026-08-14 · **Spec:** [`spec.md`](spec.md) · **Plan:** [`plan.md`](plan.md)

Cómo levantar el stack táctico y comprobar que el modelo hace lo que la spec dice. Esta guía
**valida**, no implementa.

**Es la primera vez en esta serie que el stack táctico se levanta de verdad.** Hasta ahora los tres
informes compuestos devolvían `500` porque el almacén no estaba arriba.

---

## 1. Levantar el stack táctico

Requiere el stack operativo ya en marcha, porque el modelo lee de él.

```bash
docker compose -f docker/docker-compose.tactico.yml up -d
```

Comprobar que el almacén responde:

```bash
curl -s http://localhost:8123/ping
```

**Esperado:** `Ok.`

Comprobar que el orquestador está arriba y que ve los flujos:

```bash
docker compose -f docker/docker-compose.tactico.yml ps
```

**Esperado:** almacén, metastore, planificador e interfaz web en estado saludable.

> ⚠️ **Si el almacén no arranca**, todo lo demás de esta guía es inútil y los tres informes
> compuestos existentes seguirán devolviendo `500`. Resolverlo antes de seguir.

---

## 2. Comprobar la conectividad en ambos sentidos

El orquestador tiene que alcanzar el origen y el destino.

```bash
docker compose -f docker/docker-compose.tactico.yml exec tactico-airflow-scheduler python -c "from lib.pinot_http_client import query_pinot; print(query_pinot('SELECT COUNT(*) AS n FROM Fact_Accidente'))"
```

**Esperado:** un recuento, no un error de resolución de nombre.

```bash
docker compose -f docker/docker-compose.tactico.yml exec tactico-airflow-scheduler python -c "from lib.clickhouse_http_client import execute_clickhouse; print(execute_clickhouse('SELECT 1'))"
```

---

## 3. Comprobación por escenario

### 3.1 Las dimensiones se cargan antes que los hechos

Ejecutar el flujo de dimensiones y comprobar que las cinco tablas tienen filas.

**Esperado:** `dim_tiempo`, `dim_geografia`, `dim_severidad`, `dim_unidad` y `dim_origen_despacho`
pobladas. **Si un flujo de hechos corre antes**, sus referencias apuntarán a la fila desconocida —
comportamiento correcto, pero señal de que el orden se saltó.

### 3.2 Un hito no alcanzado es ausente, nunca cero *(SC-007)*

```sql
SELECT count() FROM hecho_accidente FINAL WHERE hora_cierre IS NULL
```

**Esperado:** coincide con el número de casos abiertos.

```sql
SELECT count() FROM hecho_accidente FINAL WHERE hora_cierre = toDateTime(0)
```

**Esperado: cero.** Un solo registro aquí significa que un caso abierto se está guardando como
cerrado en 1970 — y cualquier promedio de duración quedaría destruido.

### 3.3 Recargar no duplica *(SC-005)*

Anotar el recuento de un mes, volver a ejecutar el flujo para ese mismo mes, y contar de nuevo.

```sql
SELECT count() FROM hecho_accidente FINAL WHERE toYYYYMM(fecha) = 202608
```

**Esperado:** **el mismo número exacto**. Si crece, la recarga está insertando sobre lo existente en
vez de descartar y repoblar la partición.

Comprobar además que se usó descarte de partición y **no** borrado por condición: el borrado por
condición funciona, pero se acumula como operación pendiente y con trece hechos acaba compitiendo
consigo mismo.

### 3.4 El pasado no se reescribe ⚠️ *(SC-003 — la comprobación de fondo)*

**Es la prueba que justifica el modelo entero.**

1. Anotar a qué proveedor se atribuyen los despachos de una unidad concreta.
2. **Cambiar el proveedor de esa unidad** en el sistema operativo.
3. Volver a ejecutar el flujo de dimensiones y el de despachos.
4. Consultar de nuevo los despachos **anteriores** al cambio.

```sql
SELECT proveedor, count() FROM hecho_despacho FINAL
WHERE idunidademergencia = <ID> AND fecha < <FECHA_DEL_CAMBIO>
GROUP BY proveedor
```

**Esperado:** siguen atribuidos al **proveedor anterior**.

**Si aparecen bajo el proveedor nuevo, el modelo no ha resuelto nada** y se está reproduciendo el
defecto documentado del informe de rendimiento por proveedor.

Comprobar además que la dimensión tiene **dos versiones** de esa unidad:

```sql
SELECT idunidademergencia, proveedor, valido_desde, valido_hasta, es_vigente, inicio_es_real
FROM dim_unidad FINAL WHERE idunidademergencia = <ID> ORDER BY valido_desde
```

**Esperado:** dos filas, la primera cerrada y la segunda vigente. Y la primera con
`inicio_es_real = 0`, porque su fecha de inicio es la primera carga, no un cambio observado.

### 3.5 Contar filas no es contar casos *(Regla 3 del contrato de consumo)*

```sql
SELECT count() AS intentos, uniqExact(idaccidente) AS casos FROM hecho_despacho FINAL
```

**Esperado:** `intentos > casos` si hubo reasignaciones. La revisión del sistema dejó un caso con
seis intentos; ahí la diferencia debe verse.

**Y el KPI del tablero:**

```sql
SELECT countIf(numero_intento = 1 AND resultado = 'confirmado') / uniqExact(idaccidente)
FROM hecho_despacho FINAL
```

**Esperado:** la proporción de casos resueltos al primer intento. Es el KPI ≥90 % que hasta ahora no
tenía fuente.

### 3.6 Dos informes miden lo mismo y coinciden *(SC-004)*

Calcular «casos por severidad y mes» de dos formas: agrupando por la columna desnormalizada del
hecho, y uniendo con la dimensión de severidad.

**Esperado:** **cifras idénticas**. Si difieren, la desnormalización se desincronizó de su dimensión
—el fallo clásico de este diseño— y hay que revisar el flujo de carga.

### 3.7 Un hecho sin dimensión se conserva *(SC-008)*

Con un accidente cuya calle no exista en el catálogo geográfico:

**Esperado:** el accidente **aparece** en el hecho, con la geografía marcada como desconocida.
**Perderlo sería inaceptable**: un accidente no puede desaparecer del análisis porque falte una calle
en un catálogo.

### 3.8 Los tres informes existentes se recalculan desde el modelo

Escribir la consulta equivalente de cada uno de los tres informes con tabla propia y comparar con lo
que su tabla devuelve.

**Esperado:** cifras coincidentes. **Es la condición para retirar esas tres tablas**; hasta que
coincidan, conviven.

#### Cifras de referencia — tomadas el 2026-08-14 (T005)

Corriendo los tres flujos con `airflow dags test <dag_id> 2026-08-13` sobre el stack recién
levantado. **Estas son las cifras contra las que T047 comparará el modelo antes de retirar nada.**

Ventana cubierta: **2026-02-03 → 2026-08-13** (182 períodos diarios).

| Informe | Filas | Cifras agregadas |
|---|---|---|
| `indice_calidad_historico` | 182 | índice consolidado medio **0.7296**; completitud **1.0000**; descarte **0.0542**; cobertura de evidencia **0.0082** |
| `perdida_senal_gps` | 714 | 620 accidentes distintos, 4 unidades, **28 096 779 s** de hueco acumulado; umbral 60 s |
| `rendimiento_por_proveedor` | 182 | `idcliente=1`: **4 314** despachos, rechazo **0.0939**, llegada media **669.44 s**, abortos **0.0509** |

**Cuatro observaciones del estado inicial, para quien compare después:**

1. **La completitud sale exactamente `1.0000` los 182 días.** Es el defecto que T045 corrige: la
   condición compara contra nulidad y el origen no tiene nulos, sino centinelas — así que **nada
   puede resultar incompleto jamás**. La cifra nueva **debe** ser menor; que difiera es el arreglo.
2. **Un solo proveedor.** Las 18 unidades del origen son de `idcliente=1`, así que el rendimiento por
   proveedor tiene una sola fila por período. **Es la realidad del origen, no un defecto del
   informe** — pero significa que el caso ancla de T034 tendrá que dar de alta un segundo proveedor
   para poder probar la atribución histórica: con los datos actuales pasaría en vacío.
3. **Las tres tablas son `MergeTree`, no `ReplacingMergeTree`.** `FINAL` sobre ellas falla con
   `ILLEGAL_FINAL`. Recargar el mismo período **no** duplica —conteos idénticos tras la segunda
   corrida y cero grupos `(periodo, idcliente)` repetidos—, así que la deduplicación se consigue por
   otra vía, que es justo la mutación que research D3 manda sustituir por descarte de partición.
4. **Los flujos no cargan un período: recargan la ventana entera** en cada corrida. Un `dags test`
   con intervalo de un día produjo igualmente los 182 períodos.

### 3.9 Nada sensible llegó al almacén *(Regla 8 del contrato de consumo)*

```sql
DESCRIBE TABLE hecho_accidente
```

**Esperado:** ninguna columna de latitud, longitud, nombre de persona ni identificación. Repetir
sobre `hecho_despacho` y las cinco dimensiones.

---

## 4. Verificación de que nada operativo se movió

```bash
cd backend && python -m pytest -q
```

**Esperado: verde sin cambios.** Este módulo **no toca el sistema operativo**: solo lo lee. Si alguna
suite se mueve, se escribió donde no se debía.

---

## 5. Trampas conocidas

- **Olvidar `FINAL` en una consulta** sobre un hecho acumulado o una dimensión devuelve filas
  duplicadas **de forma intermitente**, según si la fusión ya ocurrió. Es el fallo más difícil de
  diagnosticar porque no es reproducible.
- **El histórico de proveedor empieza en la primera carga.** No es un defecto de carga: el origen
  nunca guardó ese cambio. La columna que marca si el inicio es real existe para decirlo.
- **El retraso de ingesta del origen sigue aplicando.** Un caso registrado hace diez segundos puede
  no estar en la fuente cuando el flujo lo lea. La recarga del período lo recoge.
- **Los tres flujos antiguos siguen corriendo** hasta que se retiren. Mientras convivan, sus tablas y
  el modelo deben dar la misma cifra: si divergen, uno de los dos está mal.

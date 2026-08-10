# Phase 1 Data Model: Informes Tácticos Compuestos de Emergencias (Backend)

## Tabla ClickHouse 1: `perdida_senal_gps`

Alimentada por `perdida_senal_dag.py` (US1), leyendo `Dim_HistorialUbicacionUnidadEmergencia` (`idunidademergencia`, `idaccidente`, `fechahora`) ordenado cronológicamente por unidad, y `Dim_ParametrosSeguimiento.gps_umbral_senal_perdida_seg` vigente en el momento de la corrida.

```sql
CREATE TABLE IF NOT EXISTS tsi_tactico.perdida_senal_gps (
    periodo Date,
    idunidademergencia Int32,
    idaccidente String,
    inicio_hueco DateTime,
    fin_hueco DateTime,
    duracion_seg Int32,
    umbral_usado_seg Int32,
    calculado_en DateTime
) ENGINE = MergeTree()
ORDER BY (periodo, idunidademergencia, inicio_hueco)
```

**Lógica de detección (función pura testeable, `research.md` §4)**: dados los pings ordenados de una unidad, recorrer pares consecutivos; si `fechahora[i+1] - fechahora[i] > umbral_usado_seg`, emitir una fila de hueco. `umbral_usado_seg` se congela por fila (Edge Case: un cambio de configuración posterior no reinterpreta huecos ya calculados).

## Tabla ClickHouse 2: `indice_calidad_historico`

Alimentada por `indice_calidad_dag.py` (US2), combinando los 4 indicadores base (completitud, descarte, fusión — ya expuestos por `informes-tacticos-simples` sobre Pinot — y cobertura de evidencia, calculada aquí mismo desde `Dim_EvidenciaFoto` + `Fact_Accidente` estado Cerrado).

```sql
CREATE TABLE IF NOT EXISTS tsi_tactico.indice_calidad_historico (
    periodo Date,
    pct_completitud Float64,
    pct_descarte Float64,
    pct_fusion Float64,
    pct_cobertura_evidencia Float64,
    indice_consolidado Float64,
    calculado_en DateTime
) ENGINE = MergeTree()
ORDER BY periodo
```

**Fórmula del índice consolidado**: promedio simple de `pct_completitud`, `(1 - pct_descarte)`, `(1 - pct_fusion)`, `pct_cobertura_evidencia` — los 4 componentes normalizados a "más alto = mejor calidad" antes de promediar (descarte/fusión altos son señal de mala calidad, se invierten).

## Tabla ClickHouse 3: `rendimiento_por_proveedor`

Alimentada por `rendimiento_proveedor_dag.py` (US3), agrupando `Fact_Despacho` + `Fact_HistorialDespachoUnidad` por `Dim_UnidadEmergencia.idcliente` (proveedor) vigente en el momento del despacho — no el proveedor actual de la unidad (Edge Case de la spec).

```sql
CREATE TABLE IF NOT EXISTS tsi_tactico.rendimiento_por_proveedor (
    periodo Date,
    idcliente Int32,
    pct_rechazo Float64,
    tiempo_llegada_promedio_seg Float64,
    pct_abortos Float64,
    total_despachos Int32,
    calculado_en DateTime
) ENGINE = MergeTree()
ORDER BY (periodo, idcliente)
```

## Registro de ejecución de DAG (transversal)

No es una tabla de negocio separada — cada fila materializada ya lleva `calculado_en`; el log de éxito/fallo (FR-010) se satisface con los logs nativos de la tarea de Airflow (visibles en la UI, `tactico-airflow-webserver`), sin tabla adicional.

## Forma de respuesta de los 3 endpoints Django

Mismo envelope que `informes-tacticos-simples` (`{data, meta}`), con un caso adicional en `meta` para el Edge Case "período no materializado todavía":

```jsonc
{
  "data": null,
  "meta": {
    "periodo": { "desde": "2026-07-01", "hasta": "2026-07-31" },
    "materializado": false,
    "ultima_corrida": "2026-06-30T02:00:00Z"
  }
}
```

Cuando sí hay datos, `materializado: true` y `data` trae las filas de la tabla ClickHouse correspondiente al rango pedido.

## Addendum (2026-08-06): migración de los 3 DAGs a extract/transform/load-parquet

Los 3 DAGs pasaron de 1 tarea (`PythonOperator` único: extract+transform+load en una sola llamada) a 3 tareas (`extract >> transform >> load`) siguiendo el patrón de staging en Parquet descrito en `../../infraestructura/spec.md` (Addendum 2026-08-06). **Los esquemas ClickHouse de arriba y el contrato de idempotencia (`ALTER TABLE ... DELETE WHERE periodo IN (...)` + `INSERT` por período) NO cambiaron** — solo cambió cómo se ejecuta el cálculo, no qué se calcula ni dónde se guarda.

Las funciones `extract`/`transform`/`load` de cada DAG viven ahora en `dags/lib/perdida_senal_tasks.py`, `dags/lib/indice_calidad_tasks.py` y `dags/lib/rendimiento_proveedor_tasks.py` (no en el archivo del propio DAG), para que `dags/etl/dag_backfill.py` pueda reutilizarlas sin re-importar un archivo que también define un objeto `DAG` (evita `AirflowDagDuplicatedIdException`). Las funciones puras de negocio (`detectar_huecos`, `combinar_indice`, `agregar_por_proveedor` en `dags/lib/*_logic.py`) no cambiaron ni una línea — el nuevo código solo adapta `DataFrame ↔ list[dict]` alrededor de ellas.

## Fuera de alcance de esta fase

- Ningún cambio de esquema de Pinot — las 3 tablas ClickHouse son destino, nunca origen.
- La disposición visual de las 3 tarjetas dentro de los workpanels — se define en `../frontend/`.
- Reintentos/alertas de fallo de DAG más allá de lo que Airflow ya provee out-of-the-box (retries del operador) — no se construye un sistema de alertas nuevo en esta spec.

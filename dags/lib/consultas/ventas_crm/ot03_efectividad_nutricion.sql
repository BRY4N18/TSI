-- Informe #11 — Efectividad de la nutrición · OT03
--
-- Dos filas —con demo y sin demo—, cada una con su denominador. Un porcentaje
-- sin su base no permite comparar grupos de tamaño distinto.
--
-- Si no hay prospectos en el periodo, cero filas (no dos filas de ceros).
-- Si los hay, las dos filas salen aunque un grupo este vacio: pct_conversion
-- ausente, no 0 %, cuando el grupo no tiene prospectos.

WITH vigentes AS (
    SELECT
        idprospecto,
        argMax(idejecutivo, (fechahora, idasignacion)) AS vigente
    FROM hecho_asignacion_prospecto
    WHERE fecha <= {hasta:Date}
    GROUP BY idprospecto
),
base AS (
    SELECT
        p.idprospecto,
        p.desenlace,
        -- ⚠️ No `d.idprospecto IS NULL` tras LEFT JOIN: ClickHouse rellena
        -- Int32 con 0, no NULL, y todo el mundo saldria en `con_demo`.
        if(
            p.idprospecto IN (SELECT idprospecto FROM hecho_interaccion_demo),
            1,
            0
        ) AS tiene_demo
    FROM dim_prospecto AS p FINAL
    LEFT JOIN vigentes AS v ON v.idprospecto = p.idprospecto
    WHERE p.fecha_registro IS NOT NULL
      AND toDate(p.fecha_registro) BETWEEN {desde:Date} AND {hasta:Date}
      AND (
          {idejecutivo:Int32} = -1
          OR v.vigente = {idejecutivo:Int32}
      )
),
agg AS (
    SELECT
        if(tiene_demo = 1, 'con_demo', 'sin_demo') AS grupo,
        count()                                    AS prospectos,
        countIf(desenlace = 'convertido')          AS convertidos
    FROM base
    GROUP BY grupo
)
SELECT
    g.grupo                                      AS grupo,
    ifNull(a.prospectos, 0)                      AS prospectos,
    ifNull(a.convertidos, 0)                     AS convertidos,
    if(
        ifNull(a.prospectos, 0) = 0,
        NULL,
        round(a.convertidos / a.prospectos, 4)
    )                                            AS pct_conversion,
    ifNull(a.prospectos, 0)                      AS denominador
FROM (
    SELECT 'con_demo' AS grupo
    UNION ALL
    SELECT 'sin_demo' AS grupo
) AS g
LEFT JOIN agg AS a ON a.grupo = g.grupo
WHERE (SELECT count() FROM base) > 0
ORDER BY grupo

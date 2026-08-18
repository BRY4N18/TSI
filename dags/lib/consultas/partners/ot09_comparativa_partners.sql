-- Comparativa entre partners · OT09
--
-- Describe el patrón con volumen, tasa de error y latencia. Nunca con IP.

WITH
    llamadas AS (
        SELECT
            idpartner,
            count() AS n,
            countIf(clase_resultado != 'exito') AS errores,
            quantileExact(0.95)(latencia_ms) AS p95
        FROM hecho_llamada_api
        WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
        GROUP BY idpartner
    ),
    por_partner AS (
        SELECT
            p.nombre_partner AS partner,
            ifNull(l.n, 0) AS llamadas,
            round(ifNull(l.errores, 0) / nullIf(l.n, 0), 4) AS pct_error,
            l.p95 AS latencia_p95_ms
        FROM dim_partner AS p FINAL
        LEFT JOIN llamadas AS l ON l.idpartner = p.idpartner
        WHERE p.idpartner != -1
    )
SELECT
    partner,
    llamadas,
    pct_error,
    round(latencia_p95_ms, 1) AS latencia_p95_ms,
    round(latencia_p95_ms - median(latencia_p95_ms) OVER (), 1) AS desviacion_vs_mediana
FROM por_partner
WHERE {desde:Date} <= {hasta:Date}
ORDER BY partner

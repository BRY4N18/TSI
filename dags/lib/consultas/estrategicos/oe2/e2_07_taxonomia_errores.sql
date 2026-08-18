-- E2-07 Taxonomía 4xx / 5xx. Cada clase con su denominador. Sin «error total».

WITH
    total AS (
        SELECT count() AS llamadas_periodo
        FROM hecho_llamada_api
        WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
    )
SELECT
    formatDateTime(
        multiIf(
            {granularidad:String} = 'mes', toStartOfMonth({desde:Date}),
            {granularidad:String} = 'trimestre', toStartOfQuarter({desde:Date}),
            toStartOfYear({desde:Date})
        ),
        '%Y-%m'
    ) AS periodo,
    multiIf(
        codigo_http >= 500, '5xx',
        codigo_http >= 400, '4xx',
        'otro'
    ) AS clase_http,
    count() AS llamadas,
    (SELECT llamadas_periodo FROM total) AS denominador,
    round(count() / nullIf((SELECT llamadas_periodo FROM total), 0), 4) AS pct
FROM hecho_llamada_api
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
  AND codigo_http >= 400
GROUP BY periodo, clase_http
ORDER BY periodo, clase_http

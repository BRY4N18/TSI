-- E2-09 Adopción por (servicio, versión). version no es única. Se declara derivada.

SELECT
    formatDateTime(
        multiIf(
            {granularidad:String} = 'mes', toStartOfMonth({desde:Date}),
            {granularidad:String} = 'trimestre', toStartOfQuarter({desde:Date}),
            toStartOfYear({desde:Date})
        ),
        '%Y-%m'
    ) AS periodo,
    servicio,
    version_contrato AS version,
    count() AS llamadas,
    round(count() / nullIf(sum(count()) OVER (PARTITION BY periodo), 0), 4) AS pct,
    max(version_es_derivada) AS version_es_derivada
FROM hecho_llamada_api
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
  AND servicio IS NOT NULL
  AND version_contrato IS NOT NULL
GROUP BY periodo, servicio, version
ORDER BY periodo, servicio, version

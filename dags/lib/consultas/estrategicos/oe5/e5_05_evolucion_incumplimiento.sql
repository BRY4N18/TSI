-- E5-05 Evolución del incumplimiento. Mismos filtros de compromiso que E5-04.

SELECT
    formatDateTime(
        multiIf(
            {granularidad:String} = 'mes', toStartOfMonth(t.fecha),
            {granularidad:String} = 'trimestre', toStartOfQuarter(t.fecha),
            toStartOfYear(t.fecha)
        ),
        '%Y-%m'
    ) AS periodo,
    countIf(t.tiene_compromiso = 1) AS con_compromiso,
    countIf(t.tiene_compromiso = 1 AND t.desenlace_sla = 'incumplido') AS incumplidos,
    round(
        countIf(t.tiene_compromiso = 1 AND t.desenlace_sla = 'incumplido')
        / nullIf(countIf(t.tiene_compromiso = 1), 0),
        4
    ) AS pct_incumplimiento
FROM hecho_ticket AS t FINAL
WHERE t.fecha BETWEEN {desde:Date} AND {hasta:Date}
  AND (t.hora_cierre IS NOT NULL OR t.hora_resolucion IS NOT NULL)
GROUP BY periodo
HAVING con_compromiso > 0
ORDER BY periodo

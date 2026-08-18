-- E5-04 Cumplimiento de SLA. Denominador = cerrados con compromiso.

SELECT
    formatDateTime(
        multiIf(
            {granularidad:String} = 'mes', toStartOfMonth({desde:Date}),
            {granularidad:String} = 'trimestre', toStartOfQuarter({desde:Date}),
            toStartOfYear({desde:Date})
        ),
        '%Y-%m'
    ) AS periodo,
    countIf(t.tiene_compromiso = 1) AS con_compromiso,
    countIf(t.tiene_compromiso = 0) AS sin_compromiso,
    countIf(t.tiene_compromiso = 1 AND t.desenlace_sla = 'cumplido') AS cumplidos,
    countIf(t.tiene_compromiso = 1 AND t.desenlace_sla = 'incumplido') AS incumplidos,
    round(
        countIf(t.tiene_compromiso = 1 AND t.desenlace_sla = 'cumplido')
        / nullIf(countIf(t.tiene_compromiso = 1), 0),
        4
    ) AS pct_cumplimiento
FROM hecho_ticket AS t FINAL
WHERE t.fecha BETWEEN {desde:Date} AND {hasta:Date}
  AND (t.hora_cierre IS NOT NULL OR t.hora_resolucion IS NOT NULL)
GROUP BY periodo
HAVING con_compromiso > 0
ORDER BY periodo

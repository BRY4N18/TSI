-- E5-07 SLA por plan copiado en el hecho. No usa dim_plan.precio.

SELECT
    formatDateTime(
        multiIf(
            {granularidad:String} = 'mes', toStartOfMonth({desde:Date}),
            {granularidad:String} = 'trimestre', toStartOfQuarter({desde:Date}),
            toStartOfYear({desde:Date})
        ),
        '%Y-%m'
    ) AS periodo,
    ifNull(t.plan, '(sin plan)') AS plan,
    t.idplan AS idplan,
    countIf(t.tiene_compromiso = 1) AS con_compromiso,
    countIf(t.tiene_compromiso = 1 AND t.desenlace_sla = 'cumplido') AS cumplidos,
    round(
        countIf(t.tiene_compromiso = 1 AND t.desenlace_sla = 'cumplido')
        / nullIf(countIf(t.tiene_compromiso = 1), 0),
        4
    ) AS pct_cumplimiento
FROM hecho_ticket AS t FINAL
WHERE t.fecha BETWEEN {desde:Date} AND {hasta:Date}
  AND (t.hora_cierre IS NOT NULL OR t.hora_resolucion IS NOT NULL)
GROUP BY periodo, plan, idplan
HAVING con_compromiso > 0
ORDER BY periodo, plan

-- E1-09 Tiempo de onboarding. En proceso aparte; no cuentan como cero días.

WITH por_cliente AS (
    SELECT
        o.idcliente,
        max(o.dias_desde_alta) AS dias
    FROM hecho_onboarding AS o
    WHERE o.fecha <= {hasta:Date}
    GROUP BY o.idcliente
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
    round(medianIf(p.dias, c.onboarding_completo = 1), 1) AS dias_mediana,
    countIf(c.onboarding_completo = 1) AS completados,
    countIf(c.onboarding_completo = 0) AS en_proceso
FROM por_cliente AS p
INNER JOIN dim_cliente AS c FINAL ON c.idcliente = p.idcliente
WHERE {desde:Date} <= {hasta:Date}
GROUP BY periodo
HAVING completados > 0 OR en_proceso > 0
ORDER BY periodo

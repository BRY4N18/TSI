-- E1-11 Churn por cohorte. n bajo umbral → pct_churn NULL, no un 25 % anecdótico.

SELECT
    formatDateTime(
        multiIf(
            {granularidad:String} = 'mes', toStartOfMonth({desde:Date}),
            {granularidad:String} = 'trimestre', toStartOfQuarter({desde:Date}),
            toStartOfYear({desde:Date})
        ),
        '%Y-%m'
    ) AS periodo,
    c.cohorte_alta AS cohorte_alta,
    count() AS n,
    countIf(
        c.fecha_baja IS NOT NULL
        AND toDate(c.fecha_baja) BETWEEN {desde:Date} AND {hasta:Date}
    ) AS bajas,
    if(
        count() < {umbral_muestra:UInt32},
        CAST(NULL AS Nullable(Float64)),
        round(
            countIf(
                c.fecha_baja IS NOT NULL
                AND toDate(c.fecha_baja) BETWEEN {desde:Date} AND {hasta:Date}
            ) / nullIf(count(), 0),
            4
        )
    ) AS pct_churn
FROM dim_cliente AS c FINAL
WHERE c.cohorte_alta IS NOT NULL
  AND {desde:Date} <= {hasta:Date}
GROUP BY periodo, cohorte_alta
ORDER BY periodo, cohorte_alta

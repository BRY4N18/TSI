-- E1-06 Tasa de renovación. Denominador = vencidas en el período, no el stock.

SELECT
    formatDateTime(
        multiIf(
            {granularidad:String} = 'mes', toStartOfMonth({desde:Date}),
            {granularidad:String} = 'trimestre', toStartOfQuarter({desde:Date}),
            toStartOfYear({desde:Date})
        ),
        '%Y-%m'
    ) AS periodo,
    vencidas,
    renovadas,
    round(renovadas / nullIf(vencidas, 0), 4) AS tasa_renovacion
FROM (
    SELECT
        countIf(
            toDate(s.fecha_fin_prevista) BETWEEN {desde:Date} AND {hasta:Date}
        ) AS vencidas,
        countIf(
            toDate(s.fecha_fin_prevista) BETWEEN {desde:Date} AND {hasta:Date}
            AND (
                (
                    s.fecha_ultima_renovacion IS NOT NULL
                    AND toDate(s.fecha_ultima_renovacion) BETWEEN {desde:Date} AND {hasta:Date}
                )
                OR (s.fecha_cancelacion IS NULL AND s.estado_derivado = 'vigente')
            )
        ) AS renovadas
    FROM hecho_suscripcion AS s FINAL
    WHERE {desde:Date} <= {hasta:Date}
)
WHERE vencidas > 0 OR renovadas > 0
ORDER BY periodo

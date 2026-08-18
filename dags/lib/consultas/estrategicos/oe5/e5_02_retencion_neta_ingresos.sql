-- E5-02 NRR descompuesto. No copia el stub expansión=0 de OT07.

WITH
    cohorte AS (
        SELECT
            s.idcliente,
            s.id_suscripcion,
            s.precio_mensualizado AS mrr
        FROM hecho_suscripcion AS s FINAL
        WHERE s.precio_mensualizado IS NOT NULL
          AND toDate(s.fecha_alta) < {desde:Date}
          AND (
              s.fecha_cancelacion IS NULL
              OR toDate(s.fecha_cancelacion) >= {desde:Date}
          )
    ),
    movimientos AS (
        SELECT
            sumIf(m.delta_precio, m.delta_precio > 0) AS expansion,
            sumIf(-m.delta_precio, m.delta_precio < 0) AS contraccion
        FROM hecho_solicitud_cambio_plan AS m
        WHERE m.fecha BETWEEN {desde:Date} AND {hasta:Date}
          AND m.estado IN ('aprobada', 'aplicada')
    ),
    bajas AS (
        SELECT sum(c.mrr) AS churn
        FROM cohorte AS c
        INNER JOIN hecho_suscripcion AS s FINAL ON s.id_suscripcion = c.id_suscripcion
        WHERE s.fecha_cancelacion IS NOT NULL
          AND toDate(s.fecha_cancelacion) BETWEEN {desde:Date} AND {hasta:Date}
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
    round(sum(c.mrr), 2) AS mrr_inicial,
    round(ifNull((SELECT expansion FROM movimientos), 0), 2) AS expansion,
    round(ifNull((SELECT contraccion FROM movimientos), 0), 2) AS contraccion,
    round(ifNull((SELECT churn FROM bajas), 0), 2) AS churn,
    count() AS recuento,
    if(
        sum(c.mrr) = 0,
        CAST(NULL AS Nullable(Float64)),
        round(
            (
                sum(c.mrr)
                + ifNull((SELECT expansion FROM movimientos), 0)
                - ifNull((SELECT contraccion FROM movimientos), 0)
                - ifNull((SELECT churn FROM bajas), 0)
            ) / sum(c.mrr),
            4
        )
    ) AS nrr
FROM cohorte AS c
GROUP BY periodo
HAVING mrr_inicial != 0
ORDER BY periodo

-- E5-03 Movimientos aprobados. delta_precio del hecho, nunca el precio vigente del catálogo.

SELECT
    formatDateTime(
        multiIf(
            {granularidad:String} = 'mes', toStartOfMonth(m.fecha),
            {granularidad:String} = 'trimestre', toStartOfQuarter(m.fecha),
            toStartOfYear(m.fecha)
        ),
        '%Y-%m'
    ) AS periodo,
    m.tipo_movimiento AS tipo_movimiento,
    count() AS recuento,
    round(sum(m.delta_precio), 2) AS delta_ingreso
FROM hecho_solicitud_cambio_plan AS m
WHERE m.fecha BETWEEN {desde:Date} AND {hasta:Date}
  AND m.estado IN ('aprobada', 'aplicada')
GROUP BY periodo, tipo_movimiento
ORDER BY periodo, tipo_movimiento

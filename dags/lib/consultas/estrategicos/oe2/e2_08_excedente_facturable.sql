-- E2-08 Excedente facturable. No afirma cobro. Sin match de plan → no_tarificable.

SELECT
    formatDateTime(
        multiIf(
            {granularidad:String} = 'mes', toStartOfMonth({desde:Date}),
            {granularidad:String} = 'trimestre', toStartOfQuarter({desde:Date}),
            toStartOfYear({desde:Date})
        ),
        '%Y-%m'
    ) AS periodo,
    p.nombre_partner AS partner,
    ifNull(l.llamadas, 0) AS llamadas,
    p.limite_llamadas_mes AS cupo,
    pl.precio_excedente_llamada AS precio_unitario,
    if(pl.precio_excedente_llamada IS NULL, 1, 0) AS no_tarificable,
    if(
        pl.precio_excedente_llamada IS NULL,
        NULL,
        round(
            greatest(ifNull(l.llamadas, 0) - ifNull(p.limite_llamadas_mes, 0), 0)
            * pl.precio_excedente_llamada,
            2
        )
    ) AS importe_facturable
FROM dim_partner AS p FINAL
LEFT JOIN dim_plan AS pl FINAL ON pl.nombre = p.plan_api
LEFT JOIN (
    SELECT
        idpartner,
        count() AS llamadas
    FROM hecho_llamada_api
    WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
    GROUP BY idpartner
) AS l ON l.idpartner = p.idpartner
WHERE p.idpartner != -1
  AND p.estado = 'activo'
  AND {desde:Date} <= {hasta:Date}
ORDER BY periodo, partner

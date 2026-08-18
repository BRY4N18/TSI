-- E2-04 Consumo por partner frente al cupo. Ceros visibles si hay acceso.

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
    round(ifNull(l.llamadas, 0) / nullIf(p.limite_llamadas_mes, 0), 4) AS pct_cupo
FROM dim_partner AS p FINAL
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

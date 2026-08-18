-- E5-08 Reincidencia por cliente × servicio. Tres servicios distintos no cuentan.

SELECT
    formatDateTime(
        multiIf(
            {granularidad:String} = 'mes', toStartOfMonth({desde:Date}),
            {granularidad:String} = 'trimestre', toStartOfQuarter({desde:Date}),
            toStartOfYear({desde:Date})
        ),
        '%Y-%m'
    ) AS periodo,
    t.idcliente AS idcliente,
    ifNull(t.servicio, '(sin servicio)') AS servicio,
    count() AS tickets,
    countIf(t.fue_reabierto = 1) AS reabiertos
FROM hecho_ticket AS t FINAL
WHERE t.fecha BETWEEN {desde:Date} AND {hasta:Date}
GROUP BY periodo, idcliente, servicio
HAVING tickets >= 2
ORDER BY periodo, tickets DESC, idcliente, servicio

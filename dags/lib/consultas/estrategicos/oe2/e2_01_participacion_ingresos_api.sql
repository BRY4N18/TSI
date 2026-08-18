-- E2-01 Participación. Volumen de llamadas + excedente cobrado. Mix de plan API: no.

SELECT
    formatDateTime(
        multiIf(
            {granularidad:String} = 'mes', toStartOfMonth({desde:Date}),
            {granularidad:String} = 'trimestre', toStartOfQuarter({desde:Date}),
            toStartOfYear({desde:Date})
        ),
        '%Y-%m'
    ) AS periodo,
    (
        SELECT count()
        FROM hecho_llamada_api
        WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
    ) AS llamadas,
    round(
        sumIf(f.monto_con_signo, f.tipo = 'excedente_api'),
        2
    ) AS excedente_cobrado,
    round(sum(f.monto_con_signo), 2) AS ingreso_total
FROM hecho_factura AS f
WHERE f.fecha BETWEEN {desde:Date} AND {hasta:Date}
GROUP BY periodo
ORDER BY periodo

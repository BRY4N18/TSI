-- E2-02 MRR por línea. Misma regla de cobertura que E2-01: sin precio de plan API.

SELECT
    formatDateTime(
        multiIf(
            {granularidad:String} = 'mes', toStartOfMonth({desde:Date}),
            {granularidad:String} = 'trimestre', toStartOfQuarter({desde:Date}),
            toStartOfYear({desde:Date})
        ),
        '%Y-%m'
    ) AS periodo,
    if(f.tipo = 'excedente_api', 'api_excedente', 'plataforma') AS linea,
    round(sum(f.monto_con_signo), 2) AS monto,
    (
        SELECT count()
        FROM hecho_llamada_api
        WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
    ) AS llamadas
FROM hecho_factura AS f
WHERE f.fecha BETWEEN {desde:Date} AND {hasta:Date}
GROUP BY periodo, linea
ORDER BY periodo, linea

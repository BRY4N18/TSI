-- E1-03 MRR por tipo de cliente. Sin país. Desconocidos visibles.

SELECT
    formatDateTime(
        multiIf(
            {granularidad:String} = 'mes', toStartOfMonth({desde:Date}),
            {granularidad:String} = 'trimestre', toStartOfQuarter({desde:Date}),
            toStartOfYear({desde:Date})
        ),
        '%Y-%m'
    ) AS periodo,
    ifNull(nullIf(c.tipo, ''), '(desconocido)') AS tipo,
    round(sum(s.precio_mensualizado), 2) AS mrr,
    count() AS recuento
FROM hecho_suscripcion AS s FINAL
INNER JOIN dim_cliente AS c FINAL ON c.idcliente = s.idcliente
WHERE toDate(s.fecha_alta) <= {hasta:Date}
  AND (s.fecha_cancelacion IS NULL OR toDate(s.fecha_cancelacion) > {hasta:Date})
  AND (s.fecha_fin_prevista IS NULL OR toDate(s.fecha_fin_prevista) >= {hasta:Date})
  AND s.precio_mensualizado IS NOT NULL
GROUP BY periodo, tipo
ORDER BY periodo, tipo

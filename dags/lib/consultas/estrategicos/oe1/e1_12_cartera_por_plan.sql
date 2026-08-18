-- E1-12 Mezcla de cartera por plan. La evolución viaja en la comparación mom/yoy.

SELECT
    formatDateTime(
        multiIf(
            {granularidad:String} = 'mes', toStartOfMonth({desde:Date}),
            {granularidad:String} = 'trimestre', toStartOfQuarter({desde:Date}),
            toStartOfYear({desde:Date})
        ),
        '%Y-%m'
    ) AS periodo,
    s.idplan AS idplan,
    s.plan AS plan,
    round(sum(s.precio_mensualizado), 2) AS mrr,
    count() AS recuento,
    round(count() / nullIf(sum(count()) OVER (PARTITION BY periodo), 0), 4) AS pct_cartera
FROM hecho_suscripcion AS s FINAL
WHERE toDate(s.fecha_alta) <= {hasta:Date}
  AND (s.fecha_cancelacion IS NULL OR toDate(s.fecha_cancelacion) > {hasta:Date})
  AND (s.fecha_fin_prevista IS NULL OR toDate(s.fecha_fin_prevista) >= {hasta:Date})
  AND s.precio_mensualizado IS NOT NULL
GROUP BY periodo, idplan, plan
ORDER BY periodo, mrr DESC, plan

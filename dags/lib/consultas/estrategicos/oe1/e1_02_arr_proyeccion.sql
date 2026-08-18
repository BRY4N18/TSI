-- E1-02 ARR = MRR × 12. Extrapolación, no compromiso.

SELECT
    formatDateTime(
        multiIf(
            {granularidad:String} = 'mes', toStartOfMonth({desde:Date}),
            {granularidad:String} = 'trimestre', toStartOfQuarter({desde:Date}),
            toStartOfYear({desde:Date})
        ),
        '%Y-%m'
    ) AS periodo,
    round(sum(s.precio_mensualizado), 2) AS mrr,
    round(sum(s.precio_mensualizado) * 12, 2) AS arr,
    count() AS recuento,
    'extrapolacion_base' AS escenario
FROM hecho_suscripcion AS s FINAL
WHERE toDate(s.fecha_alta) <= {hasta:Date}
  AND (s.fecha_cancelacion IS NULL OR toDate(s.fecha_cancelacion) > {hasta:Date})
  AND (s.fecha_fin_prevista IS NULL OR toDate(s.fecha_fin_prevista) >= {hasta:Date})
  AND s.precio_mensualizado IS NOT NULL
ORDER BY periodo

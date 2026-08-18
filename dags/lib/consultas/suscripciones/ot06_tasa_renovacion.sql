-- Informe #3 — Tasa de renovación · OT06
--
-- Vencidas = fin previsto en el período. Renovadas = siguen vigentes.

SELECT
    formatDateTime(toStartOfMonth(toDate(fecha_fin_prevista)), '%Y-%m') AS mes,
    count()                                                              AS vencidas,
    countIf(estado_derivado = 'vigente')                                 AS renovadas,
    if(count() = 0, NULL, round(countIf(estado_derivado = 'vigente') / count(), 4))
                                                                         AS pct_renovacion
FROM hecho_suscripcion FINAL
WHERE fecha_fin_prevista IS NOT NULL
  AND vigencia_inconsistente = 0
  AND toDate(fecha_fin_prevista) BETWEEN {desde:Date} AND {hasta:Date}
GROUP BY mes
ORDER BY mes

-- Taxonomía de errores · OT09
--
-- ⚠️ Agrupa por clase_resultado antes que por código. 429 ≠ 403 ≠ 5xx.

SELECT
    toStartOfMonth({desde:Date}) AS periodo,
    clase_resultado,
    codigo_http,
    count() AS llamadas,
    round(count() / nullIf(sum(count()) OVER (), 0), 4) AS pct
FROM hecho_llamada_api
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
  AND clase_resultado != 'exito'
GROUP BY periodo, clase_resultado, codigo_http
ORDER BY periodo, clase_resultado, codigo_http

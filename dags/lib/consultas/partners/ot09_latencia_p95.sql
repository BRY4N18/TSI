-- Latencia p95 por endpoint · OT09
--
-- ⚠️ p95 y media juntas. muestras siempre. percentil_fiable marca, no filtra.

SELECT
    endpoint_path,
    round(avg(latencia_ms), 1) AS latencia_media_ms,
    round(quantileExact(toFloat64({percentil:Int32}) / 100)(latencia_ms), 1) AS latencia_p95_ms,
    count() AS muestras,
    if(count() >= {muestra_minima:Int32}, 1, 0) AS percentil_fiable
FROM hecho_llamada_api
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
GROUP BY endpoint_path
ORDER BY endpoint_path

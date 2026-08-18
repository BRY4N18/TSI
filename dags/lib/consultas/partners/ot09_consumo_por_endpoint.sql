-- Consumo por endpoint y método · OT09
--
-- Agrupa por path ya normalizado (sin cadena de consulta).

SELECT
    endpoint_path,
    metodo_http,
    count() AS llamadas,
    round(count() / nullIf(sum(count()) OVER (), 0), 4) AS pct,
    count() AS muestras
FROM hecho_llamada_api
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
GROUP BY endpoint_path, metodo_http
ORDER BY llamadas DESC, endpoint_path, metodo_http

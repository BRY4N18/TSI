-- Adopción de versiones del contrato · OT08
--
-- Agrupa por (servicio, versión). Dos servicios con 'v1' son dos filas.
-- version_es_derivada: el log no registra la versión.

SELECT
    servicio,
    version_contrato AS version,
    count() AS llamadas,
    round(count() / nullIf(sum(count()) OVER (), 0), 4) AS pct,
    max(version_es_derivada) AS version_es_derivada
FROM hecho_llamada_api
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
  AND servicio IS NOT NULL
  AND version_contrato IS NOT NULL
GROUP BY servicio, version
ORDER BY servicio, version

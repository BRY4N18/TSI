-- Volumen de expedientes por cliente y canal · OT10
--
-- Portal = casos en hecho_accidente. API = llamadas al path de accidentes.
-- El hecho de accidentes no trae idcliente; el canal portal se declara igual.

SELECT
    cliente,
    canal,
    count() AS expedientes
FROM (
    SELECT '(portal)' AS cliente, 'portal' AS canal
    FROM hecho_accidente FINAL
    WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
    UNION ALL
    SELECT toString(idcliente) AS cliente, 'api' AS canal
    FROM hecho_llamada_api
    WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
      AND idcliente IS NOT NULL
      AND position(endpoint_path, 'accidentes') > 0
)
GROUP BY cliente, canal
ORDER BY cliente, canal

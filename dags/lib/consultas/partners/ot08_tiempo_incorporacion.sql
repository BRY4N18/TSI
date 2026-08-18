-- Tiempo de incorporación por etapa · OT08
--
-- En proceso fuera de la media: no tardaron cero, siguen tardando.

WITH
    hitos AS (
        SELECT
            idpartner,
            partner,
            nullIf(
                minIf(fechahora, tipo_cambio = 'registro' AND es_cambio_efectivo = 1),
                toDateTime(0)
            ) AS t_registro,
            nullIf(
                minIf(fechahora, tipo_cambio = 'activacion_produccion' AND es_cambio_efectivo = 1),
                toDateTime(0)
            ) AS t_produccion,
            argMaxIf(tipo_cambio, fechahora, es_cambio_efectivo = 1) AS etapa
        FROM hecho_cambio_acceso
        WHERE fecha <= {hasta:Date}
        GROUP BY idpartner, partner
    )
SELECT
    partner,
    etapa,
    if(
        t_produccion IS NULL,
        NULL,
        dateDiff('day', toDate(t_registro), toDate(t_produccion))
    ) AS dias,
    if(t_produccion IS NULL, 1, 0) AS en_proceso
FROM hitos
WHERE t_registro IS NOT NULL
  AND {desde:Date} <= {hasta:Date}
ORDER BY partner

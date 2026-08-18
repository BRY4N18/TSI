-- E2-03 Integraciones activas.
-- Numerador: partners con ≥1 llamada en el período.
-- Denominador: dim_partner con acceso concedido (estado activo), no el catálogo entero.

SELECT
    formatDateTime(
        multiIf(
            {granularidad:String} = 'mes', toStartOfMonth({desde:Date}),
            {granularidad:String} = 'trimestre', toStartOfQuarter({desde:Date}),
            toStartOfYear({desde:Date})
        ),
        '%Y-%m'
    ) AS periodo,
    (
        SELECT count()
        FROM dim_partner AS p FINAL
        WHERE p.idpartner != -1
          AND p.estado = 'activo'
    ) AS partners_con_acceso,
    count(DISTINCT l.idpartner) AS partners_con_llamada,
    round(
        count(DISTINCT l.idpartner)
        / nullIf(
            (SELECT count() FROM dim_partner AS p2 FINAL WHERE p2.idpartner != -1 AND p2.estado = 'activo'),
            0
        ),
        4
    ) AS pct_adopcion
FROM hecho_llamada_api AS l
WHERE l.fecha BETWEEN {desde:Date} AND {hasta:Date}
  AND l.idpartner != -1
ORDER BY periodo

-- E5-12 Riesgo con ≥2 señales. sin_actividad_conocida, no 0 días.

WITH
    n_api AS (
        SELECT count() AS n
        FROM hecho_llamada_api
        WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
          AND idcliente IS NOT NULL
    ),
    n_tickets AS (
        SELECT count() AS n
        FROM hecho_ticket FINAL
        WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
    ),
    n_cobro AS (
        SELECT count() AS n
        FROM hecho_factura
        WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
    ),
    n_sesiones AS (
        SELECT count() AS n
        FROM hecho_sesion
        WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
    ),
    api_act AS (
        SELECT idcliente, count() AS n
        FROM hecho_llamada_api
        WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
          AND idcliente IS NOT NULL
        GROUP BY idcliente
    ),
    api_prev AS (
        SELECT idcliente, count() AS n
        FROM hecho_llamada_api
        WHERE fecha BETWEEN {desde:Date} - (dateDiff('day', {desde:Date}, {hasta:Date}) + 1)
          AND {desde:Date} - 1
          AND idcliente IS NOT NULL
        GROUP BY idcliente
    ),
    tickets_act AS (
        SELECT idcliente, count() AS n
        FROM hecho_ticket FINAL
        WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
        GROUP BY idcliente
    ),
    tickets_prev AS (
        SELECT idcliente, count() AS n
        FROM hecho_ticket FINAL
        WHERE fecha BETWEEN {desde:Date} - (dateDiff('day', {desde:Date}, {hasta:Date}) + 1)
          AND {desde:Date} - 1
        GROUP BY idcliente
    ),
    cobro AS (
        SELECT
            idcliente,
            countIf(
                estado_pago != 'pagada'
                OR pagada_primer_intento = 0
                OR ifNull(dias_mora, 0) > 0
            ) AS fallos
        FROM hecho_factura
        WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
        GROUP BY idcliente
    ),
    sesiones AS (
        SELECT u.idcliente AS idcliente, max(s.fechahora_inicio) AS ultima
        FROM dim_usuario_organizacion AS u FINAL
        INNER JOIN hecho_sesion AS s ON s.idusuario = u.idusuario
        WHERE u.tiene_pertenencia = 1
          AND u.idcliente IS NOT NULL
        GROUP BY u.idcliente
    )
SELECT
    formatDateTime(
        multiIf(
            {granularidad:String} = 'mes', toStartOfMonth({desde:Date}),
            {granularidad:String} = 'trimestre', toStartOfQuarter({desde:Date}),
            toStartOfYear({desde:Date})
        ),
        '%Y-%m'
    ) AS periodo,
    c.idcliente AS idcliente,
    toUInt8(ifNull(ap.n, 0) > 0 AND ifNull(aa.n, 0) * 2 <= ifNull(ap.n, 0)) AS senal_api,
    toUInt8(ifNull(ta.n, 0) >= 2 AND ifNull(ta.n, 0) > ifNull(tp.n, 0) * 2) AS senal_tickets,
    toUInt8(ifNull(co.fallos, 0) > 0) AS senal_cobro,
    toUInt8(se.ultima IS NULL OR toDate(se.ultima) < {desde:Date}) AS senal_sesiones,
    toUInt8(ifNull(ap.n, 0) > 0 AND ifNull(aa.n, 0) * 2 <= ifNull(ap.n, 0))
        + toUInt8(ifNull(ta.n, 0) >= 2 AND ifNull(ta.n, 0) > ifNull(tp.n, 0) * 2)
        + toUInt8(ifNull(co.fallos, 0) > 0)
        + toUInt8(se.ultima IS NULL OR toDate(se.ultima) < {desde:Date}) AS n_senales,
    (SELECT n FROM n_api) AS n_fuente_api,
    (SELECT n FROM n_tickets) AS n_fuente_tickets,
    (SELECT n FROM n_cobro) AS n_fuente_cobro,
    (SELECT n FROM n_sesiones) AS n_fuente_sesiones
FROM dim_cliente AS c FINAL
LEFT JOIN api_act AS aa ON aa.idcliente = c.idcliente
LEFT JOIN api_prev AS ap ON ap.idcliente = c.idcliente
LEFT JOIN tickets_act AS ta ON ta.idcliente = c.idcliente
LEFT JOIN tickets_prev AS tp ON tp.idcliente = c.idcliente
LEFT JOIN cobro AS co ON co.idcliente = c.idcliente
LEFT JOIN sesiones AS se ON se.idcliente = c.idcliente
WHERE c.fecha_baja IS NULL
  AND c.idcliente != -1
  AND {desde:Date} <= {hasta:Date}
HAVING n_senales >= 2
ORDER BY periodo, n_senales DESC, idcliente

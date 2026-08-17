-- Informe E6-06 — Abortos y misiones fallidas, por causa
-- Parte de ot23_abortos_perdidas. Cuenta MISIONES (filas de despacho), no
-- transiciones de estado. `en_curso` no es un fracaso: es un despacho sin
-- desenlace, y contarlo como perdido convierte cada consulta de media tarde en
-- un informe pesimista que mejora solo al día siguiente.
--
-- El denominador `misiones` es el total de intentos del período, el mismo para
-- las tres causas. Un desenlace sin casos aparece con misiones_causa = 0: un
-- cero que falta se lee como un dato que no existe.

SELECT
    g.periodo                                                   AS periodo,
    c.causa                                                     AS causa,
    g.misiones                                                  AS misiones,
    coalesce(f.misiones_causa, 0)                               AS misiones_causa,
    if(g.misiones = 0, NULL, round(coalesce(f.misiones_causa, 0) / g.misiones, 4)) AS pct
FROM (
    SELECT
        formatDateTime(
            multiIf(
                {granularidad:String} = 'mes', toStartOfMonth(fecha),
                {granularidad:String} = 'trimestre', toStartOfQuarter(fecha),
                toStartOfYear(fecha)
            ),
            '%Y-%m'
        )                                                       AS periodo,
        count()                                                 AS misiones
    FROM hecho_despacho FINAL
    WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
    GROUP BY periodo
) AS g
CROSS JOIN (
    SELECT arrayJoin(['abortado', 'rechazado', 'vencido']) AS causa
) AS c
LEFT JOIN (
    SELECT
        formatDateTime(
            multiIf(
                {granularidad:String} = 'mes', toStartOfMonth(fecha),
                {granularidad:String} = 'trimestre', toStartOfQuarter(fecha),
                toStartOfYear(fecha)
            ),
            '%Y-%m'
        )                                                       AS periodo,
        resultado                                               AS causa,
        count()                                                 AS misiones_causa
    FROM hecho_despacho FINAL
    WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
      AND resultado IN ('abortado', 'rechazado', 'vencido')
    GROUP BY periodo, causa
) AS f ON f.periodo = g.periodo AND f.causa = c.causa
ORDER BY periodo, causa

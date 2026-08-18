-- C8 · Carga entrante frente a resuelta · OT20
--
-- Días sin actividad aparecen con cero. Sin WITH FILL la pendiente mentiría.

SELECT
    dia,
    sum(creados) AS creados,
    sum(resueltos) AS resueltos,
    sum(sum(creados) - sum(resueltos)) OVER (ORDER BY dia) AS neto_acumulado
FROM (
    SELECT
        fecha AS dia,
        count() AS creados,
        toUInt64(0) AS resueltos
    FROM hecho_ticket FINAL
    WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
      AND ({idagente:Int32} = -1 OR idagente = {idagente:Int32})
    GROUP BY fecha

    UNION ALL

    SELECT
        toDate(hora_resolucion) AS dia,
        toUInt64(0) AS creados,
        count() AS resueltos
    FROM hecho_ticket FINAL
    WHERE hora_resolucion IS NOT NULL
      AND toDate(hora_resolucion) BETWEEN {desde:Date} AND {hasta:Date}
      AND ({idagente:Int32} = -1 OR idagente = {idagente:Int32})
    GROUP BY dia
)
GROUP BY dia
ORDER BY dia
WITH FILL FROM {desde:Date} TO {hasta:Date} + INTERVAL 1 DAY STEP INTERVAL 1 DAY

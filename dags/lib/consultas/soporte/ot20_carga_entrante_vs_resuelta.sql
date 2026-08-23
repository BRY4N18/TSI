-- C8 · Carga entrante frente a resuelta · OT20
--
-- Días sin actividad aparecen con cero. Sin WITH FILL la pendiente mentiría.

--
-- ⚠️ Las columnas internas se llaman `creados_dia`/`resueltos_dia` **y no pueden
-- llamarse igual que las de salida**. Con el mismo nombre, el `sum(creados)` de
-- dentro de la ventana se resolvía contra el alias de salida —que ya es un
-- agregado— y ClickHouse rechazaba la consulta entera con ILLEGAL_AGGREGATION.
-- El informe devolvía 500, no una cifra equivocada.

SELECT
    dia,
    sum(creados_dia) AS creados,
    sum(resueltos_dia) AS resueltos,
    sum(sum(creados_dia) - sum(resueltos_dia)) OVER (ORDER BY dia) AS neto_acumulado
FROM (
    SELECT
        fecha AS dia,
        count() AS creados_dia,
        toUInt64(0) AS resueltos_dia
    FROM hecho_ticket FINAL
    WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
      AND ({idagente:Int32} = -1 OR idagente = {idagente:Int32})
    GROUP BY fecha

    UNION ALL

    SELECT
        toDate(hora_resolucion) AS dia,
        toUInt64(0) AS creados_dia,
        count() AS resueltos_dia
    FROM hecho_ticket FINAL
    WHERE hora_resolucion IS NOT NULL
      AND toDate(hora_resolucion) BETWEEN {desde:Date} AND {hasta:Date}
      AND ({idagente:Int32} = -1 OR idagente = {idagente:Int32})
    GROUP BY dia
)
GROUP BY dia
ORDER BY dia
WITH FILL FROM {desde:Date} TO {hasta:Date} + INTERVAL 1 DAY STEP INTERVAL 1 DAY

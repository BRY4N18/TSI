-- C1 · Cumplimiento de SLA (BSC, meta ≥ 95 %) · OT19
--
-- ⚠️ Denominador = solo tickets con compromiso. La cobertura viaja EN LA MISMA
-- fila: excluir sin declararlo premiaría dejar tickets sin clasificar.
-- ⚠️ nullIf: un período sin compromiso devuelve ausente, no 0 %.
-- ⚠️ Límites copiados en el hecho; jamás se une con el SLA vigente hoy.
--
-- ⚠️ `hecho_ticket AS t` y `t.motivo_sin_compromiso` **calificados a propósito**.
-- Sin el alias de tabla, `countIf(motivo_sin_compromiso = ...) AS
-- motivo_sin_compromiso` hace que el analizador resuelva el argumento contra su
-- **propio alias de salida** en vez de contra la columna, y ClickHouse rechaza
-- la consulta entera con ILLEGAL_AGGREGATION («agregado dentro de otro
-- agregado»). El informe devolvía 500, no una cifra equivocada.

SELECT
    multiIf(
        {granularidad:String} = 'mes', toStartOfMonth(fecha),
        {granularidad:String} = 'semana', toStartOfWeek(fecha),
        toStartOfDay(fecha)
    ) AS periodo,

    countIf(tiene_compromiso = 1) AS con_compromiso,
    countIf(tiene_compromiso = 0) AS sin_compromiso,
    count()                       AS tickets,

    countIf(desenlace_sla = 'cumplido')   AS cumplidos,
    countIf(desenlace_sla = 'incumplido') AS incumplidos,

    round(100.0 * countIf(desenlace_sla = 'cumplido')
          / nullIf(countIf(tiene_compromiso = 1), 0), 2) AS pct_cumplimiento,

    round(100.0 * countIf(tiene_compromiso = 0)
          / nullIf(count(), 0), 2) AS pct_sin_compromiso,

    countIf(t.motivo_sin_compromiso = 'pendiente_clasificar') AS motivo_pendiente_clasificar,
    countIf(t.motivo_sin_compromiso = 'sin_compromiso')       AS motivo_sin_compromiso,
    countIf(t.motivo_sin_compromiso = 'sin_config')           AS motivo_sin_config
FROM hecho_ticket AS t FINAL
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
  AND ({idagente:Int32} = -1 OR idagente = {idagente:Int32})
GROUP BY periodo
ORDER BY periodo

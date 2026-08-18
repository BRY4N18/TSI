-- C7 · Tasa de escalado automático · OT20
--
-- ⚠️ SIN FINAL en hecho_accion_ticket: es de transacción.
-- ⚠️ uniqExact sobre el ticket: tres escalados del mismo ticket cuentan como uno.
-- ⚠️ Las dos columnas de escalado nunca se suman.

SELECT
    t.tipo_incidencia,
    t.prioridad,
    uniqExact(t.id_reclamo) AS tickets,
    uniqExactIf(a.id_reclamo, a.es_escalado_automatico = 1) AS con_escalado_automatico,
    uniqExactIf(a.id_reclamo, a.es_escalado = 1 AND a.es_escalado_automatico = 0) AS con_escalado_humano,
    round(100.0 * uniqExactIf(a.id_reclamo, a.es_escalado_automatico = 1)
          / nullIf(uniqExact(t.id_reclamo), 0), 2) AS pct_escalado_automatico
FROM hecho_ticket AS t FINAL
LEFT JOIN hecho_accion_ticket AS a
       ON a.id_reclamo = t.id_reclamo
WHERE t.fecha BETWEEN {desde:Date} AND {hasta:Date}
  AND ({idagente:Int32} = -1 OR t.idagente = {idagente:Int32})
GROUP BY t.tipo_incidencia, t.prioridad
ORDER BY tickets DESC, t.tipo_incidencia, t.prioridad

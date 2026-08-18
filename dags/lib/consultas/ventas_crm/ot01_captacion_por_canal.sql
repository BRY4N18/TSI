-- Informe #6 — Volumen de captación por canal · OT01 · CU-T04
--
-- Los prospectos sin canal aparecen como `Desconocido` y **suman en los
-- totales**. Dejarlos fuera haria que los canales sumaran menos que el embudo
-- sin que nada lo indicara.
--
-- ⚠️ Ninguna consulta de este departamento lee `activo`.

SELECT
    toDate({desde:Date})                         AS periodo,
    p.canal                                      AS canal,
    count()                                      AS prospectos,
    round(count() / sum(count()) OVER (), 4)     AS pct,
    sum(count()) OVER ()                         AS denominador
FROM dim_prospecto AS p FINAL
LEFT JOIN (
    SELECT
        idprospecto,
        argMax(idejecutivo, (fechahora, idasignacion)) AS vigente
    FROM hecho_asignacion_prospecto
    WHERE fecha <= {hasta:Date}
    GROUP BY idprospecto
) AS v ON v.idprospecto = p.idprospecto
WHERE p.fecha_registro IS NOT NULL
  AND toDate(p.fecha_registro) BETWEEN {desde:Date} AND {hasta:Date}
  AND (
      {idejecutivo:Int32} = -1
      OR v.vigente = {idejecutivo:Int32}
  )
GROUP BY p.canal
ORDER BY prospectos DESC, canal

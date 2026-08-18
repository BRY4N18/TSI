-- Informe #7 — Tasa de conversión por canal · OT01 · CU-T04
--
-- ⚠️ LEE `desenlace`, NUNCA `activo`
-- ----------------------------------
-- `Dim_Prospecto.activo` cubre a la vez convertido y perdido. Agrupar por esa
-- columna juntaria el mejor desenlace con el peor.
--
-- Un canal sin prospectos en el periodo **no aparece**. Devolver 0 % afirmaria
-- que se midio y nadie convirtio; no aparecer es «sin dato».

SELECT
    toDate({desde:Date})                         AS periodo,
    p.canal                                      AS canal,
    count()                                      AS prospectos,
    countIf(p.desenlace = 'convertido')          AS convertidos,
    if(
        count() = 0,
        NULL,
        round(countIf(p.desenlace = 'convertido') / count(), 4)
    )                                            AS pct_conversion,
    count()                                      AS denominador
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

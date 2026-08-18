-- Informe #12 — Latencia de reacción comercial · OT03
--
-- ⚠️ LOS AVISOS SIN REACCION QUEDAN FUERA DE LA MEDIANA
-- ----------------------------------------------------
-- `hubo_avance = 0` y `segundos_a_reaccion` ausente es un aviso **ignorado**,
-- no una reaccion instantanea. Incluirlos como cero haria que los peores casos
-- mejoraran el indicador. Se cuentan en `sin_reaccion` y no entran a
-- `segundos_mediana`.

SELECT
    toDate({desde:Date})                         AS periodo,
    count()                                      AS avisos,
    countIf(hubo_avance = 1)                     AS con_reaccion,
    countIf(hubo_avance = 0)                     AS sin_reaccion,
    round(medianIf(segundos_a_reaccion, hubo_avance = 1))
                                                 AS segundos_mediana
FROM hecho_notificacion_ventas
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
  AND (
      {idejecutivo:Int32} = -1
      OR idprospecto IN (
          SELECT idprospecto
          FROM (
              SELECT
                  idprospecto,
                  argMax(idejecutivo, (fechahora, idasignacion)) AS vigente
              FROM hecho_asignacion_prospecto
              WHERE fecha <= {hasta:Date}
              GROUP BY idprospecto
          )
          WHERE vigente = {idejecutivo:Int32}
      )
  )
HAVING count() > 0
ORDER BY periodo

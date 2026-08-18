-- Informe #10 — Secciones más visitadas · OT03
--
-- `top` recorta el ranking. Una seccion nula no se descarta: es un evento
-- sin seccion registrada, y dejarlo fuera haria que las visitas sumaran menos
-- que los eventos del informe de intensidad.

SELECT
    ifNull(nullIf(seccion, ''), 'sin seccion registrada') AS seccion,
    count()                                               AS visitas,
    uniqExact(idprospecto)                                AS prospectos_distintos
FROM hecho_interaccion_demo
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
GROUP BY seccion
ORDER BY visitas DESC, seccion
LIMIT {top:UInt32}

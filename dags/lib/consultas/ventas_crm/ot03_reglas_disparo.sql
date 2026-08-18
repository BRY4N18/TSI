-- Informe #13 — Reglas de disparo por tasa de acierto · OT03
--
-- Tasa = avisos que produjeron un avance / avisos de esa regla.
-- `denominador` es el total de avisos de la regla, para que la tasa sea
-- comprobable. Un aviso ignorado baja la tasa; no la mejora.

SELECT
    regla_disparada                              AS regla_disparada,
    count()                                      AS avisos,
    countIf(hubo_avance = 1)                     AS con_reaccion,
    if(
        count() = 0,
        NULL,
        round(countIf(hubo_avance = 1) / count(), 4)
    )                                            AS tasa_acierto,
    count()                                      AS denominador
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
GROUP BY regla_disparada
ORDER BY avisos DESC, regla_disparada

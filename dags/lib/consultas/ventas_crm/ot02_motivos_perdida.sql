-- Informe #5 — Motivos de pérdida por etapa de abandono · OT02 · CU-T03
--
-- Agrupa **motivo y etapa juntos**: el mismo motivo significa cosas distintas
-- en Contactado que en Negociación.
--
-- Un motivo ausente aparece como «sin motivo registrado», no se descarta.
-- Descartarlo haria que las perdidas peor documentadas desaparecieran del
-- informe que existe para verlas.

SELECT
    multiIf(
        motivo_perdida IS NOT NULL AND motivo_perdida != '',
        motivo_perdida,
        'sin motivo registrado'
    )                                                       AS motivo,
    ifNull(nullIf(etapa_anterior, ''), 'sin etapa registrada')
                                                            AS etapa_abandono,
    count()                                                 AS perdidos,
    round(count() / sum(count()) OVER (), 4)                AS pct,
    sum(count()) OVER ()                                    AS denominador
FROM hecho_transicion_embudo
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
  AND etapa_nueva = 'Perdido'
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
GROUP BY motivo, etapa_abandono
ORDER BY perdidos DESC, motivo, etapa_abandono
LIMIT {top:UInt32}

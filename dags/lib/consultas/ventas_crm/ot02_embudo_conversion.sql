-- Informe #1 — Embudo de conversión · OT02 · CU-T03
--
-- Volumen y % de paso entre etapas, medido sobre **transiciones**.
--
-- ⚠️ EL GRANO ES LA TRANSICION, NO EL PROSPECTO
-- ---------------------------------------------
-- Un prospecto puede retroceder de etapa. Contar prospectos unicos haria que
-- ese retroceso desapareciera y el embudo cuadrara de una forma que no ocurrio.
-- `denominador` es el total de transiciones que salen de `etapa_anterior`, para
-- que pct_paso * denominador = transiciones sea comprobable.
--
-- ⚠️ El acotamiento filtra por el ejecutivo vigente al corte `{hasta}`, no por
-- quien estuvo asignado alguna vez. Vive en `hecho_asignacion_prospecto`.

SELECT
    toDate({desde:Date})                                    AS periodo,
    ifNull(etapa_anterior, '(inicio)')                      AS etapa_anterior,
    etapa_nueva                                             AS etapa_nueva,
    count()                                                 AS transiciones,
    round(count() / sum(count()) OVER (PARTITION BY ifNull(etapa_anterior, '(inicio)')), 4)
                                                            AS pct_paso,
    sum(count()) OVER (PARTITION BY ifNull(etapa_anterior, '(inicio)'))
                                                            AS denominador
FROM hecho_transicion_embudo
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
GROUP BY etapa_anterior, etapa_nueva
ORDER BY transiciones DESC, etapa_anterior, etapa_nueva

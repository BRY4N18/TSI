-- Informe E6-12 — Cobertura de evidencia en casos cerrados
-- Parte de ot24_cobertura_evidencia. Solo casos CERRADOS. Separa foto de nota
-- antes de combinarlas: son capturas distintas, con dispositivos y momentos
-- distintos. Un `% con evidencia` combinado esconde cuál de las dos falta.
--
-- ⚠️ hecho_evidencia es de TRANSACCIÓN: prohibido forzar FINAL. Pedirlo falla
-- con ILLEGAL_FINAL.
--
-- Se parte de los casos, no de las evidencias. Partiendo de las evidencias, un
-- caso sin ninguna desaparece y la cobertura saldría del 100 % siempre.

SELECT
    formatDateTime(
        multiIf(
            {granularidad:String} = 'mes', toStartOfMonth(a.fecha),
            {granularidad:String} = 'trimestre', toStartOfQuarter(a.fecha),
            toStartOfYear(a.fecha)
        ),
        '%Y-%m'
    )                                                           AS periodo,
    coalesce(a.severidad, 'Desconocido')                        AS severidad,
    count()                                                     AS casos_cerrados,
    countIf(coalesce(e.fotos, 0) > 0)                           AS con_foto,
    countIf(coalesce(e.notas, 0) > 0)                           AS con_nota,
    countIf(coalesce(e.fotos, 0) > 0 AND coalesce(e.notas, 0) > 0) AS con_ambas,
    if(
        count() = 0,
        NULL,
        round(countIf(coalesce(e.fotos, 0) > 0 AND coalesce(e.notas, 0) > 0) / count(), 4)
    )                                                           AS pct_con_ambas
FROM hecho_accidente AS a FINAL
LEFT JOIN (
    SELECT
        idaccidente                     AS idaccidente,
        countIf(tipo = 'foto')          AS fotos,
        countIf(tipo = 'nota')          AS notas
    FROM hecho_evidencia
    GROUP BY idaccidente
) AS e ON e.idaccidente = a.idaccidente
WHERE a.fecha BETWEEN {desde:Date} AND {hasta:Date}
  AND a.hora_cierre IS NOT NULL
  AND a.fue_descartado = 0
  AND a.es_duplicado = 0
GROUP BY periodo, severidad
ORDER BY periodo, casos_cerrados DESC, severidad

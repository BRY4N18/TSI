-- Informe E3-03 — Evolución de la latencia p95 (MoM / YoY)
-- Serie del p95 registro → primera asignación sobre ventanas amplias.
-- Existe para detectar degradación gradual, no un salto que dispare una alarma.
--
-- ⚠️ FILTRAR POR PARTICIÓN PESO AQUÍ MÁS QUE EN NINGÚN OTRO INFORME DE LA CAPA
-- Sin `fecha BETWEEN`, una ventana anual recorre el histórico entero y se
-- degradará según crezca, sin que nada avise.
--
-- Misma población que E3-02: con asignación, no descartado, no duplicado.
-- El p95 ausente bajo muestra_minima.

SELECT
    formatDateTime(
        multiIf(
            {granularidad:String} = 'mes', toStartOfMonth(fecha),
            {granularidad:String} = 'trimestre', toStartOfQuarter(fecha),
            toStartOfYear(fecha)
        ),
        '%Y-%m'
    )                                                           AS periodo,
    countIf(hora_primera_asignacion IS NOT NULL)                AS casos_asignados,
    if(
        countIf(hora_primera_asignacion IS NOT NULL) >= {muestra_minima:UInt32},
        round(
            quantileIf(0.95)(
                dateDiff('second', fechahora_accidente, hora_primera_asignacion),
                hora_primera_asignacion IS NOT NULL
            ),
            1
        ),
        NULL
    )                                                           AS p95_seg,
    if(
        countIf(hora_primera_asignacion IS NOT NULL) >= {muestra_minima:UInt32},
        round(
            quantileIf(0.95)(
                dateDiff('second', fechahora_accidente, hora_primera_asignacion),
                hora_primera_asignacion IS NOT NULL
            ) / 60,
            2
        ),
        NULL
    )                                                           AS p95_min
FROM hecho_accidente FINAL
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
  AND fue_descartado = 0
  AND es_duplicado = 0
GROUP BY periodo
ORDER BY periodo

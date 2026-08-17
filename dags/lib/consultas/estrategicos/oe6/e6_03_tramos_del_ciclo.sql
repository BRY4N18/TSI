-- Informe E6-03 — Tramos del ciclo de emergencia
-- Consulta nueva. Los cuatro tramos son restas dentro de hecho_accidente.
--
-- ⚠️ CADA TRAMO PUBLICA SU PROPIA POBLACIÓN
-- Un caso que se confirmó y nunca se asignó entra en el primero y no en el
-- segundo. Un denominador común descartaría los ~404 que se atascaron al
-- principio, que es justo donde vive la información.
--
-- ⚠️ POR PERÍODO, NUNCA POR UNIDAD (FR-OE6-021)
-- Es lo que disuelve la decisión #35: la duración de un caso es propiedad del
-- caso. La unidad no controla cuándo se cierra el expediente, y repartir esa
-- duración entre unidades exige elegir una de forma no determinista.
--
-- Descartados y fusionados fuera de todo denominador, igual que en E6-01.

SELECT
    periodo,
    tramo,
    orden,
    casos,
    mediana_min,
    p95_min
FROM (
    SELECT
        formatDateTime(
            multiIf(
                {granularidad:String} = 'mes', toStartOfMonth(fecha),
                {granularidad:String} = 'trimestre', toStartOfQuarter(fecha),
                toStartOfYear(fecha)
            ),
            '%Y-%m'
        )                                                       AS periodo,
        'registro_a_confirmacion'                               AS tramo,
        1                                                       AS orden,
        count()                                                 AS casos,
        round(median(dateDiff('second', fechahora_accidente, hora_confirmacion) / 60), 1) AS mediana_min,
        round(quantile(0.95)(dateDiff('second', fechahora_accidente, hora_confirmacion) / 60), 1) AS p95_min
    FROM hecho_accidente FINAL
    WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
      AND fue_descartado = 0 AND es_duplicado = 0
      AND hora_confirmacion IS NOT NULL
    GROUP BY periodo

    UNION ALL

    SELECT
        formatDateTime(
            multiIf(
                {granularidad:String} = 'mes', toStartOfMonth(fecha),
                {granularidad:String} = 'trimestre', toStartOfQuarter(fecha),
                toStartOfYear(fecha)
            ),
            '%Y-%m'
        )                                                       AS periodo,
        'confirmacion_a_asignacion'                             AS tramo,
        2                                                       AS orden,
        count()                                                 AS casos,
        round(median(dateDiff('second', hora_confirmacion, hora_primera_asignacion) / 60), 1) AS mediana_min,
        round(quantile(0.95)(dateDiff('second', hora_confirmacion, hora_primera_asignacion) / 60), 1) AS p95_min
    FROM hecho_accidente FINAL
    WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
      AND fue_descartado = 0 AND es_duplicado = 0
      AND hora_confirmacion IS NOT NULL
      AND hora_primera_asignacion IS NOT NULL
    GROUP BY periodo

    UNION ALL

    SELECT
        formatDateTime(
            multiIf(
                {granularidad:String} = 'mes', toStartOfMonth(fecha),
                {granularidad:String} = 'trimestre', toStartOfQuarter(fecha),
                toStartOfYear(fecha)
            ),
            '%Y-%m'
        )                                                       AS periodo,
        'asignacion_a_llegada'                                  AS tramo,
        3                                                       AS orden,
        count()                                                 AS casos,
        round(median(dateDiff('second', hora_primera_asignacion, hora_primera_llegada) / 60), 1) AS mediana_min,
        round(quantile(0.95)(dateDiff('second', hora_primera_asignacion, hora_primera_llegada) / 60), 1) AS p95_min
    FROM hecho_accidente FINAL
    WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
      AND fue_descartado = 0 AND es_duplicado = 0
      AND hora_primera_asignacion IS NOT NULL
      AND hora_primera_llegada IS NOT NULL
    GROUP BY periodo

    UNION ALL

    SELECT
        formatDateTime(
            multiIf(
                {granularidad:String} = 'mes', toStartOfMonth(fecha),
                {granularidad:String} = 'trimestre', toStartOfQuarter(fecha),
                toStartOfYear(fecha)
            ),
            '%Y-%m'
        )                                                       AS periodo,
        'llegada_a_cierre'                                      AS tramo,
        4                                                       AS orden,
        count()                                                 AS casos,
        round(median(dateDiff('second', hora_primera_llegada, hora_cierre) / 60), 1) AS mediana_min,
        round(quantile(0.95)(dateDiff('second', hora_primera_llegada, hora_cierre) / 60), 1) AS p95_min
    FROM hecho_accidente FINAL
    WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
      AND fue_descartado = 0 AND es_duplicado = 0
      AND hora_primera_llegada IS NOT NULL
      AND hora_cierre IS NOT NULL
    GROUP BY periodo
)
ORDER BY periodo, orden

-- Informe E6-11 — Escaladas de severidad originadas en sitio
-- Parte de ot24_escaladas_severidad. Añade granularidad.
--
-- ⚠️ OPERA SOBRE DATO ESCASO
-- La fuente tiene muy pocas filas —razón por la que no se creó un hecho propio—.
-- Un porcentaje cercano a cero no significa que la severidad inicial acierte
-- casi siempre: significa que casi nadie usa la función. El servicio declara
-- cobertura parcial cuando `con_escalada` no alcanza `muestra_minima`.
--
-- Cero escaladas en un caso medido SÍ es una medición (bien clasificado). Los
-- casos con la métrica sin medir se cuentan aparte (`sin_medir`).

SELECT
    formatDateTime(
        multiIf(
            {granularidad:String} = 'mes', toStartOfMonth(fecha),
            {granularidad:String} = 'trimestre', toStartOfQuarter(fecha),
            toStartOfYear(fecha)
        ),
        '%Y-%m'
    )                                                           AS periodo,
    coalesce(severidad_inicial, 'Desconocido')                  AS severidad_inicial,
    coalesce(severidad, 'Desconocido')                          AS severidad_final,
    count()                                                     AS casos,
    countIf(num_escaladas_severidad > 0)                        AS con_escalada,
    countIf(num_escaladas_severidad IS NULL)                    AS sin_medir,
    sum(num_escaladas_severidad)                                AS escaladas_totales,
    if(
        countIf(num_escaladas_severidad IS NOT NULL) = 0,
        NULL,
        round(
            countIf(num_escaladas_severidad > 0)
            / countIf(num_escaladas_severidad IS NOT NULL),
            4
        )
    )                                                           AS pct_con_escalada
FROM hecho_accidente FINAL
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
  AND fue_descartado = 0
  AND es_duplicado = 0
GROUP BY periodo, severidad_inicial, severidad_final
ORDER BY periodo, con_escalada DESC, casos DESC, severidad_inicial, severidad_final

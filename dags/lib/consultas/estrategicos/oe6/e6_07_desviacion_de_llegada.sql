-- Informe E6-07 — Desviación de llegada frente a la referencia histórica
-- Parte de ot23_desviacion_llegada. Conserva intactas la ventana ANTERIOR al
-- período, la muestra mínima y el renombrado `ref_seg`.
--
-- ⚠️ `segundos_referencia` NO ES UN COMPROMISO OPERATIVO
-- El sistema no guarda ninguna estimación de llegada. Calcularla exigiría
-- coordenadas, excluidas por constitución. La referencia se deriva: mediana de
-- lo que tardaron despachos comparables (mismo condado y severidad) en los
-- `ventana_dias` anteriores al período medido.
--
-- ⚠️ La columna interna se llama `ref_seg` y no `segundos_referencia`
-- Si se llamara igual que el alias de salida, ClickHouse resolvería el nombre
-- dentro de `medianIf` al propio alias y fallaría con `ILLEGAL_AGGREGATION`.
--
-- Muestra insuficiente ⇒ referencia y desviación AUSENTES, nunca cero. Un `0`
-- diría «llegó exactamente a tiempo» y convertiría una unidad sin histórico
-- en una unidad ejemplar.

SELECT
    periodo                                     AS periodo,
    unidad                                      AS unidad,
    count()                                     AS llegadas_medidas,
    round(median(segundos_real))                AS segundos_reales_mediana,
    round(medianIf(ref_seg, ref_seg IS NOT NULL))
                                                AS segundos_referencia,
    round(medianIf(segundos_real - ref_seg, ref_seg IS NOT NULL))
                                                AS desviacion_mediana,
    countIf(ref_seg IS NOT NULL)                AS llegadas_con_referencia
FROM (
    SELECT
        formatDateTime(
            multiIf(
                {granularidad:String} = 'mes', toStartOfMonth(d.fecha),
                {granularidad:String} = 'trimestre', toStartOfQuarter(d.fecha),
                toStartOfYear(d.fecha)
            ),
            '%Y-%m'
        )                           AS periodo,
        d.unidad                    AS unidad,
        d.segundos_transito         AS segundos_real,
        if(
            r.llegadas_comparables >= {muestra_minima:UInt32},
            r.mediana_referencia,
            NULL
        )                           AS ref_seg
    FROM hecho_despacho AS d FINAL
    LEFT JOIN (
        SELECT
            condado                     AS condado,
            severidad                   AS severidad,
            count()                     AS llegadas_comparables,
            median(segundos_transito)   AS mediana_referencia
        FROM hecho_despacho FINAL
        WHERE fecha >= {desde:Date} - toIntervalDay({ventana_dias:UInt32})
          AND fecha <  {desde:Date}
          AND segundos_transito IS NOT NULL
        GROUP BY condado, severidad
    ) AS r ON r.condado = d.condado AND r.severidad = d.severidad
    WHERE d.fecha BETWEEN {desde:Date} AND {hasta:Date}
      AND d.segundos_transito IS NOT NULL
)
GROUP BY periodo, unidad
ORDER BY periodo, unidad

-- Informe E3-07 — Ratio demanda / capacidad por condado
-- Parte de ot22_ratio_demanda_capacidad: misma demanda y misma lectura
-- histórica de dim_unidad. Se añade granularidad, sin_capacidad y el
-- alcance de fiabilidad (Regla 6) lo emite el servicio, no el SQL.
--
-- ⚠️ LA CAPACIDAD ES LA DEL PERÍODO, NO LA FLOTA DE HOY
-- Filtrar es_vigente = 1 calcularía un ratio de hace tres meses contra
-- unidades que quizá no existían. Se cuentan versiones cuya vigencia
-- solapa el bucket. uniqExact(idunidademergencia), no versiones.
--
-- ⚠️ SIN UNIDADES: sin_capacidad = 1 y ratio NULL
-- Ni infinito, ni cero, ni un 500. Es una zona donde una emergencia no
-- tiene quién la atienda.
--
-- La demanda sigue saliendo de hecho_despacho (casos con intento), igual
-- que el táctico: la prueba de contraste exige la misma agrupación.

WITH
buckets AS (
    SELECT DISTINCT
        multiIf(
            {granularidad:String} = 'mes', toStartOfMonth(fecha),
            {granularidad:String} = 'trimestre', toStartOfQuarter(fecha),
            toStartOfYear(fecha)
        ) AS bucket
    FROM hecho_despacho FINAL
    WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
),
demanda AS (
    SELECT
        multiIf(
            {granularidad:String} = 'mes', toStartOfMonth(fecha),
            {granularidad:String} = 'trimestre', toStartOfQuarter(fecha),
            toStartOfYear(fecha)
        )                            AS bucket,
        coalesce(condado, 'Desconocido') AS condado,
        uniqExact(idaccidente)       AS casos
    FROM hecho_despacho FINAL
    WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
    GROUP BY bucket, condado
),
capacidad AS (
    SELECT
        b.bucket                         AS bucket,
        coalesce(u.condado, 'Desconocido') AS condado,
        uniqExact(u.idunidademergencia)  AS unidades_vigentes
    FROM buckets AS b
    CROSS JOIN (
        SELECT idunidademergencia, condado, valido_desde, valido_hasta
        FROM dim_unidad FINAL
        WHERE idunidademergencia != -1
    ) AS u
    WHERE u.valido_desde < addMonths(b.bucket, if({granularidad:String} = 'anio', 12, if({granularidad:String} = 'trimestre', 3, 1)))
      AND (u.valido_hasta IS NULL OR u.valido_hasta >= b.bucket)
    GROUP BY bucket, condado
)
SELECT
    formatDateTime(d.bucket, '%Y-%m')    AS periodo,
    d.condado                            AS condado,
    d.casos                              AS casos,
    coalesce(c.unidades_vigentes, 0)     AS unidades_vigentes,
    if(
        coalesce(c.unidades_vigentes, 0) = 0,
        NULL,
        round(d.casos / c.unidades_vigentes, 2)
    )                                    AS ratio,
    if(coalesce(c.unidades_vigentes, 0) = 0, 1, 0) AS sin_capacidad
FROM demanda AS d
LEFT JOIN capacidad AS c ON c.bucket = d.bucket AND c.condado = d.condado
ORDER BY periodo, condado

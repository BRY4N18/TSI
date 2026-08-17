-- Informe E3-10 — Tasa de error en el registro de accidentes
-- Complemento de ot21_completitud_campos_criticos: 1 − pct_completitud.
-- Meta: <1 % [NORMATIVO]. En la línea base es 0 % — y por eso la lista de
-- campos comprobados es obligatoria: un indicador que nunca se mueve, sin
-- esa lista, se lee como «el registro es perfecto».
--
-- ⚠️ SE MIDE CONTRA LA AUSENCIA REAL DEL MODELO
-- En Pinot no hay nulos (centinelas). Aquí IS NULL significa lo que dice,
-- porque la carga ya tradujo los centinelas. Misma predicado que OT21:
-- completo = severidad y condado presentes. El condado es la ubicación
-- resoluble; comprobar idcalle daría por bueno un caso con calle huérfana.
--
-- campos_comprobados viaja en cada fila. No es decorativo.

SELECT
    formatDateTime(
        multiIf(
            {granularidad:String} = 'mes', toStartOfMonth(fecha),
            {granularidad:String} = 'trimestre', toStartOfQuarter(fecha),
            toStartOfYear(fecha)
        ),
        '%Y-%m'
    )                                                           AS periodo,
    if({por_condado:UInt8} = 1, coalesce(condado, 'Desconocido'), '') AS condado,
    count()                                                     AS casos,
    countIf(idseveridad IS NULL OR condado IS NULL)             AS incompletos,
    if(
        count() = 0,
        NULL,
        round(countIf(idseveridad IS NULL OR condado IS NULL) / count() * 100, 4)
    )                                                           AS tasa_error,
    ['severidad', 'condado']                                    AS campos_comprobados
FROM hecho_accidente FINAL
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
GROUP BY periodo, condado
ORDER BY periodo, condado

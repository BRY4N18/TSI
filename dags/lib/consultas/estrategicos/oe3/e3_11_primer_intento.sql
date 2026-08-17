-- Informe E3-11 — Despachos resueltos al primer intento
-- Parte de ot22_primer_intento: grano de INTENTO, ordinal 1 confirmado.
-- Meta ≥90 % [CALIBRAR] → cumple siempre null.
--
-- ⚠️ CON GRANO DE CASO LOS INTENTOS FALLIDOS DESAPARECEN
-- Un caso despachado tres veces aparece como un confirmado. El indicador
-- subiría solo. El denominador son los casos cuyo primer intento cae en el
-- período, no todos los intentos.

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
    countIf(resultado = 'confirmado')                           AS resueltos_primer_intento,
    if(
        count() = 0,
        NULL,
        round(countIf(resultado = 'confirmado') / count(), 4)
    )                                                           AS pct_primer_intento
FROM hecho_despacho FINAL
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
  AND numero_intento = 1
GROUP BY periodo, condado
ORDER BY periodo, condado

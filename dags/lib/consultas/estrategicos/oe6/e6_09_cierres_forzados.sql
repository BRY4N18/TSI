-- Informe E6-09 — Cierres forzados
-- Parte de ot25_cierres_forzados. Mide el indicador del despacho.
--
-- ⚠️ MIDE `retiro_forzado`, QUE NO ES EL «CIERRE FORZADO» DEL CATÁLOGO
-- * `retiro_forzado` del despacho: 1 de 4 314.
-- * Retiro manual desde central (idusuario poblado): 451 de 3 310.
-- El modelo no puede calcular la segunda: la identidad de usuario está excluida
-- por constitución. El endpoint declara el alcance y cubre de forma parcial
-- (decisión #36). Sin esa declaración, un 1 de 3310 se lee como «esto casi no
-- pasa».

SELECT
    formatDateTime(
        multiIf(
            {granularidad:String} = 'mes', toStartOfMonth(fecha),
            {granularidad:String} = 'trimestre', toStartOfQuarter(fecha),
            toStartOfYear(fecha)
        ),
        '%Y-%m'
    )                                                           AS periodo,
    countIf(resultado = 'confirmado')                           AS despachos_confirmados,
    countIf(retiro_forzado = 1)                                 AS forzados,
    if(
        countIf(resultado = 'confirmado') = 0,
        NULL,
        round(countIf(retiro_forzado = 1) / countIf(resultado = 'confirmado'), 4)
    )                                                           AS pct_forzados
FROM hecho_despacho FINAL
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
GROUP BY periodo
ORDER BY periodo

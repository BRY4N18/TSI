-- Informe E3-13 — Pérdida de señal GPS por unidad
-- Parte de ot23_perdida_senal: mismos huecos, granularidad y grano de unidad.
--
-- ⚠️ ANALIZA TODAS LAS POSICIONES. El flujo legado veía 10 000 de 59 045
-- y publicaba 714 huecos donde hay ~3 942. Las cifras son mayores: eso es
-- el arreglo, no una regresión. No hay LIMIT.
--
-- hecho_ping_unidad es de transacción: PROHIBIDO FINAL (ILLEGAL_FINAL).
-- La primera posición de cada unidad no tiene anterior: nulo ≠ hueco de 0 s.

SELECT
    formatDateTime(
        multiIf(
            {granularidad:String} = 'mes', toStartOfMonth(fecha),
            {granularidad:String} = 'trimestre', toStartOfQuarter(fecha),
            toStartOfYear(fecha)
        ),
        '%Y-%m'
    )                                                       AS periodo,
    toString(idunidademergencia)                            AS unidad,
    proveedor                                               AS proveedor,
    countIf(segundos_desde_anterior IS NOT NULL)            AS intervalos_medidos,
    countIf(segundos_desde_anterior > {umbral_seg:UInt32})  AS huecos,
    max(segundos_desde_anterior)                            AS hueco_maximo_seg,
    if(
        countIf(segundos_desde_anterior IS NOT NULL) = 0,
        NULL,
        round(
            countIf(segundos_desde_anterior > {umbral_seg:UInt32})
            / countIf(segundos_desde_anterior IS NOT NULL),
            4
        )
    )                                                       AS pct_huecos
FROM hecho_ping_unidad
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
GROUP BY periodo, unidad, proveedor
ORDER BY huecos DESC, unidad

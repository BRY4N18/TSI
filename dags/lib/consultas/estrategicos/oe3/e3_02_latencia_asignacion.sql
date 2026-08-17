-- Informe E3-02 — Latencia operativa de asignación, registro → primera unidad
-- KPI del BSC de OE3. Meta: <2 min p95 (RNF-DES-001), NO los 100 ms del catálogo.
--
-- ⚠️ NO USA segundos_respuesta DEL DESPACHO
-- Esa columna mide oferta → confirmación de la unidad (p95 28 s): el tiempo
-- que tarda alguien en aceptar una misión. RNF-DES-001 acota el proceso
-- completo desde el registro. Son 106 s vs 28 s; publicarlos contra 100 ms
-- daría un rojo 1 060× falso.
--
-- ⚠️ LOS CASOS SIN ASIGNACIÓN SE DECLARAN Y NO ENTRAN EN LA MEDIANA
-- Contarlos como cero haría instantáneos precisamente los que nadie atendió:
-- la latencia mejoraría cuando empeora la atención.
--
-- Descartados y fusionados fuera: no hubo emergencia que asignar, o el suceso
-- vive en otra fila.
--
-- El p95 sale NULL bajo muestra_minima. sobre_umbral cuenta > 120 s.

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
    countIf(hora_primera_asignacion IS NOT NULL)                AS casos_asignados,
    countIf(hora_primera_asignacion IS NULL)                    AS excluidos_sin_asignacion,
    round(
        medianIf(
            dateDiff('second', fechahora_accidente, hora_primera_asignacion),
            hora_primera_asignacion IS NOT NULL
        ),
        1
    )                                                           AS mediana_seg,
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
    )                                                           AS p95_min,
    countIf(
        hora_primera_asignacion IS NOT NULL
        AND dateDiff('second', fechahora_accidente, hora_primera_asignacion) > 120
    )                                                           AS sobre_umbral
FROM hecho_accidente FINAL
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
  AND fue_descartado = 0
  AND es_duplicado = 0
GROUP BY periodo, condado
ORDER BY periodo, condado

-- Informe E6-01 — Tiempo global de respuesta, registro a llegada
-- KPI del BSC de OE6. Consulta nueva: la táctica solo tiene la variante por severidad.
--
-- ⚠️ SIN UNIR CON hecho_despacho
-- El hito ya está desnormalizado en el caso (`hora_primera_llegada`). Unir
-- reintroduciría el riesgo de contar intentos como casos (4 314 vs 3 651).
--
-- ⚠️ LOS TRES TÉRMINOS DEL FILTRO NO SON REDUNDANTES
-- * Sin llegada no hay tiempo de llegada. Contarlo como cero haría instantáneos
--   los casos que nadie atendió — el error que más daño hace en este informe.
-- * Un caso descartado fue una falsa alarma: nunca hubo emergencia que atender.
-- * Un caso fusionado es el mismo hecho que otro, que sigue vivo. Contar los dos
--   duplica el suceso.
--
-- El p95 sale NULL cuando la muestra no alcanza `muestra_minima`. Con cinco
-- observaciones el p95 es el máximo, no un percentil.
--
-- La granularidad se elige con multiIf sobre un parámetro ligado. Las tres
-- funciones están escritas aquí: el valor de la petición no se convierte en
-- identificador.

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
    countIf(hora_primera_llegada IS NOT NULL)                   AS casos_con_llegada,
    countIf(hora_primera_llegada IS NULL)                       AS excluidos_sin_llegada,
    round(
        medianIf(
            dateDiff('second', fechahora_accidente, hora_primera_llegada) / 60,
            hora_primera_llegada IS NOT NULL
        ),
        1
    )                                                           AS mediana_min,
    if(
        countIf(hora_primera_llegada IS NOT NULL) >= {muestra_minima:UInt32},
        round(
            quantileIf(0.95)(
                dateDiff('second', fechahora_accidente, hora_primera_llegada) / 60,
                hora_primera_llegada IS NOT NULL
            ),
            1
        ),
        NULL
    )                                                           AS p95_min
FROM hecho_accidente FINAL
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
  AND fue_descartado = 0
  AND es_duplicado = 0
GROUP BY periodo, condado
ORDER BY periodo, condado

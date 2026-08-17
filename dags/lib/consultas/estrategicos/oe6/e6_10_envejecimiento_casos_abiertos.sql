-- Informe E6-10 — Envejecimiento de casos abiertos
-- Parte de ot25_envejecimiento_cartera.
--
-- ⚠️ UN CASO ABIERTO NO TIENE FECHA DE CIERRE
-- Si la carga pusiera la fecha de carga, todos los abiertos aparecerían
-- cerrados y esta cartera saldría vacía para siempre, con la lectura
-- «no hay casos atrasados».
--
-- ⚠️ La antigüedad se mide contra el INSTANTE DE LA CONSULTA (`now()`), no
-- contra el fin del período: un caso abierto envejece mientras siga abierto
-- (FR-OE6 / T059). El rango `desde`/`hasta` selecciona qué casos entran.
--
-- `arrayLast` y no `roundDown`: roundDown exige un array constante y el de un
-- parámetro no lo es. Los cortes se ordenan antes: una lista desordenada
-- asignaría el tramo equivocado sin fallar.

SELECT
    toDate(now())                                               AS corte,
    arrayLast(
        x -> x <= dias,
        arraySort(arrayMap(x -> toInt32(x), splitByChar(',', {tramos_dias:String})))
    )                                                           AS tramo_dias,
    count()                                                     AS casos_abiertos,
    round(avg(dias), 1)                                         AS antiguedad_media_dias,
    max(dias)                                                   AS antiguedad_maxima_dias,
    countIf(severidad IN ('Grave', 'Fatal'))                    AS graves_o_fatales
FROM (
    SELECT
        dateDiff('day', fechahora_accidente, now())             AS dias,
        severidad                                               AS severidad
    FROM hecho_accidente FINAL
    WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
      AND hora_cierre IS NULL
      AND fue_descartado = 0
      AND es_duplicado = 0
)
GROUP BY tramo_dias
ORDER BY tramo_dias

-- Informe #23 — Envejecimiento de la cartera de casos abiertos · OT25
--
-- Cuántos casos siguen sin cerrar y desde hace cuánto.
--
-- ⚠️ UN CASO ABIERTO NO TIENE FECHA DE CIERRE, Y ESO ES LO QUE HACE POSIBLE ESTE INFORME
-- --------------------------------------------------------------------------------------
-- La carga deja `hora_cierre` **ausente** mientras el caso no se cierre. Si le
-- pusiera la fecha de carga —que es la tentación cuando una columna no admite
-- nulos— todos los casos abiertos aparecerían cerrados y esta cartera saldría
-- **vacía para siempre**.
--
-- Y saldría vacía de la peor manera: sin error, sin aviso, y con una lectura
-- perfectamente creíble —«no hay casos atrasados»— que es justo la contraria de
-- la verdad. El informe que avisa de los casos olvidados sería el primero en
-- olvidarlos.
--
-- La antigüedad se mide hasta el final del período consultado
-- ------------------------------------------------------------
-- Hasta `{hasta:Date}` y no hasta hoy: así el mismo informe del mismo período
-- devuelve lo mismo mañana. Medir contra hoy haría que la cartera de marzo
-- envejeciera cada vez que alguien la consulta, y dos capturas del mismo informe
-- dejarían de ser comparables.
--
-- ⚠️ Sobre `arrayLast` y no `roundDown`
-- -------------------------------------
-- `roundDown` es la función natural para esto y **no sirve aquí**: exige que el
-- array de cortes sea constante, y el de un parámetro no lo es —falla con
-- `ILLEGAL_COLUMN`, un error que habla de columnas y no de constantes—.
--
-- `arrayLast(x -> x <= dias, cortes)` hace lo mismo sobre un array calculado, y
-- devuelve `0` cuando ningún corte encaja. Ese cero es deliberado: significa
-- «más nuevo que el primer corte», no «cero días de antigüedad».
--
-- Los cortes se ordenan antes de usarlos. `arrayLast` recorre en orden, así que
-- una lista desordenada —`30,1,7`— asignaría los casos al tramo equivocado sin
-- fallar: cada caso caería en el último corte que cumpliera, que con esa lista
-- no es el mayor.

SELECT
    toDate({hasta:Date})                            AS corte,
    arrayLast(
        x -> x <= dias,
        arraySort(arrayMap(x -> toInt32(x), splitByChar(',', {tramos_dias:String})))
    )                                               AS tramo_dias,
    count()                                         AS casos_abiertos,
    round(avg(dias), 1)                             AS antiguedad_media_dias,
    max(dias)                                       AS antiguedad_maxima_dias,
    countIf(severidad IN ('Grave', 'Fatal'))        AS graves_o_fatales
FROM (
    SELECT
        dateDiff('day', fechahora_accidente, toDateTime({hasta:Date})) AS dias,
        severidad                                                      AS severidad
    FROM hecho_accidente FINAL
    WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
      -- Abierto = sin hora de cierre. Un caso descartado o fusionado **no está
      -- abierto** aunque no tenga cierre: se decidió sobre él, y arrastrarlo a la
      -- cartera de pendientes inflaría el atraso con trabajo ya resuelto.
      AND hora_cierre IS NULL
      AND fue_descartado = 0
      AND es_duplicado = 0
)
GROUP BY tramo_dias
ORDER BY tramo_dias

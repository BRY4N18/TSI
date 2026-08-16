-- Informe #11 — Tiempo de respuesta por severidad · OT22
-- Solo para contraste: el endpoint que lo sirve hoy es correcto y no se migra.
--
-- Si los casos graves se atienden antes que los leves, que es lo que el despacho
-- por severidad debería producir.
--
-- ⚠️ El intervalo es DESPACHO → LLEGADA, y se calcula con UNA sola resta
-- ---------------------------------------------------------------------
-- La tentación es sumar las dos columnas ya calculadas,
-- `segundos_respuesta + segundos_transito`. Da un número casi idéntico y está
-- **sistemáticamente mal**: las dos vienen truncadas a segundos, cada una pierde
-- medio segundo de media, y la suma llega con un sesgo de **+1 s** en todos los
-- estratos. Se midió: 467,95 s frente a 468,95 s reales, y la desviación es
-- constante, así que no se delata como ruido — parece precisión.
--
-- Un segundo sobre 468 no cambia ninguna decisión. Pero el sesgo es constante y
-- del mismo signo, así que sobrevive a cualquier promedio y a cualquier
-- comparación entre períodos: es exactamente el tipo de error que nunca se
-- descubre porque nunca parece un error.
--
-- `segundos_transito` mide **confirmación → llegada**, no despacho → llegada. La
-- diferencia entre las dos es el tiempo que la unidad tarda en aceptar, y no es
-- despreciable: unos 18 s de media.
--
-- Se publica el promedio además de la mediana porque es la magnitud que publica
-- el endpoint actual, y sin una cifra común los dos caminos no se pueden
-- contrastar. La mediana y el p90 son la mejora: el promedio de un tiempo con
-- cola larga describe un caso que no le ocurre a nadie.
--
-- Un caso sin severidad aparece bajo 'Desconocido' y no se descarta: filtrarlo
-- dejaría fuera precisamente los casos peor registrados, que son los que más
-- probablemente se atendieron mal.

SELECT
    toDate({desde:Date})                                        AS periodo,
    coalesce(severidad, 'Desconocido')                          AS severidad,
    count()                                                     AS despachos,
    countIf(hora_llegada IS NOT NULL)                           AS con_llegada,
    round(avgIf(dateDiff('second', fechahora_despacho, hora_llegada),
                hora_llegada IS NOT NULL), 2)                   AS promedio_seg,
    round(medianIf(dateDiff('second', fechahora_despacho, hora_llegada),
                   hora_llegada IS NOT NULL))                   AS mediana_seg,
    round(quantileIf(0.9)(dateDiff('second', fechahora_despacho, hora_llegada),
                          hora_llegada IS NOT NULL))            AS p90_seg
FROM hecho_despacho FINAL
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
GROUP BY severidad
ORDER BY despachos DESC, severidad

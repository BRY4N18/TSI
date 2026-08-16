-- Informe #25 — Tiempo de asignado a cierre · OT25
-- Solo para contraste: el endpoint que lo sirve hoy es correcto y no se migra.
--
-- Cuánto dura un caso desde que se le asigna una unidad hasta que se cierra.
--
-- ⚠️ Los casos SIN CERRAR quedan fuera del cálculo, y se cuentan
-- --------------------------------------------------------------
-- Un caso abierto no ha durado nada todavía: está durando. Meterlo con la
-- duración que lleva acumulada mezclaría una medición terminada con una en
-- curso, y el promedio bajaría cada vez que entrara un caso nuevo — el informe
-- mejoraría al aumentar el trabajo pendiente.
--
-- Se publica `sin_cerrar` al lado por la misma razón que en el resto del
-- catálogo: una duración media calculada sobre pocos casos cerrados no dice nada
-- de los abiertos, y sin el recuento nadie podría notarlo.
--
-- La resta se hace **una sola vez** entre las dos columnas del hito, no sumando
-- intervalos ya truncados a segundos: sumar dos columnas redondeadas introduce
-- un sesgo constante del mismo signo, que sobrevive a cualquier promedio y no se
-- delata como ruido. Es el error que apareció en OT22.

SELECT
    toDate({desde:Date})                                            AS periodo,
    count()                                                         AS casos,
    countIf(hora_cierre IS NOT NULL AND hora_primera_asignacion IS NOT NULL) AS cerrados,
    countIf(hora_cierre IS NULL)                                    AS sin_cerrar,
    round(avgIf(dateDiff('minute', hora_primera_asignacion, hora_cierre),
                hora_cierre IS NOT NULL AND hora_primera_asignacion IS NOT NULL), 2)
                                                                    AS promedio_min,
    round(medianIf(dateDiff('minute', hora_primera_asignacion, hora_cierre),
                   hora_cierre IS NOT NULL AND hora_primera_asignacion IS NOT NULL))
                                                                    AS mediana_min,
    round(quantileIf(0.9)(dateDiff('minute', hora_primera_asignacion, hora_cierre),
                          hora_cierre IS NOT NULL AND hora_primera_asignacion IS NOT NULL))
                                                                    AS p90_min
FROM hecho_accidente FINAL
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
ORDER BY periodo

-- Informe — Rotación de flota · OT12
--
-- Cuántas unidades salieron de la flota en el período, y tras cuánto tiempo.
--
-- ⚠️ UNA UNIDAD DADA DE BAJA A MITAD DE PERÍODO CUENTA HASTA SU BAJA
-- ------------------------------------------------------------------
-- Ni el período entero —diría que estuvo disponible todo el mes cuando se fue el
-- día 10— ni cero —la borraría del período en el que sí trabajó—. Las dos
-- lecturas son plausibles y las dos falsean la capacidad del mes.
--
-- El hecho es de transacción y su partición es la de la **fecha de la baja**, así
-- que filtrar por el rango ya cuenta cada baja en el período en que ocurrió. No
-- hay nada que prorratear: la baja es un instante, no un intervalo.
--
-- ⚠️ `dias_en_flota` es **ausente** cuando no se sabe cuándo entró la unidad. Hoy
-- el origen solo trae fecha de alta en 3 de 18. Un cero afirmaría que se dio de
-- baja el mismo día que entró —una anomalía operativa digna de mirarse—, y
-- fabricarla llenaría el informe de unidades fantasma con vida de un día.
--
-- Por eso se publica `con_antiguedad_conocida` al lado de la mediana: una
-- mediana calculada sobre tres unidades de dieciocho no dice nada de las quince
-- restantes, y sin el recuento nadie podría notarlo.

SELECT
    toDate({desde:Date})                                    AS periodo,
    proveedor                                               AS proveedor,
    count()                                                 AS bajas,
    countIf(tipo_baja = 'Normal')                           AS bajas_normales,
    countIf(tipo_baja != 'Normal')                          AS bajas_forzadas,
    countIf(dias_en_flota IS NOT NULL)                      AS con_antiguedad_conocida,
    round(median(dias_en_flota))                            AS mediana_dias_en_flota,
    max(dias_en_flota)                                      AS maximo_dias_en_flota
FROM hecho_baja_unidad
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
GROUP BY proveedor
ORDER BY bajas DESC, proveedor

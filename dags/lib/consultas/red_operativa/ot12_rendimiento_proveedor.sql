-- Informe — Rendimiento por proveedor · OT12
--
-- Cómo responde cada proveedor a los despachos que se le ofrecen.
--
-- ⚠️ AGRUPA POR EL PROVEEDOR DE AQUEL MOMENTO, NO POR EL ACTUAL
-- -------------------------------------------------------------
-- `hecho_despacho` guarda el proveedor **vigente al despachar**. Resolverlo
-- contra la dimensión al consultar reescribiría el pasado: un proveedor que
-- hereda las unidades de otro heredaría también sus rechazos, y uno que se marcha
-- se llevaría los suyos.
--
-- Sobre este informe se decide con qué proveedor se sigue trabajando, así que la
-- atribución no es un detalle de implementación.
--
-- Rechazado y vencido van **por separado**
-- ----------------------------------------
-- Por la misma razón que en Emergencias: un rechazo tiene una persona y un
-- motivo detrás, y la conversación es sobre criterios de aceptación; un
-- vencimiento significa que nadie contestó, y la conversación es sobre turnos y
-- sobre el aparato. Sumados, un proveedor que responde siempre y rechaza mucho
-- parece uno ausente, que es lo contrario.
--
-- La mediana de llegada se calcula con **una sola resta** entre despacho y
-- llegada. Sumar `segundos_respuesta + segundos_transito` —las dos columnas ya
-- calculadas— introduce un sesgo constante de +1 s, porque ambas vienen
-- truncadas a segundos y cada una pierde medio segundo de media. Es constante y
-- del mismo signo, así que sobrevive a cualquier promedio y no se delata como
-- ruido: parece precisión.

SELECT
    toDate({desde:Date})                                        AS periodo,
    proveedor                                                   AS proveedor,
    uniqExact(idunidademergencia)                               AS unidades,
    count()                                                     AS intentos,
    countIf(resultado = 'confirmado')                           AS confirmados,
    countIf(resultado = 'rechazado')                            AS rechazados,
    countIf(resultado = 'vencido')                              AS vencidos,
    countIf(hora_llegada IS NOT NULL)                           AS llegadas,
    round(medianIf(dateDiff('second', fechahora_despacho, hora_llegada),
                   hora_llegada IS NOT NULL))                   AS mediana_llegada_seg,
    if(
        count() = 0,
        NULL,
        round(countIf(resultado = 'confirmado') / count(), 4)
    )                                                           AS pct_aceptacion
FROM hecho_despacho FINAL
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
GROUP BY proveedor
ORDER BY intentos DESC, proveedor

-- Informe E6-05 — Rechazo y vencimiento por unidad
-- Adopta ot22_rechazo_timeout_por_unidad, que ya calcula bien: el denominador
-- son INTENTOS OFRECIDOS (filas de hecho_despacho), no transiciones de estado.
--
-- ⚠️ Eso es lo que corrige la decisión #34. El endpoint táctico publicado divide
-- entre filas de historial —cinco por cada despacho bien atendido—, con una
-- consecuencia perversa: cuanto mejor trabaja una unidad, más baja parece su
-- tasa de rechazo. Factor medido: 2,6.
--
-- Rechazo y vencimiento van SEPARADOS. Sumarlos en «no atendidos» daría 661 y
-- ocultaría que la mitad de las veces nadie contestó, que es otro problema y se
-- arregla de otra manera.

SELECT
    formatDateTime(
        multiIf(
            {granularidad:String} = 'mes', toStartOfMonth(fecha),
            {granularidad:String} = 'trimestre', toStartOfQuarter(fecha),
            toStartOfYear(fecha)
        ),
        '%Y-%m'
    )                                                           AS periodo,
    unidad                                                      AS unidad,
    count()                                                     AS ofrecidos,
    countIf(resultado = 'rechazado')                            AS rechazados,
    countIf(resultado = 'vencido')                              AS vencidos,
    if(count() = 0, NULL, round(countIf(resultado = 'rechazado') / count(), 4)) AS tasa_rechazo,
    if(count() = 0, NULL, round(countIf(resultado = 'vencido')   / count(), 4)) AS tasa_vencimiento
FROM hecho_despacho FINAL
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
GROUP BY periodo, unidad
ORDER BY periodo, tasa_rechazo DESC, tasa_vencimiento DESC, unidad
LIMIT {top:UInt32} BY periodo

-- Informe #15 — Rechazo y vencimiento por unidad · OT22
-- Solo para contraste: el endpoint que lo sirve hoy no se migra.
--
-- ⚠️ RECHAZADO Y VENCIDO SE PUBLICAN POR SEPARADO. EL INFORME ANTERIOR LOS SUMABA
-- ------------------------------------------------------------------------------
-- Suenan igual —«la unidad no atendió»— y son dos problemas distintos con dos
-- soluciones distintas:
--
-- * **rechazado**: alguien vio el despacho y dijo que no. Hay una persona y un
--   motivo, y la conversación es sobre criterios de aceptación.
-- * **vencido**: nadie contestó. No hay decisión que discutir; lo que falla es
--   que el aviso no llegó, no se vio, o no había nadie. La conversación es sobre
--   turnos y sobre el aparato.
--
-- Sumados en un solo «no atendidos», las dos desaparecen detrás de un porcentaje
-- que no dice qué arreglar. Y la suma es engañosa en la otra dirección también:
-- una unidad con muchos rechazos y ningún vencimiento está respondiendo siempre,
-- que es lo contrario de una unidad ausente.

SELECT
    toDate({desde:Date})                            AS periodo,
    unidad                                          AS unidad,
    proveedor                                       AS proveedor,
    count()                                         AS intentos,
    countIf(resultado = 'rechazado')                AS rechazados,
    countIf(resultado = 'vencido')                  AS vencidos,
    if(count() = 0, NULL, round(countIf(resultado = 'rechazado') / count(), 4)) AS pct_rechazo,
    if(count() = 0, NULL, round(countIf(resultado = 'vencido')   / count(), 4)) AS pct_vencimiento
FROM hecho_despacho FINAL
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
GROUP BY unidad, proveedor
ORDER BY rechazados DESC, vencidos DESC, unidad

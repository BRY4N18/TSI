-- Informe #10 — Tiempo de reportado a asignado · OT22
-- Solo para contraste: el endpoint que lo sirve hoy no se migra.
--
-- Cuánto tarda un caso desde que ocurre hasta que se le asigna una unidad.
--
-- ⚠️ ESTE INFORME **NO ES CONTRASTABLE** CON EL ENDPOINT ACTUAL, Y NO ES UN FALLO
-- ------------------------------------------------------------------------------
-- Los dos miden el mismo *par* de casos —3638 por ambos caminos, comprobado— y
-- **arrancan el cronómetro en instantes distintos**:
--
-- * El endpoint actual arranca en el momento en que se registró el estado
--   `REPORTADO` en el historial de estados del caso.
-- * Aquí se arranca en `fechahora_accidente`, el momento del accidente.
--
-- No son lo mismo: entre que ocurre un accidente y que alguien lo registra como
-- reportado pasa un tiempo, y ese tiempo está dentro de esta cifra y fuera de la
-- otra. Da 79,02 s aquí y 72,66 s allí, y **las dos son correctas** para lo que
-- cada una mide.
--
-- El modelo **no puede reproducir hoy la del endpoint**: `hecho_accidente` no
-- guarda el instante del estado `REPORTADO`, y añadirlo es un cambio de esquema
-- que no pertenece a esta historia. Por eso este informe queda **excluido del
-- contraste numérico**, con la exclusión declarada en la prueba en vez de
-- disimulada con una tolerancia amplia — una tolerancia del 10 % taparía esta
-- diferencia y también taparía un error de verdad.
--
-- El intervalo que se publica aquí es, además, el más útil de los dos para
-- juzgar la respuesta: al ciudadano que espera le da igual cuándo se registró su
-- aviso en el sistema.

SELECT
    toDate({desde:Date})                                            AS periodo,
    count()                                                         AS casos,
    countIf(hora_primera_asignacion IS NOT NULL)                    AS asignados,
    round(avgIf(dateDiff('second', fechahora_accidente, hora_primera_asignacion),
                hora_primera_asignacion IS NOT NULL), 2)            AS promedio_seg,
    round(medianIf(dateDiff('second', fechahora_accidente, hora_primera_asignacion),
                   hora_primera_asignacion IS NOT NULL))            AS mediana_seg,
    round(quantileIf(0.9)(dateDiff('second', fechahora_accidente, hora_primera_asignacion),
                          hora_primera_asignacion IS NOT NULL))     AS p90_seg
FROM hecho_accidente FINAL
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
ORDER BY periodo

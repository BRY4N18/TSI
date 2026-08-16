-- Informe #20 — Volumen de evidencia por unidad · OT24
--
-- ⚠️ POR UNIDAD, SIN DESGLOSE POR PERSONA (FR-034)
-- ------------------------------------------------
-- El catálogo lo pedía por técnico de campo. **No se entrega así**, y no por una
-- limitación técnica: el origen trae `idusuario` y bastaría con copiarlo.
--
-- Un ranking de qué persona sube menos fotos es una herramienta de vigilancia
-- laboral, y la pregunta que de verdad interesa —qué unidades documentan mal— se
-- responde igual sin nombrar a nadie. Seudonimizar tampoco valdría: quien tenga
-- acceso al sistema operativo puede reidentificar, así que solo aparentaría
-- resolverlo.
--
-- Este informe entrega menos de lo que el catálogo pedía, y es deliberado.
--
-- La atribución es la del momento de la captura
-- ---------------------------------------------
-- La unidad y su proveedor vienen resueltos a la versión vigente **al capturar**,
-- no a la de hoy. Un cambio de proveedor no reescribe quién documentó qué.
--
-- La unidad desconocida no es un error
-- ------------------------------------
-- Son las evidencias de casos que no tuvieron ninguna llegada registrada, así
-- que no hay unidad a la que atribuirlas. Se publican en vez de descartarse:
-- descartarlas bajaría el volumen total sin que nada indicara que faltan filas,
-- y este informe existe justamente para medir volumen.

SELECT
    toDate({desde:Date})                            AS periodo,
    idunidademergencia                              AS idunidad,
    proveedor                                       AS proveedor,
    count()                                         AS evidencias,
    countIf(tipo = 'foto')                          AS fotos,
    countIf(tipo = 'nota')                          AS notas,
    uniqExact(idaccidente)                          AS casos_documentados,
    -- Evidencias por caso, no por unidad: una unidad que atendió veinte casos y
    -- documentó uno con veinte fotos no documenta bien.
    round(count() / uniqExact(idaccidente), 2)      AS evidencias_por_caso
FROM hecho_evidencia
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
GROUP BY idunidademergencia, proveedor
ORDER BY evidencias DESC, idunidad

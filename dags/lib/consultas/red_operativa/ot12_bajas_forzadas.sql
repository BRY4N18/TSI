-- Informe — Bajas forzadas · OT12
--
-- ⚠️ TRES DESENLACES, NO DOS
-- --------------------------
-- * **Normal** — la unidad salió de la flota de forma ordenada.
-- * **Forzada** — hubo que retirarla, y **dejó un caso sin unidad**.
-- * **Forzada con reasignación** — hubo que retirarla y el caso pasó a otra.
--
-- La tercera es la que se pierde al agrupar en «forzadas», y es la diferencia
-- entre un fallo con red y uno sin ella: en la segunda alguien se quedó
-- esperando. Contarlas juntas haría que un proveedor con buena reasignación
-- pareciera igual de malo que uno que abandona casos — y sobre este informe se
-- decide con quién se sigue trabajando.
--
-- `con_caso_en_curso` viene **derivado** de que la baja trajera un accidente
-- asociado; el origen no lo dice de otra forma. Se publica **al lado** del tipo y
-- no dentro de él porque son cosas distintas: puede haber una baja normal con un
-- caso en curso.
--
-- `motivo` es una **categoría** del catálogo operativo, no una nota redactada por
-- quien da la baja. Es lo que hace útil el informe: sin él solo se sabría cuántas
-- hubo, no por qué. Un motivo ausente sale como «Sin motivo registrado» y no se
-- filtra: una baja sin justificar es precisamente la que hay que ver.

SELECT
    toDate({desde:Date})                                    AS periodo,
    proveedor                                               AS proveedor,
    coalesce(motivo, 'Sin motivo registrado')               AS motivo,
    count()                                                 AS bajas,
    countIf(tipo_baja = 'Normal')                           AS normales,
    countIf(tipo_baja = 'Forzada')                          AS forzadas,
    countIf(tipo_baja = 'Forzada_con_reasignación')         AS forzadas_con_reasignacion,
    countIf(con_caso_en_curso = 1)                          AS con_caso_en_curso,
    if(
        count() = 0,
        NULL,
        round(countIf(tipo_baja != 'Normal') / count(), 4)
    )                                                       AS pct_forzadas
FROM hecho_baja_unidad
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
GROUP BY proveedor, motivo
ORDER BY bajas DESC, proveedor, motivo

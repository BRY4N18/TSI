-- Informe #16 — Abortos y pérdidas de despacho · OT23
-- Solo para contraste: el endpoint que lo sirve hoy no se migra.
--
-- ⚠️ LOS CINCO DESENLACES SON CINCO, Y `abortado` ES UNO DE ELLOS
-- --------------------------------------------------------------
-- `resultado` toma exactamente cinco valores, y cada uno cuenta una historia
-- distinta de por qué el despacho no acabó en una atención:
--
-- * **confirmado** — la unidad aceptó. Es el único desenlace bueno.
-- * **rechazado**  — la unidad dijo que no.
-- * **vencido**    — nadie contestó a tiempo.
-- * **abortado**   — se aceptó y luego se canceló. Ya había un compromiso, y se
--                    rompió: es lo que distingue «no pudimos ir» de «no
--                    quisimos ir» y de «no nos enteramos».
-- * **en_curso**   — todavía no ha terminado. **No es un fracaso**: es un
--                    despacho sin desenlace, y contarlo como perdido convierte
--                    cada consulta hecha a media tarde en un informe pesimista
--                    que mejora solo al día siguiente.
--
-- Se enumeran los cinco como columnas y no se agrupan: agrupar por `resultado`
-- haría que un desenlace **sin ningún caso en el período desapareciera de la
-- respuesta**, y un cero que falta se lee como un dato que no existe en vez de
-- como lo que es — que no pasó ninguna vez.

SELECT
    toDate({desde:Date})                    AS periodo,
    count()                                 AS despachos,
    countIf(resultado = 'confirmado')       AS confirmados,
    countIf(resultado = 'rechazado')        AS rechazados,
    countIf(resultado = 'vencido')          AS vencidos,
    countIf(resultado = 'abortado')         AS abortados,
    countIf(resultado = 'en_curso')         AS en_curso,
    if(count() = 0, NULL, round(countIf(resultado = 'abortado') / count(), 4)) AS pct_aborto
FROM hecho_despacho FINAL
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
ORDER BY periodo

-- Informe #18 — Latencia de sincronización offline · OT24
--
-- Cuánto tarda una evidencia capturada en campo en llegar al sistema.
--
-- ⚠️ LO NO SINCRONIZADO CUENTA APARTE, Y SU LATENCIA ES AUSENTE
-- -------------------------------------------------------------
-- Una evidencia que todavía no ha llegado no tiene latencia cero —diría que
-- llegó al instante, la mejor marca posible— ni infinita —diría que no llegará
-- nunca—. No se sabe cuánto tardará, y eso es lo que se publica: cuenta en
-- `pendientes` y no entra en la mediana.
--
-- Es la distinción que más cambia la lectura. Si los pendientes entraran como
-- cero, **cuanto peor funcionara la sincronización mejor saldría la latencia**:
-- cada evidencia atascada bajaría la mediana. Publicar `pendientes` al lado es
-- lo que permite ver las dos cosas a la vez.
--
-- ⚠️ Todas las notas son pendientes, y no es culpa de esta consulta
-- -----------------------------------------------------------------
-- `Dim_NotaAccidente` **no tiene columna de sincronización** en el origen, así
-- que la latencia de una nota es genuinamente desconocida. Por eso se desglosa
-- por tipo: sin el desglose, las 51 notas pendientes esconderían por completo la
-- cifra de las fotos, y el informe parecería decir que la sincronización va
-- fatal cuando lo que pasa es que de las notas no se sabe.
--
-- `hecho_evidencia` es un hecho de **transacción**: `FINAL` está prohibido aquí
-- y fallaría con `ILLEGAL_FINAL`.

SELECT
    toDate({desde:Date})                                AS periodo,
    tipo                                                AS tipo,
    count()                                             AS evidencias,
    countIf(fechahora_sincronia IS NOT NULL)            AS sincronizadas,
    countIf(fechahora_sincronia IS NULL)                AS pendientes,
    -- Las agregadas ignoran los nulos por sí solas, así que los pendientes ya
    -- quedan fuera de la mediana sin filtrarlos: el nulo no se convierte en cero
    -- en ningún punto del camino.
    round(median(segundos_hasta_sincronia))             AS mediana_seg,
    round(quantile(0.9)(segundos_hasta_sincronia))      AS p90_seg,
    max(segundos_hasta_sincronia)                       AS maximo_seg
FROM hecho_evidencia
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
GROUP BY tipo
ORDER BY evidencias DESC, tipo

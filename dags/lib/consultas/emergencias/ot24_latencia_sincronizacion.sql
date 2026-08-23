-- Informe #18 — Latencia de sincronización offline · OT24
--
-- Cuánto tarda una evidencia capturada en campo en llegar al sistema.
--
-- ⚠️ LO QUE NO SE PUEDE MEDIR CUENTA APARTE, Y SU LATENCIA ES AUSENTE
-- --------------------------------------------------------------------
-- Una evidencia sin instante de sincronía no tiene latencia cero —diría que
-- llegó al instante, la mejor marca posible— ni infinita —diría que no llegó
-- nunca—. No se sabe cuánto tardó, y eso es lo que se publica: cuenta en
-- `sin_instante_sincronia` y no entra en la mediana.
--
-- Es la distinción que más cambia la lectura. Si esas entraran como cero,
-- **cuanto peor funcionara la sincronización mejor saldría la latencia**: cada
-- evidencia sin medir bajaría la mediana. Publicar el conteo al lado es lo que
-- permite ver las dos cosas a la vez.
--
-- ⚠️ Ninguna nota tiene instante, y no es culpa de esta consulta
-- --------------------------------------------------------------
-- `Dim_NotaAccidente` **no tiene columna de sincronización** en el origen, así
-- que la latencia de una nota es genuinamente desconocida. Por eso se desglosa
-- por tipo: sin el desglose, las notas esconderían por completo la cifra de las
-- fotos, y el informe parecería decir que la sincronización va fatal cuando lo
-- que pasa es que de las notas no se sabe.
--
-- ⚠️ **«Sin instante» NO significa «sin sincronizar».** Las evidencias del
-- origen vienen con `sincronizado = true`; lo que falta es la **fecha**. Nadie
-- escribe `Dim_EvidenciaFoto.fecha_sincronizacion` —no hay una sola ruta de
-- escritura que la rellene— y las notas ni siquiera tienen la columna.
--
-- `hecho_evidencia` es un hecho de **transacción**: `FINAL` está prohibido aquí
-- y fallaría con `ILLEGAL_FINAL`.

SELECT
    toDate({desde:Date})                                AS periodo,
    tipo                                                AS tipo,
    count()                                             AS evidencias,
    -- ⚠️ **`con_instante_sincronia`, no «sincronizadas».**
    --
    -- Esto se llamaba `sincronizadas` y `pendientes`, y con los datos reales la
    -- pantalla decía «0 sincronizadas · 50 pendientes» — **lo contrario de la
    -- verdad operativa**: las 50 evidencias están marcadas `sincronizado = true`
    -- en el origen. Un director habría leído un atasco de sincronización que no
    -- existe.
    --
    -- Lo que estas dos columnas cuentan es si hay **instante** con el que medir
    -- la latencia, no si la evidencia llegó. `Dim_NotaAccidente` no tiene esa
    -- columna y a las fotos nadie se la escribe, así que «sin instante» es lo
    -- normal y no una anomalía. El nombre nuevo lo dice; el viejo afirmaba algo
    -- que el dato no sostiene.
    countIf(fechahora_sincronia IS NOT NULL)            AS con_instante_sincronia,
    countIf(fechahora_sincronia IS NULL)                AS sin_instante_sincronia,
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

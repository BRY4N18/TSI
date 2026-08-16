-- Informe #13 — Desviación de llegada frente a la referencia histórica · OT23
--
-- Cuánto se aparta el tiempo de llegada de cada unidad de lo que suele tardarse
-- en despachos comparables.
--
-- ⚠️ `segundos_referencia` NO ES UN COMPROMISO OPERATIVO
-- -----------------------------------------------------
-- El sistema **no guarda ninguna estimación de llegada**. No existe un tiempo
-- prometido con el que comparar, así que la referencia se **deriva**: es la
-- mediana de lo que tardaron despachos comparables en el pasado.
--
-- Eso la convierte en una descripción de lo normal, no en un objetivo. Una
-- desviación positiva significa «más lento de lo habitual», nunca «incumplió un
-- plazo» — no había plazo. Presentarla como un SLA inventaría un compromiso que
-- nadie asumió, y sobre esa lectura se toman decisiones sobre proveedores.
-- Por eso el endpoint la etiqueta explícitamente (FR-032).
--
-- Por qué mediana y no promedio
-- -----------------------------
-- Un solo despacho atrapado en un corte de tráfico de dos horas desplaza el
-- promedio de toda la ventana y deja la referencia en un valor que ninguna
-- llegada real se parece. La mediana no se mueve por los extremos, que es lo que
-- se necesita de una referencia de «lo normal».
--
-- Por qué la ventana es **anterior**
-- ----------------------------------
-- Si la referencia incluyera los despachos que se están midiendo, cada unidad se
-- compararía en parte consigo misma: una unidad lenta arrastraría su propia
-- referencia hacia arriba y saldría normal. La ventana termina donde empieza el
-- período medido.
--
-- Comparables = mismo condado y misma severidad. Un accidente grave en una
-- avenida y uno leve en una calle secundaria no son el mismo trabajo.
--
-- Muestra insuficiente ⇒ referencia AUSENTE, nunca cero
-- ----------------------------------------------------
-- Con menos de `muestra_minima` llegadas comparables, la mediana existe
-- aritméticamente y no significa nada: la mediana de dos llegadas es un dato
-- anecdótico presentado como norma. En ese caso la referencia y la desviación
-- salen **nulas**. Un `0` diría «llegó exactamente a tiempo», que es lo
-- contrario de «no sabemos qué esperar» — y es la lectura que convertiría una
-- unidad sin histórico en una unidad ejemplar.
--
-- Los despachos **sin llegada** quedan fuera del cálculo: `segundos_transito` es
-- nulo cuando la unidad no llegó (rechazo, vencimiento, aborto). Contarlos como
-- cero haría parecer instantáneas las unidades que nunca aparecen.

-- ⚠️ La columna interna se llama `ref_seg` y no `segundos_referencia`
-- --------------------------------------------------------------------
-- No es cuestión de gusto. Si la columna de entrada se llamara igual que el
-- alias de salida, ClickHouse resolvería el nombre **dentro** de
-- `medianIf(segundos_referencia, …)` al propio alias —que ya es una
-- agregación— y fallaría con `ILLEGAL_AGGREGATION`. El mensaje habla de
-- agregaciones anidadas y no menciona el alias, así que la causa no se deduce
-- de él: se llega por descarte.
--
-- Para que conste, porque el error apunta a otra parte: no lo arregla usar
-- subconsultas en vez de `WITH`, ni un nivel extra de `SELECT`, ni el analizador
-- nuevo. Se probaron los tres antes de dar con el alias, y el nivel extra llegó
-- a quedarse en el fichero pareciendo la solución. Renombrar la columna es todo
-- lo que hace falta.

SELECT
    periodo                                     AS periodo,
    unidad                                      AS unidad,
    count()                                     AS llegadas_medidas,
    round(median(segundos_real))                AS segundos_reales_mediana,
    -- ⚠️ `medianIf` sobre las llegadas **con** referencia, y sin más guardián:
    -- cuando ninguna fila cumple la condición devuelve `NULL` por sí mismo —se
    -- comprobó—, que es exactamente lo que hay que decir de una unidad cuyos
    -- despachos son todos de estratos sin muestra suficiente.
    round(medianIf(ref_seg, ref_seg IS NOT NULL))
                                                AS segundos_referencia,
    round(medianIf(segundos_real - ref_seg, ref_seg IS NOT NULL))
                                                AS desviacion_mediana,
    -- Cuántas de las llegadas medidas tenían referencia comparable. Publicarlo
    -- es lo que permite distinguir «esta unidad va bien» de «de esta unidad
    -- apenas sabemos nada».
    countIf(ref_seg IS NOT NULL)                AS llegadas_con_referencia
FROM (
    -- Un despacho por fila, con **su** referencia ya resuelta. La referencia se
    -- aplica por despacho y no por unidad porque cada despacho pertenece a un
    -- estrato distinto: una unidad que atiende sobre todo casos graves en el
    -- centro no se compara con la misma cifra que otra que atiende leves en la
    -- periferia. Resolverla por unidad borraría esa diferencia justo en el
    -- informe que existe para verla.
    SELECT
        formatDateTime(toStartOfMonth(d.fecha), '%Y-%m') AS periodo,
        d.unidad                    AS unidad,
        d.segundos_transito         AS segundos_real,
        if(
            r.llegadas_comparables >= {muestra_minima:UInt32},
            r.mediana_referencia,
            NULL
        )                           AS ref_seg
    FROM hecho_despacho AS d FINAL
    LEFT JOIN (
        SELECT
            condado                     AS condado,
            severidad                   AS severidad,
            count()                     AS llegadas_comparables,
            median(segundos_transito)   AS mediana_referencia
        FROM hecho_despacho FINAL
        WHERE fecha >= {desde:Date} - toIntervalDay({ventana_dias:UInt32})
          AND fecha <  {desde:Date}              -- ventana ANTERIOR al período medido
          AND segundos_transito IS NOT NULL       -- sin llegada no hay tiempo de llegada
        GROUP BY condado, severidad
    ) AS r ON r.condado = d.condado AND r.severidad = d.severidad
    WHERE d.fecha BETWEEN {desde:Date} AND {hasta:Date}
      AND d.segundos_transito IS NOT NULL
)
GROUP BY periodo, unidad
ORDER BY periodo, unidad

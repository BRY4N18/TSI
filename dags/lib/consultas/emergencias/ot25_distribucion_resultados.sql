-- Informe #22 — Distribución de resultados y calificación media · OT25
--
-- Cómo terminaron los casos cerrados y qué nota les puso quien los cerró.
--
-- ⚠️ UNA CALIFICACIÓN AUSENTE NO ES UN CERO
-- -----------------------------------------
-- En una escala, cero es el **peor valor posible**. Presentar «no se calificó»
-- como «se calificó con la nota mínima» invierte el significado justo donde más
-- engaña: un promedio que incluyera esos ceros hundiría la media, y la
-- conclusión —«la atención es mala»— sería exactamente la contraria de lo que
-- dicen los datos.
--
-- Los casos sin calificar quedan **fuera del promedio** y se cuentan aparte en
-- `sin_calificar`. Las dos cifras juntas son lo que permite leer la media: un
-- 4,8 sobre tres casos calificados de ochocientos no dice nada de los
-- ochocientos, y sin el recuento nadie podría saberlo.
--
-- La traducción ya viene hecha de la carga: `calificacion` llega **nula** cuando
-- vale cero o cuando trae el centinela negativo de Pinot. Aquí no hay que
-- volver a filtrarla, y las agregadas ignoran los nulos por sí solas.
--
-- ⚠️ «Sin cerrar» y «cerrado sin resultado» son dos cosas distintas
-- ------------------------------------------------------------------
-- La versión obvia de esta consulta agrupa por `coalesce(resultado_atencion,
-- 'Sin cerrar')`, y **miente**: hoy hay 3636 casos con hora de cierre y solo uno
-- con resultado registrado, así que 3635 casos cerrados aparecerían como «sin
-- cerrar». El informe diría que casi nada se ha terminado cuando lo que pasa es
-- que casi nada se ha documentado al terminar.
--
-- Son dos problemas con dos responsables distintos —uno es atraso operativo y el
-- otro es un hueco de registro— y confundirlos manda a mirar el sitio
-- equivocado. Por eso el grupo se decide con `hora_cierre`, que es lo que dice
-- si el caso terminó, y no con la presencia del resultado.
--
-- El resto se agrupa por `resultado_atencion` sin normalizarlo: es el texto que
-- el sistema operativo guarda como resultado, un conjunto acotado de opciones,
-- no texto libre del usuario.

SELECT
    toDate({desde:Date})                                    AS periodo,
    multiIf(
        resultado_atencion IS NOT NULL, resultado_atencion,
        hora_cierre IS NOT NULL, 'Cerrado sin resultado registrado',
        'Sin cerrar'
    )                                                       AS resultado,
    count()                                                 AS casos,
    countIf(calificacion IS NOT NULL)                       AS calificados,
    countIf(calificacion IS NULL)                           AS sin_calificar,
    round(avg(calificacion), 2)                             AS calificacion_media,
    min(calificacion)                                       AS calificacion_minima,
    max(calificacion)                                       AS calificacion_maxima
FROM hecho_accidente FINAL
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
GROUP BY resultado
ORDER BY casos DESC, resultado

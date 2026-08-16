-- Informe #12 — Pérdida de señal GPS · OT23 · origen: CU-T13
--
-- Cuántos huecos hubo en el reporte de posición de las unidades, por proveedor.
--
-- ⚠️ CORRIGE UN TRUNCAMIENTO SILENCIOSO. LAS CIFRAS SERÁN MAYORES: ESO ES EL ARREGLO
-- ---------------------------------------------------------------------------------
-- El flujo anterior analizaba **10 000 de 59 045 posiciones** —el 16,9 %— y
-- publicaba el resultado como si fuera del total. No había ningún error: la
-- consulta no llevaba `LIMIT` explícito y recibía el tope por defecto del
-- cliente. Detectaba 714 huecos donde hay 3 942.
--
-- El truncamiento es invisible por construcción. La respuesta llega completa,
-- con su forma correcta y cifras verosímiles; lo único que falta es el 83 % de
-- los datos, y eso no aparece en ninguna parte de la respuesta.
--
-- Quien compare este informe con el anterior verá **más huecos** y pensará que
-- algo empeoró. No empeoró: se está mirando entero por primera vez.
--
-- Aquí no hay `LIMIT`. La agregación ocurre en el servidor y devuelve una fila
-- por proveedor, así que no hay nada que truncar — que es la forma de que el
-- fallo no pueda repetirse, en vez de recordar poner el tope.
--
-- Qué cuenta como hueco
-- ---------------------
-- `segundos_desde_anterior` ya viene medido de la carga: es la distancia hasta
-- el reporte previo **de la misma unidad**. Un hueco es un intervalo mayor que
-- `umbral_seg`.
--
-- La **primera posición de cada unidad no tiene anterior**, así que su medida es
-- nula. Un nulo no es un hueco de cero segundos: es un intervalo que no existe.
-- Se excluye del numerador y del denominador — contarla como buena inflaría la
-- proporción de reportes correctos con datos que no miden nada.

SELECT
    toDate({desde:Date})                                    AS periodo,
    proveedor                                               AS proveedor,
    -- El denominador se publica: es lo que permite ver que se miró todo.
    countIf(segundos_desde_anterior IS NOT NULL)            AS intervalos_medidos,
    countIf(segundos_desde_anterior > {umbral_seg:UInt32})  AS huecos,
    max(segundos_desde_anterior)                            AS hueco_maximo_seg,
    if(
        countIf(segundos_desde_anterior IS NOT NULL) = 0,
        NULL,
        round(
            countIf(segundos_desde_anterior > {umbral_seg:UInt32})
            / countIf(segundos_desde_anterior IS NOT NULL),
            4
        )
    )                                                       AS pct_huecos
FROM hecho_ping_unidad
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
GROUP BY proveedor
ORDER BY huecos DESC, proveedor

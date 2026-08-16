-- Rendimiento de despacho por proveedor, **desde el modelo** (T046).
--
-- Sustituye a la tabla `rendimiento_por_proveedor` y a su flujo propio. Es el
-- informe cuyo defecto justificó construir el modelo entero.
--
-- ⚠️ USA LA ATRIBUCIÓN HISTÓRICA, y por eso sus cifras diferirán
-- --------------------------------------------------------------
-- El flujo anterior lo dice en su propio código: «usa el `idcliente` (proveedor)
-- **actual** de `Dim_UnidadEmergencia` […] se aproxima con el proveedor vigente
-- al momento de la corrida del DAG, no con un snapshot histórico real».
--
-- Es decir: cambiar hoy de proveedor **reescribía seis meses de historia**, y la
-- cifra parecía correcta.
--
-- Aquí `proveedor` es el de la versión de unidad **vigente al despachar**. Con
-- los datos actuales las dos consultas coinciden —el origen tiene un solo
-- proveedor y ninguna unidad ha cambiado— pero divergirán en cuanto haya un
-- cambio, **y esa divergencia será el arreglo**.
--
-- Diferencia de cómputo, además de la de atribución
-- --------------------------------------------------
-- El flujo viejo contaba rechazos recorriendo el **historial de transiciones**:
-- un despacho con dos entradas «Rechazado» sumaba dos. Aquí cada intento aporta
-- **un** resultado, el terminal, así que el denominador y el numerador hablan de
-- lo mismo.
--
-- Y separa `vencido` (timeout) de `rechazado`, que el viejo sumaba juntos en
-- `pct_rechazo`. Se conserva `pct_rechazo_o_vencido` para poder comparar.

SELECT
    fecha                                                     AS periodo,
    proveedor,
    round(countIf(resultado = 'rechazado') / count(), 4)      AS pct_rechazo,
    round(countIf(resultado = 'vencido') / count(), 4)        AS pct_vencido,
    round(
        countIf(resultado IN ('rechazado', 'vencido')) / count(), 4
    )                                                         AS pct_rechazo_o_vencido,
    round(countIf(resultado = 'abortado') / count(), 4)       AS pct_abortos,
    -- Desde el despacho hasta la llegada, que es lo que medía el informe
    -- anterior. `segundos_transito` mide otra cosa —desde la confirmación— y
    -- ambas son útiles, pero confundirlas haría creer que las unidades llegan
    -- 220 segundos antes de lo que llegan.
    round(avg(dateDiff('second', fechahora_despacho, hora_llegada)), 2)
                                                              AS tiempo_llegada_promedio_seg,
    round(avg(segundos_transito), 2)                          AS tiempo_transito_promedio_seg,
    count()                                                   AS total_despachos
FROM hecho_despacho FINAL
GROUP BY fecha, proveedor
ORDER BY periodo, proveedor

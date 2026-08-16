-- Informe #24 — Retiros forzados frente a finalizaciones normales · OT25
--
-- Cuántas veces hubo que retirar a la fuerza una unidad de un caso, por
-- proveedor.
--
-- Un retiro forzado es que la unidad estaba asignada y hubo que sacarla: no
-- terminó el trabajo. Es distinto de un rechazo —ahí nunca fue— y de un
-- vencimiento —ahí nunca contestó—.
--
--
-- ⚠️ MIDE `retiro_forzado` DEL DESPACHO, QUE **NO** ES EL «CIERRE FORZADO» DEL INFORME
-- -----------------------------------------------------------------------------------
-- Son dos cosas distintas con nombres casi iguales, y la diferencia es de un
-- factor de 451 (decision pendiente #36):
--
-- * `Fact_Despacho.retiro_forzado` es un indicador del despacho. Hoy vale 1 en
--   **una** fila de 4314.
-- * El «cierre forzado» del informe operativo es una transicion a `Retirado`
--   **con `idusuario` poblado** —retiro manual desde central, frente al
--   automatico por vencimiento—. Hoy son **451** de 3310.
--
-- El modelo no puede reproducir hoy la segunda definicion: lo que distingue un
-- retiro manual de uno automatico es la presencia de `idusuario`, y la identidad
-- de persona esta excluida del modelo. La salida es un booleano derivado al
-- cargar —«el retiro fue manual»— que conserve el hecho sin la identidad, y eso
-- es un cambio de esquema pendiente de decidir.
--
-- Hasta entonces esta consulta mide el indicador del despacho, lo dice aqui, y
-- la prueba de contraste **no la compara** con el endpoint.
--
-- ⚠️ AGRUPA POR EL PROVEEDOR DE AQUEL MOMENTO, NO POR EL ACTUAL
-- -------------------------------------------------------------
-- `hecho_despacho` guarda el proveedor **vigente al despachar**. Resolverlo
-- contra la dimensión al consultar reescribiría el pasado: un proveedor que
-- hereda las unidades de otro heredaría también sus retiros forzados, y uno que
-- se marcha se llevaría los suyos.
--
-- Sobre este informe se decide qué proveedor sigue, así que la atribución no es
-- un detalle de implementación.
--
-- El denominador son los despachos **confirmados**
-- ------------------------------------------------
-- Un retiro forzado solo puede ocurrir en un despacho que la unidad aceptó.
-- Dividir entre todos los intentos —incluidos los rechazados y los vencidos—
-- diluiría la tasa con situaciones en las que un retiro era imposible, y
-- favorecería al proveedor que más rechaza.

SELECT
    toDate({desde:Date})                                            AS periodo,
    proveedor                                                       AS proveedor,
    countIf(resultado = 'confirmado')                               AS confirmados,
    countIf(retiro_forzado = 1)                                     AS retiros_forzados,
    countIf(resultado = 'confirmado' AND retiro_forzado = 0)        AS finalizaciones_normales,
    if(
        countIf(resultado = 'confirmado') = 0,
        NULL,
        round(countIf(retiro_forzado = 1) / countIf(resultado = 'confirmado'), 4)
    )                                                               AS pct_retiro_forzado
FROM hecho_despacho FINAL
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
GROUP BY proveedor
ORDER BY retiros_forzados DESC, proveedor

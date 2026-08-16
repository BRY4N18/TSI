-- Informe #26 — Cierres forzados · OT25
-- Solo para contraste: el endpoint que lo sirve hoy es correcto y no se migra.
--
-- Cuántos casos se cerraron sin que la atención terminara normalmente.
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
-- Un cierre forzado deja rastro en el despacho (`retiro_forzado`) y en el
-- resultado de la atención del caso. Se cuentan las dos cosas por separado
-- porque miden momentos distintos: el retiro es de la unidad, el resultado es
-- del caso, y un caso puede tener un retiro forzado y aun así cerrarse bien
-- porque se reasignó a otra unidad que sí terminó.
--
-- Contarlos como uno solo daría la impresión de que cada retiro forzado es un
-- caso mal cerrado, que es precisamente lo que la reasignación existe para
-- evitar.

SELECT
    toDate({desde:Date})                                            AS periodo,
    count()                                                         AS casos,
    countIf(hora_cierre IS NOT NULL)                                AS cerrados,
    countIf(a.idaccidente IN (
        SELECT idaccidente FROM hecho_despacho FINAL
        WHERE fecha BETWEEN {desde:Date} AND {hasta:Date} AND retiro_forzado = 1
    ))                                                              AS con_retiro_forzado,
    if(
        countIf(hora_cierre IS NOT NULL) = 0,
        NULL,
        round(
            countIf(a.idaccidente IN (
                SELECT idaccidente FROM hecho_despacho FINAL
                WHERE fecha BETWEEN {desde:Date} AND {hasta:Date} AND retiro_forzado = 1
            )) / countIf(hora_cierre IS NOT NULL),
            4
        )
    )                                                               AS pct_con_retiro_forzado
FROM hecho_accidente AS a FINAL
WHERE a.fecha BETWEEN {desde:Date} AND {hasta:Date}
ORDER BY periodo

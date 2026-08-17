-- Informe — Unidades por estado · OT12
--
-- Cuántas unidades hay en cada estado, según las transiciones registradas.
--
-- ⚠️ AGRUPA POR EL TEXTO DEL ESTADO, Y NO UNE CON EL CATÁLOGO
-- -----------------------------------------------------------
-- Unir con `Dim_EstadoUnidadEmergencia` es lo correcto en un modelo bien formado
-- y aquí **pierde datos en silencio**. El catálogo del origen tiene tres filas
-- —`Activa`, `Ocupada`, `Fuera de servicio`— y el histórico usa **cuatro**:
-- aparece también `En Misión`.
--
-- Medido sobre los datos de hoy: de **45 transiciones, 6 son `En Misión`**. Un
-- `INNER JOIN` con el catálogo devolvería 39, no fallaría, no avisaría, y las
-- cifras seguirían siendo verosímiles — solo que habría desaparecido el **13 %**
-- de la operación, y justamente el 13 % que representa a las unidades
-- trabajando. El informe diría que hay menos actividad de la que hay.
--
-- El hecho guarda el nombre del estado ya resuelto en la carga. El precio es una
-- columna de texto repetida; lo que se compra es que un estado nuevo en el
-- origen **aparezca** en el informe en vez de desaparecer de él.
--
-- `hecho_estado_unidad` es un hecho de **transacción**: `FINAL` está prohibido y
-- fallaría con `ILLEGAL_FINAL`.
--
-- El estado nulo sale como 'Desconocido' y no se filtra: una transición sin
-- estado registrado es un defecto de datos que hay que ver, no esconder.

SELECT
    toDate({desde:Date})                            AS periodo,
    coalesce(estado_nuevo, 'Desconocido')           AS estado,
    count()                                         AS transiciones,
    uniqExact(idunidademergencia)                   AS unidades,
    round(count() / sum(count()) OVER (), 4)        AS pct_transiciones
FROM hecho_estado_unidad
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
GROUP BY estado
ORDER BY transiciones DESC, estado

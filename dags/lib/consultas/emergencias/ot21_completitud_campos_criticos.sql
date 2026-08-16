-- Informe #3 — Completitud de campos críticos · OT21 · origen: BSC
--
-- Mide qué proporción de los casos del período llegó con sus campos críticos
-- registrados: severidad y ubicación.
--
-- ⚠️ ES EL INFORME QUE CORRIGE EL DEFECTO MÁS GRAVE DEL CATÁLOGO
-- ----------------------------------------------------------------
-- El endpoint que sirve hoy este informe agrega **directamente contra Pinot** y
-- comprueba la completitud con una condición de nulidad. En Pinot **no hay
-- nulos**: una severidad ausente llega como el centinela `-2147483648` y una
-- calle ausente como `'null'`. La condición es, por tanto, **siempre cierta**, y
-- el informe responde `100 %` completo pase lo que pase.
--
-- No falla, no avisa, y su respuesta es plausible. Solo se detecta comparándola
-- con algo — que es exactamente lo que hace este fichero.
--
-- En el modelo la ausencia **es** ausencia: la carga tradujo los centinelas a
-- `NULL` al construir `hecho_accidente`, así que aquí `IS NULL` significa lo que
-- dice. Por eso el arreglo no es una condición más lista: es haber cambiado el
-- sustrato.
--
-- Qué cuenta como completo
-- ------------------------
-- Un caso está completo si tiene **severidad** y **ubicación resoluble**. La
-- ubicación se comprueba sobre `condado` y no sobre `idcalle`: un caso puede
-- traer una calle que no está en el catálogo geográfico, y entonces el modelo lo
-- conserva con la ubicación sin resolver. Ese caso **no** está completo, y
-- comprobar `idcalle` lo daría por bueno.
--
-- `FINAL` es obligatorio: `hecho_accidente` es de instantánea acumulada, y sin
-- él las recargas duplican filas de forma intermitente.

SELECT
    toDate({desde:Date})                                       AS periodo,
    count()                                                    AS casos,
    countIf(idseveridad IS NOT NULL AND condado IS NOT NULL)    AS completos,
    -- ⚠️ Denominador cero es **sin dato**, no cero: un período sin casos no
    -- tiene una completitud del 0 %, no tiene completitud.
    if(
        count() = 0,
        NULL,
        round(countIf(idseveridad IS NOT NULL AND condado IS NOT NULL) / count(), 4)
    )                                                          AS pct_completitud
FROM hecho_accidente FINAL
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
ORDER BY periodo

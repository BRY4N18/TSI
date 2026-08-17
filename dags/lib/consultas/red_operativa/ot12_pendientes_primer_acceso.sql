-- Informe — Unidades pendientes de primer acceso · OT12
--
-- Unidades dadas de alta que **nunca llegaron a operar**.
--
-- ⚠️ El primer acceso es una derivación, no una medición
-- ------------------------------------------------------
-- El origen **no guarda ninguna fecha de primer acceso**: `Dim_Usuarios` no
-- tiene esa columna. `tuvo_primer_acceso` se deriva al cargar del estado de la
-- credencial — `Activo` significa que entró; `Cambio contraseña` es el estado
-- con el que nace una credencial recién creada.
--
-- Tiene un límite conocido: una unidad que entró y luego pidió cambio de
-- contraseña vuelve a aparecer aquí. Hoy son 2 de 31 credenciales. Se declara en
-- vez de disimularse porque este informe sirve para perseguir altas que nunca
-- arrancaron, y un falso positivo cuesta una llamada, no una decisión
-- equivocada.
--
-- ⚠️ `dias_desde_alta` es **ausente** cuando no se sabe cuándo entró la unidad.
-- Hoy son 15 de 18: el origen solo trae fecha de alta en tres. Rellenarlo con la
-- época cero daría cincuenta y seis años de antigüedad y pondría a esas unidades
-- a la cabeza de la lista de olvidadas, que es exactamente el orden que alguien
-- usaría para decidir a quién llamar primero.
--
-- Se lee la **versión vigente**: la pregunta es qué unidades están pendientes
-- ahora, no cuáles lo estuvieron.

SELECT
    idunidademergencia                              AS idunidad,
    placa                                           AS unidad,
    proveedor                                       AS proveedor,
    condado                                         AS condado,
    fecha_alta                                      AS fecha_alta,
    if(
        fecha_alta IS NULL,
        NULL,
        dateDiff('day', fecha_alta, toDateTime({hasta:Date}))
    )                                               AS dias_desde_alta
FROM dim_unidad FINAL
WHERE es_vigente = 1
  AND tuvo_primer_acceso = 0
  AND idunidademergencia != -1
  -- El rango acota por fecha de alta cuando se conoce. Las unidades **sin
  -- fecha no se filtran**: son las que más tiempo pueden llevar olvidadas, y
  -- excluirlas por no saber cuándo entraron sería perder justo el caso peor.
  AND (fecha_alta IS NULL OR toDate(fecha_alta) <= {hasta:Date})
ORDER BY dias_desde_alta DESC NULLS LAST, unidad

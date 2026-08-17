-- Informe — Disponibilidad declarada por unidad · OT12
--
-- Qué proporción del período estuvo cada unidad en un estado disponible.
--
-- ⚠️ SE MIDE TIEMPO EN ESTADO, NO NÚMERO DE TRANSICIONES
-- ------------------------------------------------------
-- Es la segunda trampa del departamento, y la peor: contar transiciones asigna
-- **0 % de disponibilidad a la unidad que nunca falló**. Una unidad que estuvo
-- activa todo el mes no tiene ninguna transición a `Fuera de servicio` — ni
-- ninguna transición en absoluto— así que un cálculo basado en contar cambios le
-- da el peor resultado posible al mejor comportamiento.
--
-- Y no falla: devuelve un número, plausible, con el signo invertido. El informe
-- que sirve para premiar a los proveedores fiables los señalaría como los peores.
--
-- Aquí cada transición abre un tramo que dura **hasta la siguiente**, y el
-- último tramo dura **hasta el fin del período**. Sin transiciones en el período
-- no hay tramos, y la disponibilidad sale **ausente**, no `0`: no se sabe en qué
-- estado estuvo, y un `0` afirmaría que estuvo caída.
--
-- ⚠️ La ausencia y el cero son cosas opuestas aquí
-- ------------------------------------------------
-- * **Ausente** — no hay transiciones que digan en qué estado estuvo.
-- * **`0`** — hubo transiciones y ninguna la dejó disponible.
--
-- La primera no es una alarma; la segunda es la más grave que puede dar este
-- informe. Rellenar la ausencia con cero convierte silencio en catástrofe, y es
-- exactamente lo que haría un `coalesce` puesto para «limpiar» la salida.
--
-- Qué cuenta como disponible: `Activa` y `En Misión`. Una unidad en misión está
-- trabajando, que es lo contrario de no estar disponible — y es el estado que el
-- catálogo del origen no tiene, así que se nombra por su texto.
--
-- `hecho_estado_unidad` es de **transacción**: `FINAL` prohibido.

SELECT
    unidad                                          AS unidad,
    proveedor                                       AS proveedor,
    count()                                         AS transiciones,
    sum(segundos_del_tramo)                         AS segundos_medidos,
    sumIf(segundos_del_tramo, disponible)           AS segundos_disponible,
    -- Denominador cero es **sin dato**, no cero por ciento: sin tramos medidos
    -- no se sabe en qué estado estuvo la unidad.
    if(
        sum(segundos_del_tramo) = 0,
        NULL,
        round(sumIf(segundos_del_tramo, disponible) / sum(segundos_del_tramo), 4)
    )                                               AS pct_disponible
FROM (
    SELECT
        unidad                                      AS unidad,
        proveedor                                   AS proveedor,
        estado_nuevo IN ('Activa', 'En Misión')     AS disponible,
        -- El tramo dura hasta la transición siguiente **de la misma unidad**, y
        -- el último hasta el fin del período. Sin el segundo, la unidad que no
        -- volvió a cambiar de estado aportaría cero segundos y desaparecería del
        -- cálculo justo por haber sido estable.
        dateDiff(
            'second',
            fechahora,
            coalesce(
                anyOrNull(fechahora) OVER (
                    PARTITION BY idunidademergencia ORDER BY fechahora
                    ROWS BETWEEN 1 FOLLOWING AND 1 FOLLOWING
                ),
                toDateTime({hasta:Date}) + toIntervalDay(1)
            )
        )                                           AS segundos_del_tramo
    FROM hecho_estado_unidad
    WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
      AND estado_nuevo IS NOT NULL
)
GROUP BY unidad, proveedor
ORDER BY pct_disponible DESC NULLS LAST, unidad

-- Informe — Motivos de rechazo de región · OT11 · indicador BSC
--
-- Por qué se rechazan las validaciones de región.
--
-- ⚠️ SOLO SOBRE VALIDACIONES RECHAZADAS (FR-018)
-- ----------------------------------------------
-- Una **aprobación no tiene motivo**, y eso es correcto: no hubo nada que
-- justificar. Si se agrupara sobre todas las validaciones, ese nulo se
-- convertiría en una categoría —«sin motivo»— y con los datos de hoy sería
-- **la causa de rechazo más frecuente del informe**, empatada con las reales.
--
-- El fallo no se nota: la categoría aparece con un nombre plausible y un conteo
-- creíble, y quien la lea concluirá que hace falta mejorar el registro de
-- motivos. La conclusión sería falsa; lo que pasa es que las aprobaciones se
-- colaron en un informe de rechazos.
--
-- Un rechazo **sí** sin motivo registrado es otra cosa, y esa sí es una
-- categoría legítima: alguien rechazó sin decir por qué. Se etiqueta aparte para
-- que se vea, porque es un hueco de registro que hay que cerrar.
--
-- `motivo` es una **categoría** del catálogo operativo, no texto redactado por
-- el validador. Es lo que hace agrupable el informe; si algún día admitiera
-- texto libre, sale del modelo.

SELECT
    toDate({desde:Date})                                    AS periodo,
    multiIf(
        motivo IS NOT NULL AND motivo != '', motivo,
        'Rechazada sin motivo registrado'
    )                                                       AS motivo,
    count()                                                 AS rechazos,
    uniqExact(idregionoperativa)                            AS regiones,
    round(count() / sum(count()) OVER (), 4)                AS pct
FROM hecho_validacion_region
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
  -- La condición que define el informe. Quitarla convierte las aprobaciones sin
  -- motivo en la causa de rechazo más común.
  AND resultado = 'Rechazada'
GROUP BY motivo
ORDER BY rechazos DESC, motivo
LIMIT {top:UInt32}

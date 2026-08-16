-- Pérdida de señal GPS, calculada **desde el modelo** (T044).
--
-- Sustituye a la tabla `perdida_senal_gps` y a su flujo propio.
--
-- Qué cambia respecto del diseño anterior
-- ---------------------------------------
-- El flujo viejo recorría 59 045 posiciones en cada corrida para encontrar los
-- huecos y materializaba el resultado en su propia tabla. Aquí el hueco ya está
-- medido en la carga (`segundos_desde_anterior`), así que detectarlo es **un
-- filtro por columna**: no hay función de ventana, no hay tabla nueva, y el
-- umbral deja de estar horneado en el ETL — se decide al preguntar.
--
-- El umbral se sustituye al ejecutar. El flujo anterior usaba 60 segundos.
--
-- ⚠️ Sin coordenadas, por diseño: la continuidad de la señal se mide con los
-- instantes. El origen las tiene y el modelo no las trajo.

SELECT
    toDate(fechahora - segundos_desde_anterior)            AS periodo,
    idunidademergencia,
    idaccidente,
    fechahora - segundos_desde_anterior                    AS inicio_hueco,
    fechahora                                              AS fin_hueco,
    segundos_desde_anterior                                AS duracion_seg,
    {umbral:UInt32}                                        AS umbral_usado_seg
FROM hecho_ping_unidad
WHERE segundos_desde_anterior > {umbral:UInt32}
ORDER BY periodo, idunidademergencia, inicio_hueco

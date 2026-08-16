-- Informe #6 — Impacto humano por ubicación · OT21 · origen: ±
--
-- Heridos, víctimas y fallecidos por condado en el período.
--
-- ⛔ Recuentos, nunca identidad
-- -----------------------------
-- Este informe cuenta personas afectadas; **no las nombra**. La identidad de
-- conductores, implicados y víctimas es una exclusión constitucional que ningún
-- cargo levanta, y el modelo no la trajo: `hecho_accidente` guarda los números,
-- no las personas.
--
-- Un caso sin recuento registrado aporta 0 a la suma pero **sí cuenta como
-- caso**: no saber cuántos heridos hubo no es lo mismo que saber que no hubo
-- ninguno, y por eso `casos` va al lado de las sumas — para que quien lea sepa
-- sobre cuántos casos se está sumando.

SELECT
    toDate({desde:Date})                AS periodo,
    coalesce(condado, 'Desconocido')    AS condado,
    sum(coalesce(num_heridos, 0))       AS heridos,
    sum(coalesce(num_victimas, 0))      AS victimas,
    sum(coalesce(num_fallecidos, 0))    AS fallecidos,
    count()                             AS casos
FROM hecho_accidente FINAL
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
GROUP BY condado
ORDER BY fallecidos DESC, victimas DESC, heridos DESC, condado

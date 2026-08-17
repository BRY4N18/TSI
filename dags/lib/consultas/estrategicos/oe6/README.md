# Catálogo de consultas estratégicas — OE6

Un fichero por informe. Django las **lee**; Airflow es el único escritor del
almacén.

## Convención de nombres

`e6_NN_<informe>.sql` — el número es el del catálogo (E6-01 … E6-12), el resto
es el nombre del informe en snake_case. El contrato HTTP usa kebab-case; el
enlace vive en `CATALOGO` del servicio, no en el nombre del fichero.

## Encabezado

Cada consulta declara en las primeras líneas **qué mide y por qué** cada
decisión no obvia. Es lo que evitó que se perdiera el motivo del renombrado
`ref_seg` en la capa táctica.

## Granularidad

`mes` · `trimestre` · `anio` se traducen **dentro** de la consulta con
`multiIf` sobre `{granularidad:String}`. El valor llega ligado por el servidor,
nunca interpolado. Las tres funciones (`toStartOfMonth`, `toStartOfQuarter`,
`toStartOfYear`) están escritas en el SQL: un valor libre no puede convertirse
en identificador.

## Prohibiciones de este catálogo

- Unir `hecho_accidente` con `dim_region` por estado. Duplica cada caso sin
  fallar (research D1). Se agrupa por condado.
- `SELECT *`.
- `FINAL` sobre `hecho_evidencia` (es de transacción: `ILLEGAL_FINAL`).
- Coordenadas, identidad de persona, texto libre.

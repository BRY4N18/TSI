# Catálogo de consultas estratégicas — OE3

Un fichero por informe. Django las **lee**; Airflow es el único escritor del
almacén. **Solo los siete construibles tienen fichero.** Los siete bloqueados
no se publican ni como consulta vacía: un `200` con ceros en E3-04 compararía
contra 1970.

## Convención de nombres

`e3_NN_<informe>.sql` — el número es el del catálogo (E3-02, E3-03, …), el resto
es el nombre del informe en snake_case. El contrato HTTP usa kebab-case; el
enlace vive en `CATALOGO` del servicio, no en el nombre del fichero.

## Encabezado

Cada consulta declara en las primeras líneas **qué mide y por qué** cada
decisión no obvia.

## Granularidad

`mes` · `trimestre` · `anio` se traducen **dentro** de la consulta con
`multiIf` sobre `{granularidad:String}`. El valor llega ligado por el servidor,
nunca interpolado.

## Prohibiciones de este catálogo

- Unir con `dim_region` o agrupar por región. Duplica cada caso sin fallar (#38).
- `SELECT *`.
- `FINAL` sobre `hecho_estado_unidad` o `hecho_ping_unidad` (`ILLEGAL_FINAL`).
- Coordenadas, identidad de persona, texto libre.
- Publicar E3-02 contra una meta de 100 ms: mide el proceso operativo, meta `<2 min p95`.

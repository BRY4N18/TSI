# Catálogo estratégico — OE4

Nueve consultas publicadas. Los seis informes bloqueados **no tienen fichero**:
un SQL suelto no debe convertirse en endpoint.

Convención: `e4_NN_<informe>.sql`. HTTP en kebab-case vive en `CATALOGO` del servicio.

- `FINAL` en `hecho_accidente`, `dim_geografia`, `dim_severidad`.
- **Nunca** `FINAL` en `hecho_evidencia`.
- **Nunca** `dim_region` ni coordenadas.
- `{desde:Date}` `{hasta:Date}` `{granularidad:String}` ligados, nunca interpolados.

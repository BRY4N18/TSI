# Catálogo de consultas — Partners y API

La definición canónica está en
`specs/002-tactico/Partners-API/informes-compuestos-modelo/backend/contracts/catalogo-consultas.md`.

## Versión final

`FINAL` es **obligatorio** en `dim_partner`, `dim_credencial_api`,
`dim_version_contrato` y `dim_cliente`. Es **prohibido** en `hecho_llamada_api`
y `hecho_cambio_acceso`. `hecho_accidente` sigue la regla de Emergencias
(`FINAL` obligatorio). `hecho_factura` es de transacción.

## Cuatro reglas propias

1. Una sola fuente de consumo: el detalle (`hecho_llamada_api`). La preagregada
   del origen **no existe** en el modelo.
2. Toda medida estadística declara `muestras`.
3. 429, 403 y 5xx no se suman: son `limite_cupo`, `autorizacion` y
   `error_servicio`.
4. Ninguna consulta nombra secreto, contacto técnico, IP de origen ni ejecutor
   de un cambio. El alcance geográfico **no se infiere**.

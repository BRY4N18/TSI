# Catálogo de consultas — Cuentas y Clientes

La definición canónica está en
`specs/002-tactico/Cuentas-Clientes/informes-compuestos-modelo/backend/contracts/catalogo-consultas.md`.

## Versión final

`FINAL` es **obligatorio** en `dim_cliente`, `dim_plan`, `dim_rol`,
`dim_usuario_rol`, `dim_usuario_organizacion` y `dim_etapa_onboarding`.
Es **prohibido** en `hecho_onboarding` y `hecho_sesion`.

## Cuatro reglas propias

1. El embudo se calcula contra `dim_etapa_onboarding`, nunca sobre las etapas observadas.
2. La duración de sesión solo sobre las que tienen cierre; las abiertas se cuentan aparte.
3. La concurrencia se mide por solape de intervalos, no contando inicios.
4. Ninguna consulta devuelve token, nombre, correo, identificación, teléfono, género ni fecha de nacimiento. Solo el informe de roles devuelve `idusuario`.

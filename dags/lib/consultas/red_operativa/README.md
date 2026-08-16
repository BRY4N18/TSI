# Catálogo de consultas — Red Operativa

La definición canónica de cada informe está en
[`contracts/catalogo-consultas.md`](../../../../specs/002-tactico/Red-Operativa/informes-compuestos-modelo/backend/contracts/catalogo-consultas.md).
Aquí solo viven las consultas.

## ⚠️ La regla propia de este departamento

**Ninguna consulta une con un catálogo de estados de unidad.**

Unir con el catálogo es lo correcto en un modelo bien formado, y aquí **pierde datos en silencio**.
`Dim_EstadoUnidadEmergencia` tiene tres filas —`Activa`, `Ocupada`, `Fuera de servicio`— y el
histórico de estados usa **cuatro**: aparece también `En Misión`, que no está en el catálogo.

Medido sobre los datos de hoy: de **45 transiciones**, **6 son `En Misión`**. Un `INNER JOIN` con el
catálogo devolvería 39 y no fallaría, no avisaría, y las cifras seguirían siendo verosímiles — solo
que el 13 % de la operación habría desaparecido, y justamente el 13 % que representa a las unidades
trabajando.

Por eso el hecho **guarda el nombre del estado**, ya resuelto en la carga, y las consultas lo leen
directamente. El precio es una columna de texto repetida; lo que se compra es que un estado nuevo en
el origen aparezca en el informe en vez de desaparecer de él.

## La segunda trampa: la disponibilidad no se mide por transiciones

Una unidad que **nunca falló** no tiene ninguna transición a `Fuera de servicio`, así que un cálculo
basado en contar transiciones le asigna **0 %** de disponibilidad — el peor resultado posible a la
unidad con el mejor comportamiento.

La disponibilidad se mide sobre **tiempo en estado**, no sobre número de cambios, y la ausencia de
transiciones significa que el estado inicial se mantuvo todo el período.

## Las reglas comunes del catálogo

Las mismas que en `../emergencias/`, y las vigilan las mismas pruebas:

- **`FINAL` obligatorio** en `dim_region`, `dim_unidad`, `dim_geografia` y `hecho_despacho`;
  **prohibido** en los hechos de transacción, donde falla con `ILLEGAL_FINAL`.
- **`ORDER BY` explícito** al final, nunca solo dentro de una función de ventana.
- **Nunca `SELECT *`**.
- **Sin dato sensible**: ni coordenadas, ni contacto de proveedor, ni **identidad del validador**.
- **Sin dato ≠ cero**, y **todo porcentaje con su denominador**.

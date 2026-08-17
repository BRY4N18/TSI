# Catálogo de consultas — Ventas y CRM

La definición canónica de cada informe está en `contracts/catalogo-consultas.md`. Aquí solo viven las
consultas.

## ⚠️ Regla 1 — ninguna consulta lee `activo`

`Dim_Prospecto.activo` **no dice si el prospecto sigue en curso**. Cubre a la vez a los que se
convirtieron y a los que se perdieron.

Medido sobre los datos de hoy: de los tres prospectos con `activo = false`, **dos son convertidos y
uno perdido**. Un informe que agrupara por esa columna juntaría el mejor desenlace posible con el
peor, y devolvería «3 inactivos» — una cifra que no significa nada y que nadie cuestionaría, porque
suena a lo que se esperaba.

Por eso el modelo trae `desenlace`, con **tres valores**: `convertido`, `perdido` y `en_curso`. Se
deriva de `motivo_inactividad` y `etapa_actual` en la carga, y las consultas lo leen ya resuelto.

## ⚠️ Regla 2 — ninguna consulta devuelve dato personal

Es el departamento con **más dato personal del sistema**: `Dim_Prospecto` trae nombres, apellidos,
correo, teléfono y cargo. **Nada de eso entra al modelo** — no se filtra en la consulta, no existe
como columna.

La diferencia importa: un dato que no se pide hoy vuelve en cuanto alguien añada un `SELECT`; un dato
que no está no puede volver por descuido.

Lo que sí entra es lo que hace analizable el embudo sin nombrar a nadie: la empresa, el tipo de
organización, el canal y el valor estimado.

## Las reglas comunes del catálogo

Las mismas que en los otros departamentos, y las vigilan las mismas pruebas:

- **`FINAL` obligatorio** en las dos dimensiones; **prohibido** en los cuatro hechos, todos de
  transacción.
- **`ORDER BY` explícito** al final, nunca solo dentro de una función de ventana.
- **Nunca `SELECT *`** — con esta fuente, un `SELECT *` sacaría el teléfono del prospecto.
- **Sin dato ≠ cero**, y **todo porcentaje con su denominador**.

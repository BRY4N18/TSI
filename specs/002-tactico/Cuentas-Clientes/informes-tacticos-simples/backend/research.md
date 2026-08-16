# Research — Informes Tácticos Simples de Cuentas y Clientes (Backend)

**Fecha:** 2026-08-14
**Spec:** [`spec.md`](spec.md) · **Plan:** [`plan.md`](plan.md)

Siete decisiones que el plan necesitaba resolver antes de diseñar. Todas se cerraron leyendo el
código real; ninguna queda como NEEDS CLARIFICATION.

---

## D1 — Rango de período opcional sin romper los 19 informes existentes

**Problema.** FR-013 pide rango de fechas opcional. `apps/informes_tacticos/periodo.py:parse_periodo`
lo exige: `"Los parámetros 'desde' y 'hasta' son obligatorios."` De esa función dependen los 19
informes agregados en producción.

**Decisión.** Crear un paquete nuevo `backend/core/informes/` con los ayudantes compartidos por los
64 listados de los 8 departamentos. **`apps/informes_tacticos/` no se toca.**

**Rationale.** Tres razones se acumulan:

1. **Riesgo cero sobre lo que funciona.** Modificar `parse_periodo` para admitir ausencia de rango
   cambiaría el comportamiento de 19 endpoints verificados. El beneficio (no duplicar ~40 líneas)
   no compensa.
2. **La ubicación correcta es `core/`, no una app.** Los listados viven en la app de cada
   departamento (`cuentas_clientes`, `ventas_crm`, …). Que `apps/cuentas_clientes` importara de
   `apps/informes_tacticos` crearía una dependencia entre apps de departamento que hoy no existe y
   que se multiplicaría por ocho.
3. **Es el patrón del repositorio.** `core/pinot/`, `core/api/`, `core/auth/` ya son el sitio de lo
   transversal.

**Alternativas descartadas.**
- *Modificar `parse_periodo` con un flag `obligatorio=True`* — cambia una firma de la que dependen
  19 endpoints; el flag por defecto los protege, pero la superficie de riesgo queda abierta.
- *Duplicar el parseo dentro de `apps/cuentas_clientes`* — habría que duplicarlo siete veces más.

**Trade-off aceptado.** Durante un tiempo convivirán dos implementaciones del período: la de
`apps/informes_tacticos` (obligatoria, para agregados) y la de `core/informes` (opcional, para
listados). Es duplicación consciente y acotada. Si algún día los 19 migran a `core/informes`, la de
la app desaparece; no al revés.

---

## D2 — Paginación por cursor sobre Pinot

**Problema.** El contrato exige cursor, no página. Pinot no tiene cursores de servidor.

**Decisión.** **Keyset pagination**, reutilizando el patrón ya probado en
`core/repositories/accidentes/accidente_repository.py:117`.

**Cómo funciona en el código existente:**

```sql
-- cursor compuesto "fecha|id" cuando el campo de orden no es único
WHERE (fechahoraaccidente < :cursor_fecha
       OR (fechahoraaccidente = :cursor_fecha AND idaccidente < :cursor_id))
ORDER BY fechahoraaccidente DESC, idaccidente DESC
LIMIT :limit
```

Se pide `limit + 1` filas; si vuelven más de `limit`, hay página siguiente y el cursor se compone
con los valores de la última fila devuelta.

**Rationale.** Es determinista, no sufre desplazamiento cuando entran filas nuevas entre páginas, y
**ya está implementado y probado** en dos repositorios (`accidente_repository`, y la variante simple
de `user_repository.list_users`, que pagina `Dim_Usuarios` por `idusuario`). Reutilizar supera a
inventar.

**Alternativa descartada.** `LIMIT/OFFSET`: no hay un solo uso de `OFFSET` en el repositorio, y con
inserciones concurrentes reparte filas repetidas o saltadas — justo lo que SC-005 prohíbe.

**Consecuencia de diseño.** Todo listado declara su campo de orden **más** un desempate por clave
primaria. Cuando el campo de orden ya es la clave primaria, el cursor es escalar.

---

## D3 — Los centinelas ya están resueltos en el cliente

**Hallazgo.** `core/pinot/client.py:40` implementa `_coerce_value`, que **ya convierte los centinelas
a `None`** antes de que el repositorio vea el dato:

| Tipo | Centinela | Resultado |
|---|---|---|
| `STRING` | texto literal `"null"` | `None` |
| `INT` | `-2147483648` | `None` |
| `LONG` | `-9223372036854775808` | `None` |
| cualquiera | `"-Infinity"`, `"Infinity"`, `"NaN"` | `None` |

**Decisión.** FR-021 se satisface **sin código nuevo** para los ocho listados, apoyándose en el
cliente. Las pruebas lo verifican de todos modos, porque es una garantía de la que dependemos.

**Límite conocido, documentado y sin impacto aquí.** `FLOAT`/`DOUBLE` **no** tienen coerción: un
`0.0` real y una métrica vacía son indistinguibles. Ninguno de los ocho listados de esta spec
expone una métrica flotante, así que no les afecta — pero **sí afectará a los compuestos**, y en
particular es una de las causas del defecto del informe de completitud.

**Consecuencia sobre FR-022.** La prohibición de usar `IS NOT NULL` como filtro de completitud sigue
en pie y es independiente de esto: la coerción ocurre **al leer el resultado**, no al filtrar en
SQL. Un `WHERE campo IS NOT NULL` lo evalúa Pinot sobre el centinela y sigue siendo siempre cierto.

---

## D4 — Un usuario con dos roles, sin romper la paginación

**Problema.** `Dim_Usuario_Rol` guarda **una fila por cada par (usuario, rol)**. Paginar sobre esa
tabla parte a un usuario de dos roles en dos filas, que además pueden caer en páginas distintas.
El escenario 2 de la User Story 1 lo prohíbe explícitamente.

**Decisión.** **Paginar sobre `Dim_Usuarios`**, no sobre la tabla de relación. Para los usuarios de
la página ya resuelta, se consultan sus roles y se adjuntan como lista.

**Rationale.** Tres problemas se resuelven de una vez:

1. La unidad de paginación pasa a ser el usuario, que es lo que el consumidor cuenta.
2. `idusuario` es clave primaria única → cursor escalar, sin desempate compuesto.
3. **FR-023 sale gratis**: un usuario sin ningún rol aparece de forma natural, con su lista de roles
   vacía. Si se paginara sobre la relación, ese usuario sería invisible — que es justo la anomalía
   que el Administrador necesita ver.

**Nota sobre el contrato.** Agrupar roles por usuario **no** convierte el listado en compuesto: es
dar forma a la respuesta, no calcular una métrica. La prueba de pertenencia del contrato habla de
`GROUP BY`, `COUNT`, ratios y series temporales; ninguno interviene aquí.

**Precedente.** `user_repository.list_users` ya pagina `Dim_Usuarios` por `idusuario ASC`.

---

## D5 — Dónde se calcula "días transcurridos"

**Problema.** FR-001 pide los días desde la solicitud, y el filtro de antigüedad mínima de la User
Story 2 depende del mismo cálculo. Depende de "ahora", que no es un dato de la tabla.

**Decisión.** Calcularlo en el **servicio**, con el instante actual **inyectable**.

**Rationale.** Un cálculo dependiente del reloj empotrado en SQL es imposible de probar de forma
determinista. El repositorio ya tiene precedente de inyección de `now` —`run_dunning` la usa para
probar los reintentos a D+3 y D+5— y esa es la razón por la que la mora se pudo verificar de punta a
punta. El filtro por antigüedad mínima se traduce a una **fecha de corte** que sí viaja al `WHERE`,
así que el filtrado sigue ocurriendo en Pinot; solo la presentación del número de días se hace en
Python.

**Alternativa descartada.** Calcular los días en SQL con la fecha actual del broker: no inyectable,
no verificable, y ata el resultado al reloj del servidor de Pinot.

---

## D6 — Alcance de "incorporación incompleta"

**Problema.** `Fact_Onboarding` registra una fila por etapa con su marca `completado`. No está
garantizado que existan filas para etapas que aún no se han iniciado.

**Decisión.** El listado devuelve **las filas existentes con `completado = false`**, y así lo declara
la spec ("una fila por cada etapa pendiente"). No se infieren etapas ausentes.

**Rationale.** Inferir qué etapas faltan exigiría cruzar con un catálogo de etapas esperadas y
calcular la diferencia — una operación de conjunto que empuja el listado hacia lo compuesto. El caso
de uso real del Administrador es *"¿quién está detenido y dónde?"*, y una fila pendiente lo responde.

**A verificar en implementación.** Si al sembrar datos se comprueba que las etapas no iniciadas **no**
generan fila, un cliente recién aprobado no aparecería en el listado hasta empezar. Es un
comportamiento aceptable —todavía no se ha detenido en ninguna parte— pero debe quedar cubierto por
una prueba que lo fije como intencional, no como accidente.

---

## D7 — Qué no puede salir nunca en la respuesta

**Problema.** Dos de los ocho listados leen tablas con material sensible: `Dim_Credencial` contiene
`contrasena`, y `Dim_UsuariosServidor` contiene `contrasena` de acceso técnico. El patrón
`SELECT *` es habitual en los repositorios existentes.

**Decisión.** Los repositorios de estos dos listados **enumeran columnas explícitamente**. Está
prohibido `SELECT *` sobre `Dim_Credencial` y `Dim_UsuariosServidor`. Se añade una prueba que falla
si la respuesta contiene una clave `contrasena` o `client_secret_hash`.

**Rationale.** El Principio V de la constitución exige tratar confidencialidad y control de acceso
antes de pasar a plan para cualquier endpoint que exponga dato sensible. Una credencial filtrada por
un informe de supervisión es exactamente el tipo de fuga que un `SELECT *` produce sin que nadie lo
note: el campo viaja, nadie lo mira, y aparece en el primer volcado de la respuesta.

**Nota.** El listado de sesiones (`Fact_Session`) expone `token`. Mismo tratamiento: se enumeran
columnas y el token no sale.

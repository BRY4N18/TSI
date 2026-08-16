# Research — Informes Tácticos Simples de Suscripciones y Facturación (Backend)

**Fecha:** 2026-08-14
**Spec:** [`spec.md`](spec.md) · **Plan:** [`plan.md`](plan.md)

Siete decisiones cerradas leyendo el código y el esquema reales.

---

## D1 — El acotamiento por organización sube a la capa transversal ⚠️

**Hallazgo.** La resolución «usuario → su cuenta cliente» ya existe, pero **vive en el sitio
equivocado y se está copiando**:

| Dónde | Qué hace |
|---|---|
| `apps/red_operativa/services/proveedor_access_service.py:23` | `resolve_cliente_activo(user_id, roles)` — **la implementación** |
| `apps/suscripciones/permissions.py` | **Importa la de Red Operativa** y deja `request.billing_idcliente` |
| `apps/soporte_cliente/services/cliente_lookup_service.py` | Consulta la pertenencia **a mano**, por su cuenta |
| `apps/seguimiento/views/cliente_expediente_views.py:70` | Consulta la pertenencia **a mano**, otra vez |
| `core/repositories/cuentas_clientes/cuenta_usuario_repository.py:95` | Otra consulta más |

Son **cuatro implementaciones del mismo salto**, y una dependencia entre apps de departamento
—Suscripciones importando de Red Operativa— que no debería existir.

**Decisión.** Ampliar `backend/core/informes/acotamiento.py` con un **segundo eje**: además del eje
«persona» que resolvió Ventas y CRM, un eje «organización» que resuelve la cuenta del solicitante.
**No se toca ninguna de las cuatro implementaciones operativas.**

**Comportamiento:**

| Rol | No indica cuenta | Indica otra cuenta |
|---|---|---|
| Administrador | Ve **todas** | Filtra por esa cuenta |
| Cliente / Proveedor | Forzado **a la suya**, resuelta por pertenencia | **Negativa** |
| Cualquier otro | Negativa | Negativa |

**Rationale.**

1. **La generalización es menor de lo temido, pero real.** El resolutor de Ventas asume que el
   titular *es* el solicitante. Aquí hay un salto de indirección en medio. Es una segunda función,
   no una reescritura.
2. **Tres departamentos más acotan por este mismo eje** —Red Operativa por proveedor de flota,
   Partners por partner, Soporte por cliente reportador—. Si no se resuelve aquí, la quinta y sexta
   copia aparecen solas.
3. **El Administrador no entra por la puerta existente.** `IsProveedorCuenta` solo admite Cliente y
   Proveedor: un Administrador que consultara facturas por esa vía recibiría un rechazo. El listado
   táctico necesita ambos comportamientos, y por eso no basta con reutilizar el permiso operativo.

**Alternativas descartadas.**
- *Reutilizar `IsProveedorCuenta` tal cual* — deja fuera al Administrador, que es la mitad del caso
  de uso táctico.
- *Que `apps/suscripciones` siga importando de `apps/red_operativa`* — perpetúa una dependencia
  entre departamentos que la capa transversal existe precisamente para eliminar.

> **Deuda anotada, fuera de alcance.** Las cuatro implementaciones operativas deberían converger en
> la pieza transversal. No se hace aquí: tocaría código verificado de cuatro departamentos por una
> mejora que no cambia comportamiento. Queda para `decisiones-pendientes.md`.

---

## D2 — «Sin cambio de plan programado» es un centinela, no una ausencia ⚠️

**Hallazgo.** `apps/suscripciones/services/cambio_plan_service.py:96` declara
`SIN_CAMBIO_PROGRAMADO = 0`, y `plan_programado_id()` devuelve ausencia solo cuando el valor es
`<= 0`. Es decir: **toda suscripción sin cambio programado tiene un `0` guardado**, no un vacío.

**Decisión.** El filtro de cambios programados usa **`idplan_programado > 0`**. Está prohibido
tratarlo como una comprobación de nulidad.

**Rationale.** Una guarda de nulidad sobre esa columna es **siempre cierta** —la base analítica no
almacena nulos, y aquí además el propio código escribe un `0` explícito—, así que el filtro
devolvería **todas** las suscripciones como si todas tuvieran una reducción pendiente. No fallaría:
daría un número plausible y equivocado. Es la misma familia de defecto que hace que el informe de
completitud muestre 100 % sin medir nada.

**Prueba obligatoria.** Con una suscripción con cambio programado y otra sin él, el filtro devuelve
**exactamente una**.

**Consecuencia de presentación.** El plan programado se devuelve como **ausencia de cambio**, nunca
como un plan con identificador cero, que además no existe en el catálogo.

---

## D3 — Una factura en disputa no es una factura impaga ⚠️

**Hallazgo.** `estado_pago` toma cuatro valores, no tres:

| Valor | Dónde se fija | Significa |
|---|---|---|
| `Pendiente` | al emitir | Esperando cobro |
| `Pagada` | cobro exitoso | Liquidada |
| `Fallida` | reintentos agotados | Mora consumada |
| **`En disputa`** | `apps/partners/domain_constants.py:102` | **Excluida del cobro automático** mientras se resuelve |

**Decisión.** El listado distingue los cuatro. El filtro de «vencidas e impagas» **excluye las que
están en disputa**, y el listado las muestra con su estado propio.

**Rationale.** Una factura en disputa está deliberadamente fuera del cobro: el cliente abrió un
reclamo y el sistema dejó de reintentarle el cargo. Presentarla como mora induciría exactamente la
acción que la regla quiere evitar —perseguir un cobro que está en discusión—, que es lo que corrigió
el hallazgo B41.

**Nota de acoplamiento.** El valor lo define el departamento de Partners, y lo consume el de
Suscripciones. No se duplica la constante: se importa. Que un estado de facturación viva en otro
departamento es una rareza del modelo, no de esta spec, y se documenta sin corregirla.

---

## D4 — El identificador de cobro no sale jamás

**Hallazgo.** `Dim_MetodoPago.tokenpasarela` **no es un hash ni una referencia opaca inofensiva**:
`apps/suscripciones/services/cobro_service.py:68` lo pasa a la pasarela para ejecutar el cargo.
Quien lo tenga, puede cobrar.

**Decisión.** Columnas enumeradas en el repositorio de métodos de pago. **Prohibido `SELECT *`.** Se
añade una prueba que inspecciona **la respuesta completa serializada**, no solo los campos
declarados en el contrato, y falla si aparece.

**Rationale.** El Principio V exige tratar explícitamente el dato sensible antes de exponerlo, y
aquí el impacto no es informativo sino económico. La prueba mira la respuesta entera porque un
`SELECT *` filtra el campo **aunque el contrato no lo mencione**: el contrato describe lo que se
pretende devolver, no lo que se devuelve.

**Se exponen** tipo, últimos dígitos y caducidad — suficiente para identificar el método ante una
persona, inútil para cobrar.

---

## D5 — La fecha de expiración del método de pago **sí** se puede comparar en la base

**Hallazgo.** `Dim_MetodoPago.fechaexpiracion` está declarada **`LONG`**, como el resto de marcas de
tiempo del sistema.

**Decisión.** Filtro de «próximos a caducar» **enteramente en la base**, sin el trabajo en dos pasos
que necesitó el listado de demos de Ventas y CRM.

**Por qué se anota.** En Ventas y CRM la columna equivalente era texto con formatos mixtos y obligó a
un filtro en dos pasos y a admitir páginas cortas. Comprobar el tipo **antes** de diseñar evitó
arrastrar aquella complejidad a un sitio donde no hacía falta. La conclusión operativa: **verificar
el tipo declarado de toda columna temporal antes de decidir el filtro**, porque el sistema no es
uniforme.

---

## D6 — Las notas de crédito y las anulaciones existen en el esquema, no en la operación

**Hallazgo.** `Fact_Factura` declara `es_nota_credito`, `id_factura_original` y `motivo_anulacion`.
`core/repositories/suscripciones/factura_repository.py:178-180` los escribe **siempre** como
`False`, `None` y `None`. Ningún código produce una nota de crédito ni anula una factura.

**Decisión.** El listado **expone el tipo de documento** para que un consumidor pueda distinguir un
cargo de una nota de crédito, pero **no ofrece un filtro** por algo que hoy tiene un solo valor.

**Rationale.** Es el cuarto caso de la serie en que el esquema declara más de lo que la operación
llena, pero **distinto de los tres anteriores**: aquí la columna sí se escribe, solo que siempre con
el mismo valor. No es un dato ausente, es una funcionalidad no construida. Exponer el tipo cuesta
nada y evita que, el día que se emitan notas de crédito, un listado de facturación las sume como si
fueran cargos. Añadir hoy un filtro que solo tiene un valor sería ceremonia.

---

## D7 — Formas de cursor y tipo de cada listado

Se reutiliza la paginación keyset de `core/informes/paginacion.py`. Nada nuevo.

| Listado | Tipo | Orden por defecto | Cursor |
|---|---|---|---|
| Suscripciones | Estado actual | `id_suscripcion DESC` | Escalar |
| Facturas | **Período opcional** | `fecha_emision DESC` | Compuesto `fecha\|id_factura` |
| Solicitudes de cambio | Estado actual | `fecha_solicitud ASC` (bandeja: lo más antiguo primero) | Compuesto `fecha\|idsolicitud` |
| Métodos de pago | Estado actual | `fechaexpiracion ASC` (lo que antes caduca, primero) | Compuesto `fecha\|idmetodopago` |

**Nota sobre el cursor de facturas.** `id_factura` es `STRING`, no entero. El desempate compara
texto, lo cual es determinista aunque no sea numéricamente ordenado — suficiente para que la
paginación no repita ni salte filas, que es lo único que el cursor necesita garantizar.

**Nota sobre las cancelaciones.** «Cancelaciones del período» se resuelve con un filtro de rango
sobre la **fecha de cancelación**, no con el período genérico del contrato: la tabla de
suscripciones guarda el estado actual, no un histórico de sucesos. Es un filtro de columna y así se
declara.

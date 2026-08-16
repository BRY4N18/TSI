# Research — Informes Tácticos Simples de Ventas y CRM (Backend)

**Fecha:** 2026-08-14
**Spec:** [`spec.md`](spec.md) · **Plan:** [`plan.md`](plan.md)

Seis decisiones cerradas leyendo el código real. Tres de ellas son hallazgos que habrían producido
informes incorrectos si se hubieran implementado desde el catálogo sin verificar.

---

## D1 — «Prospecto perdido» no es lo mismo que «prospecto inactivo» ⚠️

**Hallazgo.** Un prospecto se vuelve inactivo por **dos motivos opuestos**, y ambos dejan
`activo = false`:

| Origen | Estado resultante | Significado |
|---|---|---|
| `pipeline_service.py:17-19` | `etapa_actual='Perdido'`, `activo=false`, `motivo_inactividad='perdido'` | Se perdió la oportunidad |
| `conversion_cliente_service.py:27` | `etapa_actual='Ganado'`, `activo=false`, `motivo_inactividad='convertido'` | **Se ganó** — el prospecto ya es cliente |

**Decisión.** El filtro de prospectos perdidos usa **`motivo_inactividad = 'perdido'`**. Está
prohibido usar `activo = false` como equivalente de «perdido».

**Rationale.** Un listado de perdidos filtrado por `activo = false` incluiría **los prospectos
convertidos, es decir los éxitos, presentándolos como fracasos**. El informe no fallaría ni daría
error: mostraría un número plausible y equivocado, que es la peor clase de defecto — el mismo patrón
que el informe de completitud, que muestra 100 % y no mide nada.

**Consecuencia sobre el filtro de estado.** El filtro `estado` del listado de prospectos distingue
**tres** valores, no dos: `activo`, `perdido` y `convertido`. Reducirlo a activo/inactivo perdería
justo la distinción que importa.

**Prueba obligatoria.** Con un prospecto perdido y otro convertido sembrados a la vez, el filtro de
perdidos devuelve **exactamente uno**.

---

## D2 — El acotamiento por titularidad sube a `core/informes/`

**Problema.** FR-006 a FR-009 exigen que el resultado dependa de quién pregunta. La capa transversal
se construyó para el módulo piloto, donde el Administrador lo ve todo, así que no lo contempla.
Quedan **seis departamentos** por construir encima.

**Decisión.** Añadir `backend/core/informes/acotamiento.py` con un resolutor único, y usarlo en los
cuatro listados. **No** se implementa dentro de `apps/ventas_crm`.

**Comportamiento**, copiado del que ya existe en producción
(`apps/ventas_crm/services/consulta_notificacion_ventas_service.py:25-37`):

| Rol del solicitante | No indica titular | Indica otro titular |
|---|---|---|
| Administrador | Ve **todos** | Filtra por ese titular |
| Gerente (Ventas o Cuentas Públicas) | Forzado **a lo suyo** | **Negativa** |
| Cualquier otro | Negativa | Negativa |

**Rationale.** Tres razones:

1. **La sustitución silenciosa es peor que la negativa.** Devolver la cartera propia a quien pidió la
   ajena oculta al solicitante que pidió algo indebido, y produce un informe que parece responder a
   una pregunta que nadie hizo.
2. **No hay que inventar el comportamiento**: el módulo operativo ya lo resolvió y está verificado.
   Copiarlo mantiene coherente lo que el usuario ve en pantalla y lo que obtiene por informe, que es
   exactamente lo que exige FR-010.
3. **Seis departamentos vienen detrás.** Soporte acota por cliente reportador, Partners por partner,
   Red Operativa por proveedor de flota. Si cada uno lo resuelve por su cuenta, el patrón diverge y
   la puerta trasera aparece en el que se despiste — que es lo que casi pasó en F18.

**Alternativas descartadas.**
- *Resolverlo en cada servicio de departamento* — se reimplementaría siete veces; la primera
  divergencia es una fuga de datos.
- *Resolverlo en la vista base* — la vista no conoce qué columna representa la titularidad, que
  cambia por listado (`idusuario` en prospectos, `idusuariogerentenotificado` en notificaciones).
  El resolutor devuelve **a quién** acotar; el repositorio decide **por qué columna**.

---

## D3 — La fecha de expiración de la demo no se puede comparar en SQL ⚠️

**Hallazgo.** `demo_expiracion` está declarada **`STRING`** en el esquema, mientras que todas las
demás marcas de tiempo del sistema son `LONG` en milisegundos. Y el formato **no es uniforme**:
`apps/ventas_crm/demo_tokens.py:72-82` acepta defensivamente sufijo `Z`, sufijo `+00:00` y cadenas
**sin zona horaria**.

**Por qué importa.** Comparar cadenas ISO-8601 lexicográficamente solo funciona si el formato es
idéntico en todas las filas. Con `Z` y `+00:00` conviviendo —y peor, con valores sin zona— la
comparación da resultados incorrectos **sin error visible**.

**Decisión.** Filtro en dos pasos:

1. **Prefiltro en SQL por el prefijo de fecha** (`demo_expiracion >= 'YYYY-MM-DD'` del día actual).
   El prefijo `YYYY-MM-DD` **sí** es uniforme, sea cual sea el sufijo, así que la comparación es
   segura.
2. **Refinamiento exacto en el servicio** con el instante actual, usando el parseador que ya tolera
   los tres formatos.

**Consecuencia declarada en el contrato**: una página de este listado **puede devolver menos filas
que el `limit` pedido**, porque el servicio descarta las que expiraron hoy más temprano. El campo
que indica si hay más páginas sigue siendo la autoridad; el número de filas devueltas no lo es.

**Alternativas descartadas.**
- *Comparar la cadena completa en SQL* — es exactamente el fallo silencioso descrito arriba.
- *Traer todo y filtrar en Python* — rompe la paginación y no escala.
- *Reclasificar el listado como compuesto* — sería esconder un defecto del modelo de datos detrás de
  una etiqueta. Sigue siendo una tabla con un filtro.

> **Causa raíz, fuera del alcance de esta spec.** `demo_expiracion` debería ser `LONG` en
> milisegundos como el resto del sistema. Mientras siga siendo texto, cualquier consulta por rango
> sobre esa columna arrastra este problema. Queda anotado para `decisiones-pendientes.md`.

---

## D4 — Qué datos del prospecto salen, y cuáles no

**Problema.** `Dim_Prospecto` contiene datos personales de contacto: `gmail`, `telefono`, `nombres`,
`apellidos`. El repositorio operativo usa `SELECT *`.

**Decisión.** El listado táctico expone **empresa, nombre de contacto y cargo** —lo necesario para
identificar la oportunidad— y **no expone `gmail` ni `telefono`**. Columnas enumeradas, prohibido
`SELECT *`.

**Rationale.** El Principio V exige tratar explícitamente el dato personal antes de exponerlo. El
propósito táctico es **supervisar la cartera**, no contactar: para contactar existe la pantalla
operativa, que ya tiene esos datos y su control de acceso. Exponer menos por defecto no cuesta nada
y evita que un volcado de informe se convierta en una lista de contactos exportable.

**Reversible sin coste.** Si al usar el listado se comprueba que el dato de contacto hace falta, se
añade una columna. Lo contrario —retirarlo después de que circule— no es posible.

---

## D5 — Los días restantes de la demo se calculan en el servicio

**Decisión.** Con el instante actual **inyectable**, igual que `dias_transcurridos` en el módulo
piloto.

**Rationale.** Mismo argumento que allí: un cálculo dependiente del reloj empotrado en SQL no es
verificable de forma determinista. Aquí además es obligatorio, porque el refinamiento de D3 ya vive
en el servicio y debe usar **el mismo instante** que el cálculo de días restantes — si uno usara el
reloj del broker y otro el del proceso, una demo podría aparecer con «0 días restantes» y haber sido
ya descartada, o al revés.

---

## D6 — Formas de cursor y orden por listado

**Decisión.** Se reutiliza la paginación keyset de `core/informes/paginacion.py` construida en el
piloto. Nada nuevo.

| Listado | Orden por defecto | Cursor |
|---|---|---|
| Prospectos | `idprospecto DESC` | Escalar |
| Reasignaciones | `fechahoraasignacion DESC` | Compuesto `fecha\|idasignacion` |
| Demos activas | `demo_expiracion ASC` (prefijo de fecha), desempate `idprospecto` | Compuesto |
| Notificaciones | `fechahoranotificacion DESC` | Compuesto `fecha\|idnotificacion` |

**Nota sobre prospectos.** `prospecto_repository.list` ya pagina por `idprospecto` ascendente y ya
acepta un filtro `owner_id`. El listado táctico **no reutiliza ese método** —usa `SELECT *` y no
distingue los tres estados de D1— pero sí confirma que la clave y el patrón de cursor son los
correctos.

**Nota sobre demos activas.** El orden por `demo_expiracion` es lexicográfico sobre texto. Con el
prefiltro por prefijo de fecha de D3 el orden **por día** es correcto, que es la granularidad que el
usuario necesita («¿cuáles vencen antes?»). El orden dentro de un mismo día no está garantizado si
los formatos difieren; se documenta y se acepta.

---

## D7 — El ejecutivo ausente no se oculta

**Decisión.** Un prospecto sin ejecutivo asignado **aparece** en el listado del Administrador, con el
ejecutivo marcado como ausente (FR-020). Igual la primera asignación de un prospecto, que no tiene
responsable anterior.

**Rationale.** El cliente de la base analítica ya convierte el centinela de entero a ausencia de
valor, así que el dato llega correctamente como «no hay». Ocultar esas filas escondería justo la
anomalía que la supervisión busca: un prospecto sin dueño es un prospecto que nadie está trabajando.

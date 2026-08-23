# Hallazgos — PG-SEC-001, aislamiento multi-tenant

**Fecha:** 2026-08-23 · **Suite:** `test_aislamiento_tenant.py` · **Tarea:** T017

---

## El hallazgo principal no es una vulnerabilidad: es que casi nada está probado

La primera ejecución de la suite reportó **82 passed** y parecía una buena noticia. No lo era.

El actor de las pruebas es un `PartnerIntegracion`, y ese rol **no tiene acceso a la mayoría de los
92 endpoints con identificador**. Recibía `403` en 29 de 31 rutas con `GET`, pero por
**autorización vertical**, no por tenencia. La suite pasaba en verde sin haber ejercitado el
aislamiento ni una sola vez.

Es exactamente el modo de fallo que este bloque existe para evitar: una prueba que **da confianza
infundada**, que es peor que no tener prueba. Un `403` por rol y un `403` por tenencia se ven
idénticos desde fuera, y solo el segundo dice algo sobre IDOR.

**Corregido** añadiendo detección de vacuidad: antes de afirmar nada, la suite comprueba si el
actor puede acceder a su **propio** recurso en esa ruta. Si tampoco puede, la denegación es de rol
y el caso se marca `NO EJERCITADA` en vez de contarse como aprobado.

### Cobertura real, en tres pasos

```
Un solo actor (PartnerIntegracion)       :  2 / 92  ejercitadas
Cinco actores por materia (T078)         : 13 / 155 ejercitadas
Siete actores + siembra completa (T079)  : 13 / 62  ejercitadas
Criterio estricto de «ejercitada» (T080) : 12 / 62  ejercitadas
```

El último paso **baja** el número, y es correcto que lo haga: al exigir que el actor obtenga de
verdad su propio recurso (2xx) en vez de conformarse con «no le dieron 403», una ruta dejó de
contar. Un criterio laxo infla la cobertura declarada — justo lo que este bloque existe para
impedir.

**Las 12 ejercitadas de verdad:**

```
cliente/expedientes/<idaccidente>            partners/<idpartner>
cliente/expedientes/<idaccidente>/pdf        partners/<idpartner>/credenciales
cuentas-clientes/<idcliente>/onboarding/…    partners/<idpartner>/estado-acceso
cuentas-clientes/<idcliente>/perfil          partners/<idpartner>/metricas
cuentas-clientes/<idcliente>/preferencias    soporte/tickets/<id_reclamo>
cuentas-clientes/<idcliente>/usuarios-elegibles
```

El denominador **baja** en el tercer paso, y esa es la mejora. Al modelar qué roles están acotados
por tenant, dejan de contarse las combinaciones que nunca debieron exigir aislamiento: 62 es el
universo real, no 155.

---

## Vulnerabilidades encontradas y corregidas

Ambas son **oráculos de enumeración**, el mismo patrón que ya se cerró a mano en Partners
(`changelog.md` C4) — la diferencia es que estas las encontró la suite sola.

### V1 — `GET /api/v1/soporte/tickets/{id_reclamo}` (Soporte)

**Módulo que no se había tocado.** Es la prueba de que el enfoque transversal funciona: el patrón
no estaba solo donde se buscó a mano.

```
403 → el ticket existe pero es de otro cliente
404 → el ticket no existe
```

Un cliente iterando ids deduce **qué tickets existen en todo el sistema** sin ver ninguno.

**Corregido** con `core/seguridad/denegacion.py::resolver_o_denegar`. El agente de soporte —que
atiende tickets de cualquier cliente— conserva el `404` preciso; el cliente recibe la misma
respuesta en ambos casos.

### V2 — `GET /api/v1/partners/{idpartner}` (Partners)

Vista que **la corrección manual del 2026-08-23 no alcanzó**: entonces se arreglaron
`estado_acceso_views` y `metricas_views`, y esta quedó fuera. Aquí el `404` venía del **servicio**
(`ConsultaPartnerService`), no de la vista — la variante que T018 predijo.

Tuvo **dos capas**:

1. `404` (servicio, no existe) frente a `403` (vista, no es tuyo). Corregido enrutando el
   `not_found` del servicio por la misma decisión.
2. Ya con ambos en `403`, **el cuerpo seguía delatando**: `code: propiedad_partner` frente a
   `code: acceso_denegado`. La segunda capa solo apareció al arreglar la primera.

> El punto 2 es la lección más útil del día: **igualar el código HTTP no basta**. Mientras el
> cuerpo difiera, el oráculo sigue abierto. El motivo real vive ahora en el registro de auditoría,
> que es donde sirve, y no en la respuesta.

---

## T079 — tres cosas que la ampliación enseñó

### 1. La tenencia de un accidente **no es `idcliente`**

Va por **condados contratados**: `idcalle` → `idcondado` → el JSON `zonas_geograficas` de
`Dim_Preferencias_Cliente` (ver `cliente_expediente_views.py::_condados_cliente`). Es un eje de
propiedad distinto del de partners o tickets, y sembrar un `idcliente` en la fila no habría
servido de nada. Cada materia puede tener su propio eje, y darlo por supuesto es cómo se escribe
una prueba que no prueba.

### 2. Elegir «el rol que suena bien» deja la ruta sin examinar

Tres de mis cinco actores iniciales tenían el rol equivocado, y el síntoma era un `403`
indistinguible de una denegación legítima:

| Materia | Yo puse | El sistema exige |
|---|---|---|
| Ventas | `Gerente` | `GerenteVentas` (`IsCRMUser`) |
| Red operativa | `DirectorOperaciones` | `DirectorTecnologico` (`IsAdministradorOrDirectorTecnologico`) |
| Mi despacho | — | `Unidad` (`IsUnidadDespachoOwn`) |

Los nombres correctos salieron de leer las clases de permiso que el inventario ya expone. **El
sistema sabía la respuesta; había que preguntársela en vez de suponerla.**

### 3. No todos los roles están acotados por tenant

Al añadir `DirectorTecnologico` y `Unidad` aparecieron cuatro «fallos» que **no eran fugas**:

- `es_solo_reportador()` acota **únicamente** a Cliente y Partner; quien tiene un rol de atención
  ve los tickets de todos, que es su trabajo.
- `IsAdministradorOrDirectorTecnologico` hace al Director Tecnológico autoridad sobre **todas** las
  regiones.
- `Unidad` atiende los accidentes que se le despachan, sean de quien sean.

Modelado como `ROLES_ACOTADOS_POR_TENANT`. Sin esa distinción la suite generaría falsos positivos
—y **una suite con falsos positivos enseña a ignorarla**, que es la forma más rápida de perder una
compuerta de seguridad.

---

## T080 — el `404` de expedientes: cuatro condiciones, no una

`cliente/expedientes/{idaccidente}` devolvía `404` **incluso para el accidente propio**. No era un
fallo del sistema: la siembra no cumplía cuatro requisitos que solo se ven leyendo el servicio.

| Requisito | Qué fallaba |
|---|---|
| Estado **CERRADO** | `requiere_cerrado=True`; el accidente estaba en REPORTADO |
| Cadena `calle → ciudad → condado` | La calle ajena colgaba de la ciudad del tenant A |
| `idaccidente` en `Fact_NotificacionDespacho` | El doble de Pinot filtra por él y reventaba |
| Nombre de campo `idtipoestadoincidente` | No `idtipoestadoaccidente` |

> El segundo es el más instructivo: colgar la calle ajena de la ciudad 1 la dejaba **en el condado
> del tenant A**. El accidente «ajeno» habría sido legítimamente visible y la prueba habría
> aprobado por estar mal montada — un falso negativo silencioso, el peor tipo.

**Resultado, ya con la siembra correcta:**

```
PROPIO       200  {"data":{"accidente":{"idaccidente":"ACC-TENANT-A", …
AJENO        404  {"error":"not_found","detail":"Expediente no encontrado"}
INEXISTENTE  404  {"error":"not_found","detail":"Expediente no encontrado"}
```

✅ **El módulo ya era correcto.** Ajeno e inexistente son **idénticos** en código y cuerpo: no hay
oráculo. Pero ahora está **verificado**, no supuesto — y es la materia que maneja datos de
víctimas, así que la diferencia importa.

---

## Lo que hace falta para cubrir las restantes

**La suite necesita un actor por materia, no un actor único.** Cada endpoint exige un rol distinto,
y probar IDOR requiere *tener el rol correcto y el tenant equivocado*. Con un solo
`PartnerIntegracion` no se llega a los expedientes de cliente, ni a la red operativa, ni a
suscripciones.

Rutas no ejercitadas, agrupadas por el rol que harían falta:

| Materia | Rutas | Rol necesario |
|---|---|---|
| Expedientes de cliente | `cliente/expedientes/<idaccidente>`, `.../pdf`, `emergencias/historial/<idaccidente>/expediente` | Cliente |
| Red operativa | `red-operativa/regiones/<id>`, `.../validaciones`, `red-operativa/unidades/<id>` | Director de Operaciones / Proveedor |
| Ventas | `ventas-crm/prospectos/<id>` | Gerente de Ventas |
| Suscripciones | `suscripciones/facturas/<id_factura>` | Director Financiero |
| Partners | `partners/<id>/credenciales`, `.../metricas`, `.../estado-acceso` | Partner de integración **con datos sembrados** |

⚠️ **Las de Partners son el caso más incómodo:** el rol *sí* es el correcto, pero el actor no
alcanza ni su propio recurso porque el almacén en memoria de `conftest.py` no siembra un partner
para el usuario 3. Es un hueco del fixture, no del sistema — y demuestra que la detección de
vacuidad funciona: sin ella, esas cinco rutas habrían contado como cubiertas.

---

## Trabajo pendiente derivado

1. **Ampliar el fixture** (`tests/seguridad/conftest.py`) con un actor por materia y datos
   sembrados para ambos tenants. Es la condición para que T011–T013 signifiquen algo.
2. **Reejecutar y re-catalogar.** Solo entonces este documento podrá afirmar si hay IDOR y dónde.
3. **T018** — los siete servicios de Partners que lanzan `not_found` por su cuenta.
4. **T021** — verificar que un usuario pertenece a un único cliente; si no, el eje de aislamiento
   deja de ser escalar y la suite cambia de forma.
5. **T022** — el canal temporal (`decisiones-pendientes.md` #51).

---

## Hallazgo lateral: un `410 Gone` no contemplado

`PATCH /api/v1/cuentas-clientes/{id}/configuracion` devuelve **410**, que no estaba en el conjunto
de códigos de denegación admitidos y hacía fallar la prueba.

Revisado: **no es una vulnerabilidad**. El endpoint está retirado y el `410` es la respuesta
correcta — deniega igual. Añadido a `CODIGOS_DENEGACION`.

Merece la pena anotarlo porque ilustra por qué la suite **no afirma un código concreto** sino un
conjunto: fijar `403` habría producido un fallo espurio en un endpoint que se comporta bien.

---

## Conclusión

`PG-SEC-001` **sigue en ⚠️ Parcial**, y con razón: 13 rutas ejercitadas de 155 combinaciones.

Lo entregado: la suite existe, **no miente**, y ya encontró **dos vulnerabilidades reales** — una
en un módulo que nadie había revisado y otra en una vista que la corrección manual pasó por alto.
Ambas corregidas y verificadas.

Lo que falta es ampliar la siembra a las materias restantes (accidentes, despacho, red operativa)
para que las 142 combinaciones no ejercitadas dejen de serlo. Cada una es superficie sin examinar,
no superficie limpia.

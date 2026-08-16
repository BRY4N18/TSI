# Changelog fuera de ciclo — cambios de código no originados en `/plan`→`/tasks`

Este documento registra cambios de código aplicados directamente al detectar brechas
entre `spec.md` y el comportamiento real del sistema (vía `/speckit-analyze` extendido),
fuera del flujo normal Spec-Driven. Cada entrada debe quedar reflejada también en el
`traceability.md` de la feature afectada.

---

## 2026-08-15 — Frontend de Soporte al Cliente: `acotado_a` validado de punta a punta

Alcance: `specs/002-tactico/Soporte-Cliente/informes-tacticos-simples/frontend/` (spec, tasks),
`frontend/src/app/modules/soporte-cliente/informes/` (catálogo, 2 guards, 2 páginas, rutas),
`app.routes.ts`, `nav-links.ts`, 2 ficheros de prueba (18 pruebas),
y en backend: el `enum` de `estado` en el contrato OpenAPI **y su prueba de conformidad**.

**Se eligió este departamento para cerrar el hueco del piloto.** Cuentas y Clientes validó todo menos
el aviso de alcance, porque sus ocho listados son globales. Aquí `tickets` devuelve `propios` a un
reportador y `todos` a quien atiende, así que la garantía más delicada de la capa compartida se
ejercita contra el backend real.

### Lo verificado en navegador, con dos roles sobre los mismos datos

| | |
|---|---|
| Rol **Soporte** → `todos` | 14 filas de varias cuentas, **sin aviso** |
| Rol **Cliente** → `propios` | 12 filas de **una sola cuenta**, con el aviso |
| **Estado vacío acotado** | «No hay tickets con esos criterios. **No hay resultados entre tus registros.**» |
| **`403` real** | un Cliente sin cuenta resuelta ve el mensaje del backend, no una lista vacía |
| Guard de escalados | el Cliente queda fuera; el índice ni se lo ofrece |

El estado vacío es lo que más importa: es justo cuando no hay filas cuando «no hay» y «no hay de los
tuyos» se leen igual, y es la ambigüedad que `acotado_a` existe para evitar. Ahora está cerrada en la
pantalla, no solo en la respuesta.

### Un hueco del contrato de backend, cerrado de paso

El OpenAPI declaraba `estado` como **texto libre** y el backend **sí** lo valida contra las
constantes del dominio. Sin el `enum` declarado, el frontend no podía ofrecer un desplegable sin
copiar de un sitio que nadie comprueba — y un `400` evitable acabaría llegando al usuario. Añadido al
contrato, con la prueba de conformidad extendida para que no pueda divergir. Es la tercera vez que
este mismo patrón aparece en el departamento.

### Una regla de navegación que no se rompió

Añadir `PartnerIntegracion` al enlace del sidebar puso en rojo una prueba existente: **FR-UI-033** —la
consola de Partners y su portal no se fusionan, y ningún rol descubre la existencia del otro
departamento—. No se actualizó la prueba para que pasara: **se quitó el enlace**.

El backend sí le permite el listado, así que la ruta le responde si llega a ella; lo que no tiene es
un enlace. Queda anotado como decisión de producto en `tasks.md`, no resuelta por conveniencia.

### Verificación

Suite completa del frontend: **759 verdes** (741 previas + 18 nuevas). Backend: la prueba de
conformidad del contrato de Soporte sigue verde con el `enum` nuevo.

---

## 2026-08-15 — Piloto de frontend: los 8 listados de Cuentas y Clientes, verificados en navegador

Alcance: `specs/002-tactico/Cuentas-Clientes/informes-tacticos-simples/frontend/`
(spec, plan, tasks — **nuevos**),
`frontend/src/app/modules/cuentas-clientes/informes/` (**nuevo**: catálogo, 2 guards, 2 páginas,
rutas), `frontend/src/app/shared/informes/` (**3 correcciones**),
`app.routes.ts`, `nav-links.ts`, 3 ficheros de prueba (56 pruebas),
`.claude/launch.json` y `frontend/proxy.local.conf.json`.

**La hipótesis de la capa compartida se confirma.** Las ocho pantallas salen de **un catálogo de
definiciones y una sola página parametrizada**: ninguna implementa tabla, paginación ni manejo de
error. Añadir un listado es añadir una entrada al catálogo.

### La capa compartida necesitó tres cambios, y eso es el resultado del piloto

Se construyó antes que cualquier pantalla precisamente para descubrir esto. Los tres se corrigieron
**en `shared/informes`**, no en una página:

**1. Faltaba el formato `lista`.** Tres listados devuelven arreglos —`roles`, `roles_servidor`,
`roles_negocio`— y se pintaban con las comas pegadas de `String(['a','b'])`. De paso quedó fijado que
**un arreglo vacío es ausencia**: quien no tiene roles no tiene «cero roles», no los tiene.

**2. `controlClass` no existía.** Importé la constante de estilo y nunca la asigné al componente.
**Las 42 pruebas de Karma pasaron igual** —compila en JIT, con comprobación de plantillas más laxa— y
lo encontró el compilador AOT al arrancar el servidor de desarrollo. Es la demostración concreta de
por qué el recorrido en navegador no es opcional, y de por qué avisé al entregar la capa de que sus
plantillas aún no estaban type-checkeadas.

**3. El pipe de números fijaba el locale `'es'`**, que exige registrar sus datos; sin ellos **lanza al
renderizar**, o sea que la tabla se cae al pintar un número. Ahora usa el `LOCALE_ID` de la
aplicación.

### Dos decisiones propias del piloto

**Dos guards, no uno.** El backend declara Administrador en siete listados y Administrador o Director
Tecnológico en `accesos-tecnicos`. Un guard único con la unión de roles le daría los siete al Director
Tecnológico — la contradicción con el §5.1 del SRS que `acceso-tactico.md` marca con ⚠️. Hay una
prueba por cada mitad, y se verificó en navegador.

**El índice se genera del mismo catálogo** que las páginas y filtra por rol: al Director Tecnológico
le ofrece **solo** el suyo. Ofrecerle enlaces que su guard rechaza no sería una fuga —el guard sigue
cerrando— pero sí una interfaz que promete lo que no cumple.

### El vacío que no es un defecto

`transferencias-propiedad` devuelve cero filas **siempre**, porque nadie escribe
`Fact_HistorialTransferenciaPropiedad` (decisión #28). Su estado vacío lo dice: *«la fuente de este
informe aún no se alimenta… No es un fallo de la pantalla»*. Un «no hay transferencias» genérico
habría hecho que alguien buscara el defecto en el código.

### Verificado en navegador contra el stack real

Requirió **reconstruir los contenedores**: el de Django corría una imagen anterior a *todos* los
informes tácticos —decisión #26—, así que las 32 rutas respondían `404`. Reconstruidos `django` y
`frontend`, se recorrieron las ocho pantallas:

| Comprobación | Resultado |
|---|---|
| Las ocho con datos reales | ✅ |
| **`400` real** (`dias_minimo=-5`) | ✅ muestra el `detail` del backend, **sin** «Reintentar» y **sin** tabla vacía |
| Director Tecnológico en los siete | ✅ redirigido a `access-denied` |
| Director Tecnológico en accesos técnicos | ✅ entra |
| Índice filtrado por rol | ✅ le ofrece solo el suyo |
| Valores ausentes | ✅ guion, nunca `0` ni fecha de época |
| Vacío de transferencias | ✅ explica la #28 |
| Rango de fechas | ✅ solo en transferencias |
| Recuento total | ✅ no aparece |

### Lo que este piloto NO validó, y queda declarado

**`meta.acotado_a`.** Ninguno de los ocho listados de este departamento acota —son de Administrador y
globales—, así que la garantía más delicada de la capa **no se ejercitó de punta a punta**. La cubren
las pruebas de componente, que no es lo mismo. Se cierra con el siguiente departamento acotado:
Soporte (`propios`) o Emergencias (`zonas_contratadas`).

### Verificación

Suite completa del frontend: **741 verdes** (685 previas + 56 nuevas). Build de desarrollo limpio.

---

## 2026-08-15 — Capa compartida de frontend para los listados tácticos simples

Alcance: `specs/002-tactico/contrato-informes-simples-frontend.md` (**nuevo**),
`frontend/src/app/shared/informes/` (**nuevo**: tipos, servicio, store, dos componentes),
3 ficheros de prueba (42 pruebas).

**Ninguna página la usa todavía.** Es deliberado: se construye la capa antes del piloto, igual que
`core/informes/` se construyó antes del piloto de backend. Los 32 endpoints comparten cursor,
envelope, filtros y forma de error; hacerlos departamento por departamento habría producido siete
tablas divergentes, y la primera que se despistara habría abierto el hueco.

### Las tres cosas que la capa existe para no perder

Son cosas que el backend garantiza y que **una pantalla puede tirar a la basura sin que nada falle**,
que es lo que las hace peligrosas.

**1. `meta.acotado_a` llega a la pantalla, y sobre todo al estado vacío.** El backend lo emite para
que un resultado vacío no sea ambiguo: «no hubo accidentes graves» y «no hubo accidentes graves *en
mis zonas*» se leen igual sin él. El componente lo muestra como aviso cuando hay filas y **lo
incorpora al texto del estado vacío** cuando no las hay — que es justo cuando la ambigüedad muerde.

Toma tres valores, no dos. `todos` **no produce aviso**: un cartel permanente diciendo «lo ves todo»
sería ruido, y enseñaría a ignorar la franja donde a veces sí hay una advertencia real. Y
`zonas_contratadas` tiene texto propio: los accidentes ocurridos en una zona contratada **no
pertenecen al cliente**, así que un «tus accidentes» afirmaría algo falso sobre datos de
siniestralidad ajenos. Hay una prueba que lo exige.

**2. Un `400` se muestra como error legible, nunca como tabla vacía.** El backend rechaza en vez de
recortar, y su `detail` nombra los valores válidos. Capturarlo para pintar una tabla vacía
reintroduciría el fallo silencioso que la regla evita: el consumidor leería «no hay resultados» donde
el sistema dijo «tu petición está mal». El `detail` viaja **tal cual**; sustituirlo por un «Ha
ocurrido un error» tiraría justo la información con la que se puede corregir.

Y un `400` **no ofrece «Reintentar»**: repetir lo mismo devuelve lo mismo. Un `403` tampoco es una
lista vacía — no tener acceso es distinto de que no haya datos, y es la diferencia que el backend
eligió a propósito frente a devolver `200` con `data: []`.

**3. Un valor ausente se pinta ausente, nunca como cero.** El backend devuelve `null` de forma
deliberada —una calificación sin poner no es la nota mínima, una hora de fin ausente no es 1970— y
rellenarlo en el último paso desharía esa distinción. Hay dos pruebas emparejadas: `null` pinta un
guion, y un `0` que el backend sí devolvió pinta `0`.

### Lo que el cursor opaco impone al diseño

No hay total de resultados ni números de página, y **no se pueden inventar**: contar filas es
exactamente lo que la paginación keyset evita para no repetir ni perder registros con ingesta
continua. La navegación es siguiente/anterior, con «anterior» resuelto guardando los cursores
visitados — lo que `lista-accidentes` ya hacía a mano, ahora una sola vez y probado.

Dos detalles que la prueba fijó:

- **cambiar de filtros vuelve a la primera página.** Los cursores visitados pertenecen a la consulta
  anterior; reutilizarlos pediría continuar un recorrido que ya no existe, y la respuesta sería
  plausible y equivocada;
- **un error borra el cursor de la página siguiente.** Pertenecía a una respuesta que no llegó, y
  conservarlo dejaría avanzar sobre datos que no se leyeron.

### Dos defectos propios, encontrados al ejecutar

**Un comentario HTML con acentos graves dentro de una plantilla literal.** Cerraba la cadena y
rompía el fichero entero. Lo detectó el compilador.

**El pipe de números con locale fijo.** Fijar `'es'` exige registrar sus datos, y sin ellos el pipe
**lanza al renderizar** — es decir, la tabla se cae al pintar un número. Ahora usa el `LOCALE_ID` que
la aplicación tenga configurado.

### Verificación

`shared/informes`: 42 pruebas. Suite completa del frontend: **685 verdes**. Build de desarrollo
limpio.

⚠️ **Sin verificación en navegador**, y a propósito: ninguna página consume la capa todavía, así que
no hay nada que renderizar. Esa comprobación corresponde al piloto.

---

## 2026-08-15 — Decisión #23 resuelta: la pertenencia a una cuenta ya se puede escribir

Alcance: `config/settings.py` (una entrada), `core/repositories/cuentas_clientes/cuenta_usuario_repository.py`
(`vincular`, `desvincular`), `apps/cuentas_clientes/services/user_management_service.py`
(`idcliente` opcional en el alta), 1 fichero de prueba nuevo (10 pruebas),
`decisiones-pendientes.md` (#23 cerrada).

**Lo que faltaba era una línea.** `Dim_Usuario_Cliente` y su topic estaban declarados en
`database/tablas.json` desde el principio; lo que no existía era la entrada en
`settings.KAFKA_TOPICS`, sin la cual ningún repositorio podía publicar. No es que se olvidaran de
llamar a un método: el método no existía porque no había dónde escribir.

**La consecuencia que arrastraba era grande.** Los tres lectores de esa tabla —el expediente de
cliente en Seguimiento, los tickets en Soporte y el resolutor de pertenencia de los listados
tácticos— caían siempre en el respaldo por `admin_local_id`. De una organización con cinco usuarios,
**uno solo** veía los datos de su cuenta; los otros cuatro recibían `403`. En backend eso era una
nota; en pantalla se lee como una aplicación rota, y por eso se resolvió antes de empezar el
frontend de los listados.

**Decisión tomada:** cualquier usuario vinculado ve los datos de su organización.

### Tres cosas que se conservaron a propósito

**El respaldo por `admin_local_id` se queda.** Las cuentas creadas antes de este cambio no tienen
filas de vínculo, y quitarlo dejaría sin acceso a sus administradores. Así **no hace falta migrar
nada**: lo viejo sigue funcionando y lo nuevo suma.

**El criterio estricto sigue siendo estricto.** Red Operativa y Suscripciones acotan por
administrador local porque sus pantallas operativas lo hacen — dar de alta unidades y ver la
facturación. Si el vínculo también los ampliara, este cambio habría abierto una puerta trasera en dos
departamentos que no la pidieron. Hay una prueba que fija que `por_vinculo_a_cuenta` reconoce al
empleado y `por_admin_local` **no**.

**El `idcliente` del alta es opcional.** Los usuarios internos de TSI no pertenecen a ninguna
organización, y exigirlo dejaría sin poder crearlos. Su ausencia no vincula a nada por defecto.

### Y una que se decidió al escribirla

**`desvincular` marca inactivo, no borra.** Las tres consultas filtran por `activo = true`, así que
marcar basta para retirar el acceso. Borrar haría indistinguible «nunca perteneció» de «se le retiró
el acceso», que es justo lo que alguien necesitará saber el día que pregunte por qué un usuario dejó
de ver los datos de su cuenta.

### Verificación

Suite completa: **3601 verdes**, 2 saltadas por casos de uso retirados. Las 10 pruebas nuevas fijan
el comportamiento y, sobre todo, **la consecuencia**: sin vínculo un empleado no resuelve ninguna
cuenta —el estado en que estaba todo el sistema— y con vínculo resuelve la suya.

---

## 2026-08-15 — Listados tácticos de Emergencias (5 endpoints): un eje de acotamiento nuevo y tres correcciones de spec

Alcance: `core/informes/cobertura.py` (**nuevo**, aditivo),
`core/repositories/accidentes/` (4 repositorios de informes),
`core/repositories/seguimiento/informes_despachos_repository.py`,
`apps/accidentes/` (3 servicios, `views/informes_views.py`, `permissions.py` ampliado, 4 rutas),
`apps/seguimiento/` (1 servicio, 1 vista, 1 ruta),
`backend/conftest.py` (rama de consultas falsas **y corrección de las ramas de catálogo**),
9 ficheros de prueba nuevos (167 pruebas),
`spec.md`, `data-model.md` y el contrato OpenAPI (**corregidos**),
`specs/002-tactico/contrato-informes-simples.md` (§5.6 y §5.7).

**Es el primer módulo desde Red Operativa que amplía la capa transversal**, y por una razón
legítima: ninguno de los tres ejes anteriores acota por cobertura geográfica. La ampliación es
aditiva —`core/informes/acotamiento.py` no se tocó— y las suites de los seis departamentos previos
quedaron intactas.

### El cuarto eje no acota por titularidad

Los tres anteriores preguntan **de quién es la fila**: el ejecutivo del prospecto, la cuenta de la
suscripción, el partner de la credencial. Este no. Un cliente no ve «sus» accidentes —no son suyos en
ningún sentido— sino los de **las zonas que tiene contratadas**.

Cambian tres cosas a la vez, y por eso vive en su propio módulo en vez de ser un parámetro más:

| | Ejes de titularidad | Cobertura contratada |
|---|---|---|
| Lo que se resuelve | un identificador | **un conjunto de ubicaciones** |
| Cómo filtra | `= x` | **`IN (…)`** |
| No tener nada | no se da | **cero resultados** |

`meta.acotado_a` toma un valor propio: **`zonas_contratadas`**. Reutilizar `propios` diría algo falso.

**Sin zonas contratadas es CERO, nunca TODO.** De las dos lecturas posibles, una da el mapa de
siniestralidad completo a quien no contrató nada. La guarda se escribe explícita porque el fallo por
omisión —un `if zonas:` que se salte el filtro cuando el conjunto está vacío— cae justo en la lectura
peligrosa, y sin ruido: la respuesta conserva la forma correcta.

**El conjunto se resuelve una vez, antes de consultar.** Condados → ciudades → calles son dos
consultas por petición, sea cual sea el número de zonas, y hay una prueba que lo mide. El módulo
operativo hace hoy lo contrario a diez líneas de donde hace lo correcto: comprueba el condado **fila
a fila mientras recorre**, con un coste que crece más cuando las zonas del cliente son escasas — es
decir, cuando menos resultados va a haber.

### Tres correcciones que la implementación obligó a hacer

**1. `borrador` no se puede dar, y la spec lo pedía.** `BORRADOR` es un estado formal que vive en el
histórico. `Fact_Accidente` no guarda nada que lo distinga: un caso en borrador es `activo = true`
sin hora de fin, **idéntico a cualquier otro caso en curso**. Implementarlo devolvería **todos los
casos activos** etiquetados como detenidos en borrador — la forma correcta con el contenido
equivocado. Obtenerlo de verdad exige el histórico, que es justo lo que FR-008 prohíbe: FR-002 y
FR-008 se contradicen, y gana FR-008. Retirado de la spec, del data-model, del contrato y del
catálogo, donde la fila queda marcada ⛔ con el motivo.

**2. `cerrado` y `duplicado` no eran disjuntos.** Un duplicado que conservara hora de fin salía en
los dos filtros — contando el mismo hecho dos veces, que es exactamente el defecto que la distinción
existe para evitar. `cerrado` exige ahora además que el caso no apunte a otro.

**3. El cursor de casos y cierres era inpaginable.** `idaccidente` es **texto** —el número de caso—
y el componente de cursor convierte a entero por defecto. La primera página funcionaba y la segunda
daba `400`. Lo encontró la prueba de integridad del recorrido.

### Lo que el caso guarda, y lo que no

`Fact_Accidente` **no tiene columna de estado**. Pero tres hechos suyos distinguen las tres formas de
quedar inactivo: `activo`, `horafin` y `idaccidenteorigen`. El listado devuelve **los tres por
separado** y no un estado calculado: la exclusividad entre cerrado, descartado y fusionado la
garantiza el módulo de fusión, no este, y un campo derivado empezaría a mentir el día que esa
garantía cambiara, conservando la forma correcta.

Un recuento de «casos inactivos» sin distinguir sumaría **emergencias atendidas, falsas alarmas y
duplicados**: el trabajo realizado y el ruido descartado como la misma cosa.

Mismo criterio en despachos: «en tránsito» se deriva de las **horas del propio despacho** —despachado,
sin llegada, sin retiro—, no del histórico de estados. Y `0` es el centinela de «aún no ha ocurrido»:
una guarda por nulidad dejaría **ningún** despacho en tránsito.

### Una exención de cargo no levanta una exclusión constitucional *(§5.7)*

El Director de Operaciones ve los casos de todas las zonas y **sigue sin ver las coordenadas del
accidente ni la identidad de los implicados**. Su exención es de **acotamiento**; aquellas son
exclusiones que la constitución impone sobre el dato, no sobre quién pregunta.

La distinción importa porque el camino contrario se recorre sin querer: quien implementa una exención
de alcance puede leerla como «este rol lo ve todo». Cada listado con dato excluido lleva ahora una
prueba **con la autoridad del departamento**, no solo con el rol acotado.

### La hora que vale es la del sitio, y las dos tablas no son simétricas

La fotografía toma su hora de registro de una **columna propia**; la nota, de la **marca genérica de
modificación**, porque no tiene columna de sincronización. Tomar la equivocada devolvería la hora de
última modificación como si fuera la de captura, y **el error sería invisible** en los registros
hechos en línea —donde ambas coinciden—, apareciendo solo en los capturados sin conexión, que son
justamente los que importan.

Por eso cada prueba mira **los dos casos a la vez**: sin conexión, dos horas distintas; en línea, dos
iguales. Verificar solo uno de los dos no distinguiría una implementación correcta de otra que sella
la hora de subida en ambos campos.

> **Deuda anotada.** Que la nota carezca de columna propia de sincronización es una asimetría del
> modelo. Mientras siga así, cualquier consulta sobre sincronización de notas depende de una columna
> genérica que una actualización futura pisaría.

### Dos defectos que las pruebas encontraron en lo ya construido

**Las ramas del Pinot falso capturaban consultas ajenas.** Mis ramas de catálogo despachaban solo por
la lista de columnas, y los 19 informes agregados consultan `Dim_Calle` y `Dim_Ciudad` con **la misma
lista y distinto `WHERE`**. Resultado: tres pruebas de agregados en rojo, y —peor— filas filtradas por
la columna equivocada. Cada rama exige ahora también su cláusula `WHERE`.

**Las pruebas de coste en consultas de Partners y Soporte pasaban en vacío.** El contador envolvía
`PinotClient.query` y llamaba al original pasándole `self`; el mock que instala `mock_pinot` se llama
**sin** `self`, así que cada consulta lanzaba `TypeError`, la petición acababa en `401` y el conteo
quedaba en cero — con lo que `muchas == pocas` comparaba nada contra nada. Corregido en los tres
módulos, y añadida la guarda `pocas > 0` que impide que vuelva a pasar desapercibido.

Al arreglarlo apareció un matiz real: un catálogo que solo aplica a algunas filas cuesta **una**
consulta más para toda la página, no una por fila. La aserción de igualdad exacta hacía fallar un
comportamiento correcto; ahora es una cota fija, que es la que detecta el `N+1` de verdad.

### Verificación

`apps/accidentes` + `apps/seguimiento`: 463 pruebas verdes. Suite completa: **3591 verdes**, 2
saltadas por casos de uso retirados. Cobertura de los cuatro servicios, las dos vistas, el eje nuevo
y los cinco repositorios de informes: **95 %**.

---

## 2026-08-15 — Listados tácticos de Soporte al Cliente (2 endpoints): el módulo que verifica la capa transversal

Alcance: `core/repositories/soporte/` (2 repositorios de informes),
`apps/soporte_cliente/` (2 servicios, `informes_views.py`, `permissions.py` ampliado, 2 rutas),
`backend/conftest.py` (rama de consultas falsas),
6 ficheros de prueba nuevos (88 pruebas),
`contracts/informes-tacticos-simples.openapi.yaml`, `spec.md` y `data-model.md` (**corregidos**),
`database/seed_usuario_partner_demo.py` (comentario falso), `decisiones-pendientes.md` (#23).

**`core/informes/` no se tocó**, y esa era la hipótesis del módulo. Es el segundo consecutivo que
solo consume la capa transversal: la parametrización del criterio de pertenencia que introdujo Red
Operativa cubrió el departamento que la necesitaba —el que usa el criterio **amplio**— sin ampliarse.
Si hubiera hecho falta modificarla, la corrección iba allí, no aquí.

### El acotamiento se decide por lo que NO se tiene

Dos roles distintos —Cliente y Partner de integración— acotan por el mismo eje, y ninguno ve lo del
otro. Decidirlo por «ser Cliente» es un fallo que el módulo operativo **ya tuvo que corregir**: el
Partner reporta y no es Cliente, así que esa comparación lo habría dejado **fuera** del acotamiento,
viendo tickets ajenos.

La capa transversal lo resuelve sola: con los roles de atención como amplios y los de reporte como
acotados, un usuario con **ambos** cae en la rama amplia, que es exactamente FR-012. Y hay una prueba
que recorre toda combinación de hasta tres roles comprobando que el resolutor transversal y el
`es_solo_reportador` del módulo operativo **deciden lo mismo**. Sin ella, pantalla y listado podrían
acotar a poblaciones distintas sin que ninguna supiera de la otra.

### La spec decía cuatro valores y el dominio tiene cinco

`situacion_compromiso` se describía con cuatro situaciones: en curso, en riesgo, incumplido y sin
compromiso. Falta **`cumplido`**, que `resolver_ticket_service` escribe al resolver dentro de plazo.

Implementar las cuatro al pie de la letra habría dejado el filtro rechazando con `400` un valor
legítimo —«no es válido» cuando sí lo es— y **habría hecho imposible listar los tickets resueltos a
tiempo**. Es el mismo patrón que ya apareció en cuatro departamentos: la spec cita literales que no
coinciden con lo que el código escribe.

Corregido en los tres sitios —`spec.md`, `data-model.md` y el enum del contrato— y cerrado con una
prueba que compara el enum del OpenAPI contra las constantes del dominio. Si mañana aparece un sexto
valor, falla ahí en vez de manifestarse como un `400` inexplicable.

### `sin compromiso` no es ausencia de dato, y `sin clasificar` sí

Dos tickets pueden llegar sin situación de compromiso por motivos opuestos:

* **sin clasificar** — aún no hay contador; llega con `null`, y no se le atribuye ninguna;
* **`sin compromiso`** — está clasificado y **no se le pudo asignar plazo**; llega con su propio
  valor.

El vigilante de plazos descarta el segundo precisamente porque no tiene compromiso que vigilar: es el
único estado en que un ticket puede quedarse indefinidamente sin que ningún proceso lo mire.
Colapsarlo a `null`, u omitirlo, reintroduciría el defecto que la corrección anterior resolvió.

### El texto de los mensajes no se consulta

`Fact_Historial_Ticket` guarda `mensaje` y `es_nota_interna`. **Ninguna de las dos está en la lista
blanca**, y esa es toda la protección. La pantalla operativa las lee y filtra después —tiene que, le
hacen falta—; un listado táctico responde qué pasó, cuándo y quién lo hizo, y no necesita la prosa.

No consultarlas es más seguro que filtrarlas: un filtro correcto sigue siendo un filtro que alguien
puede olvidar al añadir un campo dentro de seis meses, y el fallo sería silencioso — la respuesta
conservaría la forma esperada, solo que con notas internas dentro.

### La autoría se decide por la ausencia de autor, no por el tipo de acción

Manual y automático están registrados **por duplicado**: el tipo de acción y la presencia de autor.
La ausencia de autor es la señal autoritativa, y es deliberada — antes se registraba al supervisor
que **recibía** el escalado como si lo hubiera ejecutado, y la corrección consistió en dejar el autor
vacío y mover al supervisor a destinatario.

Por eso `tipo_escalado` se deriva del autor. Si las dos señales se contradijeran el dato estaría
corrupto; decidir por el tipo lo **ocultaría**. Una prueba exige que coincidan en todos los registros.

De los once tipos de acción, el listado incluye exactamente dos. `alerta_sla_riesgo` es un **aviso**
—el ticket no cambia de agente ni de nivel— y `cierre_automatico_por_vencimiento` **cierra**, no
deriva. Contarlos daría la impresión de que la cola se deriva mucho más de lo que se deriva.

### Un defecto encontrado por las pruebas, el mismo de Partners

`urls.py` iba a importar `TicketsView` de `informes_views` teniendo `views.py` otra `TicketsView`
operativa: la segunda importación habría sustituido a la primera **en silencio**, y la ruta de
informes serviría el listado operativo. Resuelto con alias explícito antes de que llegara a fallar.
Es la segunda vez en dos módulos: conviene mirarlo en los departamentos que quedan.

### Un hallazgo transversal que no se arregla aquí (#23)

`Dim_Usuario_Cliente` **tiene topic de Kafka declarado** y aun así **ningún código de producción
publica en ella**. `ClienteLookupService` consulta la tabla y cae en `admin_local_id` cuando no
encuentra nada — es decir, siempre.

Consecuencia: hoy, en **todos** los departamentos, la pertenencia se resuelve de hecho por
administrador local, incluidos los listados que declaran el criterio amplio. Una organización con
cinco usuarios tiene uno solo que puede consultar sus listados acotados. Poblar esa tabla decide
quién de una organización ve qué, y eso excede a un módulo de listados. Anotado para decisión.

De paso se corrigió el comentario de `seed_usuario_partner_demo.py`, que justificaba sembrar por
`admin_local_id` diciendo que la tabla «no tiene topic de Kafka». Sí lo tiene; la conclusión práctica
era correcta y el motivo no.

### Verificación

`apps/soporte_cliente`: 202 pruebas verdes (114 previas + 88 nuevas). Suite completa: **3400 verdes**,
2 saltadas por casos de uso retirados. Cobertura de los dos servicios, las vistas y los dos
repositorios de informes: **96 %**.

---

## 2026-08-15 — Listados tácticos de Partners y API (5 endpoints) y la regla de la lista blanca

Alcance: `core/repositories/partners/` (3 repositorios de informes),
`apps/partners/` (3 servicios, `views/informes_views.py`, `permissions.py` ampliado, 5 rutas),
`apps/partners/views/urls.py` (**corrección**: colisión de nombres),
`backend/conftest.py` (rama de consultas falsas),
6 ficheros de prueba nuevos (156 pruebas),
`specs/002-tactico/contrato-informes-simples.md` (§5.5 y el recuento de listados).

**No se tocó ninguna pieza compartida.** `core/informes/` quedó igual: el acotamiento por
organización que introdujo Suscripciones y corrigió Red Operativa cubrió este departamento sin
ampliarse. Es la primera vez que la capa transversal absorbe un módulo nuevo sin cambiar.

### El estado no está en la tabla: se deriva, y ahora se deriva dos veces

`Dim_Partner` **no tiene columna `estado`**. Los seis estados de incorporación —Registrado, Plan
asignado, Pruebas activo, Pendiente de aprobación, Producción activa, Suspendido— salen de combinar
`activo`, `planapi`, las credenciales y el último evento de la bitácora.

`ConsultaPartnerService.derivar_estado` ya lo hacía, pero consulta la bitácora **una vez por
partner**. Correcto para una ficha; sobre una página de cincuenta, cincuenta consultas.

`_derivar_estado` replica la **precedencia** alimentándose de **dos consultas por lote**. Dos
derivaciones del mismo concepto es exactamente el tipo de duplicación que se paga tarde: si divergen,
el mismo partner tendría un estado en su ficha y otro en el listado, y ninguna pantalla sabría que la
otra discrepa. Por eso hay una prueba que **ejecuta las dos sobre los mismos datos** en los seis
casos y exige que coincidan.

Consecuencia declarada: el filtro `estado` empuja a SQL solo `Suspendido` y `Registrado`; los otros
cuatro comparten un pre-filtro y se refinan en Python, así que **una página puede devolver menos
filas que `limit`**. Es comportamiento del listado, no un defecto de la paginación — y por eso la
prueba de integridad del recorrido se hace sin ese filtro.

### La regla nueva: enumerar las columnas, no filtrarlas después *(§5.5)*

`Dim_CredencialAPI.client_secret_hash` autentica a quien lo tenga. Lo natural es quitarlo al
construir la fila. Lo natural **falla abierto**: el día que alguien añada otra columna sensible a la
tabla, entra por la consulta, atraviesa el filtro que no la conoce y se publica sin que ninguna
prueba se entere.

La lista blanca invierte el defecto: lo que no está enumerado no sale, y añadir una columna a la
tabla no cambia nada. Una prueba lee el propio fichero del repositorio y comprueba que ninguna
consulta literal use `SELECT *`. Otra comprueba que **el contrato OpenAPI tampoco declare** el campo:
si apareciera ahí, la implementación tendría permiso escrito para publicarlo.

Aplica igual al medio de cobro de Suscripciones y al contacto del proveedor en Red Operativa, que ya
lo hacían de facto. Ahora está escrito.

### Lo que este módulo no puede decir, y por qué se dice en otro sitio

Una credencial con `activo=False` puede estarlo porque el partner **la revocó** —decisión de
seguridad— o porque **se desactivó en cascada** al suspenderlo por impago. En `Dim_CredencialAPI` las
dos filas son **idénticas**.

El listado de credenciales no inventa el motivo: no lo tiene. La bitácora sí, con **tipos distintos**
(`revocacion_credencial` y `desactivacion_por_cascada`). Agruparlos bajo una etiqueta cómoda como
«desactivada» llevaría a reactivar en bloque tras el pago, resucitando una credencial cuyo secreto
está comprometido. Hay una prueba por cada mitad: una exige que el listado **no** traiga motivo, otra
que la bitácora **sí** los distinga.

En la misma línea, la **reactivación sin motivo es correcta**: el SRS exige motivo al cortar el
acceso, no al devolverlo. Presentarla como dato faltante induciría a «completar» un registro completo.

### Sin alcance configurado no es acceso ilimitado

`Dim_Preferencias_Cliente.zonas_geograficas` vacío significa **que nadie lo ha configurado**.
Devolver `[]` invita a leerlo como «sin restricción», y en un listado cuya función es decir qué datos
puede consumir un partner, eso daría por contratado un alcance que nadie acordó. Se devuelve `null`.

### Un defecto encontrado por las pruebas: la ruta servía la vista equivocada

`apps/partners/views/urls.py` importaba `PartnersView` de `informes_views` y, más abajo, otra
`PartnersView` de `partner_views`. La segunda importación **sustituía a la primera en silencio**, así
que la ruta de informes servía el listado operativo. Ninguna prueba del módulo operativo podía
detectarlo. Corregido con un alias explícito y comentado en el sitio.

### Verificación

`apps/partners`: 672 pruebas verdes (558 previas + 114 nuevas de informes, más las de servicio).
Cobertura de los tres servicios de informes y las vistas: 93 % (mínimo 83 %).

---

## 2026-08-15 — Listados tácticos de Red Operativa (4 endpoints) y la corrección del acotamiento

Alcance: `core/informes/pertenencia.py` (**nuevo**), `core/informes/acotamiento.py` y
`envelope.py` (ampliados de forma **compatible hacia atrás**),
`core/repositories/red_operativa/` (3 repositorios de informes),
`apps/red_operativa/` (3 servicios, 4 módulos de vistas, `permissions.py`, 4 rutas),
`apps/suscripciones/views/informes_base.py` (declara su criterio explícitamente),
`backend/conftest.py`, 10 ficheros de prueba nuevos,
`specs/002-tactico/contrato-informes-simples.md` (§5.3 y §5.4),
`decisiones-pendientes.md` (#22).

**Es el primer módulo que CORRIGE la capa transversal en vez de ampliarla**, y por eso su
comprobación de compatibilidad pesaba más que en los anteriores. Salió limpia: piloto, Ventas,
Suscripciones y los 19 informes agregados, todos sin moverse.

### La generalización de Suscripciones se quedó corta, y esto lo demuestra

El eje «organización» se diseñó allí como si **«pertenecer a una cuenta» fuese un concepto único**.
No lo es:

| Criterio | Quién cumple | Pantallas |
|---|---|---|
| **Administrador local** | Una sola persona por cuenta | Alta de unidades, facturación |
| **Vínculo a la cuenta** | Cualquier miembro | Expediente de cliente, tickets |

Unificarlos rompería la regla del contrato común —*un informe nunca más amplio que su pantalla*— en
un departamento u otro. Así que el criterio pasa a ser **parámetro explícito** y cada listado declara
el suyo. El defecto sigue siendo el estricto, que es lo que Suscripciones ya hacía: **se añadió una
opción, no se alteró la existente**.

Corregirlo ahora, con dos departamentos usándolo, fue barato. Con cinco no lo habría sido.

> **Trampa encontrada de paso.** `CuentaUsuarioRepository.get_cliente_ids_for_user` **suena** a
> criterio amplio y es el estricto: solo mira `admin_local_id`. El amplio real es
> `list_cuentas_del_usuario`.

### El defecto de mayor consecuencia de toda la serie

**`activo` significa «existe», no «puede acudir».** Los cuatro estados operativos de una unidad
—`Activa`, `Ocupada`, `En Misión`, `Fuera de servicio`— viven **solo en el histórico**, y obtenerlos
cuesta una consulta por unidad.

Un listado de flota presentado como disponibilidad llevaría a decidir cobertura sobre unidades fuera
de servicio, ocupadas o ya en camino a otro accidente. **En los módulos comerciales un error así
infla una cifra; aquí decide si alguien acude.**

Tres defensas, y la prueba comprueba las tres: el campo se llama `dado_de_alta`, la respuesta
**declara su alcance** en `meta`, y ningún campo promete disponibilidad. La regla sube al contrato
común como **§5.4**.

### Dos hallazgos más, de la misma familia

**`En_Alerta` no se agrupa con `Despublicada`.** Es una región **operativa** con cobertura
degradada: candidata a despublicarse, no despublicada. Agruparlas ocultaría exactamente la ventana en
la que OT13 puede actuar. Mismo patrón que «en disputa» vs «impaga» en Suscripciones.

**Una baja forzada trae su caso afectado; una normal, no.** No es una etiqueta: es la traza de
impacto que el SRS exige. Sumar ambos tipos convertiría un incidente operativo —un accidente que se
quedó sin su unidad— en una estadística de rotación de flota.

### Rendimiento: el riesgo que la spec anotaba

La geografía se resuelve **por lotes** —dos consultas por página, no una por fila—, reutilizando el
patrón que `ubicacion_catalogo_repository` ya tenía. La prueba **cuenta consultas con 100 unidades**
y no mide tiempo: con diez, una implementación N+1 parece igual de rápida y el defecto pasaría.

### Lo que no sale

`latitud`, `longitud` y `contactoproveedor`. La posición de una unidad es dato sensible sujeto a
control y auditoría, y no aporta a un listado de composición — para seguir una unidad en tránsito
existe el módulo de seguimiento, con su propio control.

**Verificación.** 2925 → **3162** pruebas (+237), mismas 2 omitidas, cero regresiones.

---

## 2026-08-15 — Listados tácticos de Suscripciones y Facturación (4 endpoints) y el eje «organización»

Alcance: `core/informes/acotamiento.py` (segundo eje) y `core/informes/periodo.py`
(`parse_fecha_columna`, ambos ampliados de forma aditiva),
`core/repositories/suscripciones/` (3 repositorios de informes),
`apps/suscripciones/` (3 servicios, 4 módulos de vistas, `permissions.py`, 4 rutas),
`backend/conftest.py`, 12 ficheros de prueba nuevos,
`specs/002-tactico/contrato-informes-simples.md` (regla 5 de Pinot),
`decisiones-pendientes.md` (#20 y #21). **Los 16 contratos OpenAPI del catálogo** corregidos.

**El segundo eje de acotamiento.** El primero —«persona», de Ventas y CRM— asume que el titular *es*
el solicitante. Éste tiene un **salto de indirección**: el usuario pregunta y el resultado se acota a
la cuenta cliente a la que pertenece. Red Operativa, Partners y Soporte heredan este mismo eje, así
que la quinta y la sexta copia ya no aparecerán solas.

**Y una diferencia deliberada con el resolutor operativo.** `resolve_cliente_activo` exige cuenta
`Activo`; el táctico **no**. Aquél controla escrituras; éste, la lectura de los propios registros — y
una cuenta suspendida es justamente donde su responsable mira para saber qué regularizar (FR-011).
Negárselo lo dejaría a ciegas sobre su propia deuda.

### El requisito de seguridad más fuerte de la serie

`Dim_MetodoPago.tokenpasarela` **no es un hash**: `cobro_service.py:68` lo pasa a la pasarela para
ejecutar el cargo. **Quien lo tenga, puede cobrar.** No hay nada que romper —bastaría con leer la
respuesta— y el impacto no es informativo sino económico.

La prueba inspecciona **la respuesta serializada completa** de los cuatro listados, no los campos que
el contrato declara. La razón: un `SELECT *` filtra el campo **aunque el contrato no lo mencione**.
El contrato describe lo que se pretende devolver; la respuesta es lo que se devuelve.

### Dos hallazgos que habrían producido informes equivocados

**1. «Sin cambio de plan programado» es un centinela `0`, no una ausencia.** El código escribe un `0`
explícito. Un filtro escrito como comprobación de nulidad sería **siempre cierto** y devolvería
*todas* las suscripciones como si todas tuvieran una reducción pendiente — alimentando una previsión
de ingresos con reducciones inventadas.

**2. Una factura `En disputa` no es una factura impaga.** `estado_pago` toma **cuatro** valores, no
tres. La disputa significa que el cliente abrió un reclamo y el sistema **dejó de reintentar el
cargo**; presentarla como mora induce a perseguir un cobro detenido a propósito, que es lo que
corrigió el hallazgo B41. El filtro de vencidas la excluye **en la consulta**, no en Python: filtrar
después de paginar devolvería páginas incompletas.

### Lo que se hizo bien por comprobar antes

`Dim_MetodoPago.fechaexpiracion` es `LONG`, así que el filtro de caducidad va **entero a la base**.
En Ventas y CRM la columna equivalente era texto con formatos mixtos y obligó a un filtro en dos
pasos y a admitir páginas cortas. Comprobar el tipo **antes** de diseñar evitó arrastrar aquella
complejidad, y la lección sube al contrato común como **regla 5 de Pinot**.

### Defecto sistémico corregido

**Los 16 contratos OpenAPI del catálogo táctico eran YAML inválido** — la misma descripción sin
comillas con `data: []`, repetida por copia. Ninguno se había cargado nunca con un parser. Ahora los
16 validan, y los tres departamentos implementados tienen una prueba que carga su contrato y compara
la implementación contra él.

**Verificación.** 2579 → **2925** pruebas (+346), mismas 2 omitidas, cero regresiones. La ampliación
de `core/informes/` se comprobó **aditiva** (T011): ni el piloto, ni Ventas y CRM, ni los 19 informes
agregados se movieron.

---

## 2026-08-15 — Listados tácticos de Ventas y CRM (4 endpoints) y el acotamiento por titularidad

Alcance: `backend/core/informes/acotamiento.py` (**nuevo**, transversal a 7 departamentos),
`core/informes/{envelope,vistas}.py` (ampliados de forma aditiva),
`backend/core/repositories/ventas_crm/` (3 repositorios de informes),
`backend/apps/ventas_crm/` (3 servicios, 3 módulos de vistas, `permissions.py`, 4 rutas),
`backend/scripts/seed_demo_ventas_tactico.py` (**nuevo**), `backend/conftest.py`,
13 ficheros de prueba nuevos, `specs/002-tactico/contrato-informes-simples.md` (§5.1 y §5.2),
`decisiones-pendientes.md` (#19).

**Lo que este módulo aporta a los seis departamentos restantes.** El piloto construyó el andamiaje
de forma —período, paginación, envelope—; éste construye el de **acceso**: un único resolutor de
acotamiento por titularidad, y el campo `meta.acotado_a` que declara el alcance de cada respuesta.
Soporte acotará por cliente reportador, Partners por partner, Red Operativa por proveedor de flota;
ninguno vuelve a decidir la regla.

**Pedir lo ajeno es `403`, nunca sustitución silenciosa.** Es la decisión con más consecuencias.
Devolverle su propia cartera a quien pidió la ajena produce un informe plausible que **responde a una
pregunta que nadie hizo**, y además le oculta al solicitante que pidió algo indebido. El
comportamiento se copió del que ya estaba verificado en producción
(`consulta_notificacion_ventas_service.py`), en vez de inventarlo.

### Tres hallazgos que habrían producido informes equivocados

**1. «Perdido» no es «inactivo».** Un prospecto se vuelve inactivo por dos motivos **opuestos** y los
dos dejan `activo = false`: se perdió la oportunidad, o **se ganó** y ya es cliente. Un listado de
perdidos filtrado por `activo = false` incluiría los convertidos — es decir, **presentaría los éxitos
comerciales como fracasos**, sin dar ningún error. El filtro tiene tres valores, no dos, y la
condición de cada uno vive en una tabla y no en un `if` encadenado, para que la equivalencia
prohibida no pueda colarse sin verse.

**2. La expiración de la demo no se puede comparar en SQL.** `demo_expiracion` es `STRING` cuando
todo lo demás es `LONG` epoch-ms, y el sistema acepta tres formatos (`Z`, `+00:00`, sin zona).
Compararla entera da resultados incorrectos sin error visible. Se resuelve en dos pasos: prefiltro
por el prefijo `YYYY-MM-DD` —los diez primeros caracteres sí son uniformes— y refinamiento exacto en
el servicio, **con el mismo instante** que calcula los días restantes. La causa raíz queda anotada
como decisión pendiente **#19**.

**3. Los datos de contacto no salen.** `Dim_Prospecto` guarda `gmail` y `telefono`; el propósito
táctico es supervisar la cartera, no contactar. Columnas enumeradas y prueba que mira el código,
porque el doble en memoria recorta las columnas él mismo y una prueba contra la respuesta seguiría
pasando con un `SELECT *`.

### El fixture del que depende que este módulo esté probado

`dos_carteras`. **Con una sola cartera poblada, filtrar por ejecutivo y no filtrar devuelven lo
mismo**, así que toda prueba de acotamiento pasa aunque el acotamiento no exista. Es el fallo más
fácil de cometer aquí, y por eso los dos gerentes tienen cartera a la vez y de tamaños distintos.

### Defecto preexistente corregido

**El contrato OpenAPI no era YAML válido** — una descripción sin comillas contenía `data: []`,
exactamente el mismo defecto que el del módulo piloto. Ahora hay una prueba que lo carga y compara
la implementación contra él, endpoint por endpoint.

### Lo que se declara y conviene saber

Una página de `demos-activas` **puede devolver menos filas que el `limit` pedido**: el prefiltro por
día trae de más y el refinamiento descarta con precisión de segundo. `has_next` es la autoridad; el
número de filas no lo es. Y `reasignaciones` **no lo ve un gerente** ni acotado a lo suyo: el reparto
de cartera es una decisión sobre él, no una herramienta suya.

**Verificación.** 2193 → **2579** pruebas (+386), mismas 2 omitidas, cero regresiones. La ampliación
de `core/informes/` se comprobó **aditiva** (T011): ni el piloto ni los 19 informes agregados se
movieron.

---

## 2026-08-15 — Piloto de listados tácticos: Cuentas y Clientes (8 endpoints) y la capa transversal

Alcance: `backend/core/informes/` (**nuevo**, 5 módulos), `backend/core/repositories/cuentas_clientes/`
(3 repositorios de informes + constantes canónicas en 3 existentes),
`backend/apps/cuentas_clientes/` (3 servicios, 3 módulos de vistas, `permissions.py`, 8 rutas),
`backend/conftest.py` (doble de Pinot ampliado), 14 ficheros de prueba nuevos,
`specs/002-tactico/Cuentas-Clientes/informes-tacticos-simples/`, `decisiones-pendientes.md` (#18).

**Qué se construyó.** Los 8 listados de OT04, OT17 y OT18, y con ellos **el andamiaje que los siete
departamentos restantes reutilizan**: período con rango opcional, paginación keyset por cursor,
envelope `{data, meta:{pagination, filtros}}`, vista base con las tres validaciones que el contrato
obliga a rechazar en vez de tolerar, y presentación de ausencias.

**El cursor y el `ORDER BY` salen del mismo objeto.** Es la decisión de diseño con más consecuencias:
si divergen, la consulta devuelve la página anterior en vez de la siguiente y el consumidor pagina en
círculos **sin recibir ningún error**. `Cursor` genera ambos, más la cláusula keyset con su
desempate anidado, desde una única declaración de campos.

### Tres correcciones sobre la spec, todas del mismo tipo

La spec citaba **valores literales que no existen en el sistema**. Implementarlos al pie de la letra
no habría fallado: habría devuelto `200` con `data: []` para siempre.

| Dónde | Decía | Es | Efecto de no corregirlo |
|---|---|---|---|
| L6 sesiones | `estadosession = 'Activa'` | `'Inicio sesion'` | Listado vacío permanente |
| L7 credenciales | `estadocredencial = 'Temporal'` | `'Cambio contraseña'` | Listado vacío permanente |
| L3 cuentas (OpenAPI) | `enum [... Suspendido, Baja]` | `Rechazado`, `Dado de baja` | `400` a un filtro correcto |

No es hipotético: `credential_repository.py:14` documenta que **este mismo fallo ya ocurrió** —un
seed escribía `"ACTIVA"` mientras el código comparaba contra `"Activo"`, invalidando la credencial de
todos los usuarios sembrados—. Por eso la corrección no fue cambiar un literal por otro, sino
**centralizar los estados** donde aún eran literales sueltos: `ESTADO_SESION_*` en
`session_repository`, `ESTADO_CLIENTE_*` en `cliente_repository`, y consumirlos desde el informe.

**Y un cuarto caso, de orden.** L7 debía ordenarse por `fecha_solicitud_cambio`, columna que existe
en el esquema y **ningún escritor rellena**. Un cursor sobre una columna siempre ausente no localiza
ninguna fila: la **segunda página** habría fallado, y solo con datos suficientes para que hubiera
segunda página. Se ordena por `fecha_actualizacion`, que lleva el dato y significa lo mismo; el campo
de la respuesta conserva su nombre.

### Lo que el doble en memoria no podía cubrir

`conftest.py` recorta a mano las columnas que cada consulta enumera, así que una prueba que solo
mirase la respuesta seguiría en verde si alguien cambiara una consulta a `SELECT *` —y la contraseña
viajaría contra Pinot real—. Las pruebas de research D7 tienen por eso **dos mitades**: la respuesta
y el texto de las consultas del repositorio.

Del mismo modo, las de centinelas (D3) se verifican contra `_coerce_value` y `core/informes/formato.py`,
no contra el doble, que no coerciona nada. Esa laguna produjo un defecto real durante la
implementación: `dias_transcurridos` convertía el centinela `LONG` en «hace 106.752.011.843 días».
La ausencia la decide ahora un único `marca_ausente`, compartido por la fecha que se muestra y por
los días que se calculan, para que las dos lecturas no puedan discrepar.

### Defectos preexistentes corregidos de paso

- **El contrato OpenAPI no era YAML válido**: una descripción sin comillas contenía `data: []`.
  Ninguna herramienta lo había cargado nunca. Ahora hay una prueba que lo carga y compara la
  implementación contra él, endpoint por endpoint.
- **`fechahorainiciosesion` se sembraba como texto ISO** en 16 sitios, cuando el esquema la declara
  `LONG` epoch-ms y el escritor real escribe epoch-ms. Nadie la leía, así que nadie lo notaba.

### Lo que queda abierto

`transferencias-propiedad` está implementado y verificado, pero
`Fact_HistorialTransferenciaPropiedad` **no la escribe nadie**: la transferencia solo deja rastro en
la auditoría. Contra el stack real ese endpoint devolverá vacío. Es trabajo del módulo operativo
(CU-O15) y está anotado como decisión pendiente **#18**.

**Verificación.** 1673 → **2193** pruebas (+520), mismas 2 omitidas, cero regresiones.
`apps/informes_tacticos` intacto (research D1), que era el guardián del aislamiento del piloto.

---

## 2026-08-14 — Modelo analítico táctico: esquema en estrella implementado

Alcance: `dags/` (7 módulos de dimensión y hecho, 4 flujos nuevos, 15 ficheros de prueba),
`specs/002-tactico/modelo-analitico/`, `specs/002-tactico/Emergencias/informes-tacticos-compuestos/`
(marcado como sustituido), `decisiones-pendientes.md` (#19 y #20).

**Por qué.** El diseño anterior creaba **una tabla y un flujo por informe**. Con ~105 informes
compuestos por delante, eso son ~105 tablas y ~105 flujos, cada uno con su forma de calcular lo mismo
y su oportunidad de discrepar. El modelo en estrella los resuelve con consultas.

**Qué se construyó.** 5 dimensiones y 4 hechos en `tsi_tactico`, cargados por 4 flujos de Airflow.
Los hechos van particionados por mes y la recarga **descarta la partición** en vez de borrar por
condición — que en este almacén es una mutación, y las tres tablas viejas acumulan una por corrida
con ~180 fechas literales cada una.

**El defecto que justificaba el modelo, corregido.** `dim_unidad` guarda una fila por **versión**:
cada despacho apunta a la versión vigente cuando ocurrió, así que cambiar de proveedor ya no
reescribe la historia. El flujo anterior lo reconocía en su propio código («usa el `idcliente`
**actual** […] no un snapshot histórico real»).

**Tres defectos encontrados en los informes que sustituye**, todos verificados con cifras:

1. ⚠️ **Truncamiento silencioso a 10 000 filas.** Dos consultas a Pinot sin `LIMIT` explícito reciben
   el límite por defecto del cliente. La pérdida de señal analizaba **10 000 de 59 045 posiciones**
   (16,9 %) y publicaba el resultado como completo: 714 huecos donde hay 3 942. El rendimiento por
   proveedor veía **10 000 de 19 528 transiciones**: 344 rechazos donde hay 661.
2. **La completitud del índice de calidad no podía dar otra respuesta que `1.0`**: comparaba contra
   nulidad y el origen usa centinelas.
3. **`Fact_NotificacionDespacho` no tiene hora propia de confirmación ni rechazo** y tiene 31 filas
   para 4 314 despachos. Los hitos se tomaron de `Fact_HistorialDespachoUnidad`.

**Validación.** Corriendo la lógica del flujo viejo sobre datos completos salen exactamente las
cifras del modelo (3 942 huecos, 661 rechazos, 331 abortos), y el tiempo medio de llegada coincide
al centésimo: **669.44 s**. Suite de `dags/`: **151 pasan**. Backend: **1 673 pasan, 2 omitidas**,
sin movimiento — este módulo solo lee el sistema operativo.

**Lo que NO se retiró, y por qué.** Las tres tablas y sus flujos siguen vivos: tres repositorios del
backend los leen, y dejar de refrescarlos mientras los endpoints siguen consultándolos serviría datos
congelados sin error visible. Registrado como decisión pendiente #20.

---

## 2026-08-14 — Autoridades departamentales: catálogo de roles y constantes

Alcance: `backend/scripts/_demo_seed_common.py`, `backend/core/auth/roles_tacticos.py`,
`.specify/docs/actors.md`, `.specify/docs/architecture/architectural-patterns.md`,
`specs/002-tactico/` (contrato común, `acceso-tactico.md` y las 7 specs de módulo).

**Por qué.** Los informes tácticos especificados en `specs/002-tactico/` asignaban permisos
solo a roles operativos. Al revisar el §5.1 del SRS —que define, por departamento, un
responsable operativo y una autoridad superior— se comprobó que **seis de las ocho
autoridades no existían como rol del sistema**, y que `actors.md` las documentaba en una
sección marcada como fuera de alcance.

**Roles añadidos al catálogo** (`ROLES_DEMO`, fuente única de `Dim_Rol`): `DirectorMarketing`
(17), `DirectorFinanciero` (18), `DirectorExpansion` (19), `DirectorOperaciones` (20),
`GerenteExitoCliente` (21) y `DirectorDatos` (22). `DirectorTecnologico` (6) y
`DirectorEstrategia` (14) ya existían y suman autoridad táctica sin perder su papel
operativo.

**Defecto latente corregido de paso.** `GerenteCuentasPublicas` **estaba referenciado por
código de producción en cuatro sitios de `apps/ventas_crm`** —entre ellos la asignación
automática, que enruta los prospectos del sector público a ese rol— y **no existía en el
catálogo**. Ningún usuario podía tenerlo, así que esos prospectos se quedaban sin ejecutivo
candidato. Añadido como idrol 16.

**Constantes.** Nuevo `backend/core/auth/roles_tacticos.py`, transversal en vez de duplicado
en siete `permissions.py`: dos departamentos comparten `DirectorTecnologico`, y repetir la
cadena en siete sitios es como aparecen las divergencias de un carácter que nadie detecta
hasta que un permiso deja de conceder. Expone conjuntos **por materia**, no por
departamento, porque el SRS advierte que la autoridad «no siempre es una jefatura única»:
en Suscripciones y Red Operativa está repartida, y en Cuentas y Clientes alcanza a un solo
listado.

**Dos discrepancias documentales resueltas** a favor del SRS, según lo decidido: `actors.md`
asignaba Ventas y CRM a un «Director Comercial» que ese mismo documento había introducido
—el §5.1 dice Director de Marketing—, y Cuentas y Clientes al Gerente de Éxito del Cliente
—el §5.1 dice Director Tecnológico, y **solo sobre la capa de accesos técnicos**—. El rol
`Director Comercial` queda retirado.

**Hallazgo anotado, no resuelto.** Cuentas y Clientes **no tiene autoridad de negocio**: la
única que el §5.1 le asigna es el Director Tecnológico con alcance limitado. Sus siete
listados restantes quedan bajo el Administrador, que es a la vez su responsable operativo.
Puede ser intencional o faltar un cargo; queda en `decisiones-pendientes.md`.

**Límite que se dejó explícito en código y en spec.** La autoridad accede **sin el
acotamiento por titularidad**, pero esa exención **no alcanza al dato sensible**:
coordenadas, identidad de personas implicadas, secretos de autenticación y medios de cobro
siguen excluidos de todo informe para todos los roles. Son exclusiones constitucionales, no
de acotamiento.

**Verificación.** `python -m pytest` → **1673 passed, 2 skipped**, idéntico a la línea base:
el catálogo crece de 14 a 21 roles sin identificadores ni nombres duplicados, sin reutilizar
el idrol 11 (obsoleto), y sin que ninguna suite existente se mueva. Los conjuntos de
autoridad y el predicado `es_autoridad` verificados por separado.

**Pendiente.** Ningún usuario de demo tiene todavía los roles nuevos. Sembrarlos entra con
la implementación de los informes, que es cuando habrá algo que puedan consultar.

---

## 2026-08-01 — Revisión `002-tactico` (spec vs. docs globales)

Alcance: `specs/002-tactico/`, `.specify/docs/infra/infrastructure.md`

**T1** — `spec.md` no declaraba las 9 características ISO/IEC 25010 ni trazabilidad OT (solo el `plan.md` lo hacía). Corregido: sección Constitution Compliance + enlace a `informestacticos/auditoria-esquemas-informes-v2.md`; FR-011 (ClickHouse/Postgres Airflow ≠ almacén de dominio).

**T2** — `infrastructure.md` §1 afirmaba “infraestructura de datos única / no se usa PostgreSQL” de forma absoluta, en tensión con el stack `tactico` ya documentado en §2.1. Reformulado: Kafka+Pinot = canal único del *modelo dimensional*; Postgres de Airflow = solo metastore. Encabezado §5 actualizado (ya no dice “no implementar todavía” mientras §5.1 está activo). Regla vinculante §4 añadida sobre ClickHouse/Postgres.

**T3** — Todo el feature vive bajo `specs/002-tactico/infraestructura/` (`spec.md`, plan, research, data-model, contracts, quickstart, tasks, índice). `feature.json` apunta a esa carpeta. Se eliminó `checklists/` (gate de `/specify` ya cumplido; no aporta valor operativo tras plan/tasks cerrados).

**T4** — Variable `CLICKHOUSE_DB` (default `tsi_tactico`; no `TSI-tactico` — el guion no es válido como identificador ClickHouse sin comillas). Init en `docker/tactico/clickhouse-init/`; documentado en contrato, quickstart y `.env.tactico.example`.

---

## 2026-07-15 — Módulo Emergencias (revisión spec vs. implementación)

Alcance: `despacho-inteligente`, `evidencia-unidad`, `registro-accidente`, `seguimiento-cierre-de-casos`

> Nota: el `git status` del repo también mostraba otros archivos modificados/sin trackear que
> **no** correspondían a este trabajo (cambios previos ya en curso antes de esta sesión,
> p. ej. `confirmar_despacho_service.py`, `mi_seguimiento_views.py`, extracción de templates
> `.html`, etc.). Esta entrada solo cubre lo hecho en esa sesión.

### Backend

**G1 (CRITICAL) — Jobs periódicos sin agendar.**
`run_timeout_despacho_job`, `run_gps_senal_perdida_job` y el job de depuración GPS existían
pero nadie los invocaba (no había Celery/APScheduler ni cron configurado). Se agregaron
management commands de Django (patrón `send_onboarding_reminders.py`):
`backend/apps/despacho/management/commands/run_timeout_despacho_job.py`,
`backend/apps/seguimiento/management/commands/run_gps_senal_perdida_job.py`,
`backend/apps/seguimiento/management/commands/run_gps_depuracion_job.py`.
**Pendiente:** decidir invocación en producción (cron, worker separado, Celery beat).

**G2 (HIGH) — Estado de unidad forzado a "Activa" al liberar despacho.**
Al retirar o abortar un despacho, la unidad siempre volvía a `Activa`, ignorando
`Fuera de servicio` (RN-SEG-003 no implementada). Corregido en
`backend/apps/seguimiento/services/retiro_despacho_service.py` y
`backend/apps/seguimiento/services/abortar_mision_service.py` (consultan estado actual
antes de liberar; `cerrar_caso_service.py`/`forzar_retiro_service.py` heredan el fix vía
`RetiroDespachoService`).

**G4 (HIGH) — Mensaje de error genérico en registro de accidente.**
`AccidenteListCreateView.post` respondía siempre `"duplicado_posible"` ante un
`DuplicateConflictError`, aun cuando la advertencia real era `fuera_cobertura`. Corregido
en `backend/apps/accidentes/views/accidente_views.py` (usa `advertencias[0]` real, expone
el arreglo completo).

**G5 (HIGH) — Scoring de "disponibilidad reciente" hardcodeado.**
En `consulta_candidatas_service.py`, el 15% del score de RN-DES-008 era constante
(`disp_score = 0.5`). Se agregó `_disponibilidad_reciente_score()` (score real por tiempo
continuo en estado `Activa`, tope 30 min).

**G6 (MEDIUM) — Selección de accidente "padre" en fusión usa campo incorrecto.**
`ValidacionAccidenteService.suggest_parent_id` usaba `fechahoraaccidente` en vez del
`fechahoramodificado` de la primera transición a `BORRADOR`/`REPORTADO`
(`Fact_AccidenteTipoEstadoAccidente`), per RN-REG-010b. Corregido en
`backend/apps/accidentes/services/validacion_accidente_service.py` (fallback a
`fechahoraaccidente` si no hay historial).

**G9 — Verificado sin cambios.** `registrar_posicion_gps_service.py` sí invoca
`RegistrarLlegadaService` automáticamente vía geofencing (RF-SEG-002) — falso positivo del
análisis previo.

### Frontend

**G3 (HIGH) — Auto-sync de evidencias nunca se activaba.**
`EvidenciaSyncSchedulerService.iniciarAutoSync()` existía pero no se llamaba desde ningún
lado — código muerto. Corregido: nuevo `listarIdsAccidentesPendientes()` en
`evidencia-offline-store.service.ts`; `sincronizarTodosLosCasos()` ahora usa la unión de
casos en sesión + pendientes reales en IndexedDB; `app.component.ts` invoca
`iniciarAutoSync()` en el constructor (corre durante toda la vida de la app).

**Bug preexistente (detectado al verificar G4 en el frontend) — Manejo del conflicto
409 roto.** `registro-accidente.page.ts` leía `err.error` en vez de `err.error.data`
(envoltura `{data, meta}`) y usaba `idaccidente_duplicado_sugerido` (siempre `null`) en
vez de `idaccidente_similar`. Resultado real: el diálogo de "posible duplicado" nunca se
abría y la fusión nunca funcionaba. Corregido en
`frontend/src/app/modules/accidentes/pages/registro-accidente/registro-accidente.page.ts`;
se agregó manejo explícito de `error === 'fuera_cobertura'`. Tests actualizados en
`registro-accidente.page.spec.ts`.

### Verificación realizada

- Backend: `pytest apps/despacho apps/accidentes apps/seguimiento` → 285/285 tests.
- Frontend: `tsc --noEmit` (app + spec) sin errores. (Karma/Jasmine no se pudo correr por
  falta de Chrome en el entorno; recomendado correr `ng test` localmente.)
- Docker: `docker compose -f accidentes.yml build` exitoso.

### Pendientes / fuera de alcance

- **G7** — Notificaciones push/SMS en despacho son stubs (`_default_push`/`_default_sms`
  siempre "exitosos"); requiere integración real con un proveedor.
- **G8** — Payload estructurado de alerta crítica hacia monitoreo (RF-DES-008) no
  confirmado a fondo.
- **G10 / T108** — No existe endpoint de reversión (undo) para descarte/fusión de
  accidentes; decisión de alcance pendiente. Ver `registro-accidente/tasks.md` T108.

---

## 2026-07-16 — Regularización de contrato para proxy de ruta OSRM

Alcance: `seguimiento-cierre-de-casos`

El endpoint `GET /api/v1/seguimiento/ruta` (`backend/apps/seguimiento/views/ruta_views.py`,
`core/osrm/client.py`) se implementó junto con el trabajo del 2026-07-15 pero no se agregó
al contrato OpenAPI ni a `tasks.md` en su momento (violación Principio VI — API-First).
Regularizado: contrato agregado en
`contracts/seguimiento-cierre-de-casos.openapi.yaml` (`/seguimiento/ruta`), tarea T042b y
fila CA-SEG-002b en `traceability.md`.

---

## 2026-07-31 — Auditoría de suites, paginación en Pinot e higiene de datos

Alcance: `registro-accidente`, `seguimiento-cierre-de-casos`, `evidencia-unidad`,
`despacho-inteligente`, `Red-Operativa/alta-unidades`, `Suscripciones-Facturacion`,
`Cuentas-Clientes`, infraestructura de datos (`database/`).

Origen: ejecución completa de las suites unitarias y recorrido end-to-end del sistema
contra el stack real (Kafka + Pinot + Django + Angular), no un ciclo `/plan`→`/tasks`.

### Infraestructura de datos

**D1 (CRITICAL) — Pinot recortaba en silencio toda consulta sin `LIMIT`.**
Pinot aplica un `LIMIT 10` implícito cuando la consulta no declara uno, y la respuesta no
distingue "hay 10 filas" de "hay 10 de 500". 31 consultas del repositorio no declaraban
tope, así que los repositorios filtraban y paginaban en Python sobre un recorte arbitrario
(sin `ORDER BY`, ni siquiera estable entre llamadas). Efecto verificado en el entorno real:
con 13 accidentes activos el listado mostraba 10, y filtrar por severidad operaba sobre ese
recorte. Corregido en `backend/core/pinot/client.py`: `PinotClient.query` añade un tope
explícito (`DEFAULT_QUERY_LIMIT`) cuando el SQL no trae uno, respetando los `LIMIT` propios.
Regresión en `backend/tests/regression/test_pinot_client_limit.py`.

**D2 (HIGH) — `Dim_Usuario_Cliente` y `Dim_CondadoVecino` no existían.**
Ambas se consultaban desde código productivo pero no estaban declaradas en
`database/esquemas.json` ni creadas en Pinot (`TableDoesNotExistError`).
`GET /api/v1/cliente/expedientes` respondía **500** y CU-O34 (escalamiento a condados
vecinos) fallaba al buscar adyacencias. Declaradas en `database/esquemas.json` y
`database/tablas.json`, sembradas por `database/seed_vinculos.py`.
**Causa de que los tests no lo detectaran:** el doble en memoria de `conftest.py` sí tenía
ambas tablas — el doble era más completo que la base real.

**D3 (MEDIUM) — `seed_soporte.py` publicaba `Dim_Usuario_Cliente` sin su clave primaria.**
El registro entraba con el centinela de nulo de INT y convivía como fila huérfana junto al
vínculo real. Corregido; `database/seed_flota_demo.py` retira las filas ya escritas así.

### Backend

**B1 (HIGH) — Paginación real en SQL en lugar de recorte en memoria.**
`AccidenteRepository.list_activos` traía la tabla y filtraba en Python. Reescrito para que
filtros, orden y tope viajen en el SQL, con paginación keyset por `idaccidente` y
`(filas, cursor_siguiente)` como retorno. `ConsultaAccidenteService.listar` encadena
páginas acotadas solo cuando el filtro por estado (que vive en otra tabla) deja la página
corta, con techo `MAX_PAGINAS_ENCADENADAS`. `HistorialEmergenciasService` lee por bloques
(`_leer_accidentes`) en vez de `SELECT * FROM Fact_Accidente`; además ordenaba por
`horainicio` mientras paginaba por `idaccidente`, lo que dejaba huecos entre páginas —
ahora ambas usan la misma clave. `GET /api/v1/accidentes` expone
`meta.pagination.next_cursor` y acepta `cursor`. Único escaneo amplio que se conserva:
`find_nearby` (agrupación de duplicados), acotado ahora por ventana temporal en el SQL.

**B2 (HIGH) — Rollback silencioso en importación de lote de unidades.**
`importacion_lote_unidad_service.importar` compensaba con
`unidad_repo.update(id, {"activo": False})` sin `base`, lo que releía de Pinot un registro
recién escrito por Kafka y todavía no ingerido; `update()` devolvía `None` en silencio y el
rollback no hacía nada. Dejó en la base 6 unidades activas apuntando a un `idusuario` que
nunca se persistió (no pueden iniciar sesión: CU-O30 `find_by_usuario`). Corregido pasando
el registro creado como `base`. Regresión:
`test_importar_when_credencial_falla_y_pinot_aun_no_ingirio_igual_revierte`.

**B3 (HIGH) — Filtro de flota por tipo de unidad siempre vacío.**
`UnidadEmergenciaRepository.list_active` filtraba por `idtipounidad`, columna que no existe
en `Dim_UnidadEmergencia` (la real es `tipounidademergencia`, texto). Cualquier filtro por
tipo devolvía cero unidades. Corregido en repositorio, servicio y vista; el endpoint acepta
`tipo` y mantiene `idtipounidad` como alias. La respuesta ahora expone
`tipounidademergencia` y `placa`.

**B4 (MEDIUM) — `idaccidente_duplicado_sugerido` retirado del contrato 409.**
El backend lo emitía siempre `null` y el frontend nunca lo usaba (fusiona sobre
`idaccidente_similar`, el reporte ya registrado; el duplicado rechazado por el 409 nunca
llegó a crearse). Retirado de `accidente_views.py`, del OpenAPI de `registro-accidente` y
del `spec.md` correspondiente.

**B5 (MEDIUM) — Motivo ilegible al sincronizar evidencia offline.**
`SincronizarEvidenciaService` capturaba `KeyError` y reportaba al técnico el nombre crudo
de la clave (`'estadoimplicado'`). Se agregó `_exigir_campos`, que nombra qué falta y en
cuál ítem local.

### Frontend

**F1 (HIGH) — «Mis expedientes» llevaba a una página de detalle sin `idaccidente`.**
`nav-links.ts` apuntaba a `/seguimiento/expedientes`, que cargaba `DetalleExpedientePage`
(un stub) sin parámetro: renderizaba un encabezado vacío y no pedía nada. Se creó
`ListaExpedientesPage` (listado con los tres estados, paginación por cursor y acción `eye`)
y se implementó `DetalleExpedientePage` con el chrome de workpanel del golden sample.

**F2 (MEDIUM) — La ruta `/` ignoraba la sesión.**
Redirigía siempre al portal comercial público, así que un usuario autenticado que escribía
la URL base veía "Iniciar sesión / Registrarme". Nuevo `landingRedirectGuard` que resuelve
al home del rol (misma función `homePathForRoles` que usa el login).

**F3 (MEDIUM) — `plan-detalle` fingía solo lectura con `input disabled readonly`.**
Prohibido explícitamente por el design-system, sección 5 ("en modo Ver, datos como `dl`…
nunca `input disabled`"). Reescrito al chrome del golden sample: «Volver a la lista» con
`arrow-left`, eyebrow de modo, `h1` + badge en la misma fila y datos en `dl` con `dt`
uppercase.

**F4 (LOW) — Homogeneización de estados asíncronos.**
`validacion.page.ts` mostraba la tabla de historial solo si había datos: sin skeleton, sin
error y sin vacío — "todavía no se pidió" y "vino vacío" se veían igual. Migrado a los
componentes canónicos `app-list-*`. Se homogeneizó `data-testid="error"` →
`data-testid="error-state"` en `evidencia-unidad`. Se agregó `download` al set Tabler
(`tabler-icon.component.ts`) en vez de introducir un ícono fuera del set único del sistema.

**F5 (LOW) — Paginación visible en la lista de accidentes.**
La lista pedía 20 registros y no ofrecía avanzar. Se agregó el paginador Anterior/Siguiente
con la misma convención que `catalogo-planes`
(`btn-pagina-anterior`/`btn-pagina-siguiente`), apoyado en el cursor real del backend;
cambiar un filtro reinicia la paginación.

### Suites de prueba

- **La suite backend no arrancaba**: `apps/accidentes/` no tenía `__init__.py`, así que
  pytest nombraba `apps/accidentes/tests/` como el módulo top-level `tests` y su
  `conftest.py` como el `conftest` raíz — 16 módulos fallaban al importar `PINOT_STORE` y
  la sesión se interrumpía por errores de colección. Agregados los `__init__.py` faltantes.
- `pytest.ini` tenía `testpaths = apps`, así que `backend/tests/` (incluida la regresión de
  la cadena crítica) nunca se ejecutaba. Ahora `testpaths = apps tests`.
- Los contadores de throttling de DRF persistían entre tests (viven en el caché de Django);
  un test que agotaba un scope hacía fallar con 429 a los posteriores según el orden de
  colección. Nuevo fixture autouse `reset_throttle_history` en `conftest.py`.
- El doble de Pinot se actualizó para honrar los predicados nuevos (filtros, cursor, orden
  y `LIMIT` de accidentes y flota). Sin eso los tests dejaban de medir lo que hace Pinot.

### Higiene de datos (entorno demo)

`database/higiene_datos.py` (idempotente, con `--dry-run`): desactiva unidades de prueba de
humo y unidades huérfanas (residuo de B2), consolida el rol `Unidad` duplicado (idrol 4 y 7
→ 4; los permisos se evalúan por nombre, así que el acceso no cambia) y sanea descripciones
de accidente con contenido ofensivo cargado como dato de prueba.
`database/seed_flota_demo.py` repone una flota mínima consistente (una unidad por usuario
con rol Unidad, correctamente ligada) y retira los vínculos usuario-cliente con clave
centinela.

### Verificación realizada

- Backend: `pytest` → 901 pasan, 2 skipped (antes: la suite no arrancaba).
- Frontend: `ng test` → 312 pasan (antes: 285 pasaban, 9 fallaban).
- Recorrido end-to-end contra el stack real: 34/34 pasos, incluido el recorrido paginado
  completo (13 filas en 5 páginas, sin repetidos ni faltantes) y los controles de acceso.

---

## 2026-07-31 (2) — Acceso denegado, unificación de credenciales y paginación de históricos

Alcance: `Cuentas-Clientes`, `despacho-inteligente`, `seguimiento-cierre-de-casos`,
infraestructura de datos y seeds (`database/`, `backend/scripts/`).

Continuación de la entrada anterior, sobre las dudas que quedaron abiertas allí.

### Frontend

**F6 (HIGH) — Ruta `access-denied` inexistente: 28 guards caían al portal público.**
Todos los guards de rol redirigen a `/cuentas-clientes/auth/access-denied` cuando la
sesión es válida pero el rol no alcanza. Esa ruta nunca se declaró, así que el
wildcard `**` capturaba la navegación y llevaba al portal comercial, donde el usuario
veía "Iniciar sesión / Registrarme" y parecía que se le había caído la sesión.
Creada `AccessDeniedPage` y registrada **dentro del shell autenticado**, para que el
usuario conserve su navegación: muestra la sesión vigente (correo + roles) y un CTA
«Volver a mi inicio» que resuelve con `homePathForRoles`, la misma función del login.
Los guards no se tocaron: estaban bien, faltaba el destino.

### Backend

**B6 (HIGH) — `get_current_estado` decidía el estado de una unidad sobre 10 filas.**
`HistorialEstadoUnidadRepository.list_by_unidad` traía sin `LIMIT`, ordenaba en Python
y devolvía el primero. Con el recorte implícito de Pinot (ver D1), el estado vigente
de una unidad se calculaba sobre 10 filas arbitrarias de su historial: una unidad con
más de 10 cambios de estado podía reportar uno viejo y quedar mal clasificada para
despacho. Orden, cursor y tope ahora van en el SQL.

**B7 (MEDIUM) — Traza GPS sin paginación.**
`Dim_HistorialUbicacionUnidadEmergencia` es la tabla que más rápido crece (una posición
cada ~10 s por unidad en misión ≈ 2.900 filas por jornada). `list_by_unidad` la leía
entera y sin tope, así que Pinot devolvía 10 puntos: el job de depuración GPS decidía
qué conservar mirando solo los 10 primeros, y la histéresis de geofence evaluaba la
llegada con una traza truncada. Ahora `list_by_unidad` pagina por keyset con ventana
temporal en el SQL, y `iter_by_unidad` recorre la traza completa por bloques para los
consumidores que sí la necesitan (`gps_depuracion_service`, `registrar_posicion_gps_service`).

**B8 (MEDIUM) — `estadocredencial` unificado a "Activo".**
Convivían "ACTIVA" (seeds) y "Activo" (código). El login no lo notaba porque solo
bloquea "Inactivo", pero `onboarding_service` exige `== "Activo"` y por tanto rechazaba
la credencial de **todos** los usuarios sembrados. Valores canónicos centralizados en
`credential_repository.py` (`ESTADO_CREDENCIAL_ACTIVO/INACTIVO/CAMBIO_PASSWORD`),
literales sueltos reemplazados en servicios y seeds, y las 12 filas ya escritas
migradas con `database/migra_estadocredencial.py`.

### Seeds y datos demo

**S1 (HIGH) — Dos convenciones de contraseña y un fixture E2E apuntando a la nada.**
`database/seed_usuarios.py` sembraba "Demo1234!" y `backend/scripts/*` "password123":
la misma cuenta pedía una u otra según cuál hubiera corrido último. Además
`e2e/fixtures/auth.fixture.ts` usaba cuentas `@tsi.com` tomadas de `backend/conftest.py`
—fixtures en memoria de los tests unitarios— que no existen en ningún entorno real, así
que todos los tests de Playwright fallaban en el login. Nuevo módulo compartido
`backend/scripts/_demo_seed_common.py` (`DEMO_PASSWORD`, `ESTADO_CREDENCIAL_ACTIVO`,
`DEMO_DOMAIN`), consumido por todos los seeds; fixture E2E reescrito con las 10 cuentas
reales y la contraseña como constante. Verificado: 10/10 autentican.

**S2 (HIGH) — Catálogos de roles superpuestos entre seeds.**
`database/seed_usuarios.py` definía idrol 4 = "Operador" y `seed_demo_usuarios_roles.py`
creaba otro "Operador" en idrol 11. Como `Dim_Rol` es upsert por clave primaria, el
segundo seed no agregaba: renombraba el rol de los usuarios ya vinculados al id que
pisara. De ahí el rol `Unidad` duplicado que la higiene consolidó y que reaparecía en
cada re-seed. Catálogo canónico único en `_demo_seed_common.ROLES_DEMO` + búsqueda
inversa `ROL_ID_POR_NOMBRE`; ambos seeds lo consumen.

**S3 (HIGH) — `seed_demo_director_estrategia.py` sobrescribía al Gerente de Ventas.**
Hardcodeaba `USER_ID = ROLE_ID = CRED_ID = 12` y `USER_ROLE_ID = 31`, exactamente los
del Gerente de Ventas. Correrlo **borraba** `lucia.ramos.ventas`. Detectado en vivo al
ejecutarlo; usuario restaurado y el script pasa a asignar ids libres con `_siguiente_id`.

**S4 (MEDIUM) — Flota ligada a usuarios por id fijo.**
`seed_flota_demo.py` asignaba la unidad 2 a `idusuario=4`, asumiendo que ese usuario
tenía rol Unidad. Al unificar el catálogo de roles, el usuario 4 pasó a ser Operador y
la unidad quedó ligada a alguien que no puede iniciar sesión como unidad (CU-O30
`find_by_usuario` → 403 en `mi-despacho`). Ahora la flota se liga a los usuarios que
**realmente** tienen rol Unidad, resueltos por nombre de rol; se agregó un segundo
usuario Unidad al catálogo demo (`marco.silva.unidad`) para que el despacho pueda
demostrar selección de candidata y escalamiento de zona.

**S5 (MEDIUM) — `Dim_Preferencias_Cliente` vacía.**
`zonas_geograficas` define sobre qué condados el cliente ve expedientes (RN-SEG-005);
sin la fila, el filtro resolvía a cero condados y "Mis expedientes" salía vacío aunque
hubiera casos cerrados. Sembrada en `database/seed_vinculos.py`.

### Tests de infraestructura nuevos

- `tests/regression/test_doble_pinot_vs_esquemas.py` — compara el doble en memoria de
  `conftest.py` contra `database/esquemas.json` en ambos sentidos, y verifica que toda
  tabla consultada por código productivo esté declarada. Habría detectado D2 con el
  mensaje exacto (verificado quitando las dos tablas del esquema).
- `tests/regression/test_credenciales_demo_consistentes.py` — impide que vuelvan a
  divergir la contraseña demo, el valor de `estadocredencial`, el catálogo de roles y
  las cuentas del fixture E2E.

### Verificación realizada

- Backend: `pytest` → 912 pasan, 2 skipped.
- Frontend: `ng test` → 316 pasan.
- Recorrido end-to-end contra el stack real: **42/42 pasos**, incluyendo despacho manual
  creado sobre la candidata que ofrece el sistema, detección de duplicados devolviendo el
  caso similar, y los 12 usuarios demo autenticando con una sola contraseña.
- Navegador: página de acceso denegado conserva la navegación y muestra la sesión;
  «Mis expedientes» lista un expediente real y su detalle renderiza en `<dl>` sin inputs.

---

## 2026-07-31 (3) — Escalamiento de zona demostrable, evidencia paginada y limpieza de datos demo

Alcance: `evidencia-unidad` (backend), infraestructura de datos y seeds (`database/`,
`backend/scripts/`).

Cierra las dudas de la entrada anterior.

### Backend

**B9 (MEDIUM) — Galería de evidencias con el mismo bug de clase D1.**
`EvidenciaFotoRepository.list_by_accidente` traía `SELECT * FROM Dim_EvidenciaFoto
WHERE idaccidente = ...` sin `LIMIT`, y filtraba `sincronizado`, ordenaba y paginaba
en Python **después**. Pinot recortaba a 10 filas antes de que ese filtro se aplicara:
un accidente con más de 10 fotos podía perder evidencia real de la galería sin error
visible. Filtro, orden y tope ahora viajan en el SQL. Regresión con 15 fotos
verificando que las 15 aparecen, más un recorrido paginado sin repetidos ni faltantes.

### Datos demo

**S6 — `rename_demo_unidad_gmail.py` eliminado.**
Era un one-shot que renombraba `diego.ramirez.operador@demo.tsi.com` →
`...unidad@demo.tsi.com`, contradiciendo el catálogo canónico donde el usuario 4 es
Operador. Sin referencias en el resto del repo.

**S7 — Tercera unidad y condado vecino con flota propia.**
El condado 2 (Benito Juárez) existía solo en `Dim_CondadoVecino` como adyacencia, sin
`Dim_Condado`/`Dim_Ciudad`/`Dim_Calle` propios ni unidades: todo escalamiento CU-O34
resolvía "sin unidades disponibles" aunque la consulta de adyacencia funcionara.
Agregados en `database/seed_catalogos.py` (condado, ciudad y calle de Benito Juárez) y
`database/seed_usuarios.py` (tercer usuario `valeria.cortes.unidad@demo.tsi.com`,
rol Unidad). `seed_flota_demo.py` ahora liga cada unidad a su `idcondado` propio y
resuelve los usuarios **por nombre de rol**, no por id fijo — antes asumía que
`idusuario=4` tenía rol Unidad; al unificar el catálogo de roles (ver S2 en la entrada
anterior) ese usuario pasó a ser Operador y la unidad quedaba huérfana.

Verificado end-to-end: con la flota del condado 1 agotada, escalar a zona (CU-O34)
encuentra y asigna la unidad 3 en Benito Juárez (`origen: "Escalado_zona"`), en vez de
reportar siempre "sin unidades en condados vecinos".

**S8 — `database/reset_despachos_demo.py` (nuevo).**
Cada corrida de flujo end-to-end deja despachos activos y unidades `Ocupada`/`En
Misión`; con una flota de 2-3 unidades eso agota las candidatas disponibles en pocas
corridas. El script libera los despachos activos y devuelve las unidades a `Activa`
sin tocar el estado del caso (`Fact_Accidente`) — no reemplaza un cierre real, es
mantenimiento de la flota demo. Idempotente, acepta `--dry-run`.

### Verificación realizada

- Backend: `pytest` → 914 pasan, 2 skipped.
- Frontend: `ng test` → 316 pasan (sin cambios en esta entrada).
- Recorrido end-to-end contra el stack real: **45/45 pasos**, incluyendo el camino
  completo de CU-O34 (condado local agotado → escalamiento → asignación exitosa en
  el condado vecino), verificado también en el navegador (Monitoreo de despacho
  muestra el caso escalado).

---

## 2026-08-01 — Homogeneización de estados loading/error/vacío en el frontend

Alcance: `despacho-inteligente`, `evidencia-unidad`, `seguimiento-cierre-de-casos`,
`Soporte-Cliente`, `Suscripciones-Facturacion` (frontend), `.specify/docs/design/design-system.md`.

Refactor de mantenibilidad, no corrección de bug ni de diseño: las páginas afectadas ya
cumplían el design-system (mostraban los 3 estados no felices correctamente), pero cada
una reimplementaba el mismo HTML que `app-list-loading-skeleton` / `app-list-error-state` /
`app-list-empty-state` ya encapsulan — visualmente indistinguible del golden sample, con
el costo de tener el mismo patrón duplicado en ~10 archivos.

### Migradas a los componentes compartidos

| Página | Loading | Error | Vacío |
|---|---|---|---|
| `despacho/mi-despacho` | ✓ | ✓ | ✓ |
| `despacho/monitoreo-despacho` | ✓ | ✓ | — (detalle, no aplica) |
| `evidencia-unidad/panel-disponibilidad` | ✓ | ✓ | — (detalle, no aplica) |
| `seguimiento/historial-emergencias` | ✓ | ✓ | ✓ |
| `seguimiento/mi-seguimiento` | ✓ | ✓ | ✓ |
| `soporte-cliente/detalle-ticket` | ✓ | — (sin error propio) | — |
| `soporte-cliente/mis-tickets` | ✓ | — (usa toast, no bloque) | ✓ |
| `suscripciones/plan-form` | ✓ | — (error de guardado sin retry, se deja inline) | — |
| `evidencia-unidad/galeria-evidencias` | — | — (semántica `alerta-media`, no crítica) | ✓ (con CTA proyectado) |
| `soporte-cliente/cola-agente` | — (skeleton de master-detail, forma propia) | — (banner persistente, no bloque) | ✓ |

Todos los `data-testid` (`loading-skeleton`, `error-state`, `empty-state`,
`btn-reintentar-lista`) se mantuvieron idénticos: **ningún spec de contrato de UI ni test
existente requirió cambios**, la migración es puramente de implementación.

### Deliberadamente dejadas sin migrar

- **`soporte-cliente/dashboard-soporte`** — grid de KPIs (design-system distingue
  "bloques de KPIs con ring charts" de listados; el skeleton de filas no representa la
  forma de una card de métrica).
- **`suscripciones/mi-suscripcion`** — tarjeta resumen con título propio
  ("No pudimos cargar tu suscripción") + descripción; el componente compartido es de una
  sola línea de mensaje, forzar el título ahí perdería información.
- **`cuentas-clientes/incorporacion-clientes/aprobacion-solicitudes`** — usa `@empty` de
  Angular dentro de una lista corta (una fila de texto), no un bloque de página completo.
- **`cuentas-clientes/auth/login`, `ventas-crm/registro-publico`** — falsos positivos de
  la búsqueda inicial: el `animate-pulse` detectado es el punto de estado "En vivo" del
  header, no un skeleton de carga.
- Errores con tono `alerta-media`/banner persistente en vez de bloque con "Reintentar"
  (`galeria-evidencias`, `cola-agente`, `dashboard-soporte`) se dejan inline: forzarlos al
  componente compartido cambiaría su severidad semántica (crítico vs. advertencia) o su
  patrón de interacción (bloqueante vs. banner conviviendo con datos).

### Regla añadida al design-system

Sección "Estados de carga, vacío y error": los componentes compartidos son la
implementación obligatoria para cualquier página con estos tres estados, no solo listados
Ver-only; reproducir el patrón con HTML propio solo se justifica cuando la forma del
contenido difiere genuinamente (KPIs, resumen con título) o el error no tiene una acción
de "Reintentar" con sentido.

### Verificación realizada

- Frontend: `ng test` → 316 pasan (sin cambios en el conteo — la migración no tocó ningún
  test, todos los `data-testid` se preservaron).
- `ng build` de producción sin errores nuevos.
- Recorrido end-to-end contra el stack real: 45/45 pasos.
- Navegador: `mis-tickets` (8 tickets, sin loading colgado), `mi-suscripcion` (renderiza
  sin errores) verificados tras el despliegue.

---

## 2026-08-02 — Limitaciones conocidas de los informes tácticos compuestos (`002-tactico`)

Alcance: `specs/002-tactico/Emergencias/informes-tacticos-compuestos/`, hallazgos de la
revisión final contra el stack real. No son bugs — son decisiones de diseño forzadas por
huecos del esquema actual, documentadas aquí para no volver a proponerlas sin este
contexto (una ya se resolvió, ver entrada de más abajo).

**L1 — Semántica de `materializado` en los 3 informes compuestos.** Los DAGs
(`perdida_senal_gps`, `indice_calidad_historico`, `rendimiento_por_proveedor`) reprocesan
el histórico completo en cada corrida, no una ventana incremental. Consecuencia: una vez
que un DAG corrió al menos una vez, `materializado` es `true` para *cualquier* período
consultado (incluso uno futuro sin datos) — la ausencia de filas para ese rango se lee
como "sin eventos en ese período", no como "el DAG no lo ha procesado todavía". Si en el
futuro se necesita una ventana incremental (por volumen de datos), esta semántica cambia
y hace falta una lógica de "no materializado" por período explícita (ej. una tabla de
control de corridas por rango de fechas). No es necesario hoy — el volumen de datos del
proyecto no lo justifica.

**L2 — `rendimiento_por_proveedor` usa el proveedor *actual* de cada unidad, no el
histórico.** `Dim_UnidadEmergencia.idcliente` no tiene versión histórica (sin tabla tipo
SCD) — el DAG no puede saber qué proveedor operaba una unidad en el momento de un
despacho pasado si esa unidad cambió de proveedor después. Si el negocio necesita
atribución histórica correcta de rendimiento por proveedor (ej. para negociar contratos
según desempeño pasado), hace falta una tabla nueva `Fact_HistorialProveedorUnidad` (o
similar) que registre cada cambio de `idcliente` por unidad con su vigencia — no
implementada, es un cambio de esquema más grande que L3 (tabla nueva completa vs. un
campo en tabla existente).

**L3 — `idusuario` en `Fact_HistorialDespachoUnidad` — RESUELTO 2026-08-02.** Ver la
sección "Campo `idusuario` en `Fact_HistorialDespachoUnidad`" más abajo — esta limitación
ya no aplica.

---

## 2026-08-02 — Campo `idusuario` en `Fact_HistorialDespachoUnidad`

Alcance: `database/esquemas.json`, `backend/core/repositories/despacho/`,
`backend/core/repositories/informes_tacticos/seguimiento_repository.py`, `backend/conftest.py`.

Resuelve L3 de la entrada anterior: el informe táctico "% de cierres forzados sobre total
de cierres" (`informes-tacticos-simples`) aproximaba "forzado" con
`estadonuevo = 'Retirado'` sobre el total de transiciones a estado terminal, sin poder
distinguir un retiro hecho por un Operador de uno automático por vencimiento — la tabla
no tenía forma de saber quién (o si alguien) causó la transición.

**Cambio de esquema:** campo `idusuario` (INT, nullable) añadido a
`Fact_HistorialDespachoUnidad` — `NULL`/ausente cuando la transición es automática
(sistema), poblado con el id del operador cuando la transición la causa una acción humana
explícita (ej. retiro forzado desde central).

**Cambio de código:** ver detalle en `traceability.md` de
`specs/002-tactico/Emergencias/informes-tacticos-compuestos/backend/` — repositorio de
escritura de historial de despacho actualizado para aceptar `idusuario` opcional, caso de
uso de retiro de despacho actualizado para pasar el id del operador actuante, y
`cierres_forzados()` reescrito para calcular "forzado" como `estadonuevo='Retirado' AND
idusuario IS NOT NULL` en vez de la aproximación anterior.

---

## 2026-08-13 — Soporte §3.7: B43 (tickets sin plazo y sin decirlo), B44 (el sistema firmaba como el supervisor) y F20

Alcance: `backend/apps/soporte_cliente/` (constantes, registro, reapertura, monitoreo),
`frontend/src/app/modules/soporte-cliente/` (+ pruebas). SRS §3.7.1 y R-03.

**B43 — un ticket clasificado podía quedarse sin compromiso de tiempo, en silencio.**
Registrando un ticket como `ana.torres.cliente` salió `prioridad: crítico`,
`estado: Abierto` y **`sla_status: null`**. La causa: su suscripción está *Cancelada*, así que
`AsignacionSLAService` no encuentra plan, devuelve `None`, y el ticket se guardaba sin plazo y
**sin ninguna marca**. En la cola se veía igual que cualquier otro; el vigilante de SLA lo
descarta por `idslaconfig is None` y nunca lo marca en riesgo ni lo escala.

El SRS solo admite un caso en que el contador no arranca —el ticket **sin clasificar**—, y le da
un estado propio (`Pendiente_de_clasificacion`) precisamente para que se vea. Aquí había un
tercer caso no declarado e invisible. Lo grave no es la ausencia de plazo, que puede ser
correcta: es que se presentaba como un ticket cronometrado.

Corregido con `sla_status = "sin compromiso"` cuando el ticket está clasificado pero no hay regla
aplicable —en el alta, en la clasificación manual y en la reapertura, donde además impide
conservar un «en curso» viejo que ya nadie vigila—. La cola lo destaca en ámbar y el detalle
explica el motivo. El vigilante sigue ignorándolos, pero ahora por una rama explícita.

> **Queda una decisión de negocio, no técnica** (anotada en `decisiones-pendientes.md`): si un
> cliente **sin suscripción activa** debe tener compromiso de tiempo en soporte, y con qué plan.
> Hoy no lo tiene y ya se ve; qué *debería* ocurrir no lo dice el SRS.

**B44 — el escalado automático quedaba firmado por el supervisor.** `MonitoreoSLAService`
escribía la bitácora con `idusuario=supervisor_idusuario`, de modo que decía que **él** había
escalado el ticket. R-03 del SRS: "cuando la ejecuta un proceso automático, se registra
explícitamente como acción del sistema, **lo que permite distinguir una decisión humana de una
automática**"; §3.7.1 lo repite para este caso concreto. El supervisor es el **destino**, y su
sitio es `id_agente_asignado`, no el campo de autor. Corregido y verificado contra el stack real:
tras forzar el vencimiento del ticket #14 el barrido deja
`escalado_automatico_sla | idusuario: None` y el supervisor sigue asignado.

**F20 — el historial se leía como código.** Se pintaba el `tipo_accion` crudo
(«escalado_automatico_sla») y un guion donde va el autor. Con eso, B44 era además
indetectable a simple vista: un guion se lee como dato que falta, no como «lo hizo el sistema».
Añadido `historial-ui.ts` con frases legibles por acción y la marca **«Sistema»** en las entradas
sin autor humano —el vigilante de SLA y el cierre automático—. Verificado en el navegador:
*"Escalado automáticamente por incumplimiento de SLA · Sistema"*.

**Resto de §3.7 recorrido y sin defecto**: la regla absoluta de clasificación —un ticket ligado a
un caso de emergencia activo sale **crítico** aunque el texto sea trivial: probado con "Consulta
sobre el color del botón" sobre un caso vivo—; el ticket sin clasificar no arranca contador; las
**notas internas no llegan al cliente** (filtradas en la API, no solo en la UI); la reapertura
**no crea un ticket nuevo** y conserva el historial (#7: `cierre_confirmado` + `reapertura`, mismo
agente); el escalado conserva la titularidad; y modificar un SLA **no edita**: el PATCH responde
**201** creando `idslaconfig` nuevo y cierra el anterior con `activo=false` y
`fechavigenciahasta`, de modo que los tickets viejos conservan el compromiso que estaba vigente.

Suites: backend **1673 passed, 2 skipped**; frontend **643 SUCCESS**.

---

## 2026-08-13 — §3.4 cerrada: B42 (los avisos de vencimiento no los enviaba nadie) y el ticket con nombre

Alcance: `backend/apps/partners/services/expiracion_credencial_service.py`,
`backend/apps/soporte_cliente/services/registrar_ticket_service.py` (+ pruebas).
SRS §3.4.1 y §3.4.2.

**B42 — «El sistema avisa antes del vencimiento y de nuevo al producirse»: no avisaba a nadie.**
`PartnerNotificacionService.notificar_proximo_vencimiento()` y `notificar_vencimiento()` estaban
escritos, redactados con cuidado y **con pruebas propias**… y **ningún código de producción los
llamaba**. `ExpiracionCredencialService` solo escribía la bitácora: `avisar_proximas_a_vencer()`
devolvía `avisadas: [23]` sin que saliera un correo. El partner se enteraba del vencimiento
cuando su integración empezaba a fallar contra el entorno de pruebas.

Por qué la suite no lo veía: las pruebas del notificador lo invocaban **a mano**, así que
comprobaban que el mensaje se redacta bien, no que alguien lo mande. Es la variante de laboratorio
del cuarto patrón (§6): la capacidad construida y la puerta sin cablear.

Corregido cableando ambos avisos en el servicio de expiración, con tres pruebas nuevas que
aseveran **que alguien se entera** —destinatario, nombre de credencial y días restantes— y una
cuarta que fija lo que no puede romperse: **un buzón caído no deja credenciales vencidas
operativas**. La expiración es un control de seguridad, así que el envío va en su propio
`try/except` y el barrido termina.

**Detalle de §3.4.2 pendiente desde la pasada anterior.** El rechazo de una segunda disputa decía
solo *"La factura ya tiene una disputa abierta"*; el SRS pide indicar **cuál** es el ticket
existente "para que continúe la conversación ahí". Sin el número, el mensaje es un callejón sin
salida. Ahora nombra el ticket, y el portal ya lo muestra tal cual desde F19.

**Verificado contra el stack real:** republicada la credencial de sandbox del partner 970002 con
vencimiento a 3 días y ejecutado el barrido en el contenedor →
`AVISOS ENVIADOS: [('api.rescateandino@demo.tsi.com', 'integracion-andina…', 3)]`. Antes de la
corrección, la misma ejecución devolvía `avisadas: [23]` y no enviaba nada.

**Resto de §3.4 revisado y sin defecto**: la instantánea del estado del partner en cada llamada,
el ciclo de avisos de mora (T-10/T-5, sin duplicar, y el ciclo se cierra si regulariza), las
alertas de cuota al 80 %/100 % que llegan **también al Desarrollador de APIs** y nunca mencionan
interrupción del servicio, y la regeneración del sandbox por autoservicio tras vencer —el plan y
el registro se conservan, el nombre queda libre al desactivarse la vencida, y el portal tiene el
formulario de emisión por entorno—.

> Dato de entorno, no defecto: la credencial `tablero-interno` (idcredencial 12, Sandbox) lleva el
> centinela del año 9999, que corresponde a producción. El código de emisión asigna bien la
> vigencia; es una fila sembrada a mano.

Suites: backend **1669 passed, 2 skipped**.

---

## 2026-08-13 — F18 y F19: el partner puede disputar, y el cliente tiene por dónde hacerlo

Alcance: `backend/apps/soporte_cliente/{permissions,views}.py`,
`frontend/src/app/modules/{soporte-cliente,suscripciones}/` (+ pruebas).
SRS §3.7 x §3.4.2.

**F18 — `PartnerIntegracion` recibía 403 al abrir un ticket.** El spec de Soporte listaba
como reportador solo al **Cliente**; el SRS dice que el partner puede registrar una disputa
sobre su factura. Resuelto a favor del SRS: es el mismo actor —quien recibe el servicio y
reclama—, solo que su relación con TSI pasa por la API en vez del portal, y la lectura
contraria dejaba la disputa de facturación sin nadie que pudiera abrirla desde su lado.
`ROLES_REPORTADORES = {Cliente, PartnerIntegracion}`, y la tabla de actores del spec ahora lo
recoge.

**Lo que casi se cuela con ese cambio:** el acotamiento de las vistas se decidía con
`roles == {ROL_CLIENTE}`. Admitir al partner sin tocar esa igualdad lo habría dejado **fuera
del filtro de propiedad**: viendo tickets de otros clientes y notas internas. Se sustituyó por
`es_solo_reportador(roles)` —"no tiene ningún rol de atención"— en las tres vistas que lo
usaban, con prueba dedicada: un partner de otro cliente recibe 403.

**F19 — la capacidad existía y el cliente no tenía puerta.** El formulario de «Registrar
nuevo ticket» no tenía campo `idfactura` y el detalle de factura no ofrecía disputar, así que
RF-O83.2 —y la exclusión del cobro que acababa de arreglarse en B41— eran inalcanzables desde
la UI. Añadidos:

- **«Disputar este cargo»** en el detalle de factura, que es donde el cliente está mirando el
  importe. Solo cuando queda cobro pendiente; si ya está en disputa, en su lugar se explica
  que el cobro está detenido, porque ofrecer el botón solo llevaría al 422 de RN-TIC-008.
- **Selector «Factura en disputa»** en el formulario, que llega preseleccionado desde ese
  enlace y lista solo facturas disputables.
- El texto dice **qué hace**, no qué es: "el cobro automático de ese importe se detiene hasta
  que se resuelva el ticket". Es la razón por la que alguien rellena el campo.
- El error del backend se muestra tal cual: antes un 422 de "esa factura ya tiene una disputa
  abierta" se convertía en "Error al registrar el ticket" y el cliente reintentaba a ciegas.

De paso, el tipo `EstadoPagoFactura` del frontend **no conocía `'En disputa'`**: el backend ya
podía dejar la factura en ese estado y la UI lo pintaba como estado desconocido, sin explicar
por qué el cobro se había detenido. Añadido, con badge informativo (no de error: está detenido
a propósito).

Verificado contra el stack real desde el navegador: el detalle de factura ofrece disputar y
enlaza con la factura; el formulario llega preseleccionado y envía `idfactura`; el 422 de
disputa duplicada se ve con su motivo real. Con el usuario partner: POST de ticket **201**
(antes 403), ve el suyo, **403** en el de otro cliente y su listado solo trae su `idcliente`.

Suites: backend **1665 passed, 2 skipped**; frontend **640 SUCCESS** (629 antes).

---

## 2026-08-13 — F17 y B41 corregidos: la credencial la emite quien la custodia, y la disputa congela el cobro

Alcance: `backend/apps/partners/services/promocion_produccion_service.py`,
`backend/apps/soporte_cliente/services/` (+ pruebas y contratos).
SRS §3.4.1 (onboarding de partners) y §3.4.2 x §3.7 (facturación x tickets).

**F17 — la aprobación emitía una credencial productiva que nadie podía usar.**
`PromocionProduccionService._aprobar()` llamaba a `EmisionCredencialService.emitir(...)`
y devolvía el `client_secret` en la respuesta del **Administrador**. Pero el delta
BE-DELTA-02 y la Clarification Q2 del frontend dicen textualmente lo contrario: el
secreto lo ve **quien lo custodia**, el partner, desde su portal; mostrárselo al Admin
lo obligaría a transmitirlo por un canal inseguro, que es justo lo que evita RN-PON-005.
El delta se implementó a medias: la consola descarta el secreto (FR-UI-009) y ningún
endpoint lo recupera después, así que **se generaba y se perdía**, dejando al partner con
una credencial de producción activa e inservible.

Corregido: la aprobación promueve y notifica, nada más. Devuelve
`credencial_pendiente_de_emision` (el nombre pedido) en lugar de `credencial`. Las dos
pruebas que aseveraban la emisión **codificaban el defecto**, no la regla: se reescribieron
contra Q2 —ahora comprueban que no hay `client_secret` en la respuesta y que no existe
todavía ninguna credencial de producción—. Alineados también `backend/spec.md` (la línea
que decía «Al aprobar se emite la credencial de producción») y el OpenAPI del módulo, que
contradecían a su propio delta.

**B41 — abrir una disputa no excluía la factura del cobro automático.**
`api-monitoring-and-billing` RF-APM-014 dice que una factura marcada en disputa **por
`gestion-tickets-soporte`** queda excluida del cobro y que «este módulo no abre ni resuelve
disputas: solo respeta la exclusión». Nadie ejecutaba ese marcado: el spec de Soporte
impone una sola disputa abierta por factura (RN, línea 198) pero **no menciona `estado_pago`
en ninguna parte**. Resultado: el cliente abría un ticket por un cargo y se le seguía
reintentando ese mismo cargo mientras lo discutía.

Corregido con `DisputaFacturaService` (nuevo): al registrar un ticket con `idfactura` se
republica la fila completa de `Fact_Factura` con `estado_pago = 'En disputa'`, y al cerrarse
el reclamo vuelve a `'Pendiente'`. Dos decisiones que importan:

- **No se inventó un flag propio.** Se usa `estado_pago` porque es la columna que ya
  consultan *todos* los cobradores —`TarificacionExcedenteService.en_disputa()`,
  `CobroService`, el job de dunning y la mora de suscripción— y todos exigen `'Pendiente'`.
  La exclusión sale gratis y no hubo que tocar ninguno de ellos.
- **La liberación va en los dos caminos de cierre**, no solo en la confirmación del cliente:
  un ticket auto-cerrado a los 5 días (RN-TIC-004) habría dejado la factura excluida del
  cobro para siempre. Y no pisa una factura que la resolución ya dejó `Pagada` o ajustada
  —RF-APM-014 dice «pagada o con monto ajustado según la resolución»—.

El marcado ocurre **después** de crear el ticket: si se marcase antes y la creación fallara,
la factura quedaría congelada sin reclamo que la respalde.

Cerrada además la brecha documental que originaba el defecto: `gestion-tickets-soporte/backend/spec.md`
ahora asigna explícitamente esa responsabilidad (RN-TIC-DISPUTA).

Verificado contra el stack real desde el navegador: `ana.torres.cliente` abre un ticket con
`idfactura` → Pinot pasa la factura a `En disputa` conservando `monto_total` y el resto de
columnas (la tabla es upsert: se republica la fila entera); el agente la resuelve, la
cliente confirma el cierre desde su portal y la factura vuelve a `Pendiente`.

Suites: backend **1661 passed, 2 skipped** (1655 antes, +6 nuevas). Frontend sin cambios.

**Hallazgo derivado, no corregido (F19):** el formulario de «Registrar nuevo ticket» del
portal del cliente **no tiene campo `idfactura`**, y el detalle de factura en
`suscripciones/historial-facturas` no ofrece «disputar». La capacidad existe en el backend
(y ahora congela el cobro), pero el cliente no tiene por dónde ejercerla desde la UI —el
mismo patrón «permiso concedido, puerta inexistente» de §6—. Anotado en `REVISION-SRS-ESTADO.md`.

---

## 2026-08-13 — Partners §3.4.2: B40 corregido (el job de excedente moría), B41 y F18 abiertos

Alcance: `backend/apps/partners/services/tarificacion_excedente_service.py` (+ pruebas).
SRS §3.4.2.

**B40 — la facturación de excedente no ocurría nunca.** El servicio agendaba y consultaba los
reintentos por una columna **`proximo_reintento` que no existe en `Fact_Factura`** (verificado
contra `database/esquemas.json`: la tabla tiene `reintentos` y `resultado_ultimo_reintento`).
Al escribir, Pinot descartaba el campo en silencio; al leer, **rechazaba la consulta entera**,
así que `run_facturacion_excedente_job` **abortaba con `RuntimeError` en cada ejecución**.
Efecto: ninguna factura de excedente se emitía y ningún reintento se recogía — justo el
"ingreso real no cobrado" que el SRS declara inaceptable. Es el mismo error que el código ya
documentaba haber cometido con la columna `monto` y que se creía aislado.

Corregido **sin tocar el esquema**: el vencimiento se **deriva** de `reintentos` +
`fecha_actualizacion`, que sí se persisten, y ya no se publica el campo fantasma.

**Tres pruebas codificaban el defecto**, incluido el ayudante `_factura()`, que fabricaba
filas con `monto` y `proximo_reintento` —columnas inexistentes— y por eso el doble las
aceptaba tan felizmente. Reescritas contra el esquema real, más una regresión que **asevera el
payload publicado** para que no vuelva a colarse una columna fantasma.

**Verificado contra el stack real:** el job completa (`evaluados: 4, emitidas: 0, ya emitidas:
2, omitidas: 2`), y **no duplica**: una segunda ejecución sobre el mismo período no emite nada,
que es la regla de no duplicación de RF-APM-012. La **cola de excepciones** muestra la factura
con los tres reintentos agotados, su último resultado y la acción sugerida —"Emitir la factura
manualmente"—, que es el "pendiente de emisión manual" del SRS.

**B41 — abrir una disputa no marca la factura, así que no la excluye del cobro.** Comprobado:
el ticket se crea y queda vinculado (`idfactura`), pero `Fact_Factura.estado_pago` sigue en
`Pendiente`. El mecanismo de exclusión existe —`en_disputa()` filtra los reintentos de las que
estén `En disputa`— pero **nadie escribe ese estado**, de modo que una factura en disputa se
sigue reintentando. SRS §3.4.2: *"Abrir la disputa marca la factura como en disputa, lo que la
excluye explícitamente de los intentos de cobro automático"*. **No corregido por falta de
margen en esta sesión**; queda anotado como lo siguiente a atacar.

**F18 — el partner no puede abrir la disputa.** `TicketsView` exige rol `Cliente`, `Soporte` o
`Administrador`: con el rol `PartnerIntegracion` responde **403**. El SRS dice que *"el partner
puede registrar una disputa sobre un consumo o una factura"*. Puede ser un permiso que falta o
una decisión de que la disputa la abra la cuenta cliente; **queda para decidir**.

**Regla verificada con un rol autorizado:** una segunda disputa sobre la misma factura se
rechaza con `422 "La factura ya tiene una disputa abierta"`. Matiz: el SRS pide que además
**indique cuál es el ticket existente** "para que continúe la conversación ahí", y el mensaje
no lo nombra.

Suites: **backend 1654 passed, 2 skipped**; frontend sin cambios (629).

---

## 2026-08-13 — Partners §3.4.1: ruta de onboarding recorrida entera + hallazgo F17 (pendiente de decisión)

Alcance: verificación, sin cambio de código. Datos sembrados para poder recorrerla. SRS §3.4.1.

**Entorno sembrado** (no había forma de probar la ruta: el usuario partner demo resuelve al
partner que ya está en producción):

- Suscripción del cliente `Rescate Andino Norte` (920003) reactivada a `Activa` —estaba
  Cancelada de una pasada anterior—, con lo que pasó a ser cliente elegible.
- Partner **Rescate Andino API** (`idpartner 970002`) registrado desde la consola sobre ese
  cliente.
- Usuario **`api.rescateandino@demo.tsi.com` / `password123`** (idusuario 9010, rol
  `PartnerIntegracion`) vinculado al cliente por `Dim_Usuario_Cliente`. Se eligió el vínculo
  y **no** `admin_local_id` a propósito: sobrescribirlo habría desplazado a Teresa, que es la
  administradora local de ese cliente y se usa en las pruebas de Suscripciones.

**La ruta obligatoria se cumple, sin atajos** (SRS: *Registrado → Plan asignado → Pruebas
activo → Pendiente de aprobación → Producción activa*):

- **Sin plan no hay pruebas**: la interfaz ni siquiera ofrece el formulario, y el backend
  responde `409 sin_plan` — *"El partner no tiene plan de acceso asignado; no puede emitir
  credenciales"*.
- **Sin pruebas no hay producción**: `409 ruta_invalida` — *"La solicitud requiere estar en
  «Pruebas activo»; el partner está en «Registrado». No se puede solicitar producción sin
  haber pasado por el entorno de pruebas"*.
- **El cupo se deriva del plan del cliente**: al asignar plan quedó Básico, 1.000/mes y
  30/minuto, que es lo contratado por ese cliente.
- **La activación la ejecuta una persona**: el partner solicita; el Administrador resuelve
  desde la cola. El rechazo **exige motivo** (mínimo 15 caracteres) y avisa de que ese texto
  se le envía al contacto técnico.
- **El rechazo devuelve a «Pruebas activo», no a «Registrado»**, y **su credencial de pruebas
  sigue activa** — comprobado en la API y en Pinot—, que es justo donde el SRS quiere que
  corrija lo que motivó el rechazo.
- **No hay tope de reintentos**: la segunda solicitud se aceptó sin objeción.
- **Aprobada**, el partner queda en `Producción activa` y **las credenciales de los dos
  entornos coexisten**.

**F17 — el secreto de la credencial productiva no llega a nadie. Requiere decisión.** Al
aprobar, `PromocionProduccionService` **emite** la credencial de producción y devuelve su
secreto en la respuesta… **del Administrador**, que la consola deliberadamente no muestra
(*"no es de quien aprueba"*, FR-UI-009). Los endpoints del partner filtran `client_secret`
(`_CAMPOS_SENSIBLES`), así que **el secreto se genera y se descarta**: el partner termina con
una credencial productiva activa que no puede usar. La propia consola dice al aprobar *"lo
verá únicamente el partner al emitirla"*, cuando ya está emitida.

Hay salida —revocarla entrega un reemplazo y ese sí muestra su secreto—, pero es "revoca la
credencial que nunca usaste". **No se corrigió porque la salida correcta es una decisión de
producto**: o la aprobación no emite y el partner emite después (que es lo que la copia de la
consola promete), o el partner recibe el secreto en un paso de revelación única. Queda
anotado en el documento de revisión.

Alcance: `frontend/.../pages/cola-acceso/` (nueva), `frontend/.../detalle-partner.page.ts`,
`frontend/.../mi-integracion.page.ts`, `frontend/.../partner-api.service.ts`,
`frontend/.../models/partner.types.ts`, `frontend/.../partners.routes.ts`,
`frontend/src/app/shared/layout/nav-links.ts` (+ specs). SRS §3.4.3.

**Encargo del responsable:** construir las pantallas que `partner-access-management/frontend`
declaraba pendientes. Eran las que impedían ejercitar §3.4.3 desde la interfaz.

**1. Panel de suspensiones del Administrador** (RF-PAC-005 + RF-PAC-009 b), en
`/partners/consola/suspensiones`. Lista suspendidos y partners en ciclo de mora con sus días
y su último aviso, y permite reactivar. Sin él, la reactivación —que **solo** un Administrador
puede hacer y que el sistema **nunca** ejecuta solo (RN-PAC-009)— no tenía por dónde empezar:
había que ir partner por partner.

**2. Suspender y reactivar desde la ficha del partner.** Al construir el panel apareció que la
cola solo lista morosos y suspendidos, de modo que un Administrador **no podía suspender por
las otras causas que el SRS nombra** —vencimiento de contrato, petición del cliente—. La
acción vive también en el detalle del partner, visible solo para Administrador.

**3. El partner suspendido entiende por qué** (RN-PAC-016). El portal solo decía "Tu acceso
está suspendido. Contacta al administrador."; ahora muestra **motivo, fecha, días de mora e
historial de acceso**, y aclara que puede seguir consultando su pantalla y su consumo. El
endpoint `estado-acceso` ya existía y nadie lo llamaba; solo se pide cuando hace falta
explicar una suspensión.

**Verificado de punta a punta contra Pinot**, que era el objetivo: la **regla de cascada** no
podía probarse antes.

1. Suspendido *Integradora Andina* desde la ficha → *"Credenciales desactivadas: **2**"*.
2. Como partner, el portal muestra el motivo, la fecha y el historial —y no un mensaje seco—.
3. Reactivado desde el panel → *"Credenciales restituidas: **2**. Quedan **1** sin restituir a
   propósito: fueron revocadas por seguridad y resucitarlas sería un riesgo."*
4. En Pinot: `tablero-interno` y el reemplazo `plataforma-siniestros` vuelven a `activo = true`;
   la credencial **revocada** por el partner sigue `activo = false`. **Ninguna credencial
   comprometida resucitó**, que es el tie-breaker de seguridad del spec.
5. La bitácora registra `suspension_manual` y `reactivacion` con `ejecutado_por = Administrador`
   y sus estados anterior/nuevo.

También se formateó la fecha de suspensión, que salía como ISO crudo en la pantalla del
partner (misma familia que F4/F6).

Suites: **backend 1654 passed, 2 skipped** (sin cambios); **frontend 629 SUCCESS** (eran 616).

---

## 2026-08-13 — Partners y API §3.4: construida la revocación de autoservicio (alcance pendiente, no defecto)

Alcance: `frontend/.../partner-api.service.ts`, `frontend/.../models/partner.types.ts`,
`frontend/.../mi-integracion.page.ts` (+ spec). SRS §3.4.1, §3.4.2 y §3.4.3.

**Qué faltaba y por qué no es un defecto.** El endpoint
`POST /api/v1/credenciales/{id}/revocar` está implementado y probado en el backend —con su
doble guarda de propiedad, su idempotencia y su reemplazo inmediato— y **ninguna pantalla lo
llamaba**: el portal del partner solo ofrecía emitir y regenerar. A diferencia de F9/F12/F13/F15,
**esto estaba declarado**: `partner-access-management/frontend/spec.md` es un *stub* explícito
—"pendiente de especificar tras cerrar la capa backend"— que enumera las tres superficies que
faltan. Es alcance conocido sin construir, de la familia de §7.3, no una puerta que alguien
olvidara poner.

Se construyó igualmente **una** de esas tres superficies, la de revocación, porque la regla
que implementa es de seguridad y el SRS §3.4.3 la hace autoservicio a propósito: *"es reactiva
ante un incidente de seguridad, donde esperar autorización sería el peor comportamiento
posible"*. Un partner con una credencial filtrada no tenía forma de cortarla. **Las otras dos
siguen sin construir** y quedan anotadas: el estado de acceso propio accesible estando
suspendido (RN-PAC-016) y el panel de suspensiones del Administrador (RF-PAC-005) —sin él, la
regla de cascada de suspensión y reactivación no puede ejercitarse desde la interfaz.

Corregido: botón **Revocar** por credencial vigente, con confirmación en 2 pasos en tono
destructivo que explica que las demás credenciales seguirán operando, y el secreto del
reemplazo entregado en la pantalla que ya existía para eso —una sola vez, nunca por la URL—.
No se ofrece sobre credenciales vencidas, que se **regeneran**, no se revocan.

**Verificado contra el stack real.** Revocada `plataforma-siniestros` (producción) del partner
Integradora Andina: la credencial 11 quedó `activo = false`, se emitió la **22 con el mismo
nombre y entorno** y su secreto se mostró una vez; `tablero-interno` (sandbox) siguió intacta.
Por API se comprobaron las dos guardas: revocar una ya inactiva responde **409
"La credencial ya estaba inactiva"**, y una credencial ajena responde **404**.

**Reglas de §3.4 que ya cumplían, comprobadas en el navegador:**

- **Credenciales de pruebas y producción coexisten**: el portal muestra las dos secciones y
  dice explícitamente que activar producción no elimina el acceso de pruebas.
- **Superar la cuota no bloquea**: con el consumo al **150 %** del cupo, la pantalla informa
  *"Tu servicio no se interrumpe: el excedente se factura al cierre del período"* y estima el
  excedente. Es la regla que el SRS pide no "corregir" por error.
- **Separación de entornos**: el consumo se presenta acotado a **Producción**.
- **Autodiagnóstico**: los errores del partner se listan con su código, y los `429` aparecen
  marcados como *"No cuenta como consumo facturable"*.
- **Registro de partner por nombre de cliente**: el combobox se alimenta de clientes elegibles
  —con suscripción vigente y sin partner previo—, de modo que la regla "un solo partner por
  cliente" se previene en vez de explicarse con un 409.

**Nota de entorno, no defecto.** El portal era inalcanzable al empezar: `partner.demo@demo.tsi.com`
es administrador local del cliente `E2E Onboarding`, que una pasada anterior dio de baja, y el
guard de B9 rechazaba su login —correctamente—. Se reactivó ese cliente para poder recorrer el
módulo; queda anotado en el documento de revisión.

Suites: **backend 1654 passed, 2 skipped** (sin cambios); **frontend 619 SUCCESS** (eran 616).

---

## 2026-08-13 — §3.6.1 fusión de duplicados: B37, B38 y B39

Alcance: `backend/apps/accidentes/services/fusionar_reportes_service.py`,
`frontend/.../registro-accidente.page.ts`, `frontend/.../duplicado-fusion.dialog.ts`
(+ pruebas de servicio, de página y de integración). SRS §3.6.1.

La regla: *"El sistema o el operador fusionan el duplicado con el caso real: el duplicado queda
marcado como fusionado y apuntando al caso padre, que continúa su flujo normal sin alteración.
El duplicado no se borra: queda con trazabilidad completa hacia el caso que lo absorbió."*
Ninguna de las tres partes se cumplía.

**B37 — el diálogo proponía fusionar el caso real consigo mismo.** El 409 de duplicado devuelve
`idaccidente_similar` (el caso ya registrado) y `idaccidente_principal_sugerido` (el más
antiguo de los candidatos). Con un solo candidato —el caso normal— **ambos son el mismo caso**,
y `confirmarFusion` fusionaba `idaccidente_similar` como duplicado contra el id sugerido. Al
confirmar, el accidente vivo quedaba **apuntándose a sí mismo** (`idaccidenteorigen` = él
mismo), **desactivado** y en `FUSIONADO`: el caso real desaparecía del flujo. En la prueba en
vivo solo se salvó porque el guard lo rechazó por otro motivo (B39), no porque nada lo
impidiera. Añadida la guarda explícita en el servicio.

**B38 — el segundo reporte no llegaba a existir.** El 409 rechaza el alta, así que el reporte
duplicado nunca se creaba: la fusión operaba sobre el caso preexistente y el aviso nuevo se
perdía sin dejar rastro. El SRS pide justo lo contrario —"no se borra: queda con trazabilidad
completa"—. Ahora, al confirmar la fusión, el frontend **registra el reporte forzando la
advertencia** y fusiona **ese** caso contra el padre elegido.

**B39 — no se podía fusionar en el caso normal.** El servicio exigía `BORRADOR` o `REPORTADO`
**a los dos** casos. Pero el duplicado llega minutos después, cuando el caso real ya está
buscando unidad o asignado: exigirle ese estado al **padre** bloqueaba la fusión precisamente
cuando hace falta. Verificado en vivo antes del arreglo: `409 "Fusión no permitida para el
estado actual"`. Ahora la restricción de "sin despacho" recae sobre el **duplicado** —que es lo
que dice §3.6.1— y el padre solo se rechaza si está `CERRADO`, `DESCARTADO` o `FUSIONADO`.

**Una prueba que ejercitaba el defecto sin verlo.** `test_deshacer_when_fusionado_restores_activo`
llamaba a `seed_accidente()` dos veces **sin id**, así que ambos casos eran `ACC-SEED-1`: la
prueba fusionaba un caso consigo mismo y pasaba en verde. Se le dieron ids distintos.

**Verificado de punta a punta contra Pinot.** Registrado el caso padre (que el worker despachó
hasta `BUSCANDO_UNIDAD`) y después un segundo aviso en el mismo punto y hora: el diálogo se
abrió, y al fusionar el duplicado **quedó registrado** con `idaccidenteorigen` apuntando al
padre, `activo = false` y estado `FUSIONADO`; el padre siguió en `BUSCANDO_UNIDAD`, activo y
sin `idaccidenteorigen`. También se reescribió el texto del diálogo, que hablaba de "ID del
caso padre" sin explicar qué se fusionaba con qué.

Suites: **backend 1654 passed, 2 skipped**; **frontend 616 SUCCESS**.

---

## 2026-08-13 — §3.6.4 cerrada: F15, la escalada en sitio estaba en la pantalla equivocada

Alcance: `frontend/.../detalle-accidente.page.{html,ts}`,
`frontend/.../mi-seguimiento.page.{html,ts}`. SRS §3.6.4.

**F15 — la escalada de severidad no la podía hacer nadie.** El panel «Escalar severidad» vivía
en el **detalle del accidente**, que `accidentesLecturaGuard` reserva a Operador, Técnico y
Administrador; pero el endpoint `POST /accidentes/{id}/escalar-severidad` exige el rol
**Unidad** con unidad vinculada (`IsUnidadSeguimiento`). Resultado comprobado en el navegador:
el operador rellena el panel, confirma y recibe **403**; la unidad —el actor que el SRS pone
en el sitio: *"ya en el lugar, la Unidad puede escalar la severidad del caso con lo que
efectivamente observa"*— no tenía ninguna pantalla desde donde hacerlo. Cuarta vez que aparece
el mismo patrón en Emergencias (F9, F12, F13, F14): la capacidad existe, la puerta está en la
habitación equivocada.

Corregido: el panel pasa a **Mi seguimiento**, visible cuando la unidad ya registró su llegada.
En el detalle del accidente queda una nota que explica que la severidad en sitio la actualiza
la unidad y que los cambios se ven en el historial del expediente.

**Verificado contra el stack real** con `LOTE-A3` sobre `ACC-1786589824363-3100`: la escalada
pasó la severidad de **Grave a Fatal** con 3 heridos, y `Fact_HistorialSeveridadAccidente`
guardó el cambio con `idusuario = 9006` —el usuario de la unidad—, que es la constancia de que
la escalada ocurrió **en sitio** y no desde central.

**Cancelación de caso con unidad despachada, verificada** (cerraba §3.6.4): con la grúa en el
sitio, «Cancelar caso (falsa alarma)» retiró la unidad, **la devolvió a `Activa`**, registró
el motivo en `Dim_NotaAccidente` y cerró el caso por vía corta (`horafin`,
`duracionminutos = 602`, `activo = false`) **sin pedir documentación de evidencia**, tal como
describe el SRS.

Suites sin cambios: **backend 1651**, **frontend 615**.

---

## 2026-08-12 — §3.6.4 en trayecto: F14 (la constancia no se veía), B35 y B36

Alcance: `backend/apps/seguimiento/services/gps_senal_perdida_service.py`,
`backend/apps/despacho/services/{monitoreo_despacho_service,consulta_candidatas_service}.py`,
`backend/core/repositories/accidentes/nota_accidente_repository.py`, `backend/conftest.py`,
`frontend/.../monitoreo-despacho.page.html`, `frontend/.../despacho.types.ts` (+ pruebas).
SRS §3.6.4.

**Lo que ya cumplía, comprobado contra el stack real** (caso `ACC-1786589824363-3100`):

- **Rastreo en tiempo real**: la unidad envía su posición y `Dim_HistorialUbicacionUnidadEmergencia`
  acumula la **trayectoria** (dos puntos con coordenadas y marcas distintas), con el
  acotamiento de un envío cada 10 s.
- **Pérdida de señal**: el job la detecta pasado el umbral (60 s) y **la unidad sigue
  asignada** — `activo = true` —, que es justo lo que pide el SRS: "se perdió visibilidad de
  dónde está, no la responsabilidad sobre el caso".
- **Aborto de misión**: se registra, la unidad vuelve a `Activa` y **se dispara una nueva
  asignación** sobre el mismo caso, que no se abandona.
- **Expediente del cliente**: `ana.torres.cliente@demo.tsi.com` ve sus casos cerrados acotados
  a su zona contratada (condado 1), incluido el que se cerró en esta pasada.

**F14 — la constancia de señal perdida no se veía en ninguna parte.** El aviso se escribía en
`Dim_NotaAccidente`, pero **solo el expediente lee esas notas y el expediente exige el caso
CERRADO**: durante la emergencia —el único momento en que sirve— no aparecía ni en el detalle
del accidente ni en el monitoreo ni en la galería (que filtra a notas de campo). El SRS dice
que la pérdida de señal "deja constancia **visible para el operador**", y el propio
`FR-UI-017` del spec ya lo pedía. Añadido `alertas` al estado de monitoreo y una sección
**"Avisos del caso"** en la pantalla del operador, con la nota de que la unidad sigue
asignada.

**B35 — un aviso por ciclo, no por incidencia.** El job corre cada 30 s y **creaba una nota
idéntica en cada pasada**: en la prueba real se acumularon 17 avisos del mismo despacho en
diez minutos. Una unidad fuera de cobertura media hora habría enterrado el expediente —el
mismo que consulta el cliente— bajo sesenta avisos iguales. Ahora se avisa una vez por
interrupción: si ya hay un aviso posterior a la última posición conocida, el ciclo no repite.
Si la unidad reaparece y vuelve a perderse, sí se emite un aviso nuevo.

**B36 — la unidad que abortaba recibía el mismo caso otra vez.** Verificado en vivo: `LOTE-A2`
abortó por avería y la reasignación automática le devolvió el caso a **ella misma** (despacho
4312). El SRS define la reasignación como el mismo proceso "con una unidad **nueva**", y el
efecto práctico es que una unidad averiada podía recibir el caso indefinidamente. La consulta
de candidatas excluía a quien **rechazó** pero no a quien **abortó**. Corregido y comprobado:
tras el segundo aborto, el caso pasó a la unidad 18.

**Al doble le faltaban dos consultas** (§3 del handoff): la de la última alerta con `LIKE` y la
de listado de alertas. Sin enseñárselas, las pruebas de B35 no habrían visto nada.

Suites: **backend 1651 passed, 2 skipped**; **frontend 615 SUCCESS**.

---

## 2026-08-12 — §3.6.4 Cierre de casos: F13 (no existía ninguna acción de cierre), B33 y B34

Alcance: `backend/apps/seguimiento/services/{finalizar_atencion_unidad_service (nuevo),cerrar_caso_service}.py`,
`backend/apps/seguimiento/views/{mi_seguimiento_views,urls}.py`,
`backend/core/repositories/despacho/estado_accidente_despacho_repository.py`,
`frontend/.../monitoreo-despacho.page.{html,ts}` (+ spec nuevo),
`frontend/.../mi-seguimiento.page.{html,ts}`, `frontend/.../mi-seguimiento-api.service.ts`,
`frontend/.../seguimiento.types.ts`, y las pruebas que codificaban el comportamiento anterior.
SRS §3.6.4.

**Decisión de producto (usuario, 2026-08-12): lectura literal del SRS.** La unidad cierra su
propia parte; el cierre del caso lo hace el Operador y **solo cuando todas las unidades se han
retirado**; el retiro forzado desde central es la excepción y queda registrado como tal.

**F13 — no existía ninguna acción de cierre en toda la aplicación.** `cerrarCaso`,
`cancelarCaso` y `forzarRetiro` estaban implementadas en el backend y en el cliente de API,
y **ningún componente las llamaba**: solo las pruebas. Es decir, **un caso no podía cerrarse
desde la interfaz**, lo que explica que el entorno acumule casos vivos y ninguno cerrado. Las
pruebas de esas rutas pasaban en verde porque ejercitan el cliente HTTP, no la pantalla.
Construido en el monitoreo del caso: cerrar (con resultado y observaciones), cancelar por
falsa alarma, y **forzar retiro por unidad**, con la confirmación en 2 pasos del
`design-system.md` y el aviso explícito de que el retiro forzado no es una finalización normal.

**Nueva capacidad: la unidad termina su parte.** No existía forma de hacerlo — la unidad solo
podía registrar llegada o abortar—, así que la regla "todas las unidades retiradas" no tenía
camino normal por el que cumplirse. Añadido
`POST /api/v1/mi-seguimiento/despachos/{iddespacho}/finalizar` y el botón
**"Finalizar mi atención"** en *Mi seguimiento*. El retiro queda con `retiro_forzado = false`.

**B33 — el cierre retiraba a todos en silencio y como retiro normal.** `CerrarCasoService`
retiraba por su cuenta cualquier despacho que siguiera activo. Efecto: la regla que el SRS
llama la más estricta —*"un caso solo pasa a cerrado cuando **todas** las unidades se han
retirado. No existe el cierre parcial"*— **no llegaba a aplicarse nunca**, y las unidades que
seguían trabajando se registraban como finalización normal, borrando la distinción que el SRS
exige respecto del retiro forzado. Ahora el cierre responde 409 explicando cuántas unidades
faltan y qué hacer.

**B34 — el caso retrocedía de `EN_ATENCIÓN` a `ASIGNADO`.** `publish_asignado_if_first_confirmed`
solo comprobaba que el estado actual no fuera ya `ASIGNADO`. Al sumar una unidad de apoyo a un
caso que ya se estaba atendiendo, su confirmación reescribía el estado hacia atrás: **el
expediente decía que nadie había llegado mientras la primera unidad llevaba horas en el
sitio**. El SRS dice "si es el **primer** despacho confirmado del caso". Visto en el historial
del caso real durante esta prueba.

**Pruebas que codificaban el defecto.** Cuatro aseveraban el auto-retiro (una se llamaba
literalmente `test_cerrar_when_en_atencion_auto_retira_y_cierra`). Contrastadas con el SRS y
reescritas para aseverar la regla: el cierre se rechaza mientras quede una unidad, y el caso
cierra cuando se retiran todas. El resto solo usaba el cierre como andamiaje: se les añadió el
paso de retiro, que además ejercita el endpoint nuevo.

**Verificado de punta a punta en el navegador y contra Pinot** con
`ACC-1786569480560-3023` y dos unidades:
1. Con las dos en el caso, cerrar responde *"No se puede cerrar: 2 unidad(es) siguen sin
   retirarse"* y el caso sigue abierto.
2. `LOTE-A2` finaliza su parte desde su pantalla → despacho 4305 con `retiro_forzado = false`.
3. El Operador fuerza el retiro de `LOTE-A3` → despacho 4310 con `retiro_forzado = **true**`,
   y al completarse el conjunto **el caso se cierra solo**.
4. `Fact_Accidente` queda con `horafin`, `duracionminutos = 339` y `activo = false`; las dos
   unidades vuelven a `Activa`. La evidencia adjunta no intervino en ningún momento del
   cierre, que es la regla de no bloqueo de §3.6.3.

Suites: **backend 1648 passed, 2 skipped**; **frontend 615 SUCCESS**.

---

## 2026-08-12 — §3.6.3 Evidencia en Sitio: F9/F12 (puertas que no existían), B31 y B32

Alcance: `frontend/.../mi-seguimiento.page.{html,ts,spec.ts}`,
`frontend/.../galeria-evidencias.page.{html,ts}` (+ spec nuevo),
`frontend/.../monitoreo-despacho.page.html`,
`backend/apps/despacho/services/{mi_despacho_service,rechazar_despacho_service,confirmar_despacho_service,asignacion_manual_service}.py`
(+ pruebas). SRS §3.6.2, §3.6.3 y §3.6.4.

**Lo que ya cumplía, comprobado contra el stack real** (unidad `LOTE-A2`, caso
`ACC-1786569480560-3023`):

- La unidad adjunta **fotografía y nota de campo**, en línea y en diferido.
- **Captura sin conexión conservando la hora de captura**, que es la regla central del
  módulo. Verificado en Pinot, no solo en pantalla: la nota guardada offline quedó con
  `fechahora = 00:59:14Z` (captura) y `fecha_actualizacion = 01:01:25Z` (subida), **131 s de
  diferencia**; la foto, 95 s. La nota registrada en línea tiene ambas marcas iguales. La
  hora que se conserva es la del sitio, no la de la señal.
- **Cada unidad adjunta la suya de forma independiente**: con la ambulancia `LOTE-A2` y la
  grúa `LOTE-A3` en el mismo caso, `Dim_NotaAccidente` guarda tres notas atribuidas a
  `idusuario` 9005 y 9006, sin pisarse.

**F9 — la unidad no tenía forma de llegar a la evidencia.** El permiso estaba dado (la
galería admite el rol `Unidad`) pero **no había ninguna puerta**: la barra de navegación de
la unidad tiene tres entradas y ninguna lleva ahí; `Mi despacho` y `Mi seguimiento` no
contienen un solo enlace; y el único enlace de toda la aplicación vive en el detalle del
accidente, que es pantalla de Operador y a la unidad le responde **"Acceso denegado"**.
Peor: la propia galería remataba con *"Volver al accidente"* → acceso denegado, un callejón
sin salida. Es la familia de B6. Corregido: enlace **"Evidencia del caso"** en Mi seguimiento
—junto al despacho y en el aviso de llegada— y enlace de vuelta según el rol.

**F12 — la asignación manual tampoco tenía puerta.** `/despacho/asignacion/:idaccidente`
existe y funciona, pero **nada en la aplicación enlazaba a ella**: solo se alcanzaba
escribiendo la URL. El SRS la exige como red de seguridad —*"esta vía permanece disponible
aunque la asignación automática falle"*— y es además la vía para sumar una segunda unidad.
Corregido con el botón **"Asignar unidad"** en el monitoreo del caso. **El requisito ya estaba
escrito**: `FR-UI-006` del spec de frontend pedía exactamente ese CTA. Es un caso claro de
requisito documentado y no construido, que ninguna prueba detectaba porque la ruta sí existe.
Lo mismo aplica a `FR-UI-007` (coordinar unidad adicional), que sigue sin CTA propio — hoy se
resuelve con el mismo botón, y queda anotado en §7 del documento de revisión.

**B31 — la unidad veía como pendientes despachos ya vencidos.** El vencimiento cierra el
despacho (`activo = false`) pero **no toca la notificación**, que se queda `Notificada` para
siempre; `listar_pendientes` solo miraba el estado de la notificación. Resultado comprobado
en vivo: `LOTE-A3` tenía **tres despachos "pendientes" del mismo caso**, todos muertos, y al
responder uno recibía `404 "Notificación no encontrada"` — mentira doble, porque la
notificación existe y lo que venció es el despacho. En la pantalla donde la unidad decide a
qué caso va, eso es ruido peligroso. Ahora la cola descarta los que no tienen despacho
activo, y confirmar/rechazar uno vencido responde **409 "Este despacho ya venció por falta de
respuesta y fue reasignado"**.

**B32 — con la unidad ya en el sitio no se podía pedir apoyo.** `AsignacionManualService`
solo admitía `REPORTADO`, `BUSCANDO_UNIDAD` y `ASIGNADO`: en cuanto la primera unidad
registraba su llegada y el caso pasaba a `EN_ATENCIÓN`, **ninguna otra unidad podía sumarse**
—ni por asignación manual ni por el endpoint de coordinación, que delega en el mismo
servicio—. El SRS §3.6.4 dice lo contrario con todas las letras: *"si tras la escalada hace
falta apoyo adicional, el despacho de la unidad extra se ejecuta en el módulo de Despacho"*,
y §3.6.2 describe la coordinación de varias unidades sobre un caso. Corregido admitiendo
`EN_ATENCIÓN`; `CERRADO`, `DESCARTADO` y `BORRADOR` siguen rechazándose. Verificado en el
navegador: con el caso en atención, la grúa `LOTE-A3` se despachó y confirmó sobre él.

Suites: **backend 1642 passed, 2 skipped** (eran 1638); **frontend 611 SUCCESS** (eran 608).

---

## 2026-08-12 — F7/F8: el aviso de error culpaba a la conexión, y el modal no existía para nadie que no mirara

Alcance: `frontend/src/app/shared/notifications/alert-host.component.ts`,
`…/confirm-dialog-host.component.ts` (+ sus specs, nuevos),
`frontend/src/app/modules/accidentes/pages/registro-accidente/registro-accidente.page.ts`
(+ spec), `.specify/docs/design/design-system.md` (§11, nueva). Detectados al preparar la
prueba en navegador de B27.

**F7 — el error de validación se presentaba como problema de red.** Registrar un accidente con
fecha futura devuelve `400 {"detail": "Fecha futura no permitida"}`, y la pantalla mostraba
*"No se pudo registrar el accidente. Verifica la conexión e inténtalo de nuevo."*. El detalle
que el backend sí envía se descartaba, así que el operador no sabía qué corregir y se le
mandaba a revisar la red por un campo mal escrito. Ahora el Alert muestra el detalle en los
errores 4xx; el mensaje de conexión se reserva a fallo de red y 5xx, que es cuando puede serlo.

**F8 — el Alert modal no se anunciaba como diálogo.** Era un `div` `fixed inset-0` que cubría
la pantalla y **capturaba todos los clics**, sin `role`, sin `aria-modal`, sin foco y sin
Escape: para un lector de pantalla o una navegación por teclado, la aplicación simplemente
dejaba de responder, sin nada que explicara por qué. Se descubrió en vivo — los clics de la
prueba de B27 iban al overlay invisible y parecía que el formulario estaba roto. Corregido en
los **dos** hosts, que compartían el defecto: `role="alertdialog"` / `role="dialog"`,
`aria-modal`, título y mensaje asociados, foco al abrir y cierre con Escape. En el diálogo de
confirmación el foco inicial va al botón **no destructivo** y **Escape equivale a cancelar**,
nunca a confirmar. La regla queda escrita en `design-system.md` §11, que es la autoridad.

**Verificado en el navegador** contra el stack real: el 400 de fecha futura ahora dice
*"No se pudo registrar el accidente: Fecha futura no permitida"*, el diálogo expone
`role="alertdialog"` con el foco en Aceptar y Escape lo cierra; el de confirmación de
"Descartar borrador" abre con el foco en **Cancelar** y Escape conserva el borrador.

**Suite de frontend: 608 SUCCESS** (eran 599; 9 pruebas nuevas). **Corrección importante al
estado anterior: la suite sí se puede ejecutar en esta máquina.** `.specify` y
`REVISION-SRS-ESTADO.md` §7.4 la daban por no ejecutable desde el 2026-08-12 por un fallo de
arranque de Karma con Edge; en esta sesión completó dos corridas seguidas sin tocar
configuración. La sospecha registrada entonces —procesos `msedge` del usuario abiertos— queda
reforzada: es un problema de entorno, no del proyecto.

---

## 2026-08-12 — B27 (CORREGIDO) + B28/B29: la asignación automática de despacho ya se ejecuta

Alcance: `backend/apps/despacho/consumers/runner.py` (nuevo),
`backend/apps/despacho/management/commands/run_kafka_consumers.py` (nuevo),
`backend/apps/despacho/consumers/accidente_reportado_consumer.py`,
`backend/core/repositories/despacho/despacho_repository.py`, `backend/config/settings.py`,
`backend/conftest.py`, `docker/accidentes.yml`,
`specs/003-operational/Emergencias/despacho-inteligente/backend/spec.md` (RF-DES-012).
SRS §3.6.2.

**Decisión de arquitectura (usuario, 2026-08-12).** El consumidor corre como **worker aparte
en `docker-compose`** —management command + servicio propio con `restart: unless-stopped`—,
no como hilo dentro de `runserver`. Alcance: los **dos** handlers ya registrados; el
consumidor de aborto queda fuera, no está inscrito en `apps.py`.

**B27 — el proceso que faltaba.** `register_consumer` inscribía los handlers en un
diccionario que nadie leía. Ahora `ConsumerRunner` los consume:
`python manage.py run_kafka_consumers`, servicio `despacho-worker`. Detalle de la política de
entrega en RF-DES-012 del spec: `auto_offset_reset=latest` (un worker nuevo **no** reprocesa
el historial e intenta despachar accidentes viejos), confirmación de offset manual y
posterior al proceso (*at-least-once*), y un handler que falla se registra sin detener el
bucle ni bloquear la partición —un mensaje envenenado no puede impedir el despacho del
accidente siguiente—.

**B28 — el handler no reconocía ningún evento real.** Al ir a probarlo apareció un segundo
defecto que el proceso muerto tapaba: `AccidenteReportadoConsumer` leía `event["estado"]`,
pero `EstadoAccidenteRepository.append_estado` publica **`idtipoestadoincidente`**, la FK al
catálogo. Con el worker en marcha habría registrado "ignorando evento no REPORTADO: None"
para cada accidente del sistema: la mitad de B27 habría seguido rota, ahora en silencio y con
un proceso vivo aparentando funcionar. El handler resuelve la FK.

**Por qué la suite no lo veía, y qué se cambió del doble.** El test alimentaba el handler con
un dict escrito a mano (`{"estado": "REPORTADO"}`) que ningún productor emite: la prueba
codificaba el defecto. Ahora el evento se construye **publicándolo con el repositorio real** y
tomándolo de `mock_kafka`. Al hacerlo apareció que el doble mentía en un segundo nivel:
guardaba la **referencia** al payload, y `append_estado` añade `payload["estado"]` *después*
de publicar, así que las pruebas veían un campo que jamás viaja por Kafka. El doble ahora
guarda una copia, como hace el productor real al serializar a JSON dentro de `publish()`.

**Idempotencia (consecuencia de at-least-once).** `AsignacionInteligenteService.ejecutar` no
tenía guarda: reprocesar un evento creaba un segundo despacho. El handler ahora no asigna si
el caso **ya tiene despacho activo**, lo que cubre también que el Operador haya despachado a
mano entretanto. La comprobación lee de Pinot: no cubre el reintento dentro de la ventana de
ingesta de 5–15 s, y así queda escrito en el spec en vez de aparentar que sí.

**~~B29~~ — RETIRADO el 2026-08-12, no era un defecto.** Se registró que `list_all_active()`
consultaba `Fact_Despacho WHERE activo = true` sin `LIMIT` y que por tanto el ciclo de
vencimientos solo veía diez despachos. **Es falso**: `PinotClient.query` añade
`LIMIT DEFAULT_QUERY_LIMIT` (10 000) a toda consulta que no declare uno —
`_with_explicit_limit`, ya presente en el repositorio desde antes de esta revisión—, así que
la consulta nunca estuvo bajo el recorte implícito a 10. El `LIMIT` explícito que se añadió
queda porque documenta la intención en el propio SQL, pero **no arregla nada**: no había nada
roto. La afirmación de daño ("el resto no vencía nunca") era incorrecta.

Conviene revisar con este criterio los hallazgos anteriores de la misma familia (B11, B13,
B16, B20, B25): si esa guarda del cliente ya existía cuando se registraron, sus consecuencias
también pudieron quedar sobredimensionadas. Los cambios en sí —bajar el filtro y el tope al
SQL— siguen siendo correctos y más eficientes que filtrar en Python.

**Registro de actividad.** No había `LOGGING` en `settings.py`: los loggers `tsi.*` no
llegaban a ninguna parte porque la raíz está en WARNING. Para la API se notaba poco; para un
worker sin pantalla ni respuesta HTTP, era una caja negra. Añadido un handler de consola para
`tsi` (nivel por `TSI_LOG_LEVEL`), y `PYTHONUNBUFFERED=1` en el servicio. El logger
**propaga a la raíz a propósito**: `caplog` de pytest captura ahí, y varias pruebas aseveran
el contenido del rastro de auditoría; cortar la propagación las deja sin ver nada.

**B30 — encender el registro reventó una tarea periódica.** `run_evaluacion_reglas_demo`
hacía `logger.info("evaluacion_reglas_demo", extra=result)` con
`result = {"created": …, "skipped": …}`, y **`created` es un atributo reservado de
`LogRecord`**: `logging` lanza `KeyError` al construir el registro. No se notaba porque el
logger `tsi` no tenía nivel INFO y la llamada salía antes de llegar ahí. En cuanto el nivel
sube —que es justo lo que se hace al diagnosticar un problema en producción— **la tarea
falla**. El resultado va ahora anidado bajo `resultado`. Se auditaron los demás `extra=` del
backend: los otros nueve pasan claves de dominio sin colisión.

**Verificado contra el stack real, en el navegador.** Como Operador se registró
`ACC-1786569480560-3023` sin tocar nada más. Sin intervención humana, el worker creó el
despacho **4305** sobre `LOTE-A2`, y la pantalla de monitoreo muestra el caso en
`BUSCANDO_UNIDAD` con su intento *"Ambulancia Lote A2 — Pendiente — Automatico"*. Después se
ejecutó el ciclo de vencimientos sobre `ACC-1786567280611-1700`: cuatro despachos vencidos
produjeron **cuatro reasignaciones automáticas** (4306–4309), y el expediente conserva los
intentos en `Timeout` junto a los nuevos. Antes, ese caso se quedaba encallado en
`BUSCANDO_UNIDAD` para siempre. Reiniciando el worker se comprobó el apagado limpio y que
**no reprocesa** el historial ni duplica el despacho 4305.

Suite backend: **1638 passed, 2 skipped** (eran 1629; 9 pruebas nuevas del runner y del
consumidor). Sin cambios de frontend.

---

## 2026-08-12 — B12/B13: ninguna mejora de plan podía completarse

Alcance: `backend/apps/suscripciones/services/cambio_plan_service.py`,
`backend/core/repositories/suscripciones/solicitud_cambio_plan_repository.py`,
`backend/apps/suscripciones/tests/services/test_cambio_plan_service.py`.

**Hallazgo (B12).** Detectado al probar el cambio de plan desde el navegador (SRS §3.3.1,
"una mejora de plan se autoaprueba"). `POST /api/v1/suscripciones/solicitudes-cambio-plan`
para subir de Básico a Profesional devolvía **404 "Solicitud no pendiente"**.

**Causa.** `CambioPlanService.solicitar()` creaba la solicitud y, si era mejora, llamaba
acto seguido a `aprobar(idsolicitud=...)`, que empieza por
`self.solicitudes.find_by_id(idsolicitud)`. La escritura acababa de salir por Kafka y Pinot
tarda 5-15 s en exponerla, así que la relectura devolvía vacío y la propia guarda de
`aprobar` rechazaba la solicitud recién creada. Es la trampa de "nunca releer algo recién
escrito dentro de la misma operación", esta vez dentro de una sola petición HTTP.
`SolicitudCambioPlanRepository.update()` tenía el mismo `find_by_id` al principio, así que
aunque se hubiera superado la primera guarda, el cambio de estado se habría perdido igual.

**Efecto verificado.** **Ninguna mejora de plan podía completarse.** El cliente veía un
error, la suscripción seguía en el plan viejo y quedaba una solicitud `Pendiente` huérfana
en `Fact_Solicitud_Cambio_Plan`. Como `solicitar()` rechaza con 409 si ya hay una pendiente,
a partir de ese momento el cliente **no podía pedir ningún cambio de plan**, ni mejora ni
reducción: el primer intento de mejora lo dejaba bloqueado indefinidamente.

**Hallazgo (B13), en el mismo repositorio.** `find_pendiente()` y `list()` hacían
`SELECT * FROM Fact_Solicitud_Cambio_Plan` sin `LIMIT` y filtraban en Python, bajo el
`LIMIT 10` implícito de Pinot. Con más de diez solicitudes en el sistema, la guarda de
"una sola solicitud pendiente por cliente" podía dejar de ver la pendiente y aceptar una
segunda, y a la bandeja del Administrador dejaban de llegar solicitudes sin ningún error.

**Cambio de código.** `aprobar()` se dividió en la entrada pública —que sigue releyendo y
validando, porque ahí el id viene de la URL— y `_aprobar(sol, idadmin)`, que trabaja sobre
la fila ya en memoria. La auto-aprobación de la mejora llama a `_aprobar` con el registro
recién creado, sin releer nada. Se añadió `update_from(current, changes)` al repositorio
para republicar la fila completa —la tabla es upsert— a partir de una copia en memoria;
`update()` se mantiene y ahora delega en él. `rechazar()` usa también `update_from`, con lo
que hace una consulta menos. `find_pendiente()` y `list()` pasan el filtro a SQL con
`LIMIT` explícito.

**Por qué no lo cazó la suite.** `test_upgrade_auto_aprueba` pasaba en verde porque el
doble en memoria refleja cada escritura en `PINOT_STORE` al instante: la relectura siempre
encontraba la fila. La regresión añadida
(`test_upgrade_auto_aprueba_aunque_pinot_aun_no_exponga_la_solicitud`) anula `find_by_id`
con `patch.object` para reproducir el retardo real, y falla contra el código anterior.

**Verificación.** `python -m pytest` → **1613 passed, 2 skipped**. En el navegador contra
el stack real: la mejora Básico→Profesional responde **201** con `estado: "Aprobada"`, y en
Pinot la suscripción queda `idplan=2, precio=149.0, nivel='Profesional'` y la solicitud
`Aprobada`; "Mi suscripción" muestra Profesional · $149.00. La reducción
Profesional→Básico queda `Pendiente` con el aviso de que debe aprobarla un Administrador.
El rechazo desde la bandeja del Administrador persiste `Rechazada` con su motivo.

---

## 2026-08-12 — B27 (CRÍTICO, no corregido): la asignación automática de despacho nunca se ejecuta

> **Corregido el mismo 2026-08-12** — ver la entrada «B27 (CORREGIDO) + B28/B29» más arriba.
> Este hallazgo se conserva porque describe el daño y porque al construir el worker
> aparecieron dos defectos más que este proceso muerto tapaba.

Alcance: hallazgo, sin cambio de código. SRS §3.6.2.

**Hallazgo.** Se registró un accidente como Operador, con una unidad declarada `Activa` en la
zona y la región en producción — todos los prerrequisitos del SRS cumplidos. Pasados varios
minutos, `GET /accidentes/{id}/despacho` seguía devolviendo `estado_caso: "REPORTADO"` e
`intentos: []`. **No se creó ningún despacho automático.**

**Causa.** La asignación automática la dispara un consumidor de Kafka:
`AccidenteReportadoConsumer` / `handle_accidente_reportado`, que `DespachoConfig.ready()`
inscribe con `register_consumer(...)` sobre el topic de estado de accidente. Pero ese registro
es **un diccionario en memoria que nadie lee**: `get_consumer_handlers()` no tiene ningún
llamador en todo el backend, no hay bucle de consumo, no hay management command y el
contenedor arranca solo `python manage.py runserver`. El handler está escrito, probado y
registrado — y jamás se invoca.

**Efecto.** El SRS §3.6.2 dice: *"El sistema **asigna automáticamente** la unidad más
adecuada, evaluando las unidades disponibles y su distancia al punto del accidente. Crea el
despacho, marca su origen como automático y notifica a la unidad."* Eso no ocurre nunca. Todo
caso queda en `REPORTADO` esperando que un operador despache a mano. En un departamento donde
"una demora tiene consecuencias sobre vidas humanas", el automatismo que debería ganar esos
segundos no existe en ejecución.

**Lo que sí funciona y lo salva parcialmente.** La vía manual está operativa y el SRS la
exige precisamente como red de seguridad: *"Esta vía permanece disponible aunque la
asignación automática falle — nunca debe existir una situación donde el sistema no pueda
despachar porque el algoritmo no responde."* Verificado: el despacho manual crea el caso con
`origen: "Manual"`, notifica a la unidad y mueve el caso a `BUSCANDO_UNIDAD`.

**Matiz importante: el motor automático no está roto, solo no se dispara.** Al rechazar un
despacho, la reasignación se ejecuta **de forma síncrona** desde el propio servicio de
rechazo, y ahí sí funciona: creó un despacho nuevo sobre otra unidad con
`origen: "Automatico"`. O sea que el algoritmo de selección, la creación del despacho y la
notificación están operativos y probados en vivo. Lo que falta es exclusivamente **el proceso
que consuma los eventos de Kafka**.

**Segunda consecuencia, más dañina que la primera.** El otro handler registrado en ese mismo
diccionario muerto es `handle_despacho_timeout`, que es quien reasigna cuando una unidad **no
responde**. Verificado: al ejecutar el ciclo de vencimientos, el despacho queda marcado
`Timeout` correctamente… y ahí se acaba. **No se reasigna a nadie y el caso se queda en
`BUSCANDO_UNIDAD` indefinidamente**, sin más intentos y sin aviso. Es peor que la falta de
asignación inicial: en el arranque el operador sabe que tiene que despachar a mano, pero aquí
puede creer que hay una unidad en camino hasta que se le ocurra mirar. El SRS define la
reasignación como "el punto de entrada único de toda reasignación del sistema, sin importar
si el disparador fue un rechazo, un vencimiento o un aborto" — hoy solo entra por el rechazo.

**Por qué no se corrigió aquí.** Es el mismo patrón que **G1** del 2026-07-15 ("jobs
periódicos sin agendar": los servicios existían y nadie los invocaba), que se resolvió
añadiendo management commands. Pero un consumidor de Kafka no es un job: necesita bucle de
sondeo, gestión de offsets, política de reintentos y decidir cómo se supervisa el proceso
(¿worker aparte en `docker-compose`?, ¿un `runserver` con hilo?, ¿qué pasa si muere?). Eso es
una decisión de arquitectura y despliegue, no un arreglo de una línea, y hacerla a la carrera
sería peor que dejarla escrita. **Queda como el punto más importante que atender en
Emergencias**, con la ventaja de que todo el dominio ya está construido: solo falta el
proceso que consuma.

---

## 2026-08-12 — Verificado sin cambios: despacho manual, confirmación y las reglas de flota con despacho activo

Alcance: ninguno (solo pruebas). SRS §3.6.2 y §3.5.1.

Con un accidente `REPORTADO`, una unidad con acceso propio y su disponibilidad declarada, se
recorrió la cadena completa:

- **Despacho manual**: crea el despacho con `origen: "Manual"`, lo entrega
  (`push` y `sms`) y mueve el caso a `BUSCANDO_UNIDAD`.
- **La unidad ve su pendiente** en `mi-despacho/pendientes`, con severidad, descripción,
  coordenadas y ETA.
- **Confirmación**: el despacho queda `Confirmado`, el caso pasa a **`ASIGNADO`** —primer
  despacho confirmado— y la unidad a **`En Misión`**, que el SRS define como el único estado
  que no declara nadie sino que fija el sistema al confirmarse un despacho.
- **El intento se conserva** en el historial del caso con su origen y estado.
- **Rechazo**: sin motivo responde 400 "motivo requerido" —el SRS lo exige—; con motivo, el
  despacho queda `Rechazado` conservando el texto, y **se dispara la nueva búsqueda**
  (`reasignacion_iniciada: true`), que crea un despacho sobre otra unidad con
  `origen: "Automatico"`.
- **Vencimiento**: el ciclo de timeouts marca el despacho como `Timeout` sin borrarlo.
- **Los tres desenlaces conviven en el historial.** Un mismo caso terminó mostrando el
  intento rechazado (con su motivo) y el vencido, uno detrás de otro, tal como pide el SRS
  para poder analizar después qué unidades rechazan sistemáticamente.
- **Escalado a zonas vecinas**: encuentra unidades de condados contiguos y marca el despacho
  con `origen: "Escalado_zona"`, como pide el SRS.
- **Constancia cuando no hay capacidad**: agotadas todas las unidades de las zonas vecinas,
  la llamada responde `{"message": "Sin unidades en condados vecinos", "alerta_registrada":
  true, "nota": "Escalamiento registrado"}`. Es la constancia explícita que exige el SRS —
  "el sistema no falla en silencio ante la ausencia total de unidades"—, y además queda
  registrada, no solo devuelta.
- **Varios despachos sobre un mismo caso** conviven con estado propio e independiente: el
  caso de prueba acumuló seis intentos (manual, automático por reasignación y tres
  escalados) sin que unos pisaran a otros.

Y con ese despacho activo se cerraron las cuatro reglas de Red Operativa §3.5.1 que faltaban:

- **Baja con despacho activo, por el proveedor** → 403: "solo un Administrador puede ejecutar
  la baja forzada. Espere al cierre del caso."
- **Edición de campo crítico con despacho activo** → 409 "se requiere confirmación
  explícita"; un campo no crítico (capacidad) se edita sin problema.
- **Baja forzada por Administrador**: sin `forzar` → 409 pidiéndolo explícitamente; con
  `forzar` → ejecuta, y en `Fact_BajaUnidad` queda **`tipobaja: "Forzada_con_reasignación"`
  con el `idaccidente` del caso en curso**, que es la traza del impacto que pide el SRS.
- **Unidad de baja excluida de todo despacho**: tras la baja forzada, la consulta de
  candidatas del caso devuelve `candidatas: []`. "Sin excepción alguna", como dice el SRS.

---

## 2026-08-12 — B26: una falsa alarma no se podía descartar nunca

Alcance: `backend/apps/accidentes/services/descartar_caso_service.py`,
`backend/core/repositories/despacho/despacho_repository.py`,
`backend/apps/accidentes/tests/services/test_descartar_caso_service.py`,
`backend/apps/accidentes/tests/api/test_descartar_caso_contract.py`.

**Hallazgo.** Primer defecto de Emergencias (SRS §3.6.1). Se registró un accidente como
Operador y se intentó descartarlo como falsa alarma **sin que existiera ningún despacho**:
respondió 409 "Solo se puede descartar en BORRADOR".

**Causa.** El SRS condiciona el descarte a un hecho concreto: *"El operador puede descartar
el caso registrando el motivo. Esto **solo es posible mientras no exista ningún despacho
creado**."* La guarda implementaba otra condición —estar en `BORRADOR`— que es más estricta y
distinta. Y ahí está el detalle que lo vuelve grave: el registro **se autoconfirma** a
`REPORTADO` cuando no hay advertencias (`RegistroAccidenteService`: nace en BORRADOR y pasa a
REPORTADO si `not validation.has_advertencias`). O sea que un accidente registrado
limpiamente —el caso normal— saltaba a REPORTADO en el acto y **ya nunca podía descartarse**.

**Efecto.** La falsa alarma solo era descartable en el caso raro de que el registro hubiera
disparado alguna advertencia (posible duplicado, fuera de cobertura) y se hubiera quedado en
borrador. En el camino habitual, el operador que confirma que el aviso era falso no tiene
forma de cerrarlo: el caso se queda REPORTADO, vivo y a la espera de despacho.

**Cambio de código.** La guarda ahora implementa la condición del SRS: se admite descartar en
`BORRADOR` o `REPORTADO`, y se rechaza si `DespachoRepository.list_by_accidente()` devuelve
algo. El mensaje de conflicto distingue los dos motivos ("no se puede descartar un caso en
CERRADO" vs. "el caso ya tiene despachos creados"). De paso, `list_by_accidente` llevaba
`SELECT *` sin `LIMIT`: con el recorte implícito a 10 de Pinot, un caso con varias unidades
coordinadas —una grúa sumándose a una ambulancia, que el SRS §3.6.2 contempla— habría perdido
despachos del agregado sin aviso.

**Tests que codificaban el defecto.** `test_descartar_when_not_borrador_raises` y
`test_descartar_when_reportado_returns_409` daban por buena la guarda vieja. Se reescribieron
contra la regla del SRS: REPORTADO **sin** despacho ahora se descarta (200), con despacho da
conflicto, y un caso CERRADO sigue rechazándose.

**Verificación.** `python -m pytest` → **1629 passed, 2 skipped**. Contra el stack real, el
mismo accidente que antes devolvía 409 ahora responde "Caso descartado exitosamente" con
estado `DESCARTADO`.

---

## 2026-08-12 — Verificado sin cambios: regla de origen del dato en el registro

Alcance: ninguno (solo pruebas). SRS §3.6.1.

El formulario de registro de accidente pide ubicación y hora, descripción, severidad,
vehículos involucrados, heridos, víctimas, fallecidos y origen del reporte. **No pide clima,
fotografías, conductores ni implicados**, que es exactamente lo que el SRS prohíbe capturar
desde la central ("la central no inventa lo que no ve"); esos datos quedan para el personal
en sitio. El propio servicio lo deja anotado en un comentario. Regla cumplida.

> **Anotado, no corregido:** el formulario muestra "Calle seleccionada (idcalle)" — un nombre
> de columna en pantalla, §8 del design-system. Añadido a §7.1.

---

## 2026-08-12 — B25: el conteo de cobertura podía despublicar sola una región que sí tenía unidades

Alcance: `backend/core/repositories/red_operativa/cobertura_region_read_repository.py`.

**Hallazgo.** Revisando §3.5.2. Las tres consultas de
`CoberturaRegionReadRepository` —los estados de la región, sus condados y las unidades
activas de esos condados— iban **sin `LIMIT`**, bajo el recorte implícito a 10 filas de Pinot.

**Por qué aquí es grave.** En otros sitios el `LIMIT 10` implícito hace desaparecer datos de
una pantalla. Aquí alimenta la **única acción que el SRS permite al sistema tomar sin
revisión humana**: despublicar una región al llegar a cero cobertura. Con más de diez
condados, `_condados_de_la_region` devolvía solo diez; si esos diez no tenían unidades pero
los demás sí, el conteo daba **0** y la región se despublicaba sola teniendo cobertura real.
Una zona que podía atender casos dejaba de recibirlos, sin que nadie lo decidiera. El error
va en la dirección peligrosa: subcontar nunca da un falso "hay cobertura", pero sí un falso
"no hay ninguna".

**Cambio de código.** `LIMIT` explícito en las tres consultas
(`LIMITE_CONDADOS = 1000`, `LIMITE_UNIDADES = 10000`), con el porqué escrito en el módulo.

**Verificación.** `python -m pytest` → **1626 passed, 2 skipped**. Contra el stack real, la
región `Centro` sigue contando sus 7 unidades activas y rechazando la despublicación con 409.

---

## 2026-08-12 — F6: el historial de validaciones imprimía la fecha como epoch

Alcance: `frontend/src/app/modules/red-operativa/incorporacion-regional/pages/validacion/validacion.page.ts`.

La columna FECHA/HORA del historial de intentos mostraba `1786559771844`. Mismo caso que F4
en métodos de pago: el epoch en milisegundos llega crudo a la plantilla. Corregido con
`| date: 'medium'` (`CommonModule` ya estaba importado). Verificado en el navegador: los tres
intentos de la región de prueba se leen ahora como "Aug 12, 2026, 1:36:11 PM".

---

## 2026-08-12 — Verificado sin cambios: protocolo de validación de región (dos actores)

Alcance: ninguno (solo pruebas). SRS §3.5.2.

- **Dos actores en secuencia, no indistintos.** El Administrador ejecuta el protocolo, pero
  al intentar registrar el resultado como *Aprobada* recibe **"Solo el Director Tecnológico
  puede aprobar una región para producción"**. Con el Director Tecnológico
  (`roberto.paredes.director@demo.tsi.com`) la aprobación sí procede y la región pasa a
  `Producción`.
- **El rechazo deja la región en validación.** Tras un resultado *Rechazada*, el estado
  queda `En_Validación`, no inactiva ni en producción.
- **Los intentos se acumulan.** Dos validaciones rechazadas seguidas sobre la misma región
  producen los intentos 1 y 2, **cada uno con su motivo**, y la aprobación del Director
  añade el 3 sin borrar los anteriores. El historial es consultable desde la pantalla.
- **El motivo se pide solo al rechazar**: el campo aparece al marcar *Rechazada*, que es el
  "detalle del criterio incumplido" del SRS.
- **Rechazo definitivo** existe como acción aparte, para la región que no continúa.
- **Cobertura cero.** El guardarraíl funciona: sobre una región con unidades activas, la
  despublicación automática responde 409 diciendo cuántas hay. La rama de **cero cobertura**
  no se pudo ejercitar contra el stack real —el entorno demo tiene un único estado y dos
  condados, así que dejar una región sin cobertura exigía desactivar la flota entera y
  arruinar el escenario de Emergencias—; está cubierta por
  `test_despublicacion_automatica_service.py`.

> **Cuidado al montar una región de prueba.** Una región creada sobre el mismo `idestado` que
> otra **comparte sus condados y, por tanto, su cobertura**: la región nueva reportaba las 7
> unidades de `Centro`. No es un defecto del conteo — se comprobó — sino una propiedad del
> modelo (región → estado → condados → unidades) que hace falta tener presente para no
> interpretar mal una prueba.

---

## 2026-08-12 — Verificado sin cambios: carga en lote y declaración de disponibilidad

Alcance: ninguno (solo pruebas). SRS §3.5.1.

**Carga en lote (todo o nada).**

- **Puerta del plan.** Con un cliente en plan Básico (`carga_lote_habilitada = false` en su
  suscripción) la importación responde 403 "El plan contratado no habilita la carga en lote
  de unidades". La capacidad se lee de la **suscripción**, no del plan en vivo, que es lo que
  exige R-04 del SRS.
- **Una fila mala tumba el archivo entero.** Con tres filas donde la tercera repetía una placa
  existente: `{"insertadas": 0, "usuarios_creados": 0, "fallidas": [{"fila": 3, "motivo": "Ya
  existe una unidad con placa TSI-001"}]}`. Comprobado en Pinot que **no quedó nada**: ni las
  dos unidades válidas ni sus usuarios. El proveedor recibe qué fila falló y por qué, como
  pide el SRS.
- **El reintento desde cero funciona.** Corregido el archivo, la misma carga responde
  `{"insertadas": 3, "usuarios_creados": 3, "fallidas": []}`.
- **Y de paso valida B23 en el caso más duro.** Esas tres altas asignan el rol `Unidad` tres
  veces seguidas dentro de una sola operación: en Pinot quedaron con claves **distintas**
  (`idusuariorol` 9003, 9004 y 9005) y la fila de la administradora de cliente siguió
  intacta. Antes del arreglo, este lote la habría vuelto a dejar sin roles.

**Disponibilidad — la declara siempre la propia unidad.**

- El endpoint es `POST /api/v1/mi-unidad-emergencia/disponibilidad`, de alcance propio por
  diseño: no admite nombrar otra unidad, así que la vía para que un tercero la declare "en su
  nombre" no existe estructuralmente.
- **Terceros rechazados con 403**, incluido el **Administrador** y el propio proveedor dueño
  de la unidad. Es la regla estricta del SRS ("no existe una vía por la cual un tercero la
  declare en su nombre"), ya cerrada en la decisión #12 con
  `IsUnidadEmergenciaSelfStrict` y confirmada ahora contra el stack.
- **La unidad sí puede**: con el acceso creado en su alta (rol `Unidad`), declara `Activa` y
  luego `Fuera de servicio`, y cada cambio queda en el historial con estado anterior, estado
  nuevo y marca de tiempo.
- **El alta no establece la disponibilidad.** La unidad recién creada arranca en
  `Fuera de servicio` y solo pasa a `Activa` cuando ella misma lo declara, tal como dice el
  SRS.
- **Una unidad sin correo no puede declarar nada** por construcción: sin usuario no hay login
  ni token, y este endpoint exige rol `Unidad` sobre la sesión propia. No hace falta una
  guarda adicional.

> **Observado al entrar como unidad.** El login de la unidad responde
> `requiresPasswordChange: true` sobre su credencial temporal, que es el circuito de B5. Para
> poder probar la disponibilidad se le fijó una contraseña conocida a la unidad `LOTE-A1`
> (usuario 9004) — ver §2.4 de `REVISION-SRS-ESTADO.md`.

---

## 2026-08-12 — B23: asignar un rol a un usuario le quitaba el rol a otro

Alcance: `backend/core/repositories/cuentas_clientes/role_repository.py`,
`backend/conftest.py`,
`backend/apps/cuentas_clientes/tests/repositories/test_role_repository.py`.

**Hallazgo.** Detectado de rebote: al ir a probar la restricción de flota propia, la cuenta
`teresa.beltran@demo.tsi.com` —que había entrado sin problemas un rato antes en la misma
sesión— empezó a responder "Credenciales inválidas o usuario inactivo". Su usuario estaba
activo, su credencial `Activo`, y el hash correspondía a la contraseña. Ejecutando el
servicio dentro del contenedor, el fallo real era **"Usuario sin roles asignados"**: había
perdido su fila en `Dim_Usuario_Rol`.

**Causa.** `RoleRepository.assign_role_to_user()` publicaba el payload **sin
`idusuariorol`**, que es la clave primaria de la tabla. Como Pinot no almacena NULL, la fila
aterrizaba con el defecto para INT (`Integer.MIN_VALUE`), y al ser una tabla **upsert por esa
clave**, todas las asignaciones caían en la misma fila: **cada rol nuevo sobrescribía al
anterior**. En la práctica solo podía existir una asignación hecha por esta vía en todo el
sistema.

**Efecto verificado.** Registrar una unidad de emergencia con correo —que asigna el rol
`Unidad` al usuario nuevo— **le quitó el rol a Teresa y la dejó fuera del sistema**. Ni ella
ni nadie tenía forma de relacionar una cosa con la otra: el usuario simplemente deja de poder
entrar, con un mensaje de credenciales inválidas que apunta al sitio equivocado. Afecta a
todo usuario cuyo rol se asignara por esta vía: altas de unidad con correo, autorregistro,
alta de cliente.

**Cambio de código.** `assign_role_to_user()` genera la clave con `_next_user_role_id()`
(`MAX(idusuariorol) + 1`, acotado a positivos para que las filas huérfanas con
`Integer.MIN_VALUE` no arrastren el contador), y es **idempotente**: si la asignación ya
existe la devuelve sin volver a publicar, para no consumir claves ni duplicar filas.

**Por qué no lo cazó la suite.** `test_assign_role_to_user_publishes_event` comprobaba que se
publicara el evento con `idusuario` e `idrol` — nunca que la fila tuviera clave primaria, que
es justo lo que Pinot necesita para no pisar la anterior. El doble tampoco modela el upsert.
Las regresiones nuevas aseveran que dos asignaciones a usuarios distintos reciben claves
**distintas y positivas**, y que repetir la misma no publica de nuevo. Hubo que enseñarle al
doble las dos consultas nuevas (`MAX(idusuariorol)` y el filtro por `idusuario`+`idrol`).

**Verificación.** `python -m pytest` → **1626 passed, 2 skipped**. Contra el stack real: tras
reasignarle el rol, Teresa vuelve a entrar, y su fila queda con `idusuariorol = 9002` en vez
del centinela.

> **Queda una fila huérfana** con `idusuariorol = Integer.MIN_VALUE` (usuario 9003, rol
> `Unidad`), creada antes del arreglo. Funciona —las lecturas filtran por `idusuario`— y con
> el contador ya en positivo nadie volverá a pisarla, pero conviene sanearla si se hace
> limpieza de datos. Ver §7.4.

---

## 2026-08-12 — B24: la baja de una unidad ajena revelaba que estaba en misión

Alcance: `backend/apps/red_operativa/services/baja_unidad_service.py`,
`backend/apps/red_operativa/tests/services/test_baja_unidad_service.py`.

**Hallazgo.** Probando la regla del SRS §3.5.1 "solo puede operar sobre unidades de su propia
organización". La pertenencia **sí se valida** en editar, ver y dar de baja —los tres
responden 403 "La unidad no pertenece a este proveedor"—, pero en la baja se comprobaba
**después** del despacho activo. Con una unidad ajena que además estuviera en misión, la
respuesta era "La unidad tiene un despacho activo; solo un Administrador puede ejecutar la
baja forzada": se denegaba la operación, correcto, pero de paso se le revelaba a otra
organización el estado operativo de una unidad que no es suya.

**Cambio de código.** Para quien no es Administrador, la pertenencia se comprueba antes de
mirar el despacho. La exención del Administrador quedó **acotada a la baja forzada**: sin
despacho activo la baja es gestión ordinaria de flota y se le sigue exigiendo pertenencia,
porque el SRS dice que la intervención de TSI es "la única excepción al autoservicio del
proveedor". Ese matiz lo cazó un test existente
(`test_dar_de_baja_when_admin_raises`) cuando una primera versión del arreglo le dio al
Administrador una exención general — el test tenía razón y el arreglo se acotó.

**Verificación.** `python -m pytest` → **1626 passed, 2 skipped**, con la regresión
`test_baja_de_unidad_ajena_con_despacho_responde_por_pertenencia`. Contra el stack real, con
la sesión de otro proveedor, la baja de una unidad ajena en misión responde ahora "La unidad
no pertenece a este proveedor".

---

## 2026-08-12 — Verificado sin cambios: alta de unidad con acceso y flota propia

Alcance: ninguno (solo pruebas). SRS §3.5.1.

- **Alta con correo**: responde 201 con `usuario_creado: true` e `invitacion_enviada: true`,
  y en Pinot quedan el usuario con su correo y `activo`, una **credencial temporal** en
  estado `Cambio contraseña` —así entra al circuito de cambio obligatorio de B5— y la
  asignación del rol `Unidad` (idrol 7).
- **Alta sin correo**: la unidad queda en el catálogo con `idusuario = null` y
  `usuario_creado = false`.
- **Solo flota propia**: con la sesión de otro proveedor, **ver**, **editar** y **dar de
  baja** una unidad ajena responden 403 "La unidad no pertenece a este proveedor".

---

## 2026-08-12 — B22: la placa dejaba de ser única en cuanto una unidad se daba de baja

Alcance: `backend/core/repositories/red_operativa/unidad_emergencia_repository.py`,
`backend/apps/red_operativa/services/{registro_unidad_service,importacion_lote_unidad_service}.py`,
`backend/conftest.py`,
`backend/apps/red_operativa/tests/{services/test_registro_unidad_service,api/test_reactivar_unidad_contract}.py`.

**Hallazgo.** Primer defecto de Red Operativa (SRS §3.5.1), detectado al probar la unicidad
de placa desde el formulario de alta. Registrar una unidad con la placa de otra **activa**
responde 409, correcto. Pero con la placa de una unidad **dada de baja** respondía **201**, y
quedaban dos unidades con la misma placa.

**Por qué importa.** El SRS dice "la placa es el identificador único de negocio… antes de
registrar, el sistema verifica que no exista ya una unidad con esa placa", sin distinguir por
estado. Y añade que "reactivar una unidad es posible; el registro de su baja previa permanece
como historial": al reactivar la antigua quedaban **dos unidades activas con la misma placa**.
Es además el identificador con el que las pantallas de flota y despacho nombran a la unidad
(design-system §8), así que el duplicado las vuelve ambiguas justo donde importa.

**El matiz que costó encontrar.** La comprobación no puede ser simplemente "existe la placa
en cualquier estado". La carga en lote es todo-o-nada y, como Pinot no tiene transacciones,
su *rollback* compensa **desactivando** lo ya insertado; el módulo trata lo inactivo como
liberado, y hace lo mismo con el correo ("reusa usuario inactivo… para no bloquear gmail").
Con la regla estricta, un lote que fallara dejaba sus placas bloqueadas para siempre y el
reintento —que el SRS exige que funcione— se rompía. Lo detectó
`test_importar_when_credencial_falla_gmails_quedan_reutilizables`.

**Cambio de código.** Se distingue la **baja de negocio** del **rastro de un lote
compensado**, usando un dato que ya existe: toda baja real registra motivo y tipo en
`Fact_BajaUnidad` (verificado contra el stack: una baja por el flujo normal escribe su fila
con `tipobaja = "Normal"`). `RegistroUnidadService._validar_placa_libre()` rechaza si la placa
pertenece a una unidad activa, o a una inactiva **con baja registrada** —en ese caso el
mensaje dice qué hacer: "Reactívala en vez de registrar una nueva"—, y la admite si la unidad
inactiva no tiene baja. La carga en lote llama al mismo método, así que las dos vías comparten
criterio. Se añadió `find_by_placa()` al repositorio, que busca en cualquier estado.

**Por qué no lo cazó la suite.** El doble de `conftest.py` aplicaba el filtro `activo` a
**toda** consulta por placa, mirase lo que mirase el SQL, así que `find_by_placa` recibía solo
las activas y la prueba no podía ver el fallo. Se corrigió el doble para que respete la
cláusula (`ACTIVO = TRUE` solo cuando la consulta la lleva), en la línea de lo que ya se hizo
con el JOIN de B1.

**Test que codificaba el defecto.** `test_post_reactivar_when_placa_duplicada_returns_409`
daba por bueno que el alta duplicada pasara (201) y esperaba que el choque se detectara
**al reactivar**. Como reactivar es opcional, lo normal era quedarse con el duplicado sin que
nadie lo notara. Se reescribió: ahora comprueba que el **alta** se rechaza y que la unidad
original sigue pudiendo reactivarse sin conflicto.

**Verificación.** `python -m pytest` → **1623 passed, 2 skipped**. Contra el stack real: dar
de baja una unidad por el flujo normal escribe su `Fact_BajaUnidad`, y el intento posterior de
registrar otra con esa placa responde 409 con el mensaje que indica reactivar.

> **Dato sucio detectado de paso.** Las unidades inactivas que ya había en el entorno demo
> (`HUMO-99`, `ABC-123`, `NUEVA-X1`…) **no tienen registro de baja**: `Fact_BajaUnidad` estaba
> vacía. Se desactivaron por script o por pruebas antiguas, no por el flujo del producto. Sus
> placas siguen siendo reutilizables, que es el tratamiento correcto para un rastro sin baja.

---

## 2026-08-12 — B21: una suscripción se facturaba una sola vez en su vida

Alcance: `backend/apps/suscripciones/services/renovacion_service.py`,
`backend/apps/suscripciones/tests/services/test_cambio_plan_service.py`.

**Hallazgo.** Detectado al preparar la prueba del ciclo de mora. Se venció el ciclo de una
suscripción y se ejecutó `run_renovacion_job`: respondió `{'renovadas': 1}`, la suscripción
recorrió el ciclo… y **no se emitió ninguna factura nueva**. El cliente seguía con la única
factura de su alta.

**Causa.** `GeneracionFacturaService.periodo_actual()` deriva el período de
`Fact_Suscripcion.fecha_inicio`, y la renovación solo avanzaba `fecha_fin`. Con
`fecha_inicio` clavada en la fecha del alta, **todo ciclo calculaba el mismo período**, la
guarda de "no duplicar factura del mismo período" encontraba la factura original y devolvía
esa en vez de crear una; como ya estaba `Pagada`, `ejecutar_batch()` ni siquiera la contaba
como creada.

**Efecto.** El SRS §3.3.1 dice "a fin de cada ciclo, el sistema genera automáticamente la
factura de cada suscripción activa". En la práctica se facturaba **el primer ciclo y ninguno
más**: el servicio se renovaba indefinidamente y no se volvía a cobrar nunca. Es una fuga de
ingresos silenciosa — ningún error, ningún estado raro, simplemente no aparecen facturas.

**Cambio de código.** La renovación avanza `fecha_inicio` al arranque del ciclo nuevo (el
`fecha_fin` anterior), junto con `fecha_fin`. `Fact_Suscripcion.fecha_inicio` pasa a
significar "inicio del ciclo vigente", que es lo que necesitan sus dos únicos consumidores:
`periodo_actual()` y los `ORDER BY fecha_inicio DESC` que eligen la suscripción más reciente.
No se pisa la antigüedad del cliente, que vive en otro campo y otra tabla
(`Dim_Cliente.fecha_inicio_contrato`).

**Verificación.** `python -m pytest` → **1622 passed, 2 skipped**, con la regresión
`test_cada_ciclo_renovado_factura_su_propio_periodo`. Contra el stack real, tras vencer el
ciclo y renovar, el cliente pasa a tener **dos** facturas, una por ciclo, con períodos
distintos.

---

## 2026-08-12 — Verificado sin cambios: mora, reintentos, suspensión y reactivación

Alcance: ninguno (solo pruebas). SRS §3.3.1.

Recorrido completo del ciclo de mora contra el stack real, forzando el fallo de la pasarela
con `BILLING_SIMULATOR_FAIL_RATE=1` e inyectando `now` en `run_dunning(now=...)` para situarse
en D+3 y D+5 sin tocar datos:

1. **Emisión con cobro fallido.** La factura del período nace `Pendiente` con
   `reintentos = 1` y `SIM_DECLINED` — el intento del día 0.
2. **D+3 → segundo intento**, `reintentos = 2`. **D+5 → tercero**, `reintentos = 3`.
3. **Agotados los reintentos**, la factura queda `Fallida` y la suscripción **`Suspendida`**.
4. **Acceso mínimo conservado.** En pantalla: "Estado: Suspendida · Acceso: DENEGADO", pero
   el cliente conserva "Métodos de pago" y "Reintentar cobro". "Cambiar plan" no aparece
   (F5 + la guarda B15). Es exactamente lo que pide el SRS: pierde el acceso operativo pero
   no queda "atrapado sin poder pagar".
5. **Reactivación.** "Reintentar cobro" responde 200 con
   `{estado_pago: "Pagada", estado_suscripcion: "Activa", resultado_ultimo_reintento:
   "Exitoso"}`, y Pinot confirma la factura `Pagada` y la suscripción `Activa`. **Este paso
   es el que validaba el arreglo B19 contra el sistema real**: antes, la relectura devolvía
   la factura todavía `Fallida` y la regularización se saltaba el cobro en silencio.
6. **Tras cancelar no se emite nada más.** Con la suscripción `Cancelada`, tanto
   `run_facturacion_mensual_job` como `run_renovacion_job` responden 0.

> **Anotado como deuda, no corregido.** `Fact_Factura` usa `fecha_emision` como
> `comparisonColumns` del upsert, mientras que el resto de tablas del proyecto usa
> `fecha_actualizacion`. `fecha_emision` no cambia nunca tras la emisión, así que todas las
> actualizaciones de una factura se comparan con el mismo valor y su orden depende de cuál
> llegue antes, sin protección contra un escritor rezagado. Hoy funciona porque las
> escrituras conservan `fecha_emision` y Pinot acepta el valor igual; se detectó porque un
> intento de *retrasar* `fecha_emision` fue rechazado por out-of-order. Ver §7.4.

---

## 2026-08-12 — B17–B20/F5: el ciclo de facturación y mora no funcionaba de punta a punta

Alcance: `backend/core/repositories/suscripciones/factura_repository.py`,
`backend/apps/suscripciones/services/{alta_suscripcion_service,mora_suscripcion_service}.py`,
`backend/apps/suscripciones/jobs/{facturacion_mensual_job,dunning_job}.py`,
`backend/apps/suscripciones/tests/{repositories/test_factura_repository,services/test_alta_suscripcion_service,services/test_mora_suscripcion_service}.py`,
`frontend/src/app/modules/suscripciones/pages/mi-suscripcion/mi-suscripcion.page.html`.

**Origen.** Al probar la contratación desde cero con un cliente nuevo
(`teresa.beltran@demo.tsi.com`) y ejecutar el ciclo de facturación contra el stack real.
Cuatro defectos encadenados; ninguno se veía desde la suite.

**B17 — la factura no llegaba a existir.** `run_facturacion_mensual_job` informaba
`{'facturas': 1}` y `Fact_Factura` seguía vacía. `desglose_cargos` está declarada como
columna **STRING de valor único**, y el servicio publicaba la lista de conceptos tal cual:
Pinot descartaba la fila entera con `Cannot read single-value from Collection`. Cuarta
aparición del descarte silencioso, esta vez por forma del dato y no por tipo. Corregido en el
repositorio, que es la frontera con Pinot: `_desglose_json()` serializa al escribir —también
en `update_from`, porque la tabla es upsert y republica la fila entera— y `_hidratar()`
devuelve la lista al leer, que es como la recorre la pantalla de facturas.

**B18 — contratar con método de pago ya registrado daba 500.** `AltaSuscripcionService`
emitía la factura y la cobraba con `CobroService().intentar(factura["id_factura"])`, que la
relee de Pinot. Es el mismo patrón de B14, en la ruta de alta. Teresa no lo disparó porque
contrató **sin** método; cualquier cliente que ya tuviera uno recibía un 500 al contratar.

**B19 — el cliente suspendido no podía regularizar nunca.** `MoraSuscripcionService.
regularizar()` reabre la factura a `Pendiente` y la cobra. Como la cobraba por id, Pinot
devolvía todavía la versión anterior con `estado_pago = "Fallida"`, y el cobro salía por su
guarda de "no está Pendiente" sin intentar nada; el servicio interpretaba el resultado como
fallo y volvía a marcarla `Fallida`. La suscripción se quedaba **Suspendida para siempre** —
exactamente lo que el SRS §3.3.1 quiere evitar cuando dice que el cliente "conserva el acceso
mínimo necesario para regularizar su situación, de lo contrario quedaría atrapado sin poder
pagar".

**B20 — el ciclo de mora solo miraba diez facturas.** `run_dunning` recorría
`SELECT * FROM Fact_Factura` sin `LIMIT`, y `factura_vigente_fallida()` hacía lo mismo. Bajo
el `LIMIT 10` implícito de Pinot, el resto de facturas del sistema no se reintentaban ni
suspendían nunca, y la factura fallida de un cliente concreto podía no aparecer, dejándolo
suspendido sin nada que regularizar.

**Cambio de código.** Se añadió `CobroService.intentar_factura(factura, ...)` en la entrega
anterior (B14) y ahora la usan **todos** los llamadores que ya tienen la fila: alta,
facturación mensual, mora y el job de dunning. `intentar(id_factura)` se conserva para quien
solo tiene el id. Las dos consultas sin `LIMIT` pasan a filtrar en SQL con `LIMIT` explícito,
usando los nombres de parámetro que el doble de `conftest.py` ya reconoce, para que la suite
ejercite la misma consulta que corre en producción.

**F5 — se ofrecían acciones imposibles.** Con la suscripción Cancelada o Suspendida, "Mi
suscripción" seguía mostrando el botón "Cambiar plan", que desde B15 responde siempre 409. Se
condiciona a `estado === 'Activa'`, igual que ya se hacía con "Reintentar cobro" y con el
bloque de cancelación.

**Por qué no lo cazó la suite.** El doble refleja cada escritura al instante y no valida la
forma del dato contra el esquema. Las regresiones nuevas no le preguntan: aseveran que el
payload publicado lleva `desglose_cargos` como **cadena** y que el llamador lo recibe como
lista, y anulan `find_by_id` con `patch.object` para reproducir el retardo real en el alta y
en la regularización de mora.

**Verificación.** `python -m pytest` → **1621 passed, 2 skipped**. Contra el stack real, el
ciclo completo: Teresa contrata Básico desde cero (`201`, suscripción `Activa` $49 en Pinot),
registra una tarjeta, y `run_facturacion_mensual_job` emite y cobra —
`FAC-202608-00000001`, período `2026-08`, base 49.00, impuestos 0.00, total 49.00,
`estado_pago = Pagada`, `resultado_ultimo_reintento = Exitoso`, con el desglose bien formado.
Al reejecutar el job responde `{'facturas': 0}` y el cliente sigue con **una sola** factura:
la regla de no duplicar período se cumple. La pantalla "Facturas" muestra la emisión y el
detalle desglosa "Suscripcion plan Básico — $49.00".

> **Falta todavía.** El camino de **mora con cobro fallido** —reintentos a D+3 y D+5,
> suspensión al agotarlos y reactivación al regularizar— no se ha recorrido contra el stack
> real: exige forzar el fallo de la pasarela y mover fechas de emisión. Sigue en §7.2.

---

## 2026-08-12 — B15/B16: un cliente suspendido por impago podía subirse de plan

Alcance: `backend/apps/suscripciones/services/cambio_plan_service.py`,
`backend/apps/suscripciones/services/alta_suscripcion_service.py`,
`backend/core/repositories/suscripciones/suscripcion_repository.py`,
`backend/apps/suscripciones/tests/services/test_cambio_plan_service.py`.

**Hallazgo (B15).** Probando la regla del SRS §3.3.1 "no se admite cambiar de plan sobre una
suscripción **suspendida o cancelada**". Se suspendió la suscripción de Ana Torres y se pidió
una mejora de plan: respondió **201** y, por ser mejora, se **autoaprobó y se aplicó**.

**Causa.** `CambioPlanService.solicitar()` solo comprobaba que existiera suscripción vía
`find_activa_by_cliente()`, que filtra por `activo`, no por `estado`. Suspender por mora
(`MoraSuscripcionService.suspender_por_factura`) cambia únicamente `estado` a `"Suspendida"`
y deja `activo = True`, así que la suscripción suspendida pasaba la comprobación. La guarda
que el SRS declara obligatoria sencillamente no existía.

**Efecto.** Un cliente suspendido por falta de pago podía **mejorarse solo a un plan más
caro**, con aplicación inmediata, mientras no estaba pagando. Es la misma familia que B9 del
2026-08-11 (se podía iniciar sesión con la organización dada de baja): una regla que el SRS
enuncia como obligatoria y que no estaba escrita en ninguna parte del código.

**Hallazgo (B16), destapado al mirar el repositorio.** `find_activa_by_cliente()` hacía
`SELECT * FROM Fact_Suscripcion` sin `LIMIT` y filtraba en Python, bajo el `LIMIT 10`
implícito de Pinot. Es la consulta más central del módulo —la usan el alta, el cambio de
plan, "Mi suscripción", el cobro y la mora—, así que en cuanto existan suscripciones de once
clientes, a algunos les respondería "Sin suscripción activa": sin plan, sin factura y sin
acceso, sin ningún error de por medio.

**Cambio de código.** `solicitar()` exige `estado == "Activa"` y responde **409** con un
mensaje en lenguaje del negocio ("No se puede cambiar de plan con la suscripción
suspendida"). La guarda va en el servicio y no en `find_activa_by_cliente`, porque hay
flujos que **sí** necesitan la suscripción suspendida: regularizar la mora y mostrar el
estado en pantalla. El repositorio pasa el filtro a SQL con `LIMIT` explícito y documenta que
devuelve también las suspendidas. De paso, el alta decía "Ya existe una suscripción
activo=true": se reescribió a "Esta cuenta ya tiene una suscripción vigente" — el mensaje
filtraba el nombre de una columna al usuario.

**Verificación.** `python -m pytest` → **1617 passed, 2 skipped**, con la regresión
parametrizada `test_no_se_cambia_de_plan_sobre_suscripcion_no_activa` (Suspendida y
Cancelada), que además comprueba que el plan **no** cambió. Contra el stack real, la misma
petición que antes devolvía 201 y aplicaba la mejora ahora devuelve 409. La regla de **una
sola suscripción activa por cliente** se verificó en la misma pasada: el alta sobre un
cliente que ya tiene suscripción responde 409. Con la suscripción ya **Cancelada**, la misma
petición de cambio de plan responde igualmente 409.

**Verificado sin cambios — cancelación (SRS §3.3.1).** Se canceló la suscripción de Ana
Torres desde la pantalla: queda `Cancelada` con motivo y fecha, `renovacionautomatica` pasa a
`false`, y **el servicio no se corta** — `fecha_fin` intacta y "Acceso: Permitido" en
pantalla, con el aviso "Conservarás acceso hasta la fecha de fin". Coincide con el SRS. Falta
comprobar que a partir de ahí **no se emite ninguna factura más**, que exige llegar al cierre
del período.

> **Detalle de interfaz anotado, no corregido.** Con la suscripción Cancelada o Suspendida,
> "Mi suscripción" sigue ofreciendo el botón "Cambiar plan", que ahora siempre responde 409.
> La regla ya está aplicada en el backend; lo que falta es no ofrecer la acción. Anotado en
> §7.1 de `REVISION-SRS-ESTADO.md`.

---

## 2026-08-12 — B14: el job de renovación reventaba al cobrar la factura recién emitida

Alcance: `backend/apps/suscripciones/services/cobro_service.py`,
`backend/apps/suscripciones/services/renovacion_service.py`,
`backend/core/repositories/suscripciones/factura_repository.py`,
`backend/apps/suscripciones/tests/services/test_cambio_plan_service.py`.

**Hallazgo.** Detectado al verificar contra el stack real que una reducción programada se
aplica al renovar (decisión #27, abajo). `python manage.py run_renovacion_job` terminaba con
`ValueError: factura no encontrada`.

**Causa.** Tercera aparición del mismo patrón en esta jornada.
`RenovacionService.ejecutar_batch()` emitía la factura del período nuevo y acto seguido
llamaba a `CobroService.intentar(factura["id_factura"])`, que arranca con
`facturas.find_by_id(...)`. La factura acababa de salir por Kafka, Pinot todavía no la
exponía, y el método levantaba la excepción. `FacturaRepository.update()` tenía además el
mismo `find_by_id` al principio, así que el resultado del cobro tampoco se habría guardado.

**Efecto.** La excepción no estaba capturada, así que **abortaba el batch entero**: las
suscripciones que quedaran después de la primera renovada en la misma corrida no se
renovaban, y como el job es la vía por la que se recorre el ciclo y se emite la factura,
el ciclo de facturación no avanzaba.

**Cambio de código.** Se añadió `CobroService.intentar_factura(factura, ...)`, que opera
sobre la factura ya en memoria; `intentar(id_factura)` se mantiene para los llamadores que
solo tienen el id (reintento manual, mora) y ahora delega en ella tras leerla. La renovación
usa `intentar_factura` con la factura que acaba de emitir. En el repositorio se añadió
`update_from(current, changes)` —mismo criterio que en solicitudes de cambio de plan— y las
dos escrituras del cobro (pago exitoso y fallo) pasan a usarla, con lo que dejan de releer.

**Verificación.** `python -m pytest` → **1615 passed, 2 skipped**, con la regresión
`test_renueva_aunque_pinot_aun_no_exponga_la_factura`, que anula `find_by_id` para
reproducir el retardo. Contra el stack real, `run_renovacion_job` pasa de reventar a
responder `{'renovadas': 1}`. No se generó factura nueva en esa corrida porque ya existía
una del mismo período para esa suscripción — el comportamiento correcto según el SRS
("nunca se emite una factura duplicada para el mismo período y la misma suscripción").

> **No cubierto todavía.** La emisión de factura, la mora, los reintentos y la suspensión
> siguen sin recorrerse de punta a punta; siguen en §7.2 de `REVISION-SRS-ESTADO.md`.

---

## 2026-08-12 — Decisión #27: la reducción de plan aplica al cierre del ciclo

Alcance: `database/esquemas.json`, `database/migra_plan_programado.py` (nuevo),
`backend/apps/suscripciones/services/cambio_plan_service.py`,
`backend/apps/suscripciones/services/renovacion_service.py`,
`backend/apps/suscripciones/views/suscripcion_views.py`,
`backend/apps/suscripciones/tests/services/test_cambio_plan_service.py`,
`frontend/src/app/modules/suscripciones/pages/mi-suscripcion/mi-suscripcion.page.html`,
`frontend/src/app/modules/suscripciones/services/models/suscripciones.types.ts`.

**Origen.** Al probar el cambio de plan (ver B12 arriba) se detectó que el SRS §3.3.1 dice
dos cosas incompatibles: que "una mejora de plan se autoaprueba y **aplica de inmediato**"
y, dos párrafos después, que "todo cambio de plan aplica a partir del **siguiente ciclo** de
facturación". El sistema aplicaba todo de inmediato, de modo que una reducción aprobada a
mitad de ciclo le retiraba al cliente, en el acto, un nivel de servicio que ya había pagado
hasta el fin del período; y como la factura se emite al cerrar con el precio que la
suscripción tenga en ese momento, el cliente pagaba el ciclo entero al precio bajo aunque
hubiera disfrutado medio ciclo del plan alto — justo el prorrateo que la regla prohíbe.

**Decisión (2026-08-12, opción 1).** La **mejora** sigue aplicando de inmediato; la
**reducción** aprobada queda **programada** y la aplica el job de renovación al recorrer el
ciclo. Es la única lectura que no contradice ninguna de las dos frases del SRS en el caso
que perjudica al cliente. Detalle y alternativas descartadas en `decisiones-pendientes.md`
#27.

**Cambio de código.** Columna `idplan_programado` (INT, centinela `0` = sin cambio
programado) en `Fact_Suscripcion`, con migración aditiva y respaldo previo.
`CambioPlanService._aprobar()` bifurca según el sentido del cambio: la mejora copia los
campos del plan; la reducción solo anota el plan programado y no toca plan, precio, nivel ni
severidades. En ambos casos la solicitud queda `Aprobada`: lo que se difiere es la
aplicación, no la decisión. `RenovacionService` aplica el cambio programado en la **misma
escritura** que recorre el ciclo y limpia la marca, antes de generar la factura, de modo que
el período nuevo se factura ya al precio nuevo. `GET /suscripciones/mia` devuelve
`plan_programado_nombre` —el nombre, no el id (design-system §8)— y "Mi suscripción" avisa
al cliente de la fecha en que se aplicará; sin ese aviso vería su plan actual sin saber que
el cambio ya está aprobado.

**Verificación.** `python -m pytest` → **1614 passed, 2 skipped**, con dos regresiones
nuevas: que la reducción aprobada **no** cambia el plan vigente, y que la renovación **sí**
lo aplica y limpia la marca. En el navegador contra el stack real: el Administrador aprueba
la reducción de Ana Torres a Básico y Pinot conserva `idplan=2, precio=149.0,
nivel='Profesional'` con `idplan_programado=1`; la pantalla sigue mostrando Profesional ·
$149.00 más el aviso *"Tu cambio al plan Básico ya está aprobado y se aplicará el Jun 26,
2027, al terminar el ciclo que ya pagaste."*

---

## 2026-08-12 — B10/B11/F4: el método de pago no llegaba a existir

Alcance: `core/pinot/tiempo.py`,
`backend/core/repositories/suscripciones/metodo_pago_repository.py`,
`backend/apps/suscripciones/tests/repositories/test_metodo_pago_repository.py`,
`frontend/src/app/modules/suscripciones/pages/metodos-pago/`,
`frontend/src/app/modules/suscripciones/services/models/suscripciones.types.ts`.

**Hallazgo (B10).** Detectado al probar el registro de método de pago desde el navegador
(SRS §3.3.1, RF-SUSF-002). La pantalla confirmaba "Método registrado. El PAN no se
almacena…", pero la lista seguía diciendo "Aún no hay métodos" indefinidamente. No era el
retardo de lectura tras escritura: `Dim_MetodoPago` tenía `totalDocs: 0`.

**Causa.** `MetodoPagoService.registrar()` pasaba la expiración del formulario tal cual
(`"12/30"`, formato MM/AA) y el repositorio la publicaba sin convertir. En el esquema,
`fechaexpiracion` es un `dateTimeFieldSpec` **LONG** con formato `1:MILLISECONDS:EPOCH`.
Pinot descartó la fila entera: `NumberFormatException: For input string: "12/30"` en
`pinot-server`. Es el mismo patrón de B3/B4 sobre una columna distinta — la API respondía
201 y el registro no existía.

**Efecto.** Ningún cliente podía registrar un método de cobro. Como el alta de método es
también lo que dispara la regularización de una suscripción suspendida por mora
(`MoraSuscripcionService.regularizar`), un cliente en mora **no tenía forma de
regularizar**.

**Hallazgo (B11), en el mismo fichero.** `list_by_cliente()` hacía
`SELECT * FROM Dim_MetodoPago` sin `LIMIT` y filtraba por cliente en Python. Pinot aplica
un `LIMIT 10` implícito sobre la tabla entera, así que en cuanto hubiera métodos de once
clientes, a algunos les desaparecería el suyo de la pantalla sin ningún error.

**Cambio de código.** Se añadió `mes_anio_a_ms()` a `core/pinot/tiempo.py`, junto a
`ahora_ms()` y `SIN_FECHA`, que convierte `MM/AA` (o `MM/AAAA`) al último milisegundo del
mes de expiración — una tarjeta `12/30` es válida hasta el final de diciembre de 2030 — y
devuelve `SIN_FECHA` ante cualquier valor ausente o ilegible, que es el caso de PayPal y
transferencia. El repositorio sella `fechaexpiracion` en `create()` y también en
`update()`, porque la tabla es upsert y republica la fila entera; al releer desde Pinot el
epoch puede volver como cadena numérica, y eso no se reinterpreta como `MM/AA`. El listado
pasa el filtro a SQL con `WHERE idcliente` y `LIMIT` explícito.

**F4 — La expiración se imprimía como epoch crudo.** Corregido el efecto colateral en
pantalla: la tabla mostraba `1924991999999`. Se añadió `expiracion()` en
`metodos-pago.page.ts`, que devuelve `MM/AAAA` y `—` para el centinela; el tipo
`MetodoPago.fechaexpiracion` pasó a `number | string | null`.

**Por qué no lo cazó la suite.** El doble en memoria de `conftest.py` no valida tipos
contra el esquema: aceptaba la cadena sin protestar. La regresión añadida no consulta al
doble, sino que asevera el **payload publicado a Kafka** — que `fechaexpiracion` sea `int`
y valga exactamente `1924991999999` para `12/30`, y que los valores ilegibles (`None`,
`""`, `"sin-fecha"`, `"13/30"`) caigan en `SIN_FECHA`.

**Verificación.** `python -m pytest` → **1612 passed, 2 skipped** (1607 previos + 5 nuevos).
En el navegador, con el stack real: al guardar una tarjeta `12/30` la fila aparece en Pinot
con `fechaexpiracion = 1924991999999` y la pantalla muestra `12/2030 · Activo`. Al registrar
después un PayPal, la consulta a Pinot devuelve la tarjeta con `activo = False` y el PayPal
con `activo = True` y `SIN_FECHA`, y la pantalla los muestra como `Inactivo` y
`Activo · —`: se confirma la regla del SRS de que reemplazar el método **desactiva** el
anterior en vez de borrarlo.

> **Suite de frontend no ejecutable en esta máquina.** `npx ng test` no completó ninguna
> corrida: Karma lanza Edge, ejecuta entre 6 y 296 de las 599 specs —**ninguna falla**— y
> entonces el lanzador aborta con `ChromeHeadless failed 2 times (cannot start)` y cierra
> el servidor. Ocurre igual sin los cambios de esta entrada, con timeouts ampliados y con
> perfil aislado, y hay 17 procesos `msedge` del usuario abiertos. Queda como deuda en
> §7.4 de `REVISION-SRS-ESTADO.md`. `npx tsc --noEmit` pasa, pero no valida plantillas: lo
> de esta entrada se verificó en el navegador contra el contenedor reconstruido.

---

## 2026-08-11 — B1: la asignación automática de prospectos usaba un JOIN que Pinot rechaza

Alcance: `backend/apps/ventas_crm/services/asignacion_automatica_service.py`,
`backend/conftest.py`.

**Hallazgo (B1).** Detectado al probar el registro público de prospectos desde el
navegador (SRS §3.1.1, "Inmediatamente después, el prospecto se asigna a un ejecutivo
comercial"). `POST /api/v1/ventas-crm/prospectos` devolvía **500** contra el entorno real.

**Causa.** `AsignacionAutomaticaService.asignar()` resolvía el ejecutivo con un JOIN de
tres tablas (`Dim_Usuarios` ⋈ `Dim_Usuario_Rol` ⋈ `Dim_Rol`). Pinot no admite JOIN entre
tablas en el motor de consulta de este proyecto y lo rechaza en el parser
(`errorCode 150`, `SQLParsingError ... compileToJoin`).

**Por qué no lo cazó la suite.** `backend/conftest.py` tenía una rama del doble en memoria
que reconocía literalmente `"JOIN DIM_USUARIO_ROL"` y devolvía el resultado correcto. La
suite pasaba en verde sobre una consulta que ningún Pinot real podría ejecutar — el caso
exacto de "confianza falsa" que ya advertía la documentación del doble.

**Efecto verificado.** El prospecto llegaba a crearse y luego la petición reventaba, así
que el visitante veía "No se pudo registrar" sobre un prospecto que sí existía; el segundo
intento con el mismo correo respondía "gmail ya registrado". Tras el arreglo, el registro
público responde "Registro enviado" y el prospecto queda asignado.

**Cambio de código.** La resolución rol → usuarios se hace en dos consultas, reutilizando
`RoleRepository.list_user_ids_for_role()` (idiom ya vigente en el resto del código) y
filtrando después los usuarios activos con `idusuario IN (...)`. Se eliminó la rama del
JOIN en `conftest.py` y se añadió el soporte genérico de `Dim_Usuarios ... IDUSUARIO IN`,
de modo que la suite ejercite las mismas consultas que corren en producción.

**Verificación.** `python -m pytest` → 1596 passed, 2 skipped. Registro público
comprobado click a click en el navegador contra el stack Docker.

---

## 2026-08-11 — D1/F1: identificadores internos en pantalla y límites de plan sin valor

Alcance: `.specify/docs/design/design-system.md` (§8, nueva),
`backend/apps/red_operativa/views/unidad_views.py`,
`frontend/src/app/modules/red-operativa/alta-unidades/` (detalle y contrato),
`frontend/src/app/modules/suscripciones/pages/{catalogo-planes,plan-detalle}/`.

**D1 — Regla global: no se muestran identificadores internos.** Detectado al revisar el
detalle de una unidad, que mostraba "Usuario login: 12" a quien administra la flota. Un id
no le permite al usuario verificar nada, y pedirle que lo escriba le obliga a conocer la
clave primaria de una tabla. Se añadió la §8 al `design-system.md` — que es la autoridad
de diseño — con los cuatro casos (mostrar nombre, combobox contra la tabla catálogo,
identificadores que sí son lenguaje de negocio como el número de caso o la placa, y qué
hacer cuando no hay nombre). La sección incluye la lista de pantallas que todavía
incumplen, para que la regla no se lea como ya cumplida.

**Efecto verificado.** `GET /unidades/{id}` devuelve ahora `usuario_nombre` resuelto contra
`Dim_Usuarios` (nombres + apellidos, con el correo como respaldo), y el detalle pinta ese
nombre en vez del id; sin acceso asignado muestra "Sin acceso asignado". El `idusuario`
sigue viajando en la respuesta: la regla es sobre lo que se pinta, no sobre el transporte.

**F1 — El catálogo de planes imprimía `undefined`.** "Demo sin tarifa" se mostraba como
"undefined unidades · undefined usuarios · 10000 API/mes". `limitesTexto()` interpolaba
las cuatro claves de límites sin comprobar su presencia, y ese plan solo traía las de API.
Ahora se omiten las claves ausentes y, si no queda ninguna, se muestra "Sin límites".
Corregido en las dos copias de la función (catálogo y detalle de plan).

**Dato corregido desde la propia UI (no es cambio de código).** Los planes `Magnifico` y
`Demo sin tarifa` se habían creado sin severidades ni carga en lote — el formulario sí
captura ambas, se guardaron sin marcar. Se editaron desde la pantalla de edición de planes:
`Magnifico` (Empresarial) quedó con Baja · Media · Alta y carga en lote, y `Demo sin tarifa`
(Profesional) con Baja · Media, carga en lote y los límites de unidades y usuarios que le
faltaban. El formulario ya valida "Selecciona al menos una severidad".

---

## 2026-08-11 — B2: el catálogo de planes usaba una escala de severidades que no existía

Alcance: `backend/core/repositories/suscripciones/severidad_repository.py` (nuevo),
`backend/apps/suscripciones/{services/catalogo_plan_service.py,views/plan_views.py,urls.py}`,
`backend/apps/ventas_crm/services/consulta_planes_publicos_service.py`,
`backend/apps/partners/services/consumo_datos_service.py`,
`backend/scripts/seed_planes_publicos.py`, `backend/conftest.py`,
`database/migra_severidades_plan_a_idseveridad.py` (nuevo),
`frontend/src/app/modules/suscripciones/` (form, catálogo, detalle, tipos y servicio),
specs de `subscriptions-and-billing` (spec, data-model, contrato `v1.2.0`),
`decisiones-pendientes.md` #23 (cerrada).

**Hallazgo (B2).** El formulario de plan ofrecía tres severidades escritas en duro —
`Baja`, `Media`, `Alta` — que no correspondían a ninguna fila de `Dim_Severidad`, cuyo
contenido real es `Leve`, `Moderado`, `Grave`, `Fatal`. Dos vocabularios para la misma
cosa, unidos por un diccionario puente (`SEVERIDADES_POR_NIVEL`) en Partners.

**Por qué importaba.** El gating de alcance de Partners es fail-closed: una equivalencia
mal elegida no produce un error visible, produce **cero resultados**, que el partner
interpreta como "no hubo accidentes". Además la lista escrita en el componente incumplía
el requisito de configurabilidad del SRS §6 — añadir una severidad exigía tocar código.

**Decisión de negocio (usuario, 2026-08-11).** Migrar ahora al catálogo real, y que un plan
que cubría `Alta` **siga cubriendo Grave y Fatal**: nadie pierde cobertura respecto de lo
contratado.

**Cambio.** `severidades_desbloqueadas` guarda `idseveridad` en `Dim_Plan` y en
`Fact_Suscripcion`. La validación lee los ids activos de `Dim_Severidad` en vez de una
constante. Nuevo `GET /api/v1/suscripciones/severidades` que alimenta el selector del
formulario. El portal público recibe los **nombres ya resueltos**, no ids — una vitrina sin
autenticar no muestra claves primarias (§8 del `design-system.md`). El puente de Partners
quedó borrado, y el vocabulario retirado ya no se reinterpreta: si una fila sin migrar se
colara, da conjunto vacío y falla cerrado, que es el comportamiento correcto.

**Migración de datos.** `database/migra_severidades_plan_a_idseveridad.py` reescribe las dos
tablas releyendo y republicando la fila entera (son upsert por clave primaria: publicar un
registro parcial borraría el resto de columnas). Ejecutada sobre el entorno local: 6 filas.

**Por qué la suite no lo cazaba.** `conftest.py` no tenía `Dim_Severidad` y sus planes de
prueba guardaban el vocabulario viejo, así que la escala paralela se validaba contra sí
misma. Se añadió la tabla al doble y se migraron los datos de prueba.

**Verificación.** `python -m pytest` → 1596 passed, 2 skipped. `ng test` → 589 SUCCESS.
En el navegador: el portal público y el catálogo interno muestran Leve/Moderado/Grave/Fatal;
el formulario de plan lista las cuatro severidades del catálogo; editar el plan Profesional
lo carga con Leve y Moderado marcados; y guardar el plan 4 persistió `[1, 2]` en `Dim_Plan`.

---

## 2026-08-11 — B3: `fecha_actualizacion` en ISO-8601 hacía que Pinot descartara las escrituras

Alcance: `backend/core/pinot/tiempo.py` (nuevo), once repositorios de
`core/repositories/{cuentas_clientes,red_operativa}/`,
`backend/tests/regression/test_fecha_actualizacion_epoch_ms.py` (nuevo).

**Hallazgo (B3).** Detectado al probar el autorregistro de clientes (SRS §3.2.2,
tercera puerta de entrada). El formulario respondía **201 Created** y mostraba
"Solicitud en revisión", pero `Dim_Cliente` seguía con dos filas antiguas: el
registro no existía. Lo mismo ocurría con la conversión de prospecto a cliente.

**Causa.** Las 58 tablas del proyecto declaran `fecha_actualizacion` como `LONG`
con formato `1:MILLISECONDS:EPOCH`, y en la mayoría es además la **columna de
tiempo** de la tabla y la columna de comparación del upsert. Once repositorios la
sellaban con `datetime.now(timezone.utc).isoformat()` — una cadena. Pinot no
rechaza esas filas con un error: **las descarta en silencio**. El escritor recibe
su payload de vuelta, la vista responde 201 y el usuario cree que guardó.

**Segundo efecto, peor.** `ClienteRepository._next_id()` calcula
`MAX(idcliente)+1` leyendo de Pinot. Como ninguna fila llegaba, dos altas
consecutivas —la conversión de un prospecto y un autorregistro— recibieron el
**mismo** `idcliente`. Si las filas hubieran llegado, la segunda habría pisado a
la primera sin dejar rastro, porque la tabla es upsert por clave primaria.

**Cambio.** Nuevo `core/pinot/tiempo.ahora_ms()` como única forma de sellar el
campo, y las 25 llamadas a `isoformat()` sustituidas por ella en los once
repositorios: cliente, credencial, onboarding, preferencias, rol, accesos de
servidor y usuario (Cuentas y Clientes); baja de unidad, región operativa, estado
de región y validación de región (Red Operativa). Es decir, toda la capa de
identidad y todo el ciclo de vida de regiones y bajas de unidad.

**Por qué la suite no lo cazaba.** El doble en memoria de `conftest.py` guarda lo
que le publiquen sin validar tipos, así que ningún test de servicio podía verlo.
Se añadió `tests/regression/test_fecha_actualizacion_epoch_ms.py`, que lee el
código fuente y falla si algún repositorio vuelve a usar `isoformat()` para este
campo, más una segunda prueba que verifica la premisa contra `esquemas.json`.

**Verificación.** `python -m pytest` → 1598 passed, 2 skipped. En el navegador:
un autorregistro nuevo aparece en `Dim_Cliente` con `fecha_actualizacion` en
epoch-ms, sale en la bandeja del Administrador y, al aprobarlo, queda en `Activo`
con `estado_onboarding` en `Pendiente`.

---

## 2026-08-11 — F2: nueve pantallas nunca repintaban lo que cargaban

Alcance: `.specify/docs/design/design-system.md` (§9, nueva),
`frontend/src/app/modules/cuentas-clientes/gestion-cuenta/pages/{baja,perfil,preferencias,transferencia}`,
`.../incorporacion-clientes/pages/{aprobacion-solicitudes,onboarding-wizard}`,
`.../red-operativa/incorporacion-regional/pages/{catalogo,reevaluacion,validacion}`.

**Hallazgo (F2).** La bandeja de solicitudes de cliente mostraba "No hay
solicitudes pendientes" y el botón congelado en "Actualizando…" mientras
`GET /api/v1/cuentas-clientes/solicitudes` devolvía **200 con la solicitud**.
Verificado en los registros de Django: la petición salía y respondía.

**Causa.** `app-shell.component` es `OnPush`. Estas nueve páginas guardan su
estado en campos planos y no llamaban nunca a `markForCheck()` ni usaban signals.
Un ancestro OnPush que no está marcado como sucio corta el recorrido de detección
de cambios antes de llegar al hijo, aunque el hijo use la estrategia por defecto.
La página de autorregistro, con el mismo estilo de código, sí funcionaba — porque
vive **fuera** del shell, en una ruta pública.

**Cambio.** Las nueve páginas inyectan `ChangeDetectorRef` y llaman a
`markForCheck()` en cada callback asíncrono, que es el idiom que ya seguían las
páginas de `alta-unidades`. La regla quedó escrita en la §9 del `design-system.md`,
que es la autoridad de diseño, con el aviso de que un 200 en la pestaña de red no
es evidencia de que la pantalla funcione.

**Verificación.** `ng test` → 589 SUCCESS. En el navegador, tras reconstruir el
contenedor del frontend: la bandeja lista la solicitud pendiente con su razón
social y el flujo de aprobación se completa.

---

## 2026-08-11 — B4/F3: el usuario no nacía y el botón de cerrar sesión quedaba fuera del borde

Alcance: `backend/core/pinot/tiempo.py`,
`backend/core/repositories/cuentas_clientes/user_repository.py`,
`backend/tests/regression/test_fecha_actualizacion_epoch_ms.py`,
`frontend/src/app/shared/layout/app-shell.component.ts`.

**B4 — `fechanacimiento: ""` sobre una columna LONG.** Continuación de B3, detectado al
intentar entrar con la cuenta recién autorregistrada. El alta respondía 201 y la credencial
se creaba, pero el usuario **no existía** en `Dim_Usuarios`: `UserRepository.create`
publicaba `"fechanacimiento": data.get("fechanacimiento", "")` y esa columna es
`LONG 1:MILLISECONDS:EPOCH`. Igual que con `fecha_actualizacion`, una cadena en una columna
LONG hace que Pinot descarte la fila entera sin avisar. El resultado para el usuario era
"Credenciales inválidas o usuario inactivo" sobre una cuenta que el sistema decía haber
creado. Se publica ahora `core.pinot.tiempo.SIN_FECHA` (el centinela `Long.MIN_VALUE` que
ya llevan las filas sembradas) y se añadió una tercera prueba de regresión que recorre los
repositorios buscando **cualquier** columna dateTime publicada como cadena vacía.

**F3 — El botón de cerrar sesión era inalcanzable por debajo de ~1070px.** El grupo derecho
del header estaba marcado para no encogerse y contenía el correo y los roles sin límite de
ancho. Con un correo largo el contenido medía 1068px dentro de un contenedor de 1024, y
como el documento no tiene scroll horizontal, los últimos 44px —el botón de cerrar sesión—
quedaban simplemente cortados. A 1024px, resolución de portátil corriente, **no había forma
de cerrar sesión**. Descubierto porque varios clics "fallaban" y resultó que el botón no
estaba donde el árbol de accesibilidad decía: estaba fuera de la ventana.

El header se rehízo para adaptarse **encogiendo, no recortando**: cada grupo puede
reducirse, los textos largos se truncan de forma fluida, y lo único que nunca se encoge son
los controles accionables. El correo completo y los roles quedan en el `title` del bloque de
identidad. En pantallas muy estrechas se ocultan los elementos que no informan al truncarse
—el rótulo de marca, el correo, el avatar y el selector de región, que está deshabilitado—
y el botón conserva su icono con etiqueta accesible.

**Verificación.** Barrido de 320, 375, 768, 900, 1024, 1280, 1440 y 1600 px comprobando por
DOM que ningún elemento del header sobresale del borde: sin desbordes en ninguno.
`ng test` → 589 SUCCESS. `python -m pytest` → 1599 passed, 2 skipped.

---

## 2026-08-11 — B5: no existía forma de definir la contraseña definitiva (CU-O04)

Alcance: `backend/apps/cuentas_clientes/services/cambio_password_service.py` (nuevo),
`backend/apps/cuentas_clientes/views/password_reset_views.py`,
`backend/apps/cuentas_clientes/views/urls.py`,
`backend/apps/cuentas_clientes/tests/services/test_cambio_password_service.py` (nuevo),
`frontend/src/app/modules/cuentas-clientes/auth/{pages/password-reset.page.ts,services/password-reset.service.ts}`,
spec `RF-AUT-006b` y contrato `auth-rbac.openapi.yaml`.

**Hallazgo (B5).** Detectado al entrar por primera vez con la cuenta recién aprobada. El
login funcionaba y el sistema forzaba el cambio de contraseña, tal como exige el SRS §3.2.1
—"obliga a definir una contraseña definitiva antes de permitir cualquier otra acción"—,
pero la pantalla a la que redirigía era la de **recuperación**, que solo sabe enviar otra
contraseña temporal. El usuario quedaba en un bucle cerrado: pedir temporal → entrar con
temporal → que le pidan pedir otra temporal. Nunca podía activar su cuenta.

**Alcance real del fallo.** Afectaba a **todo** usuario nacido con credencial temporal: los
tres caminos de alta de cliente (conversión desde el embudo, entrada directa y
autorregistro), el reenvío de invitación, la recuperación de contraseña olvidada y cada
unidad de emergencia dada de alta con correo. Es decir, ninguna cuenta creada por el sistema
podía llegar a usarse; solo funcionaban las cuentas sembradas por script.

**Por qué estaba así.** El paso estaba especificado —`FR-UI-007` dice "pantalla
`password-reset` para solicitud (correo) **y cambio de contraseña definitiva**", y el
catálogo lo recoge como CU-O04— pero nunca se implementó: no había endpoint en el contrato,
la pantalla solo traía la mitad del flujo, y `CredentialRepository.activate_credential()`
existía sin que nadie la llamara. La etapa `cambio_password` del asistente de incorporación
tampoco cambia la contraseña: solo marca la etapa como completada.

**Cambio.** Nuevo `POST /api/v1/auth/password-change`, autenticado, que exige la contraseña
vigente además de la nueva —sin eso, un token robado bastaría para apropiarse de la cuenta—,
rechaza menos de 8 caracteres y rechaza repetir la vigente, y deja `estadocredencial` en
`Activo`. La pantalla muestra ahora el formulario de contraseña nueva cuando el cambio es
forzado, y al terminar cierra la sesión abierta con la temporal para que el usuario entre
con la definitiva. Se documentó como `RF-AUT-006b` en el spec y se añadió al contrato.

**Verificación.** `python -m pytest` → 1603 passed, 2 skipped (4 nuevas de CU-O04).
`ng test` → 589 SUCCESS. En el navegador, recorrido completo: entrar con la temporal →
la pantalla pide la definitiva → guardar → `Dim_Credencial` queda en `Activo` → volver a
entrar con la definitiva ya no fuerza ningún cambio.

---

## 2026-08-11 — B6: la incorporación guiada no era alcanzable

Alcance: `backend/apps/cuentas_clientes/services/auth_service.py`,
`frontend/src/app/modules/cuentas-clientes/auth/{services,guards,pages}`,
spec `FR-UI-007` y `FR-UI-022`, contrato `auth-rbac.openapi.yaml` (`LoginData.cuenta`).

**Hallazgo (B6).** Con la cuenta ya aprobada y la contraseña definitiva puesta, el cliente
aterrizaba en "Mis tickets". El asistente de incorporación —que existe, funciona y muestra
las tres etapas del SRS §3.2.2— **solo se alcanzaba escribiendo la URL**: no había entrada
en el menú del cliente ni redirección tras el login. En la práctica la incorporación no
llegaba a ocurrir nunca, y con ella se quedaban sin hacer el perfil corporativo y las
preferencias operativas de las que dependen los avisos y los informes del cliente.

**Cambio.** El login devuelve ahora `cuenta` con `idcliente`, `estadoOnboarding` y
`onboardingPendiente`, resuelto con `ClienteRepository.find_by_admin_local`. Es `null` para
los usuarios internos de TSI. Con ese dato, tanto el login como la resolución de la raíz `/`
llevan al asistente por delante del home del rol: hasta completar la incorporación la cuenta
no está lista para operar. Un `returnUrl` explícito conserva prioridad, para no romper los
enlaces profundos.

**Nota sobre el contrato.** Es una ampliación aditiva de `LoginData`; los clientes que no
lean el campo no se ven afectados.

**Verificación.** `python -m pytest` → 1603 passed, 2 skipped. `ng test` → 594 SUCCESS
(5 nuevas). En el navegador: Teresa Beltrán inicia sesión y aterriza directamente en la
configuración inicial de su cuenta, en la etapa "Cambio de contraseña".

**Higiene de datos del entorno.** Las cuentas 920002 y 920003 compartían `admin_local_id`
porque, mientras B3/B4 estaban vivos, Pinot descartaba las escrituras y `_next_id()`
reutilizó el mismo identificador. Con dos cuentas para el mismo administrador local,
`find_by_admin_local` (LIMIT 1) resolvía de forma arbitraria. La cuenta huérfana se marcó
como `Rechazado_Anulado` —el estado de anulación del propio producto, que esa consulta ya
excluye— en vez de borrarla (R-01 del SRS). No es un defecto del sistema: es residuo de los
fallos ya corregidos.

---

## 2026-08-11 — B7: las preferencias operativas capturaban 2 de las 4 dimensiones del SRS

Alcance: `frontend/src/app/modules/cuentas-clientes/shared/preferencias-operativas-form.component.ts`
(nuevo, con sus pruebas), `.../incorporacion-clientes/pages/onboarding-wizard/`,
`.../gestion-cuenta/pages/preferencias/`, spec `FR-UI-013` y `FR-UI-014`.

**Hallazgo (B7).** Detectado al completar la incorporación guiada de una cuenta nueva. El
SRS §3.2.2 y §3.2.3 enumeran cuatro preferencias operativas —umbrales de alerta, canales de
notificación, zonas geográficas de interés y destinatarios de reportes— y la UI solo pedía
el canal y el teléfono. La pantalla de Gestión de Cuenta pedía todavía menos, y el canal
como campo de texto libre en vez de un selector. `Dim_Preferencias_Cliente` y el endpoint
ya soportaban las cuatro: era la interfaz la que nunca las preguntaba.

**Efecto verificado.** Tras completar la incorporación, la fila quedaba con
`umbrales_alerta {}`, `zonas_geograficas []` y `destinatarios_reportes ''`, sin forma de
corregirlo desde ninguna pantalla. `zonas_geograficas` no es un dato decorativo: decide qué
expedientes puede consultar el cliente (§3.6.4) y qué puede leer un partner consumidor de
datos —`ConsumoDatosService.zonas_contratadas()` es **fail-closed**, así que vacío significa
cero resultados, y el partner lo interpreta como "no hubo accidentes"—.

**Decisión de negocio (usuario, 2026-08-11).** El "umbral de alerta" es el **tiempo máximo
de llegada de la unidad**: el cliente fija unos minutos y se le avisa si un caso suyo los
supera. Se guarda como `{"tiempo_llegada_max_min": N}`.

**Cambio.** Un único componente `app-preferencias-operativas-form` con las cuatro
dimensiones, compartido por la incorporación y la gestión de cuenta —antes cada pantalla
capturaba un subconjunto distinto—. Las zonas se eligen con un selector encadenado país →
estado → condado alimentado del catálogo geográfico y se muestran como etiquetas con su
nombre; en ningún momento se escribe ni se enseña un identificador. El canal pasó de texto
libre a selector, y el teléfono solo se pide cuando el canal lo necesita.

**De paso.** La etapa de perfil corporativo llegaba vacía y obligaba a reescribir la razón
social y el nombre comercial que la cuenta ya había declarado, contra el principio del SRS
de heredar lo capturado "sin volver a digitarlos". Ahora se precarga. Y el encabezado de
preferencias muestra la razón social en lugar de `Cliente #920003`.

**Verificación.** `ng test` → 599 SUCCESS (5 nuevas sobre la serialización, incluidos los
centinelas `'null'` de Pinot). En el navegador, sobre la cuenta Rescate Vial Andino:
umbral 25 min, canal "ambos", zonas Cuauhtemoc y Benito Juarez, dos destinatarios. En base:
`umbrales_alerta {"tiempo_llegada_max_min":25}`, `zonas_geograficas [1,2]`,
`destinatarios_reportes` con ambos correos.

---

## 2026-08-11 — B8/B9: la pertenencia a la organización no se comprobaba en ningún sitio

Alcance: `backend/core/repositories/cuentas_clientes/cuenta_usuario_repository.py`,
`backend/apps/cuentas_clientes/services/{transferencia_propiedad_service.py,auth_service.py}`,
sus pruebas, y las pantallas de gestión de cuenta del frontend.

Ambos hallazgos salieron de la misma raíz: la pertenencia de un usuario a una organización
cliente vive en `Dim_Usuario_Cliente` —que Seguimiento y Soporte ya consultan para resolver
a qué cuenta pertenece alguien—, pero Cuentas y Clientes la deducía del `admin_local_id`.
Con ese criterio una organización tiene como mucho una persona, cuando el plan contratado
limita precisamente el «número máximo de usuarios» de la organización.

**B8 — Se podía transferir la cuenta a alguien de otra empresa.** El SRS §3.2.3 exige
designar a otro responsable «de su misma organización». `_cliente_role_users()` listaba a
**todo usuario activo con rol Cliente del sistema entero**, y el guardián de la operación,
`_is_eligible_transfer_target()`, solo comprobaba que estuviera activo y tuviera ese rol.
La comprobación de pertenencia no existía, pese a que el mensaje de error ya decía «Usuario
no pertenece a la cuenta». Verificado en el navegador: la lista de candidatos para
**Rescate Vial Andino** ofrecía a la responsable de **Empresa Demo Torres**.

Se añadieron `list_miembros`, `es_miembro` y `list_cuentas_del_usuario` al repositorio,
leyendo `Dim_Usuario_Cliente` e incluyendo al administrador local aunque le falte la fila de
vínculo. La lista de candidatos y el guardián usan ahora la pertenencia real. Tras el
arreglo, la lista solo ofrece a los miembros de la propia cuenta y el endpoint responde
`404 "Usuario no pertenece a la cuenta"` ante un intento entre organizaciones.

**Deliberadamente fuera de alcance:** `user_belongs_to_cliente`, que gobierna **quién entra**
a las pantallas de la cuenta, se dejó como estaba. Ampliarlo dejaría entrar a más gente y eso
es una decisión de permisos, no una corrección.

**B9 — Se podía iniciar sesión con la organización dada de baja.** El SRS §3.2.1 es
explícito: el login falla si la persona fue desactivada **y si la organización a la que
pertenece fue dada de baja**, y llama a ambas validaciones obligatorias. La segunda no
existía. La baja marcaba la cuenta como `Dado de baja` y expulsaba las sesiones abiertas,
pero nada impedía abrir una nueva: el personal de un cliente cuyo contrato terminó seguía
entrando y operando con normalidad.

El login comprueba ahora las cuentas del usuario y lo rechaza si todas están dadas de baja.
Quien no pertenece a ninguna cuenta cliente —el personal interno de TSI— no se ve afectado.

**Verificación.** `python -m pytest` → 1607 passed, 2 skipped (4 nuevas). `ng test` → 599
SUCCESS. Contra el sistema en marcha, tras dar de baja la cuenta E2E: el usuario de esa
organización pasó de **200 a 401**, un cliente con cuenta activa sigue en 200 y el
Administrador interno también.

**De paso.** Se retiraron los identificadores crudos de las pantallas de perfil,
transferencia, baja e incorporación, que ahora nombran la cuenta por su razón social
(§8 del `design-system.md`).

**Comprobado y correcto, sin cambios.** La baja es lógica: la fila del cliente conserva su
razón social y su historial de incorporación, y las sesiones quedan en `Expulsado`, no
borradas. El cliente no puede abrir la pantalla de baja —es del Administrador (SRS §3.2.3)—
y el control de acceso lo impide correctamente.

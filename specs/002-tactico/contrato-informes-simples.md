# Contrato común — Informes tácticos simples

**Fecha:** 2026-08-14
**Alcance:** los **66 listados** por construir del catálogo
`informestacticos/TSI-Informes-Tacticos-Requeridos-por-OT.md`, repartidos en 8 departamentos.
**Estado:** define el **backend**. La ubicación en pantalla se decide por separado y **no** debe
influir en este contrato.

Este documento existe para que las 8 specs de departamento no inventen ocho esquemas distintos de
paginación, filtro y envelope. Lo que aquí se fija **no se vuelve a discutir** en cada spec: cada
una solo declara sus informes, sus tablas y sus roles.

---

## 1. Qué es un informe simple, operativamente

Un listado llano sobre la BDR: **una tabla, filtros, orden y paginación**. Nada más.

**La prueba de pertenencia.** Si el informe necesita `GROUP BY`, `COUNT`, `SUM`, `AVG`, una serie
temporal, un ratio o datos de una segunda tabla de hechos, **no pertenece a este contrato**: es
compuesto y va por la vía de ClickHouse. No hay casos intermedios que negociar.

> **Si el informe es compuesto, sus reglas están en otro sitio.** Desde 2026-08-14 los informes
> compuestos se resuelven **con una consulta sobre el modelo analítico**, no creando una tabla y un
> flujo por informe. Antes de especificar uno, leer:
>
> - [`modelo-analitico/contracts/contrato-consumo.md`](modelo-analitico/contracts/contrato-consumo.md)
>   — las 8 reglas de consulta. La 2 es obligatoria y su omisión produce **cifras infladas de forma
>   intermitente**: los hechos de instantánea acumulada y las dimensiones exigen forzar la versión
>   final.
> - [`modelo-analitico/contracts/esquema-analitico.md`](modelo-analitico/contracts/esquema-analitico.md)
>   — el esquema, y el §4.bis con el procedimiento para añadir un hecho, una dimensión o una métrica
>   si el modelo aún no cubre lo que el informe necesita.
>
> El módulo `Emergencias/informes-tacticos-compuestos/` queda **sustituido**: su diseño de una tabla
> por informe es justo lo que el modelo reemplaza.

**La única excepción permitida** es resolver un identificador contra su tabla catálogo para mostrar
la etiqueta en vez del número (`idseveridad` → `Dim_Severidad.severidad`). Es una traducción, no una
agregación, y además la exige `design-system.md` §8, que prohíbe mostrar identificadores internos en
pantalla. Se resuelve con una segunda consulta al catálogo y un mapeo en memoria — el patrón que ya
usa `registro_repository._nombres_calles()`.

---

## 2. Contrato HTTP

Se hereda `.specify/docs/architecture/api-standards.md`. Lo específico de estos endpoints:

| Aspecto | Convención |
|---|---|
| **Ruta** | `/api/v1/informes/<departamento>/<informe>` en kebab-case |
| **Método** | `GET`, siempre. Un listado no muta nada. |
| **Autenticación** | Bearer JWT, obligatoria. Sin excepciones anónimas. |
| **Éxito** | `{ "data": [...], "meta": { "pagination": {...}, "filtros": {...}, "acotado_a": "propios\|todos" } }` |
| **Error** | `{ "error": "...", "detail": "...", "code": "..." }` |
| **Paginación** | Cursor, nunca página. `?cursor=<opaco>&limit=<n>` |
| **Límite** | `limit` por defecto **50**, máximo **500**. Un `limit` mayor responde `400`, no se recorta en silencio. |

**Ejemplo de ruta:** `/api/v1/informes/cuentas-clientes/solicitudes-pendientes`

El segmento `<departamento>` es el del catálogo, no el de la app Django que lo implementa. Así el
consumidor no necesita saber que los listados de Emergencias viven repartidos entre `accidentes`,
`despacho` y `seguimiento`.

---

## 3. Filtros

### 3.1 El período es opcional, y esto es un cambio deliberado

`apps/informes_tacticos/periodo.py` exige `desde` y `hasta`: los 19 informes agregados existentes
son todos series temporales y sin rango no significan nada.

**En los listados eso es falso.** "Solicitudes de alta pendientes", "cuentas por estado" o
"credenciales próximas a vencer" describen el **estado actual**, no un intervalo. Exigirles un rango
obligaría al consumidor a inventar uno.

Por tanto:

- Los listados de **estado actual** no aceptan `desde`/`hasta`. Declararlos es `400`.
- Los listados de **hechos del período** (facturas emitidas, bajas de unidad, escalados) aceptan
  `desde`/`hasta` **opcionales**; omitirlos devuelve todo el histórico paginado.
- **Ninguno** acepta `granularidad`: eso es de agregados, y aquí no hay agrupación.

Cada spec de departamento declara, informe por informe, a cuál de los dos tipos pertenece.

### 3.2 Filtros propios

Cada informe declara los suyos como query params planos, en `snake_case`, y todos son **opcionales**.
Un valor no reconocido en un filtro de enumeración responde `400` nombrando los válidos — nunca se
ignora en silencio.

### 3.3 Orden

`?orden=<campo>` y `?dir=asc|desc`. Cada spec declara qué campos admite y cuál es el defecto. El
orden por defecto debe ser **estable y determinista** (típicamente la clave primaria descendente),
porque sin él la paginación por cursor devuelve filas repetidas o saltadas.

---

## 4. Reglas de Pinot que este contrato hace obligatorias

Las tres trampas que ya causaron defectos reales en este sistema. No son recomendaciones.

**1. `NULL` no existe: se comparan centinelas.** Pinot convierte todo nulo en `'null'` (texto), `0`
(métrica) o `Long.MIN_VALUE` (fecha). **Está prohibido usar `IS NOT NULL` como filtro de
completitud** — es siempre cierto. Es el defecto que hoy hace que el informe de completitud de
campos críticos mida la nada (`registro_repository.py:91`). Todo filtro de "campo ausente" compara
contra el centinela explícito.

**2. Sin JOIN.** Si el listado necesita dos tablas de hechos, no es un listado. Ver §1.

**3. El `LIMIT` es explícito.** `core/pinot/client.py:79` ya inyecta `LIMIT 10_000` a toda consulta
que no lo declare, así que el recorte silencioso a 10 filas está neutralizado. Aun así, **cada
consulta de listado declara su propio `LIMIT` derivado del `limit` de la petición**: apoyarse en el
tope global significa traer 10.000 filas para mostrar 50.

**4. Las escrituras tardan 5–15 s en ser visibles.** Un listado leído justo después de escribir
puede no mostrar el registro nuevo. **No es un fallo**: no se compensa con reintentos ni con
esperas; se documenta en la spec del departamento donde importe.

**5. Verificar el tipo declarado de toda columna temporal ANTES de diseñar su filtro.**
*(Añadido el 2026-08-15, lección de Ventas y CRM → Suscripciones.)*

El sistema **no es uniforme**. Casi todas las marcas de tiempo son `LONG` en milisegundos, pero
`Dim_Prospecto.demo_expiracion` es `STRING` **y con tres formatos conviviendo** (`Z`, `+00:00` y sin
zona). Comparar esa columna entera en SQL da resultados incorrectos **sin ningún error visible**:
filas vigentes desaparecen del listado y la respuesta sigue siendo un `200` plausible.

| Tipo declarado | Filtro |
|---|---|
| `LONG` epoch-ms | Comparación completa en la base. Nada especial. |
| `STRING` con formato ISO | **Prefiltro por el prefijo `YYYY-MM-DD`** + refinamiento en el servicio. Y hay que **declarar que una página puede devolver menos filas que el `limit`**. |

El coste de no comprobarlo es asimétrico: asumir `LONG` cuando es texto produce un informe que
miente; asumir texto cuando es `LONG` solo produce complejidad de más. En Suscripciones, comprobar
que `Dim_MetodoPago.fechaexpiracion` era `LONG` **antes** de diseñar evitó arrastrar el filtro en dos
pasos a un sitio donde no hacía falta.

---

## 5. Permisos

Se reutiliza el patrón de `apps/informes_tacticos/permissions.py`: una clase por conjunto de roles,
que valida contra `.specify/docs/actors.md` y falla cerrado.

**Regla transversal:** el acceso a un listado **nunca es más amplio que el acceso a la pantalla
operativa del mismo dato**. Si un Gerente de Ventas solo ve sus prospectos asignados, el listado
táctico de prospectos acotado a él devuelve lo mismo. Un informe no puede ser la puerta trasera que
salta un acotamiento — es exactamente el fallo que casi se cuela en F18 con el rol de partner.

**Excepción única: la autoridad departamental.** Un responsable de departamento accede a los
informes de su departamento **sin el acotamiento por titularidad**, porque su función es supervisar y
no tiene pantalla operativa que espejar. Quién es esa autoridad en cada departamento lo fija
[`acceso-tactico.md`](acceso-tactico.md), derivado del §5.1 del SRS.

**La excepción no alcanza al dato sensible.** Coordenadas, identidad de personas, secretos de
autenticación, medios de cobro y texto interno siguen excluidos **de todos los informes, para todos
los roles**: son exclusiones constitucionales, no de acotamiento.

Cada spec declara los roles de sus informes y, cuando aplique, **el acotamiento por titularidad**
(propios vs todos) — que se aplica al responsable operativo, no a la autoridad.

### 5.1 El resolutor de acotamiento es uno solo *(añadido el 2026-08-15, desde Ventas y CRM)*

`backend/core/informes/acotamiento.py` implementa la regla para los siete departamentos que acotan.
No se reimplementa por departamento: **la primera divergencia es una fuga de datos**, y es
exactamente lo que casi ocurre en F18 con el rol de partner.

| Rol del solicitante | No indica titular | Indica otro titular |
|---|---|---|
| Rol amplio (Administrador, autoridad departamental) | Ve **todos** | Filtra por ese titular |
| Rol acotado (Gerente, Cliente, Partner, Proveedor…) | Forzado **a lo suyo** | **Negativa `403`** |
| Cualquier otro | Negativa | Negativa |

**Pedir lo ajeno es `403`, nunca sustitución silenciosa.** Devolverle su propia cartera a quien pidió
la ajena le oculta que pidió algo indebido —no puede corregir lo que no sabe que hizo mal— y produce
un informe que **responde a una pregunta que nadie hizo**.

El resolutor devuelve **a quién** acotar. **Por qué columna** lo decide cada repositorio, y cambia
por listado: `idusuario` en la cartera de prospectos, `idusuariogerentenotificado` en las
notificaciones. Esa separación es la que permite reutilizarlo cuando el eje sea cliente, partner,
proveedor o zona contratada.

### 5.2 `meta.acotado_a` es obligatorio en todo listado que acote

Declara si el resultado está limitado a la titularidad del solicitante (`propios`) o abarca a todos
(`todos`).

**Sin él, un resultado vacío es ambiguo.** Un Gerente no puede distinguir «no hay prospectos
perdidos» de «no hay prospectos perdidos **míos**» — que es la misma ambigüedad que la negativa
explícita evita en el otro extremo, aplicada al caso en que la petición sí fue legítima.

Un rol amplio que filtra por un titular concreto sigue declarando **`todos`**: no ha reducido su
alcance, ha elegido mirar a uno. Declararlo `propios` le haría creer que ve su propia cartera.

**Es opcional para los listados sin eje de titularidad** —los ocho del módulo piloto—, que no lo
emiten. Obligarles a declararlo les haría inventarse un valor que no significa nada.

### 5.3 El criterio de pertenencia se declara por listado *(añadido el 2026-08-15, desde Red Operativa)*

⚠️ **«Pertenecer a una organización» significa dos cosas distintas en este sistema**, y ninguna es
la correcta en abstracto:

| Criterio | Quién cumple | Pantallas que lo usan |
|---|---|---|
| **Administrador local** | **Una sola persona** por cuenta | Alta de unidades, facturación |
| **Vínculo a la cuenta** | **Cualquier miembro** | Expediente de cliente, tickets |

`core/informes/pertenencia.py` los expone nombrados, y **cada listado declara el suyo**. No es una
opción de configuración: es una afirmación sobre a qué pantalla está espejando ese listado.

**Unificarlos rompería la regla de §5 en un departamento u otro.** Con el criterio amplio, un
empleado al que la pantalla de alta de unidades rechaza vería por informe la flota completa de su
organización — la puerta trasera exacta que la regla prohíbe. Con el estricto, los usuarios de
Soporte perderían sus propios tickets.

> **Trampa conocida.** `CuentaUsuarioRepository.get_cliente_ids_for_user` **suena** a criterio
> amplio y es el estricto: solo mira `admin_local_id`. El amplio real es `list_cuentas_del_usuario`.

### 5.4 Un listado cuyo alcance pueda malinterpretarse lo declara en su respuesta

Cuando el nombre de un listado o de sus campos pueda leerse como algo que el listado **no** dice, la
respuesta lo declara en `meta.alcance`.

Lo introduce el listado de flota de Red Operativa, y el motivo es de consecuencia y no de estilo:
`dado_de_alta` significa que la unidad **existe**, no que pueda acudir. La disponibilidad operativa
—`Activa`, `Ocupada`, `En Misión`, `Fuera de servicio`— vive solo en el histórico y **no está en ese
listado**. Un consumidor que lo leyera como cobertura decidiría sobre unidades fuera de servicio,
ocupadas o ya en camino a otro accidente.

Tres defensas, y las tres hacen falta:

1. el **nombre del campo** dice lo que el dato significa (`dado_de_alta`, no `disponible`);
2. la respuesta **declara su alcance**, para quien no leyó la spec;
3. **ningún campo** promete un dato que el listado no tiene.

**Solo lo declara el listado que lo necesita.** Añadirlo a todos convertiría una advertencia
deliberada en ruido, y el consumidor dejaría de leerla.

### 5.5 El repositorio enumera las columnas que devuelve *(añadido el 2026-08-15, desde Partners y API)*

Ninguna consulta de un listado usa `SELECT *`. Cada repositorio declara su **lista blanca** de
columnas, y una prueba lee el propio fichero para comprobar que ninguna consulta literal pide todas.

El motivo no es de estilo. La alternativa natural —quitar los campos sensibles al construir la fila,
o filtrarlos con una lista negra— **pasa las pruebas de hoy y falla el día que alguien añada una
columna sensible a la tabla**: el campo nuevo entra por la consulta, atraviesa el filtro que no lo
conoce y se publica. Falla abierta y en silencio, que es la peor forma de fallar en algo que decide
qué datos salen.

Lo introduce `Dim_CredencialAPI`, cuyo `client_secret_hash` autentica a quien lo tenga; aplica igual
al medio de cobro de Suscripciones y al contacto del proveedor en Red Operativa. La lista negra puede
conservarse como segunda línea, nunca como la primera.

El **contrato OpenAPI** es la tercera: una prueba comprueba que el documento no declare esos campos.
Si un día apareciera ahí, la implementación tendría permiso escrito para publicarlo.

### 5.6 El acotamiento por cobertura no es acotamiento por titularidad *(añadido el 2026-08-15, desde Emergencias)*

Los tres primeros ejes acotan por **quién es el dueño de la fila**: el ejecutivo de un prospecto, la
cuenta de una suscripción, el partner de una credencial. Emergencias introduce un cuarto que no lo
hace: un cliente no ve «sus» accidentes —no son suyos en ningún sentido— sino los de **las zonas que
tiene contratadas**.

Cambian las tres cosas a la vez, y por eso vive en su propio módulo (`core/informes/cobertura.py`) en
vez de ser un parámetro más de `resolver_organizacion`:

| | Ejes de titularidad | Eje de cobertura |
|---|---|---|
| Lo que se resuelve | un identificador | **un conjunto de ubicaciones** |
| Cómo filtra el repositorio | `= x` | **`IN (…)`** |
| No tener nada | no se da | **cero resultados** |

**`meta.acotado_a` toma un valor propio: `zonas_contratadas`.** Reutilizar `propios` diría algo
falso —que el listado abarca lo que le pertenece— cuando abarca lo que ocurrió donde contrató
cobertura.

**Dos reglas que un eje de conjunto obliga a escribir:**

1. **Conjunto vacío no es «no filtrar».** `None` significa «sin filtro»; `frozenset()` significa
   «ninguna ubicación». Confundirlos da el listado completo a quien no contrató nada, y sin ruido: la
   respuesta conserva la forma correcta. Un `if zonas:` que se salte el filtro cuando el conjunto
   está vacío cae exactamente en la lectura peligrosa, así que la guarda se escribe **explícita**.
2. **El conjunto se resuelve una vez, antes de consultar.** Traducir la cobertura a ubicaciones
   encadenando catálogos cuesta un número fijo de consultas por petición. Comprobarla fila a fila
   —como hace hoy el módulo operativo, a diez líneas de donde hace lo correcto— no es un filtro: el
   trabajo crece con las filas recorridas, y crece **más** cuando las zonas del cliente son escasas,
   que es cuando menos resultados va a haber.

### 5.7 Una exención de autoridad no levanta una exclusión constitucional *(añadido el 2026-08-15, desde Emergencias)*

La autoridad departamental está exenta del **acotamiento**: ve todas las cuentas, todas las zonas,
todas las situaciones. **No está exenta de las exclusiones de dato sensible.**

Lo introduce Emergencias, donde las dos cosas conviven en el mismo listado: el Director de
Operaciones ve los casos de todas las zonas, y **sigue sin ver las coordenadas del accidente ni la
identidad de los implicados**. Son exclusiones que la constitución impone sobre el dato, no sobre
quién pregunta, y un cargo no las levanta.

La distinción importa porque el camino contrario es fácil de recorrer sin querer: quien implementa
una exención de alcance puede leerla como «este rol lo ve todo». Cada listado con dato excluido lleva
una prueba **con la autoridad del departamento**, no solo con el rol acotado.

---

## 6. Lo que se reutiliza tal cual

De `apps/informes_tacticos/`, que está bien construido y sería un error rehacer:

| Pieza | Uso |
|---|---|
| `envelope.py` → `informe_response()` | Envelope `{data, meta}`. Se extiende con `pagination`. |
| `periodo.py` → `Periodo`, `parse_periodo()` | Solo para los listados de hechos del período, con el rango pasado a opcional. |
| `permissions.py` | Patrón de clase de permiso; **no** las clases concretas, que son de Emergencias. |
| `core/pinot/client.py` | Cliente y su `_with_explicit_limit`. |
| `core/pinot/tiempo.py` | Sellado de marcas de tiempo. |

---

## 7. Dónde vive cada cosa

**Specs**, una por departamento:

```
specs/002-tactico/<Departamento>/informes-tacticos-simples/backend/
    spec.md  plan.md  tasks.md  data-model.md  research.md
    quickstart.md  traceability.md
    contracts/informes-tacticos-simples.openapi.yaml
```

Departamentos: `Cuentas-Clientes`, `Ventas-CRM`, `Suscripciones-Facturacion`, `Red-Operativa`,
`Partners-API`, `Emergencias`, `Soporte-Cliente`, `Analitica-Inteligencia`.

**Código**, dentro de la app del departamento que ya existe:

| Departamento | App Django | Listados |
|---|---|:--:|
| Cuentas y Clientes | `apps/cuentas_clientes` | 10 |
| Ventas y CRM | `apps/ventas_crm` | 8 |
| Suscripciones y Facturación | `apps/suscripciones` | 9 |
| Red Operativa | `apps/red_operativa` | 8 |
| Partners y API | `apps/partners` | 5 |
| Emergencias | `apps/accidentes`, `apps/seguimiento` | 5 |
| Soporte al Cliente | `apps/soporte_cliente` | 5 |
| Analítica e Inteligencia | ⚠️ **`apps/analitica` no existe** | 5 |

> **Decisión pendiente.** Analítica e Inteligencia es el único departamento sin app propia. Sus 5
> listados son además los que dependen de tablas que aún no existen (programación de informes,
> registro de modelos). Se recomienda **dejarlo para el final** y decidir entonces si nace como app
> propia o si sus listados se reparten.

Dentro de cada app, los listados van en un submódulo propio para no mezclarse con la operación:

```
apps/<departamento>/
    views/informes_views.py
    services/informes_service.py
    urls.py            (añade las rutas /informes/...)
core/repositories/<departamento>/informes_repository.py
```

---

## 8. Lo que este contrato NO define

- **La pantalla.** Qué informe se ve dónde, en qué tablero y con qué agrupación visual es una
  decisión de frontend, posterior y separada. Ningún endpoint debe asumir una pantalla.
- **La exportación.** Si los listados se descargan en CSV o Excel, y con qué permisos.
- **La programación.** Envío periódico por correo es OT14 y depende de una tabla que no existe.

---

## 9. Módulo renombrado, no superado

`specs/002-tactico/Emergencias/informes-tacticos-agregados/` describe los **19 informes agregados**
hoy en producción (`backend/apps/informes_tacticos/`).

**Se llamaba `informes-tacticos-simples`, y se renombró el 2026-08-14** por dos razones: su nombre
decía "simples" con el significado del proyecto —*una tabla en Pinot, sin ClickHouse*—, no con el de
este contrato; y ocupaba el nombre que necesitaba el módulo de listados de Emergencias. El nombre
nuevo describe lo que el módulo realmente contiene.

**El código no se tocó**: sigue vivo, en producción y en su mayoría verificado. Lo que cambió es
la carpeta de su spec y las referencias internas.

**No debe tomarse como precedente de forma ni de nomenclatura** para los listados nuevos: sus
informes agregan, y por eso ahora lo dice su nombre.

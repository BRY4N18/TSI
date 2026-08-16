# Contrato común — Informes tácticos simples (frontend)

**Fecha:** 2026-08-15
**Alcance:** los **32 endpoints** de listados tácticos simples ya construidos en backend, repartidos
en 7 departamentos.
**Contraparte:** [`contrato-informes-simples.md`](contrato-informes-simples.md) — el contrato de
backend. Lo que allí se decidió **no se vuelve a decidir aquí**; este documento dice cómo llega a la
pantalla.

Este documento existe por la misma razón que su contraparte: **los 32 listados son la misma pantalla
32 veces**. Sin una capa común saldrían siete tablas distintas resolviendo cursor, filtros y errores
cada una a su manera, y la primera que se despistara abriría el hueco. Es exactamente lo que
`core/informes/` evitó en backend.

---

## 1. Qué hay ya construido, y qué no

| Pieza | Estado |
|---|---|
| `shared/ui/list-states/` — vacío, error, skeleton, clases de tabla | ✅ Existe. **Se reutiliza tal cual.** |
| `shared/ui/icon/` — iconos Tabler | ✅ Existe |
| Paginación por cursor | ⚠️ Resuelta **a mano** en `lista-accidentes` (pila de cursores). No es compartida. |
| Barra de filtros | ⚠️ Reescrita en cada página |
| `meta.acotado_a` en pantalla | ❌ **No existía.** Lo añade este contrato. |
| `meta.alcance` en pantalla | ❌ **No existía.** Lo añade este contrato (§2.4). |
| Manejo del `400` de filtro/límite | ❌ **No existía** como patrón |

Lo que este contrato añade es lo de las cuatro últimas filas.

> **Estado al 2026-08-15:** implementado y verificado en navegador en los siete departamentos. Los
> tres valores de `acotado_a` y la advertencia de `alcance` se comprobaron contra el backend real.

---

## 2. Las cuatro cosas que el backend garantiza y la pantalla puede tirar a la basura

Son las que justifican que exista este documento. Si el frontend las pierde, buena parte del trabajo
de backend deja de tener efecto — y **sin que nada falle**, que es lo que las hace peligrosas.

### 2.1 `meta.acotado_a` se muestra siempre que venga

El backend lo emite para que **un resultado vacío no sea ambiguo**. Un cliente tiene que poder
distinguir «no hubo accidentes graves» de «no hubo accidentes graves **en mis zonas**». Si la tabla
lo ignora, vuelve exactamente la ambigüedad que costó construirlo.

Toma **tres valores**, no dos:

| Valor | Qué significa | Cómo se presenta |
|---|---|---|
| `todos` | Sin acotar | **No se muestra nada.** Es el caso normal; un aviso permanente sería ruido |
| `propios` | Limitado a la titularidad del solicitante | Aviso: *«Solo tus registros»* |
| `zonas_contratadas` | Limitado a la cobertura contratada | Aviso: *«Solo las zonas que tienes contratadas»* |

**El aviso acompaña al resultado vacío, no solo al lleno.** Es justo cuando no hay filas cuando la
ambigüedad muerde: el estado vacío tiene que decir *«no hay resultados **entre los tuyos**»*.

> ⚠️ **`zonas_contratadas` no es `propios`.** Los accidentes de una zona contratada no pertenecen al
> cliente. Un texto que diga «tus accidentes» afirma algo falso sobre datos de siniestralidad ajenos.

### 2.2 Un `400` se muestra como error, nunca como tabla vacía

El backend **rechaza** en vez de recortar: `limit` sobre el máximo, filtro de enumeración con valor
desconocido, rango de fechas en un listado de estado actual, cursor corrupto. Todos responden `400`
con un `detail` que **nombra los valores válidos**.

Un frontend que capture el error y pinte la tabla vacía reintroduce el fallo silencioso que la regla
evita: el consumidor vería «no hay resultados» donde el sistema dijo «tu petición está mal».

- El `detail` del backend **se muestra tal cual**. Está escrito para que quien lo lea pueda corregir
  la petición sin abrir la spec; sustituirlo por un «Ha ocurrido un error» tira esa información.
- Un `400` **no** ofrece «Reintentar»: reintentar lo mismo da lo mismo. Ofrece corregir el filtro.
- Un `403` tampoco es una tabla vacía. Dice que no tienes acceso, que es distinto de que no haya
  datos — y es la diferencia que el backend eligió a propósito frente a devolver `200 data: []`.

### 2.3 El cursor es opaco: **no hay números de página**

Esto **restringe el diseño**, y conviene saberlo antes de dibujar nada:

- No hay total de resultados. **No se puede mostrar «120 registros» ni «página 3 de 8».**
- No se puede saltar a una página arbitraria.
- Solo se sabe si hay siguiente (`meta.pagination.has_next`).

La navegación es **siguiente / anterior**, con «anterior» resuelto en el cliente guardando los
cursores ya visitados. Es lo que `lista-accidentes` ya hace a mano y lo que la capa común absorbe.

> Inventar un contador —«mostrando 1–50 de muchos»— o paginar con números obligaría a contar filas,
> que es justo lo que la paginación keyset evita para no repetir ni saltar registros con ingesta
> continua.

### 2.4 `meta.alcance` advierte de una lectura equivocada, y se muestra siempre

Distinto de `acotado_a`, y conviene no confundirlos:

| | Responde | Cuándo se muestra |
|---|---|---|
| `acotado_a` | **a quién** pertenece lo que se ve | cuando es distinto de `todos` |
| `alcance` | **qué describe** el listado | **siempre que venga**, con filas o sin ellas |

Lo emite **un solo listado**: la composición de flota de Red Operativa. `dado_de_alta` significa que
la unidad **existe**, no que pueda acudir — su disponibilidad operativa vive en el histórico y no
está en ese listado. Quien lo leyera como cobertura decidiría sobre unidades fuera de servicio,
ocupadas o ya en camino a otro accidente.

Se muestra también con la lista vacía porque advierte de **una lectura equivocada del listado**, no
de un recorte de los datos: no depende de que haya filas.

**Un valor desconocido no se pinta crudo.** `meta.alcance` es un identificador, no un texto para el
usuario; mostrarlo tal cual daría una advertencia ilegible justo donde hace falta que se entienda.

---

## 3. Forma de la capa compartida

```
shared/informes/
    informes-listado.types.ts      Envelope, paginación, filtros, error
    informes-listado.service.ts    GET genérico: arma query, pagina, traduce errores
    informes-listado.component.ts  Tabla + estados + paginación + aviso de alcance
    informes-filtros.component.ts  Barra de filtros declarativa
```

**Un solo servicio para los 32 endpoints.** Todos comparten contrato, así que el servicio recibe la
ruta y los filtros; no hay un servicio por departamento. Lo que sí es propio de cada listado es la
**declaración de columnas y filtros**, que vive en su módulo.

### 3.1 Las columnas se declaran, no se maquetan

Cada listado declara un arreglo de columnas —clave, etiqueta, alineación y formato— y el componente
común pinta la tabla. Maquetar 32 `<table>` a mano garantiza que se desalineen.

**El formato de una celda ausente es del componente, no de cada página.** El backend devuelve `null`
para lo ausente de forma deliberada —una calificación sin poner no es un cero, una hora de fin
ausente no es 1970— y la pantalla lo pinta con un guion, nunca con `0`, `—` inventado por la página
ni cadena vacía.

### 3.2 Los filtros se declaran, no se reescriben

Cada listado declara sus filtros con tipo (`texto`, `numero`, `booleano`, `enumeracion`, `fecha`) y
el componente común arma el formulario y la query. Con eso:

- un filtro sin valor **no viaja** en la URL — coherente con que `meta.filtros` solo refleja los
  aplicados;
- las enumeraciones se pintan como desplegable con los valores válidos, que es la mejor forma de que
  el `400` no llegue a producirse.

### 3.3 El rango de fechas solo aparece donde el listado lo admite

El backend distingue **estado actual** (rechaza `desde`/`hasta` con `400`) de **hechos del período**
(los acepta opcionales). La declaración del listado lo dice, y la barra de filtros **no pinta** el
selector de fechas en los de estado actual.

Mostrarlo y dejar que el backend lo rechace sería ofrecer un control que solo sirve para provocar un
error.

---

## 4. Reglas de accesibilidad y responsive

Se hereda lo que el proyecto ya aplica en `lista-accidentes` y en `list-table.styles.ts`:

- **Tabla en escritorio, tarjetas en móvil** (`hidden md:table` + tarjetas). Una tabla de ocho
  columnas en un teléfono no se lee.
- Los estados vacío, error y cargando ya tienen componente y `data-testid`; **se reutilizan**.
- El aviso de alcance es texto, no solo color: un `badge` que solo se distinga por el tono no informa
  a quien no distingue esos tonos.

---

## 5. Qué NO entra en la capa común

| Fuera | Por qué |
|---|---|
| Exportación a CSV/Excel | Fuera de alcance en las 7 specs de backend |
| Gráficas | Son de informes **agregados**, que ya tienen su camino (`workpanels` de Emergencias) |
| Edición en línea | Los 32 endpoints son de **solo lectura** |
| Guardar filtros del usuario | No hay backend para ello; inventarlo aquí crea estado que nadie persiste |
| Recuento total de resultados | ⛔ Imposible con cursor. Ver §2.3 |

---

## 6. Dónde vive cada cosa

```
frontend/src/app/
    shared/informes/                       ← la capa común (este contrato)
    modules/<departamento>/informes/
        <listado>.page.ts                  ← declara columnas y filtros
        <departamento>-informes.routes.ts
        guards/<departamento>-informes.guard.ts
```

El guard de rol por departamento **ya tiene precedente**: `emergencias-informes.guard.ts`. Se sigue
el mismo patrón, con los roles que el permiso de backend declara — y con la misma regla: el guard
abre la puerta, **el alcance lo decide el backend**. Un guard nunca decide qué filas se ven.

---

## 7. Verificación

Cada listado, en su spec de departamento, comprueba al menos:

1. la tabla pinta las columnas declaradas y **ninguna más**;
2. `acotado_a` distinto de `todos` produce el aviso, **también con la lista vacía**;
3. un `400` muestra el `detail` del backend y **no** una tabla vacía;
4. un `403` se distingue de un resultado vacío;
5. la paginación avanza y retrocede sin repetir ni perder filas;
6. un valor ausente se pinta como ausente y **nunca como cero**.

Las tres primeras son las que este contrato existe para garantizar.

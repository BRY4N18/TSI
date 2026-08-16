# Contrato — Cómo un informe consulta el modelo analítico

**Fecha:** 2026-08-14 · **Esquema:** [`esquema-analitico.md`](esquema-analitico.md)

Reglas que **todo informe compuesto** debe respetar al consultar el modelo. No son
recomendaciones: cada una previene un fallo concreto que ya ha ocurrido en este proyecto o que el
diseño hace posible.

---

## Regla 1 — Ningún informe crea su propia tabla ⛔

Si un informe necesita un hecho, una dimensión o una columna que no existe, **se modifica el modelo**
—su spec y el flujo de carga del hecho correspondiente—, no se añade una tabla del informe.

**Por qué.** Es de donde venimos: tres informes, tres tablas. Sin esta regla, el primero que no
encaje añadirá la suya, el segundo también, y en veinte informes estaremos otra vez con una tabla
por informe, cifras que no cuadran entre sí y ~105 flujos de carga.

---

## Regla 2 — Toda consulta fuerza la versión final ⚠️

Las tablas con deduplicación pueden contener **temporalmente dos versiones de la misma fila** hasta
que la fusión ocurre en segundo plano. Aplica a **los dos hechos acumulados y a todas las
dimensiones**.

**Toda consulta debe forzar la versión final** con `FINAL` o equivalente.

**Por qué.** Sin ello, un informe devuelve cifras **infladas de forma intermitente**: correctas al
consultar después de una fusión, dobladas al consultar antes. Es el peor tipo de fallo posible en un
informe porque **no es reproducible** — quien lo reporte verá que "ahora sale bien".

---

## Regla 3 — Contar filas de despacho no es contar casos ⚠️

El hecho de despacho tiene grano de **intento**. Un caso con cuatro reasignaciones aporta **cuatro
filas**.

| Pregunta | Cómo se responde |
|---|---|
| ¿Cuántos intentos hubo? | Contar filas |
| ¿Cuántos casos se despacharon? | Contar **casos distintos** |
| ¿Cuántos se resolvieron al primer intento? | Filas con `numero_intento = 1` y resultado confirmado |

**Por qué.** Es la consecuencia directa del grano elegido, y la confusión más probable. Un informe
que cuente filas creyendo que cuenta casos **inflará la cifra en proporción a los rechazos** — es
decir, dará peor imagen cuanto peor haya ido la operación, en la dirección equivocada.

---

## Regla 4 — Un hito ausente no es un cero ni una fecha ⚠️

En los hechos acumulados, un hito no alcanzado se guarda ausente.

| Uso correcto | Uso incorrecto |
|---|---|
| Caso abierto = hito de cierre ausente | Tratar el ausente como fecha de carga |
| Promedio de duración solo sobre los cerrados | Promediar incluyendo los abiertos como duración cero |

**Por qué.** Un promedio de duración que incluya los casos abiertos como cero hunde la media, y
además **empeora cuanto más trabajo hay en curso** — justo al revés de lo que debería.

---

## Regla 5 — Elegir conscientemente entre historia y presente

Las dimensiones versionadas permiten dos lecturas, y **son distintas**:

| Lectura | Cómo | Cuándo |
|---|---|---|
| **Histórica** | Unir por la clave de versión que el hecho guarda | «Qué proveedor atendió estos despachos» |
| **Actual** | Unir por la clave de negocio y filtrar la versión vigente | «Qué proveedor tiene hoy estas unidades» |

**Por qué.** Ambas son legítimas y responden preguntas distintas. Elegir la equivocada da una cifra
plausible: la histórica reatribuiría el presente, y la actual **reescribe el pasado** — que es
exactamente el defecto que este modelo corrige.

---

## Regla 6 — Declarar desde cuándo la atribución es fiable ⚠️

Las versiones cuyo inicio no es un cambio observado están marcadas.

**Un informe que agrupe por un atributo versionado debe poder decir desde cuándo su atribución es
exacta.** Para la unidad y su proveedor, esa fecha es **la primera carga del modelo**: antes, nada en
el origen historiza ese cambio.

**Por qué.** Sin declararlo, el modelo cometería el error que corrige: presentar «no lo sabemos» como
«siempre fue así». Un informe de hace seis meses agrupado por proveedor, con historia que empieza
hoy, devolvería el proveedor actual para todo ese período **y parecería correcto**.

---

## Regla 7 — Filtrar por partición cuando se consulte un período

Los hechos se particionan por mes. Filtrar por la columna de fecha permite descartar particiones
enteras sin leerlas.

**Por qué.** Es la diferencia entre leer un mes y leer el histórico completo. No es corrección, es
que un informe que no filtre se volverá lento a medida que el histórico crezca, sin que nada avise.

---

## Regla 8 — Los datos sensibles no están, y no deben pedirse

El modelo **no contiene** coordenadas, identidad de personas implicadas, contacto de clientes ni
texto libre de notas.

Si un informe los necesitara, **no se añaden al modelo**: se replantea el informe. La constitución
somete esos datos a control de acceso y auditoría propios, y un almacén analítico consultable por
informes no es el sitio.

---

## Lista de verificación para un informe nuevo

Antes de dar por buena la consulta de un informe compuesto:

- [ ] No crea ninguna tabla propia (Regla 1)
- [ ] Fuerza la versión final en hechos acumulados y dimensiones (Regla 2)
- [ ] Si cuenta despachos, distingue intentos de casos (Regla 3)
- [ ] Si promedia tiempos, excluye los procesos sin cerrar (Regla 4)
- [ ] Si agrupa por un atributo versionado, eligió conscientemente historia o presente (Regla 5)
- [ ] Si agrupa por proveedor, declara desde cuándo la atribución es fiable (Regla 6)
- [ ] Filtra por fecha para descartar particiones (Regla 7)
- [ ] No requiere dato sensible (Regla 8)

# Contrato común — Informes estratégicos

**Fecha:** 2026-08-16
**Alcance:** los **80 informes** del catálogo
`informestacticos/TSI-Informes-Compuestos-Requeridos-por-OE.md`, repartidos en **6 objetivos
estratégicos (OE1–OE6)**.
**Estado:** define el **backend**. La pantalla se decide por separado y **no** debe influir aquí.
**Contraparte táctica:** [`specs/002-tactico/contrato-informes-simples.md`](../002-tactico/contrato-informes-simples.md).
**Sustrato:** [`specs/002-tactico/modelo-analitico/`](../002-tactico/modelo-analitico/) — el mismo
almacén analítico. **No se crea uno nuevo.**

Este documento existe por la misma razón que su contraparte táctica: para que las 6 specs de OE no
inventen seis formas distintas de declarar un período, una meta, una comparación y un dato que falta.
Lo que aquí se fija **no se vuelve a discutir** en cada spec: cada una declara sus informes, sus
fuentes y sus autoridades.

---

## 1. Qué es un informe estratégico, operativamente

**Los 80 son compuestos. No hay capa de listados.** No existe un listado llano que satisfaga a
quien decide sobre expansión, precios o inversión: la pregunta estratégica siempre es *cuánto,
comparado con qué, y respecto a qué meta*.

Por eso **no hay aquí el par simples/compuestos** que estructura la capa táctica. El eje de corte
es otro.

### La prueba de pertenencia

Un informe pertenece a esta capa si cumple **al menos dos** de estas cuatro:

| | Rasgo |
|:--:|---|
| 1 | **Agrega a nivel de empresa**, no de departamento ni de cola de trabajo |
| 2 | **Compara períodos** — mes contra mes, año contra año, o cohorte contra cohorte |
| 3 | **Se contrasta contra una meta** declarada del tablero BSC (§7 del marco) |
| 4 | **Cruza perspectivas** — Finanzas × Operación × Calidad × Cobertura |

Si solo cumple una, casi siempre es un informe **táctico** de supervisión departamental y su sitio
es `specs/002-tactico/`. La diferencia no es de tamaño ni de dificultad: es **de quién pregunta y
para decidir qué**.

> **El caso que más se va a confundir.** «Cumplimiento de SLA» existe en las dos capas. El táctico
> (OT19) responde *qué tickets voy a incumplir esta semana*; el estratégico (E5-04) responde *si el
> compromiso de ≥95 % se sostuvo el trimestre y en qué planes se rompe*. Misma tabla, distinta
> pregunta, distinto destinatario. **No se reutiliza el endpoint táctico**: su acotamiento y su
> ventana son los equivocados para esta pregunta.

---

## 2. Contrato HTTP

Se hereda `.specify/docs/architecture/api-standards.md`. Lo específico de estos endpoints:

| Aspecto | Convención |
|---|---|
| **Ruta** | `/api/v1/informes/estrategicos/<oe>/<informe>` en kebab-case |
| **Método** | `GET`, siempre |
| **Autenticación** | Bearer JWT, obligatoria. Sin excepciones anónimas. |
| **Éxito** | `{ "data": [...], "meta": { "periodo": {...}, "comparacion": {...}, "objetivo": {...}, "cobertura": "completa\|parcial" } }` |
| **Error** | `{ "error": "...", "detail": "...", "code": "..." }` |
| **Paginación** | **No hay cursor.** Un agregado devuelve su serie o su reparto completos. |
| **Rankings** | Los informes de tipo «top N» aceptan `?top=<n>`, por defecto **10**, máximo **100** |

**Ejemplo:** `/api/v1/informes/estrategicos/oe1/mrr-mensual`

El segmento `<oe>` es `oe1`…`oe6`. El `<informe>` es el nombre del catálogo en kebab-case, **no su
código**: `mrr-mensual`, no `e1-01`. El código vive en la spec y en la trazabilidad; la ruta debe
poder leerse sin el catálogo delante.

### 2.1 Por qué no hay paginación por cursor

Es la diferencia de forma más visible con la capa táctica, y no es una omisión.

Un listado táctico devuelve filas de las que **solo importan las primeras**: la cola se atiende por
orden. Un agregado estratégico devuelve **un reparto o una serie que solo significa entera**. Paginar
la distribución de la cartera por plan permitiría leer «el 40 % está en Básico» sin ver que falta la
mitad del reparto — una cifra correcta que induce una conclusión falsa.

Cuando el volumen sea grande el informe **acota por período o por top N**, que reduce la pregunta.
Nunca corta el resultado de una pregunta que ya se hizo.

---

## 3. El período aquí es obligatorio, y esto invierte la regla táctica

El contrato táctico hizo el rango **opcional** porque la mitad de sus listados describen el estado
actual. **Aquí es al revés y sin excepciones útiles.**

| Parámetro | Obligatoriedad | Valores |
|---|---|---|
| `desde` / `hasta` | **Obligatorios** | Fecha ISO. Omitirlos es `400`, no «todo el histórico». |
| `granularidad` | Obligatoria | `mes` · `trimestre` · `anio` |
| `comparacion` | Opcional, por defecto `ninguna` | `mom` · `yoy` · `ninguna` |

**Por qué obligatorio.** Un MRR sin período no es un número peor: no es un número. Y «todo el
histórico» como defecto silencioso produciría la cifra más plausible y más inútil de todas — un
acumulado desde el principio de los tiempos presentado junto a una meta mensual.

### 3.1 La comparación exige ventanas iguales

Cuando se pide `mom` o `yoy`, el período anterior tiene que tener **la misma longitud** que el
actual. Comparar un mes en curso de 11 días contra un mes completo de 30 da una caída del 63 % que
**no ocurrió**.

Dos consecuencias obligatorias:

1. El informe declara en `meta.comparacion` **las dos ventanas exactas** que comparó, no solo el
   porcentaje. Quien lea la cifra tiene que poder ver contra qué se calculó.
2. Si el período actual está **en curso**, se declara `parcial: true`. Un mes incompleto comparado
   contra meses cerrados es la forma más fácil de inventar una tendencia a la baja.

---

## 4. Metas: qué es un compromiso y qué es una conjetura

El catálogo marca cada meta con `[NORMATIVO]` o `[CALIBRAR]`, y **la diferencia tiene que llegar a
la respuesta**. Es la regla más importante de este contrato.

| Marca | Qué es | Cómo se presenta |
|---|---|---|
| `[NORMATIVO]` | Umbral técnico obligatorio adoptado como criterio del sistema (ISO/IEC 25010) | Semáforo real. Por debajo **es un incumplimiento**. |
| `[CALIBRAR]` | Valor de referencia **sin línea base**. Meta tentativa, no compromiso. | Se muestra como referencia. **Nunca como incumplimiento.** |

`meta.objetivo` lo declara siempre:

```json
"objetivo": { "valor": 99.99, "unidad": "%", "tipo": "NORMATIVO", "cumple": true }
```

```json
"objetivo": { "valor": 8, "unidad": "%", "tipo": "CALIBRAR", "cumple": null }
```

**`cumple` es `null` en todo objetivo `[CALIBRAR]`.** No es un `false` pendiente de comprobar: es la
afirmación de que la pregunta no se puede responder todavía porque el umbral no está calibrado
contra nada.

**Por qué importa tanto.** Pintar en rojo un `[CALIBRAR]` presenta como fracaso una meta que nadie
midió nunca — y la decisión que sigue a ese rojo (recortar un canal, cerrar un mercado) se toma
sobre una cifra inventada. Es el mismo fallo, en la dirección contraria, que el catálogo evita al
distinguir las dos marcas desde el origen.

---

## 5. Un dato que falta se declara; no se rellena ni se calla

El catálogo marca **5 informes ⛔ no construibles** y varios ⚠️ parciales. Esto es lo que se hace
con cada caso:

| Situación | Qué se construye |
|---|---|
| ⛔ **No construible** — falta la fuente entera (CAC, NPS, margen) | **No hay endpoint.** La spec lo declara, con el prerrequisito nombrado. No se publica un `200` vacío. |
| ⚠️ **Parcial** — la mitad es calculable (E2-01 sin precio de API) | Endpoint que devuelve **solo la parte medible** y declara `meta.cobertura: "parcial"` con `meta.falta: [...]` |
| **Período sin datos** | `data` vacío y `meta.cobertura: "completa"`. **No es un cero.** |

**Un `404` para lo no construible, no un `200` con ceros.** Un tablero que recibe ceros los pinta, y
un CAC de 0 € se lee como una captación gratis perfecta. El silencio de un endpoint que no existe es
recuperable; una cifra falsa en una diapositiva de dirección no lo es.

**Sin dato no es cero** es además la Regla 4 del modelo analítico, y aquí pesa más que en táctico:
un hito ausente promediado como cero hunde la media *y mejora cuanto peor va la operación*.

---

## 6. Reglas del modelo analítico: se heredan, no se repiten

Todo informe estratégico es una consulta sobre el modelo, así que le aplican **las 8 reglas** de
[`modelo-analitico/contracts/contrato-consumo.md`](../002-tactico/modelo-analitico/contracts/contrato-consumo.md)
sin ninguna atenuación. No se copian aquí. Las tres que más van a morder en esta capa:

- **Regla 1 — ningún informe crea su tabla.** Si un OE necesita un hecho o una columna que no
  existe, se amplía el modelo. El catálogo ya nombra los seis prerrequisitos (`registro_predicciones`,
  `registro_modelos`, `catalogo_productos_inteligencia`, encuestas NPS, programación de informes,
  `idpais` en `dim_cliente`). **Son cambios del modelo, no tablas de informe.**
- **Regla 2 — forzar la versión final.** En una serie anual de 12 puntos, un fallo intermitente de
  duplicación no se nota: da un mes alto que parece un buen mes.
- **Regla 8 — el dato sensible no está y no se pide.** Un informe de dirección no es una excepción:
  ningún cargo levanta una exclusión constitucional.

---

## 7. Un informe que sirve a dos OE se especifica una vez

El catálogo ya lo declara para **E3-02, E3-10, E3-11 y E3-12**, compartidos entre OE3 y OE6.

**La regla general:** el informe vive en el OE que **define su meta**, y el otro lo referencia. Nunca
se implementa dos veces «porque cada OE quiere el suyo» — dos implementaciones de la misma métrica
divergen, y entonces el tablero muestra dos latencias p95 distintas y nadie sabe cuál creer. Es
exactamente el problema que el modelo analítico existe para evitar, un nivel más arriba.

### 7.1 El catálogo cuenta preguntas, no endpoints ⚠️

Igual que pasó en táctico —donde 68 filas se resolvieron en 32 endpoints—, al cruzar los seis OE
aparecen **cuatro informes declarados dos veces con otro nombre**:

| Par | Es el mismo informe |
|---|---|
| **E1-06** y **E5-09** | Tasa de renovación de suscripciones |
| **E1-09** y **E5-13** | Tiempo de onboarding: registro a activación |
| **E1-10** y **E5-14** | Embudo de abandono en onboarding |
| **E1-11** y **E5-10** | Churn de cliente por cohorte |

No es un error del catálogo: OE1 los pide como resultado de la captación y OE5 como resultado de la
retención, y ambas lecturas son legítimas. Pero **son una sola consulta**, y se construyen una vez.

**El recuento real, entonces:**

| | Informes |
|---|:--:|
| Declarados en el catálogo | 80 |
| − duplicados entre OE1 y OE5 | −4 |
| **Distintos** | **76** |
| − no construibles ⛔ | −5 |
| **Por construir** | **71** |

Cada spec de OE declara, para los informes compartidos, **cuál es el OE dueño** y cuál referencia.

---

## 8. Permisos

**No los decide este contrato.** Viven en [`acceso-estrategico.md`](acceso-estrategico.md), que
aplica una regla propia de esta capa:

> **Un informe estratégico lo ve la autoridad del departamento dueño del dato que mide**, no toda la
> dirección por defecto.

Lo que sí fija este contrato, porque es transversal:

- **Fallar cerrado.** Se reutiliza el patrón de `apps/informes_tacticos/permissions.py` y las
  constantes de `backend/core/auth/roles_tacticos.py`, que ya nombran las ocho autoridades.
- **No hay acotamiento por titularidad.** Ningún informe de esta capa se acota a «lo propio»: son
  agregados de empresa. Por eso **`meta.acotado_a` no se emite** — obligarle a declarar un valor
  produciría un `todos` que no significa nada, contra lo dicho en §5.2 del contrato táctico.
- **La exención de autoridad no levanta una exclusión constitucional** (§5.7 del contrato táctico).
  Cada informe con dato excluido lleva su prueba **con el rol de máxima autoridad**, no solo con uno
  acotado.
- **El repositorio enumera sus columnas** (§5.5 del contrato táctico). Ninguna consulta usa
  `SELECT *`.

---

## 9. Dónde vive cada cosa

**Specs**, una por objetivo estratégico:

```
specs/001-estrategico/
    contrato-informes-estrategicos.md      ← este documento
    acceso-estrategico.md                  ← quién ve qué
    OE1-posicionamiento-captacion/
        OE1-posicionamiento-captacion.md   ← índice del módulo (no README)
        backend/                           ← capa activa
            spec.md  plan.md  tasks.md  data-model.md  research.md
            quickstart.md  traceability.md
            contracts/informes-estrategicos-oe1.openapi.yaml
        frontend/                          ← aplazada
    OE2-monetizacion-api/
    OE3-escalabilidad-multiregion/
    OE4-inteligencia-predictiva/
    OE5-retencion-ciclo-vida/
    OE6-respuesta-y-vidas/
```

Se mantiene el patrón layered de las otras dos capas: índice `{modulo}.md` con el nombre de la
carpeta, `backend/` activo primero, `frontend/` aplazado. Speckit apunta a **una capa** vía
`.specify/feature.json`.

**Código.** A diferencia de táctico, estos informes **no se reparten por app de departamento**: un
OE cruza varios y repartirlos por app volvería a fragmentar la métrica que el modelo unifica.

```
backend/apps/informes_estrategicos/
    views/oe1_views.py … oe6_views.py
    services/
    permissions.py
    urls.py
core/repositories/informes_estrategicos/
dags/lib/consultas/estrategicos/
```

---

## 10. Orden de construcción: la capa estratégica depende de la táctica

*(Añadido el 2026-08-16, al verificar el sustrato de los seis OE contra el almacén.)*

**Un OE solo es especificable cuando los hechos que consume están cargados en el modelo analítico.**
Y esos hechos los carga **el módulo táctico de informes compuestos del departamento dueño**, no esta
capa. Es la dependencia que gobierna el orden de trabajo, y no era evidente al escribir este contrato.

Estado medido el 2026-08-16 — el almacén tiene **13 tablas, todas de Emergencias más la geografía**:

| Departamento | Compuestos tácticos | Consultas cargadas |
|---|---|--:|
| Emergencias | 78/78 ✅ | 26 |
| Red Operativa | 22/67 en curso | 2 |
| Cuentas · Partners · Soporte · Suscripciones · Ventas | **0** | 0 |

Y lo que eso implica para cada objetivo:

| OE | Sustrato | Construible | spec | plan | tasks |
|:--:|---|:--:|:--:|:--:|:--:|
| **OE6** Respuesta y vidas | Emergencias completo | 12 / 12 | ✅ | ✅ | ✅ 92 **implementado** |
| **OE3** Escalabilidad | Emergencias + Red Op + `dim_condado_vecino` | 7 / 14 | ✅ | ✅ | ✅ 72 **implementado** (2026-08-16) |
| **OE4** Inteligencia predictiva | Emergencias completo | 9 / 15 | ✅ | ✅ | ✅ 80 |
| **OE2** Monetización API | — | 10 / 11 *(al desbloquear)* | ✅ | ⏸ | ⏸ |
| **OE1** Posicionamiento | — | 10 / 13 *(al desbloquear)* | ✅ | ⏸ | ⏸ |
| **OE5** Retención | — | 9 / 15 *(al desbloquear)* | ✅ | ⏸ | ⏸ |

### Los tres bloqueados: spec sí, plan no

**OE1, OE2 y OE5 están especificados y su `/plan` está deliberadamente detenido.** La distinción
importa:

- **La spec se escribe ahora** porque documenta **qué necesita la capa estratégica de cada módulo
  táctico**, y eso es útil *antes* de construirlos. Si `hecho_suscripcion` no congela la periodicidad,
  el MRR no se puede normalizar; es más barato saberlo ahora.
- **El plan no**, porque no hay contra qué verificarlo. Los tres objetivos que sí lo tienen
  produjeron **once correcciones al catálogo**, y las once salieron de medir: el eje de región
  muerto, las regiones sin fecha de arranque, E3-02 mezclando latencia técnica con tiempo operativo,
  E3-12 midiendo un suceso que no ocurre, `distanciamillas` que sí existía, E4-14 imposible por la
  idempotencia. **Ninguna se deduce del catálogo.**

### Y la dependencia es doble

No basta con que los tácticos carguen los hechos. **El dato de origen de esos tres objetivos es de
escala de demostración**, medido el 2026-08-16:

| Fuente | Filas | | Fuente | Filas |
|---|--:|---|---|--:|
| `Fact_Suscripcion` | **4** | | `Fact_LogLlamadaAPI` | **18** |
| `Fact_Factura` | **6** | | `Fact_Reclamo` | **14** |
| `Dim_Cliente` | **4** | | `Dim_Prospecto` | 10 |
| `Fact_Onboarding` | **3** | | `Fact_Interaccion_Demo` | **0** |

Frente a los **4 252 accidentes** de Emergencias. Un MRR sobre 4 suscripciones, un churn por cohorte
sobre 4 clientes y un cumplimiento de SLA sobre 14 tickets **son cifras anecdóticas con forma de
indicador**. Por eso las tres specs obligan a declarar `cobertura: "parcial"` en casi todos sus
informes.

**Consecuencia práctica:** el camino que desbloquea la capa estratégica no pasa por ella. Pasa por
terminar los compuestos tácticos de **Partners** —el más limpio, un solo departamento desbloquea OE2
entero—, y después Suscripciones, Ventas, Cuentas y Soporte.

### Cinco huecos que ningún módulo táctico resuelve

Los tres objetivos bloqueados comparten algo peor que la falta de sustrato: **cinco informes cuyo
prerrequisito no lo produce nadie**, y tres de ellos son indicadores del BSC.

| Hueco | Bloquea | Coste de cerrarlo |
|---|---|---|
| `Dim_Cliente` **no tiene país ni estado** | E1-07, E1-08 *(BSC: mercados activos)* | Una columna, pedida al alta |
| No hay **fuente de costos de marketing** | E1-05 *(BSC: CAC)* | Fuente externa |
| No hay **tabla de encuestas** | E5-01 *(BSC: NPS)* | **Una pregunta al cerrar un ticket** |
| No hay **tabla de programación de informes** | E5-11 | Es OT14, ya diseñada |
| `Dim_Partner.planapi` **no tiene precio** | E2-01, E2-02 *(parciales)* | Una columna |

⚠️ **Dos de estos huecos dejan a un objetivo sin poder medir lo que le da nombre:** OE1 se llama
«internacional» y no sabe de qué país es un cliente; OE5 es el objetivo de la satisfacción y nunca le
preguntó nada al cliente.

---

## 11. Lo que este contrato NO define

- **La pantalla y el tablero.** Qué informe se ve dónde y con qué semaforización visual es decisión
  de frontend, posterior y separada. Ningún endpoint asume una pantalla.
- **El tablero integral (CU-E01), los escenarios (CU-E09) y el reporte gerencial (CU-E10).** No son
  un séptimo OE: **agregan** los informes de los seis. Si necesitan spec, será de composición y
  presentación, y va después de que existan sus fuentes.
- **La exportación** a PDF o Excel del reporte gerencial.
- **La programación** de envíos periódicos: depende de una tabla que no existe (misma bloqueo que
  E5-11).

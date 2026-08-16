# Research — Informes Compuestos de Emergencias sobre el Modelo

**Fecha:** 2026-08-14 · **Plan:** [`plan.md`](plan.md)

Ocho decisiones. Las cifras que aparecen aquí están **medidas contra el sistema real**, no
estimadas.

---

## D1 — Dónde vive la definición de un informe

**Hallazgo.** Hoy la definición de un informe compuesto está **repartida en tres sitios**: la
consulta al origen en el módulo de tareas del flujo, la lógica de agregación en un módulo aparte, y
la forma de la respuesta en el repositorio de Django. Para cambiar cómo se mide algo hay que tocar
tres ficheros en dos contenedores distintos.

**Decisión.** Cada informe es **un fichero SQL parametrizado** en `dags/lib/consultas/emergencias/`,
y esa es su definición canónica. El backend lo lee y lo ejecuta; no lo reescribe.

**Rationale.** Un informe es una pregunta con una respuesta bien definida. Cuando esa pregunta vive
en un solo sitio, dos informes que miden lo mismo **no pueden divergir**, porque no hay dos textos
que mantener sincronizados. Es el mismo argumento por el que existe el modelo.

Vivir junto al modelo —y no dentro del backend— importa: la consulta y el esquema que la sostiene
cambian por las mismas razones y deben revisarse juntos.

**Alternativa descartada.** *Construir la consulta en Python en el repositorio* — permite componer
filtros con comodidad y hace que la definición del informe deje de ser legible de un vistazo. El
informe pasa a ser el resultado de ejecutar un programa en vez de un texto que se puede leer, revisar
y comparar con el catálogo.

---

## D2 — Cómo se aplica la regla de la versión final ⚠️

**Hallazgo.** Los hechos de instantánea acumulada y las dimensiones usan un motor que deduplica **en
segundo plano**. Entre la escritura y la fusión, una consulta sin forzar versión final devuelve
**ambas versiones**: la cifra sale inflada de forma intermitente y se corrige sola al rato. Está
probado ejecutablemente en `dags/tests/test_regla_final.py`.

Y no es uniforme: `hecho_estado_unidad` y `hecho_ping_unidad` son de transacción, y pedirles versión
final **falla con error**. Ya ocurrió al escribir una prueba de la fase 5.

**Decisión.** La regla se aplica **en la consulta**, no en el repositorio, y el catálogo de consultas
declara para cada informe qué hechos toca. Una prueba comprueba que **toda consulta que toca un hecho
acumulado o una dimensión fuerza la versión final, y ninguna que toca uno de transacción lo hace**.

**Rationale.** Es una regla que se olvida en el caso 27 de 26, y su fallo no es reproducible. Que
una prueba la vigile sobre el texto de las consultas convierte «hay que acordarse» en «no compila».

**Alternativa descartada.** *Envolver toda consulta en el repositorio añadiendo el modificador* —
rompería los dos hechos de transacción, y distinguirlos desde el repositorio exigiría que este
conociera el motor de cada tabla: acoplamiento al revés.

---

## D3 — El informe se calcula al preguntar, no al cargar

**Hallazgo.** El diseño anterior precomputaba: cada corrida recalculaba el histórico completo y lo
materializaba. Eso obliga a decidir **de antemano** el desglose y el umbral. El informe de pérdida de
señal tiene el umbral horneado en su flujo, y cambiarlo exige recargar la tabla entera.

**Decisión.** Los informes se calculan **al consultar**, sobre los hechos ya cargados. Los parámetros
—umbral, agrupación, rango— son de la pregunta, no de la carga.

**Rationale.** El almacén es columnar y los hechos están particionados por mes: agregar unos miles de
filas de un período es lo que esta clase de almacén hace bien. A cambio, un informe nuevo o una
variante de uno existente **no requieren recargar nada**.

**Alternativa descartada.** *Vistas materializadas por informe* — vuelven a atar el desglose al
momento de la carga y reintroducen, con otro nombre, la tabla por informe.

**Límite reconocido.** Si algún informe llega a tardar de más con volúmenes mayores, la salida es una
vista materializada **para ese informe concreto**, documentada como excepción medida — no como
patrón por defecto.

---

## D4 — Qué exige ampliar el modelo, y qué no

**Hallazgo.** Contrastando los 26 informes contra el esquema real:

| Cobertura | Informes |
|---|--:|
| Se sostienen hoy tal cual | **19** |
| Exigen métricas nuevas en `hecho_accidente` | 4 |
| Exigen un hecho de evidencia nuevo | 2 |
| Exige un hecho de cambio de severidad | 1 |

**Decisión.** Ampliar el modelo con **cinco métricas y un hecho**, según el §4.bis de su contrato:

1. `num_notas` en `hecho_accidente` — cobertura de evidencia (#17).
2. `num_conductores`, `num_implicados`, `num_elementos_clima` en `hecho_accidente` — completitud del
   enriquecimiento (#19).
3. `resultado_atencion` y `calificacion` en `hecho_accidente` — distribución de desenlaces (#24).
4. **`hecho_evidencia`**, de transacción, grano una evidencia levantada — latencia de sincronización
   (#18) y volumen por unidad (#20).
5. El cambio de severidad se resuelve como **métrica**, no como hecho: `num_escaladas_severidad` y
   `severidad_inicial` en `hecho_accidente` (#21).

**Rationale.** La regla del §4.bis es clara: si el atributo pertenece a una entidad ya modelada, es
una columna de ella y no una tabla nueva. Un caso tiene un número de implicados; no hace falta un
hecho para contarlo. La evidencia sí lo merece: tiene **dos instantes propios** —capturada y
sincronizada— y su grano no es el caso.

**Alternativa descartada para #21.** *Un hecho de cambios de severidad* — su fuente tiene **1 fila**
para 4 252 casos. Crear un hecho, un flujo y un DAG para una tabla que la operación no rellena es
coste sin retorno; como métrica del caso, si algún día se llena, la cifra aparece sola.

---

## D5 — La estimación de llegada, que el origen no guarda ⚠️

**Hallazgo.** Ninguna tabla del sistema operativo guarda una estimación de llegada. No hay columna de
ETA ni parámetro del que derivarla. Y `Dim_ParametrosSeguimiento`, donde vivirían los umbrales de
seguimiento, tiene **0 filas**.

**Decisión (del usuario, 2026-08-14).** Construir una **referencia derivada del histórico**: mediana
del tiempo de llegada de despachos comparables —mismo condado y misma severidad— sobre una ventana
anterior al despacho medido. La desviación es la diferencia entre la llegada real y esa referencia.

**Rationale y sus cuatro salvaguardas.** La objeción a esta opción era concreta: **presentar un
cálculo propio como si fuera un compromiso operativo**. Se acota por diseño, no por advertencia en la
documentación:

1. **Mediana, no promedio** — un solo traslado extremo desplazaría el promedio y volvería «normal» lo
   que no lo es.
2. **Ventana anterior al despacho medido** — un despacho no puede formar parte de su propia
   expectativa; si lo fuera, cualquier desempeño parecería normal.
3. **Sin muestra suficiente ⇒ sin dato**, nunca cero — cero significaría «llegó justo a tiempo», que
   es lo contrario de «no sabemos qué esperar».
4. **Etiquetado obligatorio** como valor de referencia derivado del histórico, nunca como objetivo o
   SLA.

**Alternativa descartada.** *Estimar por distancia entre unidad y accidente* — exigiría coordenadas,
que el modelo excluye por diseño, y produciría una expectativa que ignora el tráfico y la vía. Peor
dato y a mayor coste de privacidad.

**Lo que sigue sin poder medirse.** Si en el futuro la operación empieza a comprometer un tiempo de
llegada, ese compromiso **es otro dato** y este informe deberá compararse contra él, no contra la
mediana. La distinción debe sobrevivir a este módulo.

---

## D6 — El desglose por persona no entra

**Hallazgo.** El informe #20 del catálogo pide «volumen de evidencia por unidad **y técnico de
campo**». El técnico es una persona, y el modelo excluye la identidad para todos los roles, incluida
la autoridad departamental.

**Decisión (del usuario, 2026-08-14).** **Solo por unidad.**

**Rationale.** Es un choque entre Idoneidad funcional y Seguridad por diseño, y la constitución da
precedencia a Seguridad en su excepción de dominio. La pregunta útil se conserva —qué unidades
documentan bien— sin la parte que convierte un informe de calidad documental en un instrumento de
evaluación individual.

**Alternativa descartada.** *Seudonimizar al técnico* — sólo aparenta resolverlo: quien tenga acceso
al sistema operativo puede reidentificar cruzando unidad y fecha, y el modelo habría incorporado una
columna cuya única función es esa.

---

## D7 — Qué se hace con los tres informes que ya existen

**Hallazgo.** Tres de los 26 ya están construidos con el diseño anterior y **siguen sirviéndose desde
sus tablas propias**. Sus cifras difieren de las del modelo por defectos propios ya medidos:
truncamiento silencioso a 10 000 filas en dos de sus consultas.

**Decisión.** Este módulo **los redefine sobre el modelo pero no los apaga**. La retirada depende de
qué se decida con sus endpoints (decisión pendiente #20 del proyecto), que no es una decisión de este
módulo.

**Rationale.** Dejar de refrescar unas tablas que el backend sigue leyendo serviría **datos
congelados sin error visible** — peor que cualquiera de los dos extremos.

**Consecuencia operativa.** Durante la convivencia, **el mismo informe dará dos cifras según por
dónde se pida**. Hay que decirlo en la documentación del módulo, porque quien lo descubra sin
contexto lo tomará por un fallo de la migración cuando es lo contrario.

---

## D8 — Cinco fuentes vacías, y qué significa para las pruebas ⚠️

**Hallazgo.** Medido contra el sistema operativo con 4 252 casos: `Fact_Conductor_Accidente`,
`Dim_ParametrosDespacho` y `Dim_ParametrosSeguimiento` con **0 filas**;
`Fact_HistorialSeveridadAccidente` y `Fact_CierreAccidente` con **1**; evidencia, implicados y clima
con **3**; notas con **51**.

Es el **sexto caso en este proyecto** del mismo patrón: el esquema declara algo que la operación casi
nunca rellena.

**Decisión.** Los informes afectados **se construyen igual**, y sus pruebas se escriben con **datos
sintéticos en la partición de prueba**, no contra los datos reales. Además, cada uno lleva una prueba
que verifica que **distingue el cero medido de la ausencia de dato**.

**Rationale.** Una prueba que afirme «la cobertura de evidencia es 0,07 %» sobre datos reales pasaría
hoy y fallaría el día que alguien suba una foto. Y lo más importante: sin datos sintéticos, **una
consulta rota y una fuente vacía se ven exactamente igual** — ambas devuelven cero.

**Lo que no resuelve este módulo.** Si esas fuentes están vacías porque el sistema operativo nunca
las rellena, hay un hueco funcional en la capa operativa que ningún informe puede arreglar. Queda
señalado en el apartado *Riesgos* de la spec para que nadie publique un 0 % como indicador sin
haberlo comprobado antes.

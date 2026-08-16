# Research — Informes Compuestos de Suscripciones y Facturación

**Fecha:** 2026-08-14 · **Plan:** [`plan.md`](plan.md)

Ocho decisiones. Las cifras están **medidas contra el sistema real**.

---

## D1 — Los cinco defectos del origen se resuelven al cargar ⚠️

**Hallazgo.** Sobre solo cuatro suscripciones y seis facturas aparecen **cinco defectos distintos**:

| Defecto | Evidencia |
|---|---|
| `activo` no dice si está vigente | Una suscripción `Cancelada` con `activo = true` |
| `motivocancelacion` no implica cancelación | Una `Activa` con motivo `'prueba fin de ciclo'` |
| Vigencia invertida | Una con `fecha_fin` anterior a `fecha_inicio` |
| Centinela de plan | `idplan_programado = 0` en las cuatro |
| Tres formas de «sin motivo» | Nulo, cadena vacía y ausencia |

**Decisión.** Los cinco se resuelven **una vez, al cargar**: el hecho de suscripción guarda un estado
derivado, una marca de dato inconsistente y un plan programado ya normalizado a ausente.

**Rationale.** Trece consultas no pueden acordarse de cinco trampas. Y ninguna de las cinco **falla**
si se ignora: producen un MRR inflado, un motivo atribuido a quien no canceló, una duración negativa
y un plan inexistente — todos números que parecen razonables.

Es el mismo criterio ya aplicado con `activo` en Emergencias y en Ventas. **Tercera vez, tercer
departamento**: el patrón no es una anomalía de una tabla, es cómo está construido el sistema
operativo.

**Alternativa descartada.** *Documentar las trampas y confiar en las consultas* — la documentación no
se ejecuta.

---

## D2 — La suscripción es una instantánea acumulada

**Hallazgo.** Una suscripción tiene hitos que avanzan: alta, renovaciones, suspensión, reactivación,
cancelación. Y su **estado vigente cambia** sin que la entidad deje de ser la misma.

**Decisión.** `hecho_suscripcion` es una **instantánea acumulada** —una fila por suscripción, una
columna por hito—, como el accidente y el despacho. Es el tercero de ese tipo del modelo.

**Rationale.** Con grano de transición, saber cuántas suscripciones están vigentes hoy exigiría
reconstruir el estado de cada una recorriendo su historial **en cada consulta**. Eso es exactamente
lo que el modelo existe para evitar: el MRR es la pregunta más frecuente del departamento y debe ser
una suma, no una reconstrucción.

⚠️ **Consecuencia obligatoria**: sus consultas **deben forzar la versión final**. Sin eso, una
suscripción actualizada aparecería dos veces y el MRR saldría inflado **de forma intermitente**.

**Alternativa descartada.** *Hecho de transacción por cambio de estado* — daría un histórico
perfecto de transiciones y convertiría la pregunta más común en la más cara.

---

## D3 — El MRR normaliza a mensual, y lo que no se puede normalizar se declara ⚠️

**Hallazgo.** Las suscripciones tienen `periodicidad` —Mensual en las medidas— y **una la tiene
nula**. También hay una con precio `0` (plan demo).

**Decisión.** El MRR **normaliza toda periodicidad a mensual** antes de sumar, usa el **precio de la
suscripción** y no el de lista del plan, y **excluye las suscripciones sin periodicidad**,
contándolas aparte.

**Rationale del precio.** El catálogo tiene un plan `Magnifico` de nivel Empresarial a **120** y otro
Empresarial a **399**. El precio de lista del plan no es lo que el cliente paga; el de la suscripción
sí. Un MRR calculado sobre tarifas de catálogo mediría lo que se debería cobrar, no lo que se cobra.

**Rationale de la exclusión.** Una periodicidad ausente no se puede normalizar: no se sabe cada
cuánto se cobra ese precio. Repartirlo como si fuera mensual sería inventar. Contarlo como cero
también, en la dirección contraria.

**Y la variación se descompone en cuatro.** Nuevo, expansión, contracción y baja. Un MRR plano puede
esconder una fuga compensada por altas, y el neto solo lo diría cuando ya fuera tarde.

**Alternativa descartada.** *Usar el precio del plan* — más simple, y mide otra cosa.

---

## D4 — La vigencia invertida se aísla, no se corrige ⚠️

**Hallazgo.** Una suscripción de cuatro tiene `fecha_fin` **anterior** a `fecha_inicio`.

**Decisión.** El modelo la **marca como dato inconsistente** y la **excluye de toda métrica de
duración**, contándola aparte. **No la corrige ni la descarta.**

**Rationale.** Las tres salidas posibles y por qué solo una sirve:

- **Corregirla** —intercambiar las fechas, o poner el fin a nulo— sería inventar un dato y **borrar
  la evidencia del defecto**. El origen seguiría produciéndolos y nadie lo sabría.
- **Descartarla** perdería una suscripción real, con su ingreso real, de un cliente real.
- **Aislarla y contarla** conserva el ingreso donde no depende de la duración, evita el número
  negativo, y **deja el defecto visible** para quien deba arreglarlo en la capa operativa.

**Lo que preocupa de verdad.** Es **una de cuatro filas**. En una cartera de cientos, esa proporción
sería un problema serio de calidad de dato, y el modelo lo haría visible en vez de propagarlo.

---

## D5 — Los límites y las severidades se despliegan en columnas

**Hallazgo.** `Dim_Plan.limites` es texto estructurado —`{"unidades_max": 25, "usuarios_max": 10,
"api_calls_mes": 10000, ...}`— y `severidades_desbloqueadas` es una lista, también en texto: `'[1, 2]'`.

**Decisión.** Ambos se **despliegan en columnas** al cargar la dimensión de plan.

**Rationale.** Si cada consulta tuviera que interpretar el texto, esa lógica quedaría repartida por
todo el catálogo, y **la primera que lo interprete distinto producirá una cifra distinta** para la
misma pregunta. Desplegarlo al cargar lo resuelve en un sitio y convierte «comparar lo usado contra
lo contratado» en comparar dos columnas.

**Alternativa descartada.** *Interpretar el texto en cada consulta* — el almacén sabe hacerlo, y esa
capacidad es justo la que permite que trece consultas discrepen.

---

## D6 — Ningún medio de cobro entra al modelo ⚠️

**Hallazgo.** `Dim_MetodoPago` guarda token de pasarela, últimos dígitos y fecha de expiración;
`Dim_Cliente` guarda identificador fiscal.

**Decisión.** **Ninguno se copia.** El modelo conserva **si el cliente tiene método vigente** y
**cuándo caduca**, nunca cuál ni de quién.

**Rationale.** El informe que los necesita —«clientes sin método de pago activo»— pregunta por la
**ausencia**, no por el medio. Y el que avisa de caducidad necesita la fecha, no el número. La
utilidad analítica no requiere el dato sensible, así que el dato sensible no entra.

Es el mismo criterio que las coordenadas en Emergencias y la identidad del prospecto en Ventas.
**Tercera vez, y en el departamento donde el dato es financiero**: si la regla aguanta aquí, aguanta.

**Alternativa descartada.** *Copiar los últimos dígitos «que no identifican»* — combinados con
cliente y fecha, sí identifican, y no aportan nada a ningún informe.

---

## D7 — Este módulo se abstiene de modelar lo que no le pertenece ⚠️

**Hallazgo.** La utilización de límites tiene tres dimensiones y una —llamadas API— vive en
`Fact_LogLlamadaAPI`, corazón de **Partners y API**, aún sin especificar.

**Decisión (del usuario, 2026-08-14).** Entregar **unidades y usuarios**, declarar que falta la
tercera, y **no modelar el hecho de llamadas**.

**Rationale.** Es la primera vez en la serie que un módulo **se abstiene explícitamente** de modelar
algo que técnicamente podría. Modelarlo aquí obligaría a Partners a vivir con un diseño que no
eligió, o a rehacerlo — y rehacer un hecho ya cargado es mucho más caro que esperar.

**Y no devuelve un campo vacío.** Un `llamadas: null` en la respuesta diría «este cliente no consume
la API», que es una afirmación **distinta** de «todavía no lo medimos». La ausencia se declara en
texto, no con un hueco que alguien rellene.

---

## D8 — MRR y NRR se miden por mes natural

**Hallazgo.** El período por defecto de todos los informes tácticos son los últimos 30 días. Para un
indicador financiero eso produce cifras que **no se pueden comparar entre sí**.

**Decisión.** MRR, NRR y la variación mes a mes usan **mes natural**; el resto de informes conserva
el rango libre.

**Rationale.** Comparar «los últimos 30 días» con «los 30 anteriores» mezcla meses de 28 y 31 días y
períodos que cortan a mitad de ciclo de facturación. El MRR de febrero y el de marzo son
comparables; el de dos ventanas móviles solapadas, no.

**Consecuencia.** Un cliente que pida MRR con fechas arbitrarias recibe **el mes natural que las
contiene**, y la respuesta lo declara. Es preferible a devolver una cifra que parece responder a la
pregunta y no lo hace.

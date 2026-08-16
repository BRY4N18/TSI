# Research — Informes Compuestos de Partners y API

**Fecha:** 2026-08-14 · **Plan:** [`plan.md`](plan.md)

Ocho decisiones. Las cifras están **medidas contra el sistema real**.

---

## D1 — Una sola fuente de consumo: el detalle ⚠️

**Hallazgo.** El sistema operativo tiene **dos fuentes que no cuadran**:

| Fuente | Qué dice |
|---|---|
| `Fact_APIIntegracion` | **500 llamadas y 4 errores** por fila, 40 filas |
| `Fact_LogLlamadaAPI` | **18 registros** de detalle en total |

No difieren en el margen: **difieren en un orden de magnitud**.

**Decisión (del usuario, 2026-08-14).** Manda **el detalle**, y la preagregada **no se carga al
modelo**.

**Rationale.** Tres informes del catálogo —p95 por endpoint, consumo por endpoint y método, y
taxonomía de errores— **son imposibles sobre una agregación previa**: la información que necesitan se
perdió al agregar. Elegir la fuente que da cifras mayores costaría exactamente esos tres.

**Y no cargarla es la mitad importante de la decisión.** Tenerla al lado en el modelo sería una
invitación permanente a usarla el día que el detalle diera un número incómodo, y el departamento
volvería a tener dos verdades — con la diferencia de que entonces ambas estarían en el almacén
analítico, con apariencia de haber sido validadas.

**El precio, dicho.** Las cifras serán bajas. Por eso FR-008 obliga a devolver **sobre cuántas
llamadas** se calculó cada medida: quien lea un informe debe poder distinguir **poco consumo** de
**poco registrado**.

**Alternativa descartada.** *Cargar ambas y un informe de contraste* — convierte una discrepancia del
origen en una función del modelo, y sigue sin decidir cuál creer.

---

## D2 — La p95 se calcula al consultar, y declara sus muestras ⚠️

**Hallazgo.** Las métricas de consumo actuales dan **solo latencia media**, y el catálogo lo señala
como defecto. El BSC pide **p95**.

**Decisión.** El hecho guarda **una fila por llamada con su latencia**, y la p95 se calcula al
consultar, devolviendo siempre el **número de muestras**.

**Rationale.** Un percentil no se puede reconstruir desde una media: hay que tener las
observaciones. Es la razón técnica exacta de que la métrica actual no pueda dar p95, y el mejor
argumento de todo el proyecto a favor de guardar el detalle.

**Por qué el número de muestras es obligatorio.** Una p95 sobre 18 llamadas **es un número, no un
indicador**. Con dos endpoints en los datos actuales, la p95 de uno de ellos podría ser literalmente
su segunda llamada más lenta. Devolver el tamaño de la muestra convierte una cifra engañosa en una
cifra honesta.

**Y por qué importa la media también.** Media y p95 juntas dicen algo que ninguna dice sola: si la
p95 es muy superior a la media, hay una cola de llamadas lentas que la media esconde — que es
justamente el problema que el BSC quiere vigilar.

---

## D3 — El motivo de inactividad se deriva de la bitácora ⚠️

**Hallazgo.** `Dim_CredencialAPI` tiene `activo` y **ninguna columna de motivo**. Revocación,
desactivación en cascada y expiración producen **exactamente el mismo estado**.

El motivo sí existe, en `Fact_HistorialAccesoPartner.tipo_cambio`, con valores como
`revocacion_credencial`, `desactivacion_por_cascada` y `suspension_manual`.

**Decisión.** La dimensión de credencial guarda un **motivo de inactividad derivado** al cargar, del
último cambio de acceso que la afectó.

**Rationale.** Es el mismo criterio ya aplicado tres veces —`activo` en Emergencias, en Ventas y en
Suscripciones—: **resolver la ambigüedad una vez, al cargar**, en vez de confiar en que trece
consultas se acuerden. Y aquí importa especialmente porque los tres motivos tienen **responsables
distintos**: una revocación es una decisión, una cascada es una consecuencia, y una expiración es el
paso del tiempo.

⚠️ **Con una advertencia medida.** La bitácora tiene los mismos defectos ya documentados al
especificar Red Operativa: **eventos que no cambian el estado** —un `revocacion_credencial` con
`Activo → Activo`— y **eventos duplicados a milisegundos**. La derivación debe usar el mismo criterio
de colapso que la reconstrucción de versiones.

---

## D4 — Dos centinelas de fecha, y ninguno es una fecha ⚠️

**Hallazgo.**

| Columna | Valor | Significa |
|---|---|---|
| `Dim_CredencialAPI.fecha_expiracion` | `253402300799000` — año **9999** | «Nunca expira» |
| `Dim_VersionContratoAPI.fecha_retiro` | `0` — época cero | «No retirada» |

**Decisión.** Ambos se traducen a **ausente** al cargar.

**Rationale.** Es el mismo patrón que los centinelas de Pinot que ya obligaron a corregir la
completitud en Emergencias, pero **al revés**: allí el centinela hacía que nada pareciera incompleto;
aquí hace que todo parezca vigente para siempre.

**El número lo dice todo**: un promedio de días hasta la expiración incluyendo el año 9999 daría
**2,9 millones de días**. No es un error que pase desapercibido — es uno que hace evidente que nadie
lo comprobó.

**Y el de la época cero es más peligroso porque sí pasa desapercibido**: una versión «retirada en
1970» ordena antes que cualquier otra, así que un informe de versiones retiradas la mostraría primera
con toda naturalidad.

---

## D5 — La versión se deriva del endpoint, y se declara derivada

**Hallazgo.** `Fact_LogLlamadaAPI` **no registra la versión del contrato**. Pero el endpoint la
contiene: `/api/v1/datos/accidentes`.

Y `Dim_VersionContratoAPI.version` vale `'v1'` — **con una trampa**: hay dos filas con `'v1'`, para
servicios distintos. La versión **no es única por sí sola**.

**Decisión.** La versión se **deriva del endpoint** al cargar, la clave de agrupación es
**(servicio, versión)**, y el informe **declara que el dato es derivado**.

**Rationale.** Un indicador BSC construido sobre una derivación tiene que decirlo. La extracción
depende de que el path mantenga su forma, y **el día que cambie, la derivación no fallará: devolverá
otra cosa**. Declararlo es lo que permite que alguien lo revise cuando las cifras se muevan sin
explicación.

**Alternativa descartada.** *Registrar la versión en el log del sistema operativo* — es la solución
de fondo y es trabajo en la capa operativa; queda anotado. Mientras tanto, la derivación es correcta
y verificable.

---

## D6 — Ni secretos, ni contacto, ni IP ⚠️

**Hallazgo.** Este departamento guarda los datos más sensibles del sistema desde el punto de vista de
seguridad:

| Dato | Dónde |
|---|---|
| Hash del secreto de cliente | `Dim_CredencialAPI.client_secret_hash` |
| Contacto técnico del partner | `Dim_Partner.contacto_tecnico_nombre`, `_gmail` |
| **IP de origen de cada llamada** | `Fact_LogLlamadaAPI.iporigen` |
| Quién ejecutó cada cambio de acceso | `Fact_HistorialAccesoPartner.ejecutado_por` |

**Decisión.** **Ninguno entra al modelo.**

**Rationale.** El hash es un secreto aunque esté cifrado, y ningún informe lo necesita. El contacto
es dato personal. **La IP es el caso más interesante**: identifica a un consumidor concreto y podría
parecer útil para «detectar patrones anómalos» (informe del catálogo) — pero ese informe se responde
con **volumen, códigos de error y latencia por partner**, que es lo que describe un patrón anómalo.
La IP añadiría capacidad de rastreo sin añadir capacidad de análisis.

**Es la cuarta vez que aparece el mismo choque** —técnico de campo, validador de región,
administrador de solicitudes, y ahora ejecutor de cambios de acceso— **y la cuarta con la misma
resolución**. La regla está asentada.

---

## D7 — El alcance geográfico se retira, y no se infiere ⚠️

**Hallazgo.** El informe pide detectar **consultas fuera de la zona habilitada**. Las zonas
contratadas están en las preferencias del cliente (`'[1,2]'`); el log guarda **endpoint, código y
latencia**, y nada sobre el ámbito de la respuesta.

**Decisión (del usuario, 2026-08-14).** El informe **queda fuera de alcance**, y el modelo **no
infiere la zona** de los parámetros del endpoint.

**Rationale.** La inferencia sería técnicamente posible —los endpoints traen parámetros— y **fallaría
en silencio**: en cuanto un cliente consultara con un parámetro distinto, el informe no distinguiría
«consulta fuera de zona» de «no supe leer la consulta». Las dos se verían igual, y una de ellas es
una acusación de incumplimiento de contrato.

**Es una decisión de tipo distinto a las demás de la serie.** En otros casos se entregó una parte y
se declaró la que faltaba —el CAC, la utilización de límites—. Aquí no hay parte que entregar: sin
la zona consultada, el informe **no existe**, solo puede aparentarlo.

**Lo que sigue faltando.** Que el log registre la zona. Queda anotado como carencia del sistema
operativo, no como informe pendiente de especificar.

---

## D8 — Los dos informes ya construidos conviven, y este módulo no los toca

**Hallazgo.** Dos de los catorce ya existen, **en la app de partners y no en la de informes
tácticos**: el reporte mensual de consumo y las métricas de consumo —estas últimas con el defecto
documentado de dar solo media—.

**Decisión.** Este módulo entrega **sus equivalentes sobre el modelo** y **deja los originales
sirviendo**.

**Rationale.** Es la misma situación de Emergencias: retirarlos depende de la decisión pendiente #20
del proyecto, y adelantarla aquí dejaría el tablero de consumo sin fuente mientras tanto.

**La diferencia con Emergencias.** Allí trece endpoints correctos convivían con sus equivalentes, y
se añadió una prueba de contraste. Aquí uno de los dos **es incorrecto por diseño** —da media donde
el BSC pide p95—, así que **la comparación no aplica**: sus cifras deben diferir, igual que las de la
pérdida de señal.

**Consecuencia que hay que decir.** Durante la convivencia, el mismo partner tendrá **dos latencias
publicadas**. La del modelo es la correcta, y la documentación del módulo debe decirlo, porque quien
las compare sin contexto tomará por error lo que es el arreglo.

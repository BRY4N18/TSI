# Research — Informes Compuestos de Ventas y CRM

**Fecha:** 2026-08-14 · **Plan:** [`plan.md`](plan.md)

Siete decisiones. Las cifras están **medidas contra el sistema real**.

---

## D1 — El desenlace del prospecto se resuelve al cargar, no al consultar ⚠️

**Hallazgo.** `Dim_Prospecto.activo = false` cubre **dos resultados opuestos**: 2 prospectos
convertidos y 1 perdido. Un informe que agrupe por esa columna presentaría el éxito y el fracaso como
lo mismo.

**Y el origen sí los distingue**, en dos sitios: `motivo_inactividad` (`convertido` / `perdido`) y
`etapa_actual` (`Ganado` / `Perdido`).

**Decisión.** La dimensión de prospecto guarda un **desenlace de tres valores** —convertido, perdido,
en curso— derivado al cargar. Ninguna consulta lee `activo`.

**Rationale.** Es la diferencia entre resolver el problema una vez y confiarlo trece veces. Si cada
consulta tuviera que derivarlo, **la primera que lo olvide mezclará conversiones con pérdidas y no
fallará**: devolverá un número perfectamente plausible.

Es el mismo criterio que ya se aplicó en Emergencias con `activo`, que allí cubría cerrado,
descartado y fusionado.

**Alternativa descartada.** *Copiar `activo` al modelo y documentar la trampa* — la documentación no
se ejecuta. Una columna que miente sigue mintiendo aunque haya un comentario al lado.

---

## D2 — El embudo se mide sobre transiciones, no sobre el estado actual

**Hallazgo.** `Fact_Pipeline` tiene 24 transiciones sobre 10 prospectos, con seis pares
etapa-anterior → etapa-nueva distintos. `Dim_Prospecto.etapa_actual` solo dice **dónde está ahora**.

**Decisión.** El hecho de embudo tiene **grano de transición**, y los informes de paso entre etapas
se calculan sobre él.

**Rationale.** El estado actual no dice por dónde pasó un prospecto. Con grano de prospecto, uno que
recorrió cinco etapas y otro que saltó directo a «Ganado» se ven idénticos, y el embudo —cuyo objeto
es precisamente medir el paso— no tendría nada que medir.

Es exactamente el mismo argumento por el que el despacho tiene grano de intento.

**Consecuencia sobre el retroceso de etapa.** Un prospecto puede volver atrás. El porcentaje de paso
se calcula **sobre transiciones**, no sobre prospectos únicos, y el informe lo declara — si no, la
suma de porcentajes desconcierta a quien la lea.

---

## D3 — La permanencia en una etapa incluye el tramo abierto ⚠️

**Hallazgo.** La duración en una etapa es la diferencia entre transiciones consecutivas. Pero **la
etapa actual de un prospecto no tiene transición de salida**.

**Decisión.** El tiempo en la **etapa vigente al final del período** se cuenta **hasta el fin del
período**. Y un prospecto sin ninguna transición cuenta desde su registro.

**Rationale.** Sin esto, los prospectos **estancados no aparecen en la medida** — y son exactamente
los que el informe existe para encontrar. Un embudo que solo mide etapas ya abandonadas presenta como
rápidos a los prospectos que llevan tres meses parados.

Es el mismo defecto que la disponibilidad de unidades en Red Operativa: medir solo lo que cambió deja
fuera lo que no se ha movido, que suele ser el problema.

**Alternativa descartada.** *Medir solo las etapas cerradas* — es más simple, es correcto en su
propia definición, y responde a una pregunta que nadie hizo.

---

## D4 — La carga por ejecutivo se atribuye al de entonces

**Hallazgo.** `Fact_Asignacion` registra reasignaciones con su instante y sus dos ejecutivos —
anterior y actual. Hay 9 asignaciones sobre 10 prospectos.

**Decisión.** Un **hecho de asignación** con grano de asignación, y la carga histórica se atribuye al
ejecutivo **vigente en el momento medido**.

**Rationale.** Es el mismo problema de unidad↔proveedor, con una diferencia importante: **aquí el
origen sí lo historiza**. `Fact_Asignacion` guarda el instante de cada cambio, así que la atribución
histórica es **exacta desde el primer día**, sin la marca de «inicio no real» que necesitan la unidad
y la región.

Es el primer caso del proyecto donde el historial existe en el origen y **no hay que declarar
ninguna limitación**.

**Alternativa descartada.** *Versionar la dimensión de prospecto por ejecutivo* — funcionaría, y
duplicaría un historial que el origen ya tiene bien. El hecho de asignación es más fiel a lo que hay.

---

## D5 — Ningún dato personal del prospecto entra al modelo ⚠️

**Hallazgo.** `Dim_Prospecto` es **la tabla con más dato personal de todo el sistema**: nombres,
apellidos, correo, teléfono, cargo y empresa. Un prospecto es una persona identificada, no una
entidad de negocio anónima.

**Decisión.** La dimensión de prospecto del modelo **no copia ninguno de esos campos**. Conserva
empresa, tipo de organización, canal, etapa, desenlace y valor estimado.

**Rationale.** Ningún informe del catálogo necesita saber quién es el prospecto: todos agregan por
canal, etapa, tipo de organización o ejecutivo. La utilidad analítica **no requiere la identidad**,
así que la identidad no entra — igual que las coordenadas en Emergencias.

**La empresa sí entra** porque es la unidad de negocio —un municipio, una aseguradora— y no una
persona.

**Alternativa descartada.** *Copiar y filtrar en la consulta* — el dato estaría en el almacén, y una
consulta nueva podría exponerlo sin que nadie lo revise. No copiarlo lo hace imposible por
construcción.

---

## D6 — Los dos hechos de OT03 se construyen aunque sus fuentes estén vacías

**Hallazgo.** `Fact_Interaccion_Demo` y `Fact_NotificacionVentas` tienen **0 filas** y sostienen 5 de
los 13 informes.

**Y aquí sí se pudo diagnosticar la causa**: ambos repositorios **publican a Kafka** —comprobado en
`core/repositories/ventas_crm/`—, así que el camino de escritura existe y está implementado. El vacío
es de **entorno**: nadie ha ejercitado una demo.

**Decisión.** Los dos hechos y sus cinco informes se construyen igual, y **sus pruebas van con datos
sintéticos**.

**Rationale.** Aplazarlos no ahorraría trabajo —sería idéntico más tarde— y dejaría OT03 entero sin
especificar. Con datos sintéticos, además, **una consulta rota y una fuente vacía dejan de verse
igual**: ambas devuelven cero.

**Diferencia con Emergencias, que importa.** Allí cinco fuentes estaban vacías y **no se pudo
determinar si la operación llegaba a escribirlas**. Aquí sí, y el diagnóstico cambia la conclusión:
no hay hueco funcional que reportar, solo un entorno sin ejercitar.

---

## D7 — El CAC se entrega a medias, y sin sitio donde encajar el resto ⚠️

**Hallazgo.** El coste por canal **no existe en ninguna tabla del sistema**: ni inversión
publicitaria, ni presupuesto por campaña, ni coste imputado. El catálogo lo apoya en prospectos y
clientes, que dan solo el denominador.

**Decisión (del usuario, 2026-08-14).** Entregar **clientes convertidos por canal**, y **no devolver
ninguna columna de coste, ni siquiera vacía**.

**Rationale.** Lo segundo es lo que hace honesta a la decisión. Una columna `coste: null` en la
respuesta es una invitación a rellenarla desde el frontend o desde una hoja de cálculo, y el tablero
acabaría mostrando **un CAC que el sistema no puede sostener** — con la apariencia de dato calculado.

Sin esa columna, quien quiera un CAC tiene que traer el coste **y hacerse responsable de él**, que es
exactamente donde debe estar la responsabilidad mientras el dato no exista.

**Alternativa descartada.** *Aceptar el coste como parámetro de la consulta* — produce el indicador
completo y su valor depende de un número que teclea quien pregunta. Un informe cuyo resultado cambia
según quién lo pide no es un indicador.

**Lo que sigue faltando.** Si algún día se registra la inversión por canal, este informe se amplía
con el numerador y pasa a ser el CAC de verdad. La decisión de hoy no cierra esa puerta.

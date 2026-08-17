# Research — OE3, Escalabilidad Multi-Región sin Degradación

**Fecha:** 2026-08-16 · **Spec:** [`spec.md`](spec.md) · **Plan:** [`plan.md`](plan.md)

Todo lo de aquí se comprobó **contra el stack levantado** —`tactico-clickhouse` y el Pinot
operativo— y contra el código. Donde hay una cifra, se midió.

**Resultado neto: el reparto de informes cambia, aunque el total de construibles no.** Uno que la
spec daba por bueno no lo es (E3-12) y otro que daba por bloqueado se desbloquea (E3-08).

---

## D1 — E3-02 está mal especificado: el catálogo mezcla dos métricas distintas ⚠️

**Es el hallazgo principal del plan, y afecta al informe insignia del MVP.**

El catálogo define E3-02 así:

> *«Latencia de despacho p95 global y por región — p95 del tiempo solicitud→confirmación de unidad;
> alerta ≤100 ms `[NORMATIVO]`»*, con fuente `hecho_despacho (fechahoradespacho, fechahoraconfirmacion)`.

**Esa frase contiene dos métricas incompatibles.** «Solicitud → confirmación de unidad» es un tiempo
**operativo**: alguien mira un aviso y acepta una misión. «≤100 ms» es una latencia **técnica**: lo
que tarda el algoritmo de asignación en responder. No pueden ser la misma cifra.

### Lo medido

| Medida | Mediana | p95 |
|---|--:|--:|
| Oferta de despacho → confirmación de la unidad (`segundos_respuesta`) | 17 s | **28 s** |
| Registro del accidente → primera asignación | 38 s | **106 s** = 1,77 min |

Contra una meta de **100 ms**, el p95 de 106 s está **1 060 veces por encima**. Publicar E3-02 tal
como el catálogo lo define daría un rojo permanente contra un compromiso `[NORMATIVO]`, y el rojo
sería **falso**: no mide lo que la meta promete.

### La meta que sí existe, y se cumple

`despacho-inteligente/backend/spec.md` **RNF-DES-001** fija la meta operativa real:

> *«El proceso completo desde el registro del accidente hasta la confirmación de unidad asignada debe
> completarse en **menos de 2 minutos en el percentil 95** (meta operativa del BSC).»*

Medido: **p95 = 1,77 min**, con **58 casos de 3 638 por encima de 2 minutos (1,6 %)**. ✅ **Se cumple.**

### Decisión

**E3-02 mide el tiempo operativo registro → primera asignación, contra la meta `<2 min p95` de
RNF-DES-001.** La latencia técnica de ≤100 ms **se separa** y pasa a US4, junto al uptime: es una
métrica de instrumentación de la aplicación, no de los datos de operación.

**Por qué no al revés.** La alternativa —conservar la meta de 100 ms y declarar E3-02 inmedible—
sacrificaría un informe que **sí se puede construir, sí tiene meta y sí se cumple**, y dejaría a US1
sin su indicador principal. La meta de 2 minutos no es un invento de este plan: está escrita en la
spec operativa del módulo que ejecuta el despacho, y el propio catálogo la llama «meta operativa del
BSC».

**Consecuencia documental:** la spec se corrige, y el catálogo estratégico queda por corregir en dos
puntos —la meta de E3-02 y la separación de la latencia técnica—.

---

## D2 — E3-12 no es medible: el sistema no registra que el algoritmo falle ⛔

La spec lo daba por construible en US1. **No lo es.**

El catálogo lo define como *«mediana del tiempo entre la falla del algoritmo y la intervención del
operador»*. Eso exige dos cosas: que exista un instante en que el algoritmo falló, y que la
intervención manual venga después.

### Lo medido

```
manual_tras_automatico:        1
manual_sin_automatico_previo:  1082
```

**De los 1 083 despachos manuales, 1 082 no siguen a ningún intento automático.** Y 918 de ellos son
`numero_intento = 1`: el despacho manual **es** el primer intento sobre ese caso. El operador
despachó a mano desde el principio, no tras una falla.

### Decisión

**E3-12 pasa a US4, como no construible.** Su bloqueo no es de agregación: es que **el suceso que
mide no se registra en ninguna parte**. El sistema anota el origen de un despacho, no que un
algoritmo se rindiera.

**Lo que sí se podría medir, y por qué no se hace:** «tiempo desde el registro hasta el despacho
manual». Es otra cosa, y llamarla reasignación tras falla afirmaría que hubo una falla en 1 082 casos
donde nadie ha demostrado que la hubiera. Un indicador `[NORMATIVO]` no puede descansar sobre esa
sustitución.

**Prerrequisito para levantarlo:** que el módulo de despacho registre el evento «asignación automática
sin candidatas» con su instante. El flujo ya existe —la spec operativa dice que escala a zonas vecinas
y deja constancia— pero no como un hecho con marca de tiempo que el analítico pueda leer.

---

## D3 — E3-08 sí se desbloquea: `Dim_CondadoVecino` existe y tiene datos ✅

La spec lo daba por bloqueado y pedía evaluarlo (`FR-OE3-019`). **Evaluado: se desbloquea.**

Consultado el Pinot operativo:

```
idcondado  idcondadovecino  activo
1          2                True
2          1                True
```

La tabla existe, tiene datos y es **simétrica** —cada condado declara al otro como vecino—, que es lo
que E3-08 necesita para responder «cuántos condados vecinos tienen al menos una unidad disponible».

**Decisión:** cargar `Dim_CondadoVecino` al modelo analítico como dimensión, siguiendo el §4.bis del
contrato de esquema. Es un cambio **aditivo**: dimensión nueva, sin tocar hechos existentes.

⚠️ **Con dos condados, el informe dará una fila por condado y un vecino cada uno.** No es un
resultado interesante todavía, pero **es correcto**, y la alternativa —dejarlo bloqueado— sería
declarar inmedible algo que sí se mide. La escasez de datos se declara; la imposibilidad, no.

**Alternativa descartada:** derivar la vecindad de la geografía (condados del mismo estado). Sería una
suposición sobre adyacencia física que la tabla ya responde con dato real, y en cuanto haya más de
dos condados por estado daría vecinos falsos.

---

## D4 — La historización de región sigue bloqueada, y no hay derivación honesta

E3-04, E3-05 y E3-06 necesitan la fecha real en que cada región entró en producción. Confirmado que
no existe:

```
nombre_region        estado_ciclo_vida  valido_desde         inicio_es_real
Centro               Producción         1970-01-01 00:00:00  0
Region Prueba Norte  Producción         1970-01-01 00:00:00  0
```

**Se evaluaron dos derivaciones y se descartan las dos:**

| Derivación | Por qué no |
|---|---|
| Tomar la fecha del **primer accidente** de la región | E3-04 mide *días desde la incorporación hasta la primera emergencia atendida*. Derivar el inicio del primer caso hace que **la medida sea siempre cero por construcción** |
| Tomar la fecha de la **primera validación aprobada** (`Dim_ValidacionRegion`) | Es la fecha en que se aprobó, no en que entró en producción. Puede haber días o meses entre ambas, y la meta es de 30 días: el error sería del mismo orden que lo medido |

**Decisión:** los tres siguen bloqueados. **Prerrequisito:** historizar el cambio de estado de región
en el sistema operativo — hoy `Dim_RegionOperativa.estadoregion` se sobrescribe. Está anotado en
`decisiones-pendientes.md` #38 junto al eje de región, porque **la misma tabla puente resolvería los
dos**.

---

## D5 — Consultas propias con prueba de contraste, igual que OE6

Tres de los siete construibles ya tienen consulta táctica, y dos están **publicadas** como endpoint:

| Informe | Consulta táctica | ¿Publicada? |
|---|---|:--:|
| **E3-07** Ratio demanda / capacidad | `ot22_ratio_demanda_capacidad` | **Sí** *(migrado — corrige la capacidad)* |
| **E3-11** Primer intento | `ot22_primer_intento` | **Sí** |
| **E3-10** Tasa de error de registro | `ot21_completitud_campos_criticos` | **Sí** *(es su complemento)* |
| **E3-02**, **E3-03**, **E3-13**, **E3-08** | — / `ot23_perdida_senal` | E3-13 sí |

**Decisión:** el mismo patrón que OE6 (research D2 de aquel módulo): consultas propias en
`dags/lib/consultas/estrategicos/oe3/`, con **prueba de contraste** que falla si divergen de la
táctica con la misma agrupación y período. No se tocan las consultas tácticas publicadas y
verificadas.

**Y se reutiliza el armazón de OE6 sin duplicarlo**: `periodo_estrategico.py`, `objetivo.py`,
`envelope.py` y el repositorio. Si OE6 no está implementado, sus fases 1 y 2 son prerrequisito de
este módulo.

---

## D6 — La autoridad repartida se implementa por materia, no por departamento

`acceso-estrategico.md` §4.3 reparte OE3 entre tres autoridades. `roles_tacticos.py` ya expone el
patrón correcto y su docstring explica por qué:

> *«Este módulo expone conjuntos por materia y no un simple "autoridad del departamento X". Un
> `es_autoridad_de(departamento)` invitaría a conceder de más justo en los tres casos donde el SRS
> pide lo contrario.»*

**Decisión:** un conjunto de roles **por informe**, no por módulo:

| Informe | Autoridad |
|---|---|
| E3-02, E3-03, E3-10, E3-11 | `DirectorOperaciones` |
| E3-07, E3-08, E3-13 | `DirectorExpansion` · `DirectorOperaciones` *(E3-07 y E3-13 tocan despacho y flota)* |
| Los bloqueados, cuando existan | `DirectorTecnologico` · `DirectorExpansion` según materia |
| Todos | `Gerente` |

**Es la primera vez en la capa estratégica que el acceso no es uniforme dentro de un módulo**, así
que la prueba de permisos tiene que comprobar **exclusiones**, no solo accesos:
`DirectorExpansion` **no** entra en los informes de despacho.

---

## D7 — OE3 es el primer módulo que puede semaforizar, pero con menos metas de las previstas

Tras D1 y D2, las metas `[NORMATIVO]` realmente medibles quedan en **dos**:

| Informe | Meta | Medido | ¿Cumple? |
|---|---|--:|:--:|
| **E3-02** Registro → primera asignación | `<2 min p95` | **1,77 min** | ✅ |
| **E3-10** Tasa de error de registro | `<1 %` | **0 %** | ✅ |
| **E3-11** Despachos al primer intento | `≥90 %` `[CALIBRAR]` | — | `null` |

⚠️ **La prueba transversal de OE6 —«ningún `cumple` booleano»— no aplica aquí, y copiarla sería un
error.** Aquí la comprobación es la inversa para E3-02 y E3-10.

### Una advertencia sobre E3-10

Su tasa de error es **0 %** porque los 4 252 casos tienen severidad y calle. Cumple la meta, pero
**un indicador que estructuralmente nunca se mueve no es una señal**: si mañana el registro se
degradara en un campo que este informe no comprueba, seguiría marcando 0 %.

**Decisión:** E3-10 **declara en su respuesta qué campos comprueba**. Sin esa lista, un 0 % permanente
se lee como «el registro es perfecto» cuando dice «los dos campos que miro están completos».

---

## D8 — El reparto de informes cambia respecto de la spec

Consecuencia de D1, D2 y D3. **El total de construibles no se mueve —siete—, pero cambian de sitio:**

| Historia | Spec original | Tras la investigación |
|---|---|---|
| **US1** El rendimiento | E3-02, E3-03, E3-10, E3-11, **E3-12** *(5)* | E3-02, E3-03, E3-10, E3-11 *(4)* |
| **US2** La tensión | E3-07, E3-13 *(2)* | E3-07, E3-13, **E3-08** *(3)* |
| **US3** Maduración regional ⛔ | E3-04, E3-05, E3-06, **E3-08** *(4)* | E3-04, E3-05, E3-06 *(3)* |
| **US4** Fuera del sistema ⛔ | E3-01, E3-09, E3-14 *(3)* | E3-01, E3-09, E3-14, **E3-12** *(4)* |

**US4 se renombra** de «lo que este sistema no produce» a **«lo que el sistema no registra ni
produce»**: ahora agrupa dos bloqueos distintos —fuentes externas y sucesos que la aplicación no
instrumenta— y los dos exigen lo mismo, tocar algo que no es este módulo.

---

## Resumen de incógnitas resueltas

| Incógnita | Estado |
|---|:--:|
| ¿Se puede cargar `Dim_CondadoVecino`? (`FR-OE3-019`) | ✅ Sí — E3-08 se desbloquea (D3) |
| ¿Se puede derivar la fecha de arranque de una región? | ✅ Resuelta: **no**, y las dos derivaciones se descartan con motivo (D4) |
| ¿Es coherente la meta de E3-02? | ✅ Resuelta: **no lo era**. Se separa en dos métricas (D1) |
| ¿Es medible E3-12? | ✅ Resuelta: **no** — 1 082 de 1 083 manuales sin falla previa (D2) |
| ¿Cómo se implementa la autoridad repartida? | ✅ Conjuntos por informe (D6) |

**Ninguna `NEEDS CLARIFICATION` queda abierta.**

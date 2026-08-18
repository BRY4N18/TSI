# Feature Specification: Informes Compuestos de Cuentas y Clientes sobre el Modelo Analítico

**Feature Branch**: `002-tactico/Cuentas-Clientes/informes-compuestos-modelo/backend`

**Created**: 2026-08-14

**Status**: Implemented

**Input**: User description: "Informes tácticos compuestos de Cuentas y Clientes — los 9 informes agregados de OT04, OT17 y OT18, resueltos con consultas sobre el modelo analítico"

---

## Contexto

Sexto departamento sobre el modelo analítico. Cuentas y Clientes responde a **quién es cliente, desde
cuándo y con qué acceso**: incorpora cuentas nuevas, sostiene su ciclo de vida y controla el acceso
por rol.

**Es el dueño natural de `dim_cliente`**, la dimensión conformada que creó Suscripciones porque fue
el primer módulo que la necesitó. **Este módulo la amplía, no la recrea** — es la prueba de que las
dimensiones compartidas del modelo funcionan en la dirección que importaba: el departamento dueño
llega después y no tiene que rehacer nada.

**Ningún informe compuesto existe.**

> ### ⚠️ Cinco hallazgos medidos antes de especificar
>
> **1. ⚠️ Solo 2 de 21 usuarios tienen pertenencia a organización declarada.** El sistema tiene **dos
> definiciones incompatibles**: `Dim_Cliente.admin_local_id` —que da un administrador por cliente— y
> `Dim_Usuario_Cliente` —con **3 filas para 2 usuarios distintos**—. Dos informes dependen de saber
> qué usuarios pertenecen a qué cliente. Ver *Aclaración pendiente*.
>
> **2. El onboarding solo registra lo que se completó.** `Fact_Onboarding` tiene 3 filas, **todas con
> `completado = true`** y todas del mismo cliente. Un embudo de abandono no puede medirse contando
> abandonos: **hay que medirlo por ausencia**, comparando contra las etapas esperadas.
>
> **3. Las sesiones son eventos, no intervalos.** 513 inicios frente a 195 cierres: la mayoría de las
> sesiones **no tiene evento de cierre**. Una duración media calculada solo sobre las cerradas mediría
> las sesiones que terminaron bien, que es otra cosa.
>
> **4. `Fact_Session` guarda el token de sesión.** Es el dato más sensible del departamento y **no
> entra al modelo** bajo ningún concepto.
>
> **5. `Fact_HistorialTransferenciaPropiedad` está vacía**, y un cliente `Activo` tiene el estado de
> onboarding **nulo**.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - El Administrador sostiene el ciclo de vida de la cuenta (Priority: P1) 🎯 MVP

Los cuatro informes de **OT17**: cuánto dura una cuenta, cuántas se dan de baja y por qué, qué
clientes se acercan al tope de usuarios de su plan y cuáles llevan tiempo sin actividad.

**Why this priority**: contiene el indicador BSC de **churn**, que hoy no tiene fuente, y responde a
la pregunta que sostiene el negocio: **cuántos clientes se van y por qué**.

**Independent Test**: dar de baja un cliente y comprobar que aparece en la cohorte de su mes de alta,
no en la del mes de baja.

| # | Informe | OT | Origen |
|--:|---|---|---|
| 1 | **Tasa de baja (churn) por cohorte de alta**, con motivo | OT17 | **BSC** |
| 2 | Antigüedad media de cuenta, por tipo de cliente y plan | OT17 | ± |
| 3 | Usuarios por cliente frente al tope de su plan | OT17 | ± |
| 4 | Cuentas en riesgo: sin actividad de sesión en N días | OT17 | ± |

**Acceptance Scenarios**:

1. **Given** un cliente dado de alta en enero y de baja en junio, **When** se pide el churn por
   cohorte, **Then** cuenta en la **cohorte de enero**. Agruparlo por el mes de baja mediría cuándo se
   fue la gente, no **qué cohortes retienen peor** — que es lo que el indicador existe para responder.
2. **Given** un cliente activo desde hace dos años y otro de hace un mes, **When** se pide la
   antigüedad media, **Then** se calcula sobre **la fecha de alta y el momento actual**, no sobre
   fechas de baja que no existen.
3. **Given** un cliente cuyo plan permite 10 usuarios, **When** se pide la ocupación, **Then**
   devuelve **usuarios y tope**, no solo el porcentaje.
4. **Given** un cliente sin ninguna sesión en 90 días, **When** se piden las cuentas en riesgo,
   **Then** aparece con **los días transcurridos desde su última sesión**.
5. **Given** un cliente **sin ninguna sesión registrada nunca**, **When** se piden las cuentas en
   riesgo, **Then** aparece marcado como **sin actividad conocida**, no con «0 días»: nunca haber
   entrado y haber entrado hoy son lo contrario.

---

### User Story 2 - El Administrador vigila la incorporación de clientes (Priority: P2)

Los tres informes de **OT04**: cuánto se tarda en completar el alta, dónde se atasca la gente y
cuántas solicitudes se aprueban.

**Why this priority**: contiene el segundo indicador BSC del departamento, y el embudo de abandono es
el informe que dice **dónde arreglar el proceso**. Va después del ciclo de vida porque su fuente hoy
tiene tres filas de un solo cliente.

| # | Informe | OT | Origen |
|--:|---|---|---|
| 5 | **Tiempo de onboarding**: días de registro a última etapa | OT04 | **BSC** |
| 6 | Embudo de abandono: % de clientes que supera cada etapa | OT04 | ± |
| 7 | Tasa de aprobación frente a rechazo, por tipo de organización | OT04 | ± |

**Acceptance Scenarios**:

1. **Given** un cliente que completó tres etapas de cinco, **When** se pide el embudo, **Then**
   aparece como **detenido en la cuarta**. ⚠️ El sistema **solo registra las etapas completadas**: el
   abandono se deduce de **qué falta**, no de un registro de abandono que no existe.
2. **Given** un cliente que aún no ha terminado, **When** se pide el tiempo de onboarding, **Then**
   queda **fuera de la media** y se cuenta aparte: sigue en proceso, no tardó cero.
3. **Given** una solicitud rechazada, **When** se pide la tasa de aprobación, **Then** cuenta en el
   denominador: fue una solicitud resuelta.

---

### User Story 3 - El Administrador controla el acceso por rol (Priority: P3)

Los dos informes de **OT18**: cuánta gente entra a la vez y quién acumula roles que no deberían
coincidir.

**Why this priority**: el objetivo se cumple de forma **preventiva** —que el control por rol
funcione—, no detectiva. Estos dos informes lo vigilan, pero no sostienen ninguna decisión diaria.

| # | Informe | OT | Origen |
|--:|---|---|---|
| 8 | Sesiones concurrentes por día y franja horaria; duración media | OT18 | ± |
| 9 | Usuarios con acumulación de roles incompatibles | OT18 | ± |

**Acceptance Scenarios**:

1. **Given** sesiones sin evento de cierre, **When** se pide la duración media, **Then** se calcula
   **solo sobre las cerradas**, y las abiertas se cuentan aparte. ⚠️ Con 513 inicios y 195 cierres,
   una media que ignore esa diferencia describiría **el 27 % de las sesiones** como si fueran todas.
2. **Given** un usuario con dos roles que la política declara incompatibles, **When** se pide el
   informe, **Then** aparece con **ambos roles nombrados**.
3. **Given** un usuario con dos roles compatibles, **When** se pide el informe, **Then** **no
   aparece**: acumular roles es el mecanismo previsto del sistema, no un defecto.

---

### Edge Cases

- **Un cliente sin ninguna sesión registrada.** Aparece como **sin actividad conocida**, nunca con
  «0 días».
- **Un cliente aún en onboarding.** Fuera de la media de tiempo, contado aparte.
- **Una sesión sin cierre.** Fuera de la duración media, contada aparte.
- **Una sesión que cruza la medianoche.** Cuenta en las dos franjas horarias que toca, y el informe
  lo declara para que la suma de franjas no desconcierte.
- **Un cliente con `estado_onboarding` nulo pero estado activo.** El estado de onboarding se deriva
  de las etapas registradas, no de esa columna.
- **Un cliente sin plan.** No tiene tope de usuarios: su ocupación es **sin dato**, no 0 %.

---

## Requirements *(mandatory)*

### Funcionamiento general

- **FR-001**: Cada informe DEBE resolverse con **una consulta sobre el modelo analítico**, sin crear
  tablas ni flujos por informe.
- **FR-002**: Si falta un dato, DEBE ampliarse el modelo según su procedimiento de crecimiento.
- **FR-003**: Los informes NO DEBEN consultar el sistema operativo.
- **FR-004**: Toda consulta sobre un hecho acumulado o una dimensión DEBE forzar la versión final.
- **FR-005**: Todo informe DEBE aceptar un rango de fechas y devolver solo ese período.

### La dimensión de cliente, que ya existe

- **FR-006**: Este módulo **DEBE ampliar `dim_cliente`**, creada por Suscripciones, y **NO DEBE**
  crear una dimensión de cliente propia. Dos dimensiones del mismo cliente serían dos verdades.
- **FR-007**: La ampliación DEBE añadir lo que este departamento necesita —etapa de onboarding
  derivada, fecha de baja, motivo de baja y cohorte de alta— **sin alterar** las columnas que
  Suscripciones ya usa.

### El ciclo de vida

- **FR-008**: El churn DEBE agruparse por **cohorte de alta**, no por período de baja: la pregunta es
  qué cohortes retienen peor, no cuándo se fue la gente.
- **FR-009**: La antigüedad DEBE medirse desde el alta hasta **la baja o el momento actual**, según
  corresponda.
- **FR-010**: La ocupación de usuarios DEBE devolver **usuarios y tope**, no solo el porcentaje.
- **FR-011**: Un cliente **sin plan** DEBE devolver ocupación **sin dato**, nunca 0 %.
- **FR-012**: Las cuentas en riesgo DEBEN distinguir **«sin sesión desde hace N días»** de **«sin
  ninguna sesión registrada»**: nunca haber entrado y haber entrado hoy son lo contrario, y un cero
  las confundiría.

### La incorporación

- **FR-013**: El embudo de abandono DEBE derivarse de **la ausencia de etapas completadas**, contra
  el catálogo de etapas esperadas. ⚠️ El sistema **no registra abandonos**: solo escribe lo que se
  completó.
- **FR-014**: El catálogo de etapas esperadas DEBE ser **explícito y parametrizable**, no inferido de
  las etapas observadas: si se infiriera, una etapa que nadie ha completado nunca **desaparecería del
  embudo**, que es justo la que más importa.
- **FR-015**: El tiempo de onboarding DEBE medirse **solo sobre los clientes que lo completaron**;
  los que siguen en proceso se cuentan aparte y **no como cero**.
- **FR-016**: El estado de onboarding DEBE derivarse de **las etapas registradas**, no de la columna
  de estado del cliente, que está **nula en un cliente activo**.

### El acceso

- **FR-017**: La duración media de sesión DEBE calcularse **solo sobre sesiones con cierre
  registrado**, y las abiertas DEBEN contarse aparte. Con 513 inicios y 195 cierres, ignorar la
  diferencia describiría el 27 % como si fuera el total.
- **FR-018**: Las sesiones concurrentes DEBEN medirse por **solape de intervalos**, no por conteo de
  inicios en la franja.
- **FR-019**: Una sesión que **cruza la medianoche** DEBE contar en ambas franjas, y el informe DEBE
  declararlo.
- **FR-020**: La incompatibilidad de roles DEBE definirse como una **política explícita y
  parametrizable**. ⚠️ Acumular roles es el **mecanismo previsto** del sistema —el multi-rol es una
  decisión de arquitectura documentada—, así que solo son incompatibles las combinaciones que alguien
  declare como tales.
- **FR-021**: El informe DEBE **nombrar los roles** de la combinación detectada, no solo señalar al
  usuario.

### Presentación y límites

- **FR-022**: Ninguna respuesta DEBE incluir **token de sesión**. Es el dato más sensible del
  departamento y no lo necesita ningún informe.
- **FR-023**: Ninguna respuesta DEBE incluir **identidad de un usuario**: ni nombre, ni apellidos, ni
  correo, ni identificación, ni teléfono, ni género, ni fecha de nacimiento.
- **FR-024**: El informe de roles incompatibles DEBE identificar al usuario por **su clave**, no por
  su nombre: la combinación de roles es el hallazgo, y quien deba actuar puede resolver la identidad
  en el sistema operativo, con su propia auditoría.
- **FR-025**: Ninguna respuesta DEBE incluir **identificador fiscal** del cliente.
- **FR-026**: Un denominador de cero DEBE presentarse como **sin dato**, nunca como cero.
- **FR-027**: Un período sin datos DEBE devolver un resultado vacío explícito.

### Acceso

- **FR-028**: Los informes DEBEN ser de solo lectura.
- **FR-029**: El **Administrador** DEBE acceder a todos los informes del departamento.
- **FR-030**: El **Director Tecnológico** DEBE acceder a los informes de **acceso técnico** (OT18).
  ⚠️ Según el §5.1 del SRS, en este departamento su autoridad **alcanza solo a esa capa**, no al
  ciclo de vida ni a la incorporación.
- **FR-031**: Un **cliente** NO DEBE acceder a ningún informe de este módulo.
- **FR-032**: La exención de la autoridad NO DEBE alcanzar al dato sensible.

### Ampliaciones del modelo

- **FR-033**: El modelo DEBE incorporar un **hecho de etapa de onboarding**, con su instante de
  completado.
- **FR-034**: El modelo DEBE incorporar un **hecho de sesión**, con inicio, cierre si lo hubo y
  duración, **sin token ni identidad**.
- **FR-035**: El modelo DEBE incorporar una **dimensión de rol** y la **asignación de roles por
  usuario**, para poder detectar combinaciones.
- **FR-036**: El modelo DEBE conservar la **pertenencia usuario ↔ cliente**, con su cobertura
  declarada.

#### La pertenencia usuario ↔ cliente *(decisión 2026-08-14)*

El sistema tiene dos definiciones incompatibles y ninguna cubre a todos los usuarios. Se decidió
**usar la relación explícita y declarar cuánto abarca**.

- **FR-037**: La pertenencia DEBE tomarse de **la relación explícita usuario ↔ cliente**, y **NO** de
  la columna de administrador del cliente: esa columna conoce **solo al administrador**, no a los
  miembros, y usarla para contar usuarios respondería otra pregunta.
- **FR-038**: Los dos informes que dependen de ella DEBEN devolver **qué porcentaje de los usuarios
  del sistema tiene pertenencia conocida**. Hoy es el **9,5 %**, y sin ese número «1 de 10 usuarios»
  se leería como ocupación real cuando es cobertura del dato.
- **FR-039**: Los usuarios **sin pertenencia declarada** DEBEN contarse aparte como **organización
  desconocida**, y NO DEBEN repartirse entre clientes ni asignarse al cliente de su administrador.
- **FR-040**: Las dos fuentes de pertenencia **NO DEBEN combinarse**. Un administrador y un miembro
  son cosas distintas, y mezclarlos daría una cobertura mayor a costa de contar dos conceptos como
  uno.

---

## Success Criteria *(mandatory)*

- **SC-001**: Los 9 informes se obtienen sin que exista ninguna tabla dedicada a un informe.
- **SC-002**: El churn de un cliente dado de alta en enero y de baja en junio aparece en la **cohorte
  de enero**.
- **SC-003**: Un cliente **sin ninguna sesión** aparece como sin actividad conocida, **no con 0
  días**.
- **SC-004**: El embudo de abandono muestra una etapa **que nadie ha completado nunca**, en lugar de
  omitirla.
- **SC-005**: Un cliente aún en onboarding **no aparece** con tiempo cero.
- **SC-006**: La duración media de sesión se calcula sobre las cerradas, y las abiertas se declaran
  aparte.
- **SC-007**: Un usuario con dos roles **compatibles** no aparece en el informe de incompatibilidades.
- **SC-008**: Ningún informe devuelve token de sesión, identidad de usuario ni identificador fiscal,
  **para ningún rol**.
- **SC-009**: `dim_cliente` sigue sirviendo los informes de Suscripciones **con las mismas cifras**
  tras la ampliación.
- **SC-010**: Añadir estos informes **no altera** ninguna cifra de los cinco departamentos
  anteriores.
- **SC-011**: Los informes que dependen de la pertenencia declaran **qué porcentaje de usuarios la
  tiene conocida**, de modo que la ocupación de un plan no se confunda con la cobertura del dato.
- **SC-012**: Los usuarios sin pertenencia declarada **no se reparten** entre clientes: aparecen como
  organización desconocida.

---

## Assumptions

- **El modelo analítico está cargado**, las fases 1 y 2 de Emergencias implementadas, y **`dim_cliente`
  cargada por Suscripciones**.
- **El período por defecto** son los últimos 30 días; el churn por cohorte usa **mes natural**.
- **El umbral de inactividad** por defecto son **90 días**, parametrizable. El sistema no define
  ninguno.
- **El catálogo de etapas de onboarding** se declara explícitamente en el modelo, a partir de las
  etapas del proceso documentado.
- **La política de roles incompatibles** se declara explícitamente: no hay ninguna en el sistema.
- **El frontend queda fuera de alcance.**

---

## Riesgos ⚠️

### El onboarding se mide sobre un solo cliente

`Fact_Onboarding` tiene **3 filas, todas del mismo cliente y todas completadas**. El tiempo de
onboarding —indicador BSC— y el embudo de abandono se calcularían sobre esa única trayectoria.

Peor: **sin ninguna etapa incompleta registrada, un embudo mal diseñado mostraría 100 % de
finalización en todas las etapas** y parecería un proceso perfecto. Por eso FR-013 y FR-014 exigen
medir por ausencia contra un catálogo explícito.

### Dos definiciones de pertenencia, y ninguna cubre el sistema

`Dim_Cliente.admin_local_id` da **un administrador por cliente** —4 clientes, 4 administradores— y
`Dim_Usuario_Cliente` tiene **3 filas para 2 usuarios distintos**, sobre un total de **21 usuarios**.

Cualquiera que se elija, **la mayoría de los usuarios del sistema no tiene organización conocida**.
Ver *Aclaración pendiente*.

### `Fact_HistorialTransferenciaPropiedad` está vacía

Sostiene un informe simple de otro módulo, no de este. Se anota porque es el mismo patrón ya visto
seis veces: el esquema declara algo que la operación no rellena.

---

## Aclaración, resuelta el 2026-08-14

**Informes #3 y #4 → se usa la relación explícita usuario ↔ cliente, con la cobertura declarada**
(FR-037 a FR-040).

De las dos definiciones incompatibles, se toma la que **puede contar usuarios**; la columna de
administrador conoce solo al administrador y respondería otra pregunta.

**Lo que hace honesta a la decisión es FR-038**: los informes devuelven **qué porcentaje de los
usuarios del sistema tiene pertenencia conocida** —hoy el **9,5 %**—. Sin ese número, «1 de 10
usuarios» se leería como ocupación real cuando en realidad es **cobertura del dato**, y un cliente
parecería tener sitio de sobra cuando quizá esté lleno.

**Y FR-040 impide la tentación razonable**: combinar ambas fuentes daría más cobertura a costa de
contar administradores y miembros como si fueran lo mismo.

**Lo que sigue faltando** es que la operación registre la pertenencia de los 19 usuarios restantes.
Es una carencia del sistema operativo, no de este módulo.

---

## Dependencias

- **[`modelo-analitico/`](../../../modelo-analitico/)** — el sustrato.
- **[`Emergencias/informes-compuestos-modelo/`](../../Emergencias/informes-compuestos-modelo/)** —
  aporta la plomería.
- **[`Suscripciones-Facturacion/informes-compuestos-modelo/`](../../Suscripciones-Facturacion/informes-compuestos-modelo/)** —
  ⚠️ **creó `dim_cliente` y `dim_plan`**. Este módulo **las amplía, no las recrea**.
- **[`acceso-tactico.md`](../../../acceso-tactico.md)** — la autoridad limitada del Director
  Tecnológico en este departamento.

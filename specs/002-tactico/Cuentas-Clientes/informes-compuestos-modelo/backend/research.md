# Research — Informes Compuestos de Cuentas y Clientes

**Fecha:** 2026-08-14 · **Plan:** [`plan.md`](plan.md)

Ocho decisiones. Las cifras están **medidas contra el sistema real**.

---

## D1 — `dim_cliente` se amplía, no se recrea ⚠️

**Hallazgo.** `dim_cliente` existe en el modelo: la creó **Suscripciones**, que fue el primer módulo
que la necesitó. Este departamento es su **dueño natural** y llega el sexto.

**Decisión.** Se **amplía** con lo que falta —cohorte de alta, fecha y motivo de baja, etapa de
onboarding derivada— **sin tocar** las columnas que Suscripciones ya usa, y una prueba comprueba que
sus informes siguen dando las mismas cifras.

**Rationale.** Es el momento en que se comprueba si el modelo compartido funciona **en la dirección
difícil**. Que un módulo cree una dimensión y otro la consuma es fácil; que el **dueño llegue después
y no tenga que rehacerla** es lo que distingue una dimensión conformada de una tabla que alguien puso
primero.

Si se recreara, habría **dos verdades sobre el mismo cliente**, y los ingresos por tipo de cliente de
Suscripciones dejarían de cuadrar con las cuentas activas de este módulo — sin que nada fallara.

**Alternativa descartada.** *Crear `dim_cuenta` como entidad separada* — el argumento sería que una
«cuenta» y un «cliente» son cosas distintas conceptualmente. En este sistema **no lo son**: comparten
identificador, estado y plan.

---

## D2 — El abandono se mide por ausencia, contra un catálogo explícito ⚠️

**Hallazgo.** `Fact_Onboarding` tiene **3 filas, todas con `completado = true`** y todas del mismo
cliente. **El sistema no registra abandonos**: solo escribe lo que se completó.

**Decisión.** El embudo se calcula **por ausencia**: para cada cliente y cada etapa del catálogo, se
mira si hay registro de completado. Y el **catálogo de etapas es una dimensión explícita**, no
inferida de lo observado.

**Rationale del catálogo explícito, que es la parte que importa.** Si las etapas se infirieran de las
filas existentes, **una etapa que nadie ha completado nunca no aparecería en el embudo**. Con los
datos actuales —tres etapas registradas de un proceso que tiene más— el informe mostraría
**100 % de finalización en todas las etapas** y describiría un proceso perfecto.

**Es la etapa donde todos abandonan la que no se vería.** Y es exactamente la que el informe existe
para encontrar.

**Alternativa descartada.** *Deducir el abandono de `Dim_Cliente.estado_onboarding`* — esa columna
está **nula en un cliente activo**, y en cualquier caso da un estado, no una trayectoria: diría que
alguien está «Pendiente» sin decir dónde se detuvo.

---

## D3 — Las sesiones son eventos; la duración solo se mide donde existe ⚠️

**Hallazgo.** `Fact_Session` tiene 718 filas repartidas en **513 inicios, 195 cierres y 10
expulsiones**. La mayoría de las sesiones **no tiene evento de cierre**.

**Decisión.** La duración media se calcula **solo sobre las sesiones con cierre registrado**, y las
abiertas se cuentan aparte.

**Rationale.** Hay tres formas de tratarlas y dos son mentira:

- **Ignorarlas** y promediar solo las cerradas **sin decirlo**: describiría el 27 % de las sesiones
  como si fueran todas — y precisamente las que terminaron bien.
- **Contarlas como duración cero**: hundiría la media con sesiones que probablemente fueron largas.
- **Contarlas hasta el momento actual**: inventaría una duración para sesiones que quizá cerraron sin
  registrarse.

La única honesta es **medir lo medible y declarar cuánto se midió**.

**Y las expulsiones son un tercer desenlace**, no un cierre: una sesión expulsada terminó, pero no
porque el usuario se fuera.

---

## D4 — La concurrencia se mide por solape, no por conteo de inicios

**Hallazgo.** «Sesiones concurrentes por día y franja horaria» es la consulta más cara del módulo:
exige saber **cuántos intervalos se solapan** en cada instante, no cuántas sesiones empezaron.

**Decisión.** Se mide por **solape de intervalos**, y una sesión que cruza la medianoche **cuenta en
ambas franjas**, con el informe declarándolo.

**Rationale.** Contar inicios por franja responde a «cuánta gente entró», que es otra pregunta: diez
sesiones de un minuto repartidas por la hora y diez simultáneas dan el mismo número y describen
situaciones opuestas. La concurrencia es una medida de **carga**, no de volumen.

**Lo de la medianoche hay que decirlo** porque hace que la suma de franjas sea **mayor** que el total
de sesiones, y quien vea eso sin explicación pensará que hay un error de conteo.

---

## D5 — Ni token, ni identidad, ni identificador fiscal ⚠️

**Hallazgo.** Este departamento guarda lo más sensible del sistema en términos de acceso:

| Dato | Dónde |
|---|---|
| **Token de sesión** | `Fact_Session.token` |
| Nombre, apellidos, correo, identificación, teléfono | `Dim_Usuarios` |
| **Género y fecha de nacimiento** | `Dim_Usuarios` |
| Identificador fiscal del cliente | `Dim_Cliente.nit_identificacion` |

**Decisión.** **Ninguno entra al modelo.**

**Rationale.** El token es una credencial viva: copiarlo a un almacén analítico lo expone a cualquier
consulta y a cualquier copia de seguridad. Género y fecha de nacimiento son **datos especialmente
protegidos** y ningún informe del catálogo los menciona siquiera.

**Es la sexta vez que esta exclusión aparece** —coordenadas, identidad de prospecto, medios de cobro,
secretos de API, ejecutores de cambios, y ahora sesión e identidad de usuario— y la sexta con la
misma resolución. Ya no es una decisión: es una propiedad del modelo.

---

## D6 — El usuario se identifica por su clave, y solo donde hace falta ⚠️

**Hallazgo.** El informe de roles incompatibles **necesita señalar a alguien** para ser accionable.
Decir «hay 3 combinaciones peligrosas» no permite actuar.

**Decisión.** Se identifica al usuario **por su clave**, nunca por su nombre, y **solo en ese
informe**.

**Rationale.** Es la primera vez en la serie que la solución no es agregar. En Emergencias, Red
Operativa, Suscripciones y Partners el desglose por persona se eliminó porque **el informe seguía
siendo útil sin él** — «qué unidades documentan bien» no necesita nombres.

Aquí no: un riesgo de segregación de funciones **es de una persona concreta**, y un informe que no
diga cuál no sirve para arreglarlo.

La clave numérica es el compromiso: **identifica sin exponer**, y quien deba actuar resuelve el
nombre en el sistema operativo, **donde ese acceso queda auditado** — que es exactamente donde debe
quedar registrado que alguien consultó quién es un usuario.

---

## D7 — El churn se agrupa por cohorte de alta

**Hallazgo.** «Tasa de baja por cohorte de alta» admite dos lecturas: agrupar por el mes en que se
dieron de baja, o por el mes en que se dieron de alta.

**Decisión.** Por **cohorte de alta**.

**Rationale.** La pregunta del indicador es **qué cohortes retienen peor**, no cuándo se fue la
gente. Agrupar por mes de baja produce una serie que sube y baja con el volumen de altas de meses
anteriores, y no permite comparar: una cohorte de enero con 50 clientes y otra de febrero con 5 se
mezclan en el mismo número.

Por cohorte de alta, en cambio, cada grupo se compara consigo mismo a lo largo del tiempo, que es
para lo que sirve un análisis de retención.

---

## D8 — La incompatibilidad de roles es una política, no un cálculo

**Hallazgo.** El sistema **no define ninguna combinación de roles como incompatible**. Y el multi-rol
**es un mecanismo previsto**: la arquitectura documenta explícitamente que una persona acumula roles
mediante filas en la tabla puente, **sin herencia**.

Los datos lo confirman: hay usuarios con dos roles activos.

**Decisión.** La incompatibilidad se declara como **política explícita y parametrizable** en el
modelo. Sin política declarada, el informe **no devuelve nada**.

**Rationale.** Un informe que marcara «usuarios con más de un rol» estaría denunciando **el
funcionamiento normal del sistema**. La acumulación no es el problema; ciertas combinaciones lo son
—quien aprueba y quien ejecuta, por ejemplo— y **eso lo decide el negocio, no el modelo**.

**Que devuelva vacío sin política es deliberado.** Es preferible a inventar una lista de
combinaciones peligrosas que nadie ha aprobado y presentarla como un hallazgo de auditoría.

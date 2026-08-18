# Acceso a los informes estratégicos — quién ve qué

**Fecha:** 2026-08-16
**Alcance:** los **76 informes distintos** de OE1–OE6 (80 del catálogo, menos 4 duplicados entre OE1
y OE5 — ver §7.1 del contrato).
**Autoridad de la asignación departamental:** `informestacticos/TSI-SRS-Especificacion-de-Requisitos.md`
§5.1, la misma fuente que resolvió la capa táctica.
**Contraparte táctica:** [`specs/002-tactico/acceso-tactico.md`](../002-tactico/acceso-tactico.md).

Este documento resuelve, en un solo sitio, quién accede a cada informe estratégico. **Es la fuente
que cada spec de OE debe citar** en su sección de permisos, en lugar de decidirlo por su cuenta.

---

## 1. La regla, y por qué no es la del marco

El §13.1 del marco asigna **«Alta Dirección»** como actor de los diez CU estratégicos, sin más
detalle. Aplicado literalmente, eso significa *todo el mundo arriba ve los 76 informes*.

**No se aplica así.** La regla de esta capa es:

> ### Un informe estratégico lo ve la autoridad del departamento **dueño del dato que mide**.

Un Gerente de Éxito del Cliente no tiene por qué ver el margen por región; un Director Financiero no
tiene por qué ver la tasa de rechazo por unidad de emergencia. Cada uno responde por lo suyo, y el
informe estratégico de su materia es la versión de empresa de lo que ya supervisa.

**Por qué se aparta del marco.** «Alta Dirección» describe el *nivel* de la decisión, no el *permiso*
de lectura. Concederlo como permiso convertiría los informes estratégicos en el camino corto para ver
consolidado lo que en la capa táctica está deliberadamente repartido — y esa capa repartió la
autoridad porque el propio §5.1 advierte que **«no debe leerse como una cadena de mando única»**.
Un informe no puede ser la puerta trasera que salta un reparto: es la misma regla del §5 del contrato
táctico, un nivel más arriba.

### Lo que la regla NO relaja

- **El dato sensible sigue excluido para todos.** Coordenadas, identidad de implicados, secretos de
  autenticación, medios de cobro y texto interno **no aparecen en ningún informe**, sea cual sea el
  cargo. Son exclusiones constitucionales, no de acotamiento (§5.7 del contrato táctico).
- **Ver no habilita a decidir.** Un informe no concede la acción que describe.
- **No hay acotamiento por titularidad en esta capa.** Son agregados de empresa: o se accede al
  informe entero, o no se accede. No existe una «versión propia» de un MRR consolidado.

---

## 2. La única excepción: el rol `Gerente`

Los tres CU que no producen informes propios —**CU-E01** (tablero integral), **CU-E09** (escenarios
de expansión) y **CU-E10** (reporte gerencial consolidado)— **agregan los seis OE por definición**.

Si nadie puede leer los seis, esos tres casos de uso no son construibles por nadie, y el marco se
comprometió con ellos.

Por eso se define **un solo rol transversal**, `Gerente`, que accede a los 76:

| Rol | Alcance | Justificación |
|---|---|---|
| `Gerente` | **Los 76 informes de OE1–OE6** | Es el actor de CU-E01, CU-E09 y CU-E10, que cruzan los seis objetivos por construcción |

**Es uno, no un grupo.** No se crea un «grupo Alta Dirección» que acumule directores: eso reintroduce
por la puerta de atrás lo que la §1 acaba de cerrar. Cada director entra por su departamento; el
Gerente entra por el tablero.

> ⚠️ **Si esta excepción se retira**, CU-E01, CU-E09 y CU-E10 quedan sin destinatario posible y hay
> que declararlos fuera de alcance explícitamente. No se pueden mantener en el catálogo y a la vez
> negar el rol que los ejecuta.

---

## 3. Roles: los que existen y el que hay que crear

**Ya existen** como autoridades departamentales, implementados en
`backend/core/auth/roles_tacticos.py` desde el 2026-08-14:

`DirectorMarketing` · `DirectorFinanciero` · `DirectorEstrategia` · `DirectorTecnologico` ·
`DirectorExpansion` · `DirectorOperaciones` · `GerenteExitoCliente` · `DirectorDatos`

**Hay que crear uno:**

| Rol | Autoridad de |
|---|---|
| `Gerente` | El tablero estratégico integral — los 76 informes |

Ya figura en `.specify/docs/actors.md` como actor estratégico *«fuera de alcance»*. **Este documento
lo trae a alcance**, igual que el 2026-08-14 hizo con las ocho autoridades departamentales.

---

## 4. Mapa OE → departamento dueño → autoridad

Es la aplicación de la regla del §1, informe por informe. La columna **Departamento dueño** es la
que manda: la autoridad sale de ella vía §5.1, no al revés.

Todos los informes son además accesibles por `Gerente` (§2), que no se repite en cada fila.

### 4.1 OE1 — Posicionamiento y Captación Digital *(13 informes, 12 propios)*

| Informe | Departamento dueño | Autoridad |
|---|---|---|
| **E1-01** MRR mensual y variación MoM | Suscripciones *(resultado)* | `DirectorFinanciero` |
| **E1-02** ARR y proyección anual | Suscripciones *(resultado)* | `DirectorFinanciero` |
| **E1-03** MRR y ARPU por segmento | Suscripciones *(catálogo + resultado)* | `DirectorEstrategia` · `DirectorFinanciero` |
| **E1-04** Embudo de conversión digital | Ventas y CRM | `DirectorMarketing` |
| **E1-05** CAC por canal ⛔ | Ventas y CRM | `DirectorMarketing` |
| **E1-06** Tasa de renovación | Suscripciones *(resultado)* | `DirectorFinanciero` |
| **E1-07** Mercados activos ⚠️ | Red Operativa *(crecimiento)* + Suscripciones | `DirectorExpansion` · `DirectorFinanciero` |
| **E1-08** Cartera y MRR por mercado ⚠️ | Red Operativa *(crecimiento)* + Suscripciones | `DirectorExpansion` · `DirectorFinanciero` |
| **E1-09** Tiempo de onboarding | Cuentas y Clientes | ⚠️ **sin autoridad** — ver §5 |
| **E1-10** Embudo de abandono en onboarding | Cuentas y Clientes | ⚠️ **sin autoridad** — ver §5 |
| **E1-11** Churn de cliente por cohorte | Cuentas y Clientes | ⚠️ **sin autoridad** — ver §5 |
| **E1-12** Distribución de cartera por plan | Suscripciones *(catálogo)* | `DirectorEstrategia` |
| **E1-13** Velocidad del ciclo de venta | Ventas y CRM | `DirectorMarketing` |

> **E1-06, E1-09, E1-10 y E1-11 son los cuatro compartidos con OE5** (§7.1 del contrato). OE1 es el
> dueño de los cuatro: el catálogo los introduce aquí primero y su meta BSC se define en la
> perspectiva Financiera. OE5 los referencia.

### 4.2 OE2 — Monetización del Ecosistema de APIs *(11 informes)*

| Informe | Departamento dueño | Autoridad |
|---|---|---|
| **E2-01** Participación de ingresos por API ⚠️ | Partners y API + Suscripciones | `DirectorTecnologico` · `DirectorFinanciero` |
| **E2-02** MRR por línea: plataforma vs API ⚠️ | Partners y API + Suscripciones | `DirectorTecnologico` · `DirectorFinanciero` |
| **E2-03** Clientes con integración activa | Partners y API | `DirectorTecnologico` |
| **E2-04** Intensidad de consumo por partner | Partners y API | `DirectorTecnologico` |
| **E2-05** Latencia p95 por endpoint | Partners y API | `DirectorTecnologico` |
| **E2-06** Disponibilidad de la API pública | Partners y API | `DirectorTecnologico` |
| **E2-07** Taxonomía de errores 4xx / 5xx | Partners y API | `DirectorTecnologico` |
| **E2-08** Excedente facturable por partner | Partners y API + Suscripciones | `DirectorTecnologico` · `DirectorFinanciero` |
| **E2-09** Adopción de versiones del contrato | Partners y API | `DirectorTecnologico` |
| **E2-10** Comparativa entre partners | Partners y API | `DirectorTecnologico` |
| **E2-11** Crecimiento del ecosistema de partners | Partners y API | `DirectorTecnologico` |

Es el OE más limpio: un solo departamento dueño, con Finanzas entrando **solo donde hay dinero**.

### 4.3 OE3 — Escalabilidad Multi-Región *(14 informes)*

Autoridad repartida, como en la capa táctica: **Tecnológico valida, Expansión decide dónde crecer,
Operaciones responde por el despacho.**

| Informe | Departamento dueño | Autoridad |
|---|---|---|
| **E3-01** Uptime global por región | Infraestructura | `DirectorTecnologico` |
| **E3-02** Latencia de despacho p95 *(compartido OE6)* | Emergencias | `DirectorOperaciones` · `DirectorTecnologico` |
| **E3-03** Evolución de la latencia p95 | Emergencias | `DirectorOperaciones` |
| **E3-04** Tiempo de puesta en operación regional | Red Operativa *(validación + crecimiento)* | `DirectorTecnologico` · `DirectorExpansion` |
| **E3-05** Curva de maduración de región nueva | Red Operativa *(crecimiento)* | `DirectorExpansion` |
| **E3-06** Rendimiento por cohorte de región | Red Operativa *(crecimiento)* | `DirectorExpansion` |
| **E3-07** Ratio demanda / capacidad | Red Operativa + Emergencias | `DirectorExpansion` · `DirectorOperaciones` |
| **E3-08** Cobertura de respaldo por condado | Red Operativa *(crecimiento)* | `DirectorExpansion` |
| **E3-09** Margen operativo por región ⛔ | Suscripciones *(resultado)* | `DirectorFinanciero` |
| **E3-10** Tasa de error de registro *(compartido OE6)* | Emergencias | `DirectorOperaciones` |
| **E3-11** Despachos al primer intento *(compartido OE6)* | Emergencias | `DirectorOperaciones` |
| **E3-12** Tiempo de reasignación manual *(compartido OE6)* | Emergencias | `DirectorOperaciones` |
| **E3-13** Pérdida de señal GPS | Emergencias + Red Operativa *(flota)* | `DirectorOperaciones` · `DirectorExpansion` |
| **E3-14** Cobertura de pruebas ⛔ | Infraestructura | `DirectorTecnologico` |

> **Los cuatro compartidos con OE6 viven aquí**, porque es OE3 quien define su meta `[NORMATIVO]`.
> OE6 los referencia sin reimplementarlos (§7 del contrato).

### 4.4 OE4 — Inteligencia Predictiva *(15 informes)*

Dueño principal **Analítica e Inteligencia**, con Emergencias como dueño del dato de origen: el
expediente del accidente es suyo, y su calidad se mide contra su operación.

| Informe | Departamento dueño | Autoridad |
|---|---|---|
| **E4-01** Índice de calidad del histórico | Analítica + Emergencias | `DirectorDatos` · `DirectorOperaciones` |
| **E4-02** Completitud de campos críticos | Analítica + Emergencias | `DirectorDatos` · `DirectorOperaciones` |
| **E4-03** Campos con mayor tasa de ausencia | Analítica + Emergencias | `DirectorDatos` · `DirectorOperaciones` |
| **E4-04** Calidad por origen: central vs campo | Analítica + Emergencias | `DirectorDatos` · `DirectorOperaciones` |
| **E4-05** Mapa de concentración de siniestralidad | Analítica | `DirectorDatos` |
| **E4-06** Patrón horario y climático | Analítica | `DirectorDatos` |
| **E4-07** Precisión del modelo predictivo ⚠️ | Analítica | `DirectorDatos` |
| **E4-08** Contraste predicción vs ocurrencia ⚠️ | Analítica | `DirectorDatos` |
| **E4-09** Unidades preposicionadas ⚠️ | Analítica + Red Operativa | `DirectorDatos` · `DirectorExpansion` |
| **E4-10** Versiones del modelo predictivo ⚠️ | Analítica | `DirectorDatos` |
| **E4-11** Productos de inteligencia vendidos ⚠️ | Analítica + Suscripciones *(catálogo)* | `DirectorDatos` · `DirectorEstrategia` |
| **E4-12** Impacto humano por zona | Analítica + Emergencias | `DirectorDatos` · `DirectorOperaciones` |
| **E4-13** Impacto vial por zona | Analítica + Emergencias | `DirectorDatos` · `DirectorOperaciones` |
| **E4-14** Latencia de ingesta al analítico | Analítica | `DirectorDatos` |
| **E4-15** Cobertura del histórico por región | Analítica + Red Operativa | `DirectorDatos` · `DirectorExpansion` |

### 4.5 OE5 — Retención y Ciclo de Vida *(15 informes, 11 propios)*

| Informe | Departamento dueño | Autoridad |
|---|---|---|
| **E5-01** NPS / satisfacción global ⛔ | Soporte al Cliente | `GerenteExitoCliente` |
| **E5-02** Retención neta de ingresos (NRR) | Suscripciones *(resultado)* | `DirectorFinanciero` |
| **E5-03** Movimientos de plan con delta de ingreso | Suscripciones *(catálogo + resultado)* | `DirectorEstrategia` · `DirectorFinanciero` |
| **E5-04** Cumplimiento consolidado de SLA | Soporte al Cliente | `GerenteExitoCliente` |
| **E5-05** Evolución del incumplimiento de SLA | Soporte al Cliente | `GerenteExitoCliente` |
| **E5-06** Rendimiento por agente de soporte | Soporte al Cliente | `GerenteExitoCliente` |
| **E5-07** SLA desglosado por plan | Soporte al Cliente + Suscripciones | `GerenteExitoCliente` · `DirectorEstrategia` |
| **E5-08** Reincidencia de soporte | Soporte al Cliente | `GerenteExitoCliente` |
| **E5-09** → **referencia a E1-06** | Suscripciones | `DirectorFinanciero` |
| **E5-10** → **referencia a E1-11** | Cuentas y Clientes | ⚠️ **sin autoridad** — ver §5 |
| **E5-11** Reportes sin corrección posterior ⛔ | Analítica | `DirectorDatos` |
| **E5-12** Cuentas en riesgo de churn | ⚠️ **cruza cuatro departamentos** | ver §6 |
| **E5-13** → **referencia a E1-09** | Cuentas y Clientes | ⚠️ **sin autoridad** — ver §5 |
| **E5-14** → **referencia a E1-10** | Cuentas y Clientes | ⚠️ **sin autoridad** — ver §5 |
| **E5-15** Antigüedad media de cuenta | Cuentas y Clientes + Suscripciones | ⚠️ ver §5 · `DirectorEstrategia` |

### 4.6 OE6 — Tiempo de Respuesta y Seguridad de Vidas *(12 informes)*

**El único OE con un solo dueño.** Los doce son de Emergencias, y su autoridad es
`DirectorOperaciones`:

| Informe | |
|---|---|
| **E6-01** Tiempo global de respuesta: registro a llegada | `DirectorOperaciones` |
| **E6-02** Tiempo de respuesta por severidad | `DirectorOperaciones` |
| **E6-03** Desglose de tiempos por tramo del ciclo | `DirectorOperaciones` |
| **E6-04** Asignación automática vs manual | `DirectorOperaciones` |
| **E6-05** Tasa de rechazo y timeout por unidad | `DirectorOperaciones` |
| **E6-06** Abortos y misiones fallidas | `DirectorOperaciones` |
| **E6-07** Desviación entre ETA y llegada real | `DirectorOperaciones` |
| **E6-08** Impacto humano agregado | `DirectorOperaciones` |
| **E6-09** Cierres forzados desde central | `DirectorOperaciones` |
| **E6-10** Envejecimiento de casos abiertos | `DirectorOperaciones` |
| **E6-11** Escaladas de severidad en sitio | `DirectorOperaciones` |
| **E6-12** Cobertura de evidencia por severidad | `DirectorOperaciones` |

⚠️ **La exclusión de coordenadas e identidad de implicados rige también para el Director de
Operaciones**, exactamente igual que en la capa táctica. Es constitucional.

---

## 5. Hallazgo heredado: Cuentas y Clientes sigue sin autoridad

**Seis informes se quedan sin jefatura departamental**: E1-09, E1-10, E1-11 y sus tres referencias
desde OE5 (E5-13, E5-14, E5-10), más el tramo de cuenta de E5-15.

No es un olvido de este documento. El §5.1 del SRS **no asigna autoridad de negocio a Cuentas y
Clientes**: solo el Director Tecnológico, y limitado a la capa de accesos técnicos. La capa táctica
resolvió el hueco dejándolos bajo el **Administrador**, que es su responsable operativo y su única
visión de conjunto.

**Aquí no se hace eso, y el motivo es la propia regla del §1.**

El Administrador es un rol **operativo**. Concederle el churn consolidado por cohorte y el tiempo de
onboarding de toda la empresa le daría la lectura de dirección de un departamento del que nadie
responde a nivel estratégico — que es más de lo que tiene en la capa táctica, no menos.

**Decisión:** esos seis informes quedan accesibles **solo por `Gerente`** hasta que se resuelva quién
es la autoridad de Cuentas y Clientes. Es la opción conservadora: prefiere que un informe lo vea una
persona de menos a que lo vea un rol que no debería.

> Queda registrado como **decisión pendiente**, arrastrando la que ya abrió `acceso-tactico.md` §4.
> Las dos se resuelven juntas o ninguna.

---

## 6. E5-12 no tiene un departamento dueño, y por eso es distinto

«Cuentas en riesgo de churn» cruza **cuatro señales de cuatro departamentos**: caída de consumo de
API (Partners), alza de tickets (Soporte), fallos de cobro (Suscripciones) y ausencia de sesiones
(Cuentas).

Ningún departamento es dueño del informe: **el informe existe precisamente porque ninguna de las
cuatro señales, por separado, predice nada.**

Es el único caso del catálogo donde la regla del §1 no decide. Dos salidas, y se elige la segunda:

| Salida | Consecuencia |
|---|---|
| Concederlo a las cuatro autoridades | Cada una vería las señales de los otros tres departamentos, sin serlo. Es la puerta trasera que §1 cierra. |
| **Concederlo solo a `Gerente`** ✅ | Es un informe de dirección por naturaleza: la acción que sigue —intervenir una cuenta en riesgo— es transversal y no la ejecuta ningún departamento solo. |

---

## 7. Resumen de la asignación

| Autoridad | Informes a los que accede |
|---|:--:|
| `Gerente` | **76** *(todos)* |
| `DirectorOperaciones` | 25 |
| `DirectorDatos` | 16 |
| `DirectorTecnologico` | 15 |
| `DirectorFinanciero` | 12 |
| `DirectorExpansion` | 10 |
| `GerenteExitoCliente` | 6 |
| `DirectorEstrategia` | 6 |
| `DirectorMarketing` | 3 |

**Ningún director llega a un tercio del catálogo**, y esa es la comprobación de que la regla del §1
se aplicó de verdad. Si alguna autoridad se acercara al total, sería señal de que la asignación
degeneró en «Alta Dirección lo ve todo» con otro nombre.

El más alto es `DirectorOperaciones` con 25 de 76, y es coherente: Emergencias es el núcleo del
sistema, es dueño único de OE6 entero y comparte OE3 y OE4. Que la operación de emergencias pese más
que las finanzas en un sistema cuya razón de existir es despachar ambulancias no es una anomalía de
la asignación.

> **`DirectorMarketing` con solo 3 informes no es un error.** Ventas y CRM aporta el embudo y el
> ciclo de venta; el resultado económico de esa captación es de Suscripciones, y el CAC no es
> construible. Es el reflejo fiel de dónde vive el dato.

---

## 8. Estado de aplicación

| Documento | Cambio | Estado |
|---|---|:--:|
| `contrato-informes-estrategicos.md` §8 | Remite aquí en lugar de decidir permisos | ✅ |
| `.specify/docs/actors.md` | El rol `Gerente` es autoridad del tablero | ✅ |
| `backend/core/auth/roles_tacticos.py` | `ROL_GERENTE` y conjuntos OE3/OE6 | ✅ |
| `ROLES_DEMO` idrol 23 | Fila `Gerente` en el catálogo de seed | ✅ código; **correr el seed** para Pinot |
| Specs de OE1–OE6 | Citan este documento | ✅ existen |

### Semilla en Pinot

El rol `Gerente` y las seis autoridades tácticas **están en código**. Falta **ejecutar el seed** de
`Dim_Rol` en el entorno para que un usuario demo pueda acumular `Gerente`. No es trabajo de spec.

---

## 9. Lo que este documento NO decide

- **Quién asigna el rol `Gerente` a una persona.** Es competencia del Administrador, como cualquier
  otro rol.
- **Si Cuentas y Clientes debe tener autoridad de negocio propia.** Anotado como pendiente, arrastrado
  desde la capa táctica.
- **La pantalla.** Que un director tenga acceso a un informe no dice en qué tablero lo ve.
- **El acceso de los actores estratégicos restantes** —Director de Producto, Director de RRHH,
  Legal—, que siguen fuera de alcance: ninguno es autoridad de un departamento del §5.1.

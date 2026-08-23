# Acceso a los informes tácticos — quién ve qué

**Fecha:** 2026-08-14
**Autoridad:** `informestacticos/TSI-SRS-Especificacion-de-Requisitos.md` §5.1 y §5.2.
**Alcance:** los **32 endpoints** de listados especificados en los ocho módulos, más los informes
compuestos y el modelo analítico.

Este documento resuelve, en un solo sitio, quién accede a cada informe táctico. **Es la fuente que
cada spec de módulo debe citar** en su sección de permisos, en lugar de decidirlo por su cuenta.

> **Sobre el número.** El catálogo enumera 68 informes simples, pero varios de ellos son la misma
> consulta con distinto filtro. Al especificarlos se consolidaron en **32 endpoints**. Son esos los
> que aquí se clasifican.

---

## 1. Las dos columnas del §5.1 son dos capas

El SRS asigna a cada departamento un **responsable operativo** —que ejecuta y decide en el día a
día— y una **autoridad superior** —que fija los criterios bajo los que ese trabajo se hace—.

**Son dos capas, no dos niveles de permiso sobre lo mismo.** El marco lo define igual: el nivel
táctico es *planeación y control por departamento, mensual o semanal*; el operativo es *ejecución
diaria*.

### Pero no todos los listados son tácticos

Al revisarlos uno por uno aparece que **una parte de lo especificado no es supervisión: son
herramientas de trabajo** que hoy no existen en ninguna pantalla.

Un listado de «solicitudes de alta pendientes con su antigüedad» no es un informe de gestión: es la
bandeja con la que el Administrador aprueba. Dárselo solo a una autoridad dejaría al Administrador
aprobando una por una, como hoy.

Por eso cada endpoint se clasifica en **una de tres clases**:

| Clase | Qué es | Destinatario |
|:---:|---|---|
| **B** | **Bandeja operativa** — herramienta de trabajo diario | Responsable operativo, con su acotamiento |
| **S** | **Supervisión táctica** — planeación y control | Autoridad departamental, sin acotamiento |
| **A** | **Ambas** — sirve a los dos, con distinto propósito | Los dos, cada uno con su alcance |

---

## 2. El principio de acotamiento, y su excepción

El contrato común fija que **un informe nunca es más amplio que la pantalla operativa del mismo
dato**, para impedir que se convierta en la puerta trasera que salta un acotamiento.

> **Excepción explícita: la autoridad departamental.** Accede a los informes de su departamento
> **sin acotamiento por titularidad**, porque su función es supervisar y no tiene pantalla operativa
> que espejar.

**Lo que la excepción NO cubre:**

- **El dato sensible sigue excluido para todos.** Coordenadas de accidentes, identidad de personas
  implicadas, secretos de autenticación, medios de cobro y texto interno **no aparecen en ningún
  informe**, sea cual sea el cargo de quien consulta. Son exclusiones constitucionales, no de
  acotamiento.
- **Ver no habilita a ejecutar.** Un informe no concede la acción que describe.

---

## 3. Roles: los que existen y los seis que hay que crear

**Ya existen:** `Administrador` · `Cliente` · `Operador` · `Proveedor` · `Unidad` · `Tecnico` ·
`Despacho` · `DirectorEstrategia` · `DirectorTecnologico` · `DesarrolladorAPIs` ·
`PartnerIntegracion` · `Soporte` · `SupervisorSoporte` · `GerenteVentas` · `GerenteCuentasPublicas`

**Hay que crear seis**, todos autoridad departamental del §5.1:

| Rol | Autoridad de |
|---|---|
| `DirectorMarketing` | Ventas y CRM |
| `DirectorFinanciero` | Suscripciones y Facturación |
| `DirectorExpansion` | Red Operativa |
| `DirectorOperaciones` | Emergencias |
| `GerenteExitoCliente` | Soporte al Cliente |
| `DirectorDatos` | Analítica e Inteligencia |

---

## 4. La autoridad no siempre es una jefatura única

El SRS lo subraya, y **aplicarlo mecánicamente sería un error**:

> *«En algunos departamentos la autoridad está repartida por materia en lugar de concentrada en un
> solo cargo […] no debe leerse como una cadena de mando única.»*

| Departamento | Reparto |
|---|---|
| **Suscripciones** | Estrategia decide catálogo y precios; Financiero responde por el resultado |
| **Red Operativa** | Tecnológico decide la validación de regiones; Expansión, el crecimiento |
| **Cuentas y Clientes** | Tecnológico gobierna **solo la capa de accesos técnicos** |

### Hallazgo (resuelto): Cuentas y Clientes no tenía autoridad de negocio

La única que el §5.1 le asignaba era el Director Tecnológico, limitado a accesos técnicos. Sus
informes de altas, incorporación, ciclo de vida y sesiones **no tenían jefatura por encima del
Administrador** — que era a la vez su responsable operativo y su única visión de conjunto.

Eso se volvió un problema concreto el 2026-08-19, al decidir que el Administrador **opera y no lee
gestión**: siete de los nueve informes compuestos del departamento se habrían quedado sin que nadie
pudiera abrirlos. Se leían por ser administrador del sistema, no por responder de ellos.

**Resolución: se creó el `DirectorCuentas`**, autoridad del **ciclo de vida** y la
**incorporación**. La autoridad del departamento queda repartida, como en Suscripciones y Red
Operativa:

| Materia | Autoridad |
|---|---|
| Ciclo de vida (churn, antigüedad, cuentas en riesgo, usuarios vs tope) | **Director de Cuentas** |
| Incorporación (tiempo de onboarding, embudo de abandono, tasa de aprobación) | **Director de Cuentas** |
| Accesos técnicos (concurrencia de sesiones, roles incompatibles) | **Director Tecnológico** |

⚠️ Cada uno entra a su materia y **no** a la del otro: quien fija los criterios técnicos de acceso
no es quien responde de por qué se van los clientes.

⚠️ El orden importó: retirar al Administrador **antes** de crear el cargo habría dejado esos siete
informes inalcanzables.

---

## 5. Clasificación de los 32 endpoints

### Cuentas y Clientes — 8 endpoints

| # | Listado | Clase | Destinatario principal | También accede |
|---|---|:---:|---|---|
| 1 | Solicitudes de alta pendientes | **B** | Administrador *(las aprueba)* | — |
| 2 | Incorporación incompleta | **B** | Administrador *(reenvía invitación)* | — |
| 3 | Cuentas por estado | **S** | Administrador *(única visión de conjunto)* | — |
| 4 | Transferencias de propiedad | **S** | Administrador | — |
| 5 | Usuarios y sus roles | **A** | Administrador *(gestiona roles a diario)* | — |
| 6 | Sesiones abiertas | **B** | Administrador *(revoca sesiones)* | — |
| 7 | Credenciales temporales | **B** | Administrador *(da seguimiento)* | — |
| 8 | Accesos técnicos | **S** | **Director Tecnológico** | Administrador |

⚠️ El Director Tecnológico accede **solo al 8**. Ampliarlo contradiría el §5.1.

---

### Ventas y CRM — 4 endpoints

| # | Listado | Clase | Destinatario principal | También accede |
|---|---|:---:|---|---|
| 1 | Prospectos | **A** | Gerente de Ventas / Cuentas Públicas *(su cartera)* | **Director de Marketing** *(todas)* |
| 2 | Reasignaciones | **S** | **Director de Marketing** | Administrador |
| 3 | Demos activas | **B** | Gerente *(actúa antes de que expire)* | **Director de Marketing** |
| 4 | Notificaciones enviadas | **B** | Gerente *(reacciona a la alerta)* | **Director de Marketing** |

Las demos y las notificaciones son bandejas puras: su valor es actuar **antes** de que la
oportunidad se enfríe. El reparto de cartera, en cambio, es decisión de jefatura.

---

### Suscripciones y Facturación — 4 endpoints · **autoridad repartida**

| # | Listado | Clase | Destinatario principal | También accede |
|---|---|:---:|---|---|
| 1 | Suscripciones | **A** | Administrador *(consulta)* · Cliente *(la suya)* | **Director de Estrategia** |
| 2 | Facturas | **A** | Administrador *(gestiona mora)* · Cliente *(las suyas)* | **Director Financiero** |
| 3 | Solicitudes de cambio de plan | **B** | Administrador *(las resuelve)* | **Director de Estrategia** |
| 4 | Métodos de pago y caducidad | **B** | Administrador *(previene el cobro fallido)* | **Director Financiero** |

El reparto no es cosmético: composición de cartera y movimientos de plan alimentan decisiones de
catálogo; facturación y cobro, decisiones económicas.

---

### Red Operativa — 4 endpoints · **autoridad repartida**

| # | Listado | Clase | Destinatario principal | También accede |
|---|---|:---:|---|---|
| 1 | Composición de flota | **A** | Empresa Proveedora *(la suya)* · Administrador | **Director de Expansión** |
| 2 | Bajas de unidad | **S** | **Director de Expansión** | Administrador · Proveedor *(las suyas)* |
| 3 | Regiones operativas | **A** | Administrador *(desatasca las detenidas)* | **Director Tecnológico** · **Director de Expansión** |
| 4 | Intentos de validación | **S** | **Director Tecnológico** *(fija los criterios)* | Administrador |

El Tecnológico valida; el de Expansión decide dónde crecer. Ambos necesitan el estado de las
regiones; solo el primero necesita el detalle de por qué se rechazan.

---

### Partners y API — 5 endpoints

| # | Listado | Clase | Destinatario principal | También accede |
|---|---|:---:|---|---|
| 1 | Partners | **A** | Desarrollador de APIs · Partner *(el suyo)* | **Director Tecnológico** |
| 2 | Credenciales y caducidad | **B** | Desarrollador de APIs *(renueva)* · Partner *(las suyas)* | **Director Tecnológico** |
| 3 | Cambios de acceso | **S** | **Director Tecnológico** | Desarrollador de APIs · Partner *(los suyos)* |
| 4 | Versiones del contrato | **S** | **Director Tecnológico** *(decide retiros)* | Desarrollador de APIs |
| 5 | Alcance de datos | **S** | **Director Tecnológico** | Desarrollador de APIs |

---

### Emergencias — 5 endpoints

| # | Listado | Clase | Destinatario principal | También accede |
|---|---|:---:|---|---|
| 1 | Casos | **A** | Operador *(consulta histórico)* · Cliente *(zonas contratadas, cerrados)* | **Director de Operaciones** · Administrador |
| 2 | Despachos | **A** | Operador | **Director de Operaciones** · Administrador |
| 3 | Fotografías de evidencia | **A** | Operador *(recupera la no sincronizada)* | **Director de Operaciones** · Administrador |
| 4 | Notas de campo | **A** | Operador *(ídem)* | **Director de Operaciones** · Administrador |
| 5 | Cierres con resultado | **S** | **Director de Operaciones** | Operador · Administrador |

⚠️ **La exclusión de coordenadas e identidad de implicados rige también para el Director de
Operaciones.** Es constitucional, no de acotamiento.

La evidencia sin sincronizar es bandeja aunque parezca supervisión: **es evidencia que hay que ir a
recuperar**, y quien la recupera es el Operador.

---

### Soporte al Cliente — 2 endpoints

| # | Listado | Clase | Destinatario principal | También accede |
|---|---|:---:|---|---|
| 1 | Tickets | **A** | Agente *(prioriza su cola)* · reportadores *(los suyos)* | **Gerente de Éxito del Cliente** · Administrador |
| 2 | Escalados | **S** | **Gerente de Éxito del Cliente** | Agente · Administrador |

`SupervisorSoporte` ya existe y **no es lo mismo**: es el destinatario operativo de un escalado
automático, no la autoridad del departamento. Conviven.

---

### Analítica e Inteligencia — *módulo aplazado*

Autoridad: **Director de Datos**. Se aplicará cuando el módulo se especifique.

---

## 6. Resumen de la clasificación

| Clase | Endpoints | Qué significa |
|:---:|:--:|---|
| **B** — Bandeja operativa | **9** | Herramientas de trabajo que hoy no existen; su valor es actuar |
| **S** — Supervisión táctica | **11** | Planeación y control; su valor es decidir criterios |
| **A** — Ambas | **12** | Sirven a los dos con propósitos distintos |

**Casi dos tercios (21 de 32) tienen un destinatario operativo.** Es la constatación de que buena
parte de lo especificado no es «informes de gestión» sino trabajo diario que faltaba — y explica por
qué asignarlos solo a la jefatura los habría dejado sin usar.

---

## 7. Estado de aplicación — **hecho el 2026-08-14**

**La lógica de acotamiento no cambió.** Se mantiene tal cual para el responsable operativo. Lo que se
añadió es la autoridad departamental, exenta de ese acotamiento.

| Módulo | Cambio aplicado | Estado |
|---|---|:--:|
| Cuentas y Clientes | Sección `FR-020a–c`: Director Tecnológico **solo** en accesos técnicos; los otros siete sin autoridad | ✅ |
| Ventas y CRM | Sección `FR-011a–c`: Director de Marketing en los 4, sin acotamiento | ✅ |
| Suscripciones | Sección `FR-012a–e`: Estrategia en 1 y 3; Financiero en 2 y 4 | ✅ |
| Red Operativa | Sección `FR-013a–d`: Expansión en 1, 2 y 3; Tecnológico en 3 y 4 | ✅ |
| Partners y API | Sección `FR-014a–c`: Director Tecnológico en los 5 | ✅ |
| Emergencias | Sección `FR-014a–c`: Director de Operaciones en los 5 | ✅ |
| Soporte al Cliente | Sección `FR-014a–d`: Gerente de Éxito del Cliente en los 2 | ✅ |
| Modelo analítico | Sin cambios: no expone informes, los alimenta | — |

**Documentación de apoyo, también actualizada:**

- `.specify/docs/actors.md` — los seis roles pasan de «fuera de alcance» a autoridades
  departamentales implementadas; corregidas las dos discrepancias con el §5.1 (Ventas decía
  «Director Comercial», Cuentas decía «Gerente de Éxito del Cliente»). ✅
- `.specify/docs/architecture/architectural-patterns.md` — retirada la afirmación de que los actores
  tácticos siguen fuera de alcance. ✅
- `specs/002-tactico/contrato-informes-simples.md` — la regla de acotamiento gana su excepción
  explícita, con el límite de que no alcanza al dato sensible. ✅

### Catálogo de roles — **hecho**

Los seis roles de autoridad y las constantes viven en `backend/core/auth/roles_tacticos.py` y en
`ROLES_DEMO` (`backend/scripts/_demo_seed_common.py`):

| idrol | Rol JWT |
|------:|---|
| 6 | `DirectorTecnologico` *(ya existía; suma autoridad táctica)* |
| 14 | `DirectorEstrategia` *(ya existía; suma autoridad táctica)* |
| 17 | `DirectorMarketing` |
| 18 | `DirectorFinanciero` |
| 19 | `DirectorExpansion` |
| 20 | `DirectorOperaciones` |
| 21 | `GerenteExitoCliente` |
| 22 | `DirectorDatos` |
| 23 | `Gerente` *(tablero estratégico integral; no es autoridad de un departamento táctico)* |

Quien asigna esos roles a personas sigue siendo el Administrador (§8). `DirectorDatos` no tiene
módulo táctico: Analítica sigue aplazada.

---

## 8. Lo que este documento NO decide

- **Quién asigna los nuevos roles a personas.** Es competencia del Administrador, como cualquier
  otro rol.
- **Si Cuentas y Clientes debe tener autoridad de negocio propia.** Anotado como pendiente.
- **El acceso a los informes estratégicos.** El §5 del SRS no los cubre; la Alta Dirección tiene su
  propio catálogo.

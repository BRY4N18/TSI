# Especificación: Monitoreo y Facturación de API

> **Capa Speckit:** `backend/` — dominio, API, RF/RN/CA.  
> **Índice del módulo:** [`../api-monitoring-and-billing.md`](../api-monitoring-and-billing.md).  
> **UI (Interaction Capability):** [`../frontend/spec.md`](../frontend/spec.md) — no duplicar aquí detalles de pantallas.

## 1. Objetivo

Medir lo que cada partner consume, mostrárselo, y cobrarle el excedente. Cubre la API que el partner consume realmente, el registro de cada llamada en el instante en que ocurre, la comparación del consumo contra el cupo contratado con sus alertas, y la emisión de la factura de excedente al cierre del período.

El módulo **no** emite credenciales (dueño = `partner-api-onboarding`), **no** revoca ni suspende (dueño = `partner-access-management`), **no** emite el documento de factura (dueño = `subscriptions-and-billing`) y **no** gestiona disputas (dueño = `gestion-tickets-soporte`).

## 2. Contexto

Este es el módulo que convierte la integración en dinero. El SRS declara que la línea de ingresos por consumo de datos «está vendida en el plan y **no es exigible**» hasta que exista el componente que la controle y la cobre — este es ese componente.

**Casos de uso incluidos:**

- **CU-O51**: Consumir los datos mediante la integración. La API que el partner llama desde sus sistemas: valida la credencial en cada petición, entrega solo los conjuntos de datos habilitados por su nivel de acceso y filtra por las zonas geográficas contratadas.
- **CU-O52**: Registrar el consumo realizado por cada partner. Cada llamada se contabiliza en el mismo instante en que ocurre, con su detalle técnico completo; alimenta las métricas del partner, la consola del Desarrollador de APIs y el reporte mensual.
- **CU-O53**: Aplicar los límites de consumo definidos por el plan. Compara el consumo acumulado contra el cupo del plan vigente y notifica al aproximarse y al alcanzarlo. **No bloquea** (RN-APM-002).
- **CU-O54**: Tarificar el consumo de integraciones del período. Al cierre de mes separa consumo incluido de excedente, verifica que no exista ya una factura para ese partner y período, y emite. Ante fallo, reintenta de forma escalonada.

El módulo escribe `Fact_APIIntegracion` y `Fact_LogLlamadaAPI`, lee `Dim_Partner`, `Dim_CredencialAPI`, `Dim_EstadoIntegracion`, `Dim_Servicio`, `Dim_Preferencias_Cliente` y `Dim_Plan`, y escribe `Fact_Factura` (tabla de `subscriptions-and-billing`).

## Clarifications

### Session 2026-08-08 — Jerarquía de fuentes y renumeración canónica

- Q: ¿Qué numeración de CU se usa? → A: La **canónica del catálogo** (`TSI-Catalogo-CU-RF-RNF.md` §5.5): **CU-O51–CU-O54**. La de `PortalPartnersAPI.md` está obsoleta y colisiona con CUs vigentes de otros departamentos.

  **Mapa legacy → canónico de este módulo:**

  | Legacy (Portal) | Canónico | Caso de uso |
  |---|---|---|
  | — (declarado «fuera del alcance» en Portal) | **CU-O51** | Consumir los datos mediante la integración |
  | CU-O74 (escritura de logs) + CU-O73 (consultar métricas) + CU-O75 (reporte mensual) | **CU-O52** | Registrar el consumo realizado por cada partner |
  | CU-O74 (alertas de cuota) | **CU-O53** | Aplicar los límites de consumo del plan |
  | CU-O78 (facturación de excedentes) + CU-O83 (excepción de facturación) | **CU-O54** | Tarificar el consumo del período |
  | CU-O82 (registrar disputa) | **fuera de este módulo** | Vive en Soporte como CU-O83 / RF-O83.2, ya implementado |

- Q: **RF-O53.2 del catálogo dice «Restringir o degradar el servicio al superarse el límite, según la política configurada», pero el SRS declara lo contrario.** ¿Cuál manda? → A: **El SRS.** RN-11 y §3.4.2 son explícitos: *«superar la cuota no bloquea el servicio. No hay corte automático»*, y el SRS añade que lo documenta *«precisamente para que nadie la corrija asumiendo que debería bloquear»*. Se implementa pay-as-you-go puro: alerta + factura de excedente. **RF-O53.2 queda como divergencia documentada y el catálogo debería corregirse.** Ver RN-APM-002.
- Q: `PortalPartnersAPI.md` asume 3 reintentos con 1 hora de espera entre cada uno. → A: **Obsoleto.** El SRS fija **tres reintentos con espera creciente: 1 h, 6 h y 24 h**. Ver RN-APM-013.
- Q: ¿La disputa de facturas es CU de este módulo? → A: **No.** Es `CU-O83 / RF-O83.2` de `gestion-tickets-soporte`, ya implementado con `Fact_Reclamo.idfactura` (STRING). Este módulo solo debe **excluir del cobro automático** las facturas en disputa. Ver RN-APM-016.

### Session 2026-08-08 — Estado del esquema heredado

- Q: ¿Qué cambios de esquema ya están aplicados y verificados? → A: `Fact_Factura.tipo` (`suscripcion` | `excedente_api`, default `suscripcion`) habilita la verificación de no duplicación de RF-O54.3; `Fact_Reclamo.idfactura` migrado INT → STRING para que la disputa enlace con el UUID de factura. Ambos verificados (`database/verifica_factura_reclamo.py`, 15/15). Ver `decisiones-pendientes.md` #17.
- Q: ¿Cómo se representan los valores ausentes? → A: **Pinot no almacena `NULL`** en este proyecto. Toda regla se expresa contra centinelas explícitos, nunca con `IS NULL`. Ver `partner-api-onboarding/backend/spec.md` § 15 D2 y RN-APM-018.
- Q: `Dim_EstadoIntegracion` está **vacía** (0 filas). → A: Es el catálogo que da sentido a `Fact_APIIntegracion.idestadointegracion` (copia histórica del estado del partner al momento de la llamada). Debe sembrarse en este módulo con los estados del ciclo de vida del partner. Ver RF-APM-005.

### Session 2026-08-08 — Concurrencia

- Q: En `partner-api-onboarding` se aceptó validar la unicidad con «consultar y luego escribir», asumiendo el retraso de ingesta de Pinot (5–15 s). ¿Vale aquí? → A: **No.** Aquel caso era una acción manual de un Administrador, de volumen bajísimo. **CU-O52 escribe una fila por cada llamada a la API**: con un plan de 100 000 llamadas/mes se llega a decenas de escrituras por segundo. Ninguna regla de este módulo puede depender de leer en Pinot lo que se acaba de escribir. Ver RN-APM-004 y RN-APM-008.

## 3. Actores

| Actor | Rol en este módulo | Interacción principal |
|---|---|---|
| **Partner de integración** | Consumidor de datos | Llama a la API desde sus propios sistemas con su credencial, y consulta sus métricas de consumo, errores y latencia. |
| **Desarrollador de APIs** | Vigilante técnico | Dispone de la consola de registros en tiempo real con el detalle de cada llamada, y recibe las alertas cuando un partner se acerca o supera su cuota. |
| **Cliente** | Consultor del gasto | Consulta el reporte mensual de consumo de su organización. |
| **Administrador** | Receptor de excepciones | Recibe la alerta cuando la facturación de excedente agota sus reintentos y queda pendiente de emisión manual. |
| **Sistema** | Medidor y tarificador | Registra cada llamada en el instante, evalúa el consumo contra el cupo, dispara alertas y ejecuta el corte mensual con sus reintentos. |

## 4. Requisitos funcionales

### RF-APM-001: Consumo de datos autenticado por credencial (CU-O51 / RF-O51.2)

El sistema debe exponer los endpoints de datos que el partner consume desde sus sistemas, autenticados **por credencial de API** (no por sesión JWT humana).

En cada petición, **antes de entregar dato alguno**, debe:

1. Resolver la credencial presentada contra `Dim_CredencialAPI` verificando su hash.
2. Rechazar con HTTP 401 si la credencial no existe, si `activo=false` (revocada o suspendida en cascada) o si está vencida (`fecha_expiracion < ahora`).
3. Rechazar con HTTP 403 si el partner dueño tiene `Dim_Partner.activo=false` (suspendido por `partner-access-management`).
4. Rechazar con HTTP 403 si el cliente **no tiene suscripción vigente** (`Fact_Suscripcion.estado` suspendida o cancelada). **Añadido 2026-08-08** por la decisión D2 de `partner-access-management`: las dos suspensiones son independientes por origen y **el acceso exige ambas condiciones**. Sin esta comprobación, un cliente con la suscripción suspendida seguiría consumiendo la API — hueco que existía y que esta decisión cierra.
5. Determinar el `entorno` de la credencial (`Sandbox` | `Producción`), que califica **todo** lo que ocurra después.

**La comprobación de vigencia se deriva de los datos, no de un job** (mismo criterio que RF-PON-006): una credencial vencida deja de servir aunque ningún proceso la haya marcado todavía.

### RF-APM-002: Alcance de datos según el nivel de acceso (CU-O51 / RF-O51.1)

El sistema debe entregar **únicamente los conjuntos de datos habilitados por el nivel de acceso del partner**, determinado por el plan contratado por su cliente:

- **Severidades:** solo casos cuya severidad esté en `Dim_Plan.severidades_desbloqueadas` del plan vigente (mismo campo que gobierna qué casos recibe la flota, RN-SUSF-002).
- **Servicio:** solo los `Dim_Servicio` a los que la credencial da acceso.

Un conjunto de datos no habilitado no se devuelve vacío ni parcial: se rechaza con HTTP 403 indicando qué nivel de acceso haría falta.

### RF-APM-003: Filtrado por zonas geográficas contratadas (CU-O51 / RF-O51.3)

El resultado debe filtrarse por las zonas geográficas que el cliente tiene contratadas, leídas de `Dim_Preferencias_Cliente.zonas_geograficas` (JSON de `idcondado`) — **el mismo mecanismo que ya usa `seguimiento-cierre-de-casos` para RF-O82.2**, no uno nuevo.

Un cliente sin zonas configuradas no recibe todos los datos por defecto: recibe **conjunto vacío**. El filtro falla hacia el lado cerrado, porque exponer siniestralidad de zonas no contratadas es una fuga de datos, no una comodidad.

### RF-APM-004: Registro de cada llamada en el instante (CU-O52 / RF-O52.1, RF-O52.3)

**Cada llamada real a la API se registra en el mismo instante en que ocurre.** No existe un proceso posterior que agregue o consolide: el dato nace completo.

Por cada petición atendida, el sistema debe escribir **dos filas, juntas**:

1. **`Fact_LogLlamadaAPI`** — detalle técnico: `endpoint`, `metodohttp`, `codigohttp`, `iporigen`, `latenciams`, `fechallamada`, `idpartner`, `idcredencialapi`.
2. **`Fact_APIIntegracion`** — la misma llamada con columnas orientadas a reporte y facturación: `llamadas=1`, `errores=0|1` según el `codigohttp`, `latencia`, `entorno`, `idpartner`, `idcliente`, `idservicio`, `idestadointegracion`, `fechahora`.

Los reportes (RF-APM-009) y el cálculo de excedente (RF-APM-011) se resuelven **en el momento de la consulta**, agregando sobre `Fact_APIIntegracion`. **No existe tabla de agregados precalculados** (RN-APM-003).

El registro **no debe poder hacer fallar la petición del partner**: si la publicación del evento falla, se responde igualmente al partner y el fallo se registra para reconciliación. Perder una medición es malo; caerse la API por no poder medir es peor.

### RF-APM-005: Copia histórica del estado de la integración (CU-O52)

Cada registro de consumo guarda **una copia del estado del partner en ese momento exacto** en `Fact_APIIntegracion.idestadointegracion` (FK a `Dim_EstadoIntegracion`). Esto permite reportar consumo histórico con precisión aunque el partner haya cambiado de estado o de plan después.

**`Dim_EstadoIntegracion` está vacía y debe sembrarse** en este módulo con los estados del ciclo de vida del partner (`Pruebas activo`, `Producción activa`, `Suspendido`), alineados con los estados derivados de `partner-api-onboarding`.

`idestadointegracion` **no es la fuente de verdad del estado actual** — esa es `Dim_Partner.activo` más el `entorno` vigente de la credencial (RN-APM-006).

### RF-APM-006: Separación estricta de entornos (CU-O52)

El consumo del entorno de pruebas y el de producción **nunca se mezclan, ni siquiera para el mismo partner**.

**Todo reporte y todo cálculo de facturación se refiere exclusivamente a `entorno='Producción'`.** Toda consulta de agregación de este módulo lleva ese filtro de forma obligatoria; una consulta sin él es un defecto, no una variante.

### RF-APM-007: Métricas de consumo del partner (CU-O52)

El **Partner de integración** debe poder consultar en cualquier momento sus métricas del período vigente: llamadas realizadas, errores y latencia promedio, agregadas sobre `Fact_APIIntegracion` filtrado por su `idpartner` y `entorno='Producción'`.

Un partner solo puede consultar **sus propias** métricas (control de propiedad obligatorio, HTTP 403 en otro caso). Un partner suspendido **sí** puede seguir consultando su historial: es una lectura que no afecta al estado y le sirve precisamente para entender por qué se le suspendió.

### RF-APM-008: Consola de registros en tiempo real y autodiagnóstico (CU-O52)

El **Desarrollador de APIs** debe disponer de una consola con el detalle de cada llamada, leyendo `Fact_LogLlamadaAPI` ordenado por `fechallamada` descendente, filtrable por partner, credencial, endpoint, código HTTP y rango temporal.

**Los errores de la propia integración quedan registrados con su código**, de modo que el partner **puede diagnosticar sus propios fallos** sin escalar a un Administrador: toda llamada con `codigohttp` 4xx/5xx se registra igual, con `errores=1`.

> «Tiempo real» está limitado por el retraso de ingesta de Pinot (5–15 s). La consola muestra el dato tan pronto como es consultable; no promete latencia cero (RNF-APM-003).

### RF-APM-009: Reporte mensual de consumo (CU-O52 / RF-O52.2)

El **Cliente** y el **Administrador** deben poder obtener el reporte de consumo de un mes: total de llamadas, errores y latencia promedio, agregado por `idpartner`, `entorno='Producción'` y período.

Un mes sin llamadas registradas devuelve **cero en todas las métricas**; no es un error, es el caso límite normal de una agregación sobre conjunto vacío.

### RF-APM-010: Comparación contra el cupo y alertas (CU-O53 / RF-O53.1, RF-O53.3)

El sistema debe comparar el consumo acumulado del período contra el cupo del plan vigente, congelado en `Dim_Partner.limitellamadasmes` y `limitellamadasminuto` (RF-PON-003).

Debe **notificar al partner al aproximarse y al alcanzar su límite**, y alertar al Desarrollador de APIs en los mismos momentos. Los avisos no se duplican dentro del mismo período.

**Esta comparación no restringe el servicio en ningún caso** (RN-APM-002).

**Distinción obligatoria entre cupo comercial y tasa instantánea** (§ 15 D2). Son dos mecanismos separados y no deben confundirse:

| | Cupo mensual (`limitellamadasmes`) | Tasa por minuto (`limitellamadasminuto`) |
|---|---|---|
| **Qué es** | Compromiso comercial del plan | Protección técnica de la plataforma |
| **Al superarse** | **Nunca bloquea.** Alerta y genera excedente facturable | Devuelve **HTTP 429** con `Retry-After` |
| **Se factura** | Sí, como excedente al cierre (CU-O54) | **No.** Una petición rechazada con 429 no se atendió, así que no es consumo |
| **Origen** | RN-11 del SRS | `api-standards.md` (throttling DRF) |

Un `429` **no es «aplicación de la cuota»**: RN-APM-002 sigue intacta, porque el cupo mensual sigue sin bloquear y sigue generando excedente. Lo que se limita es el *ritmo* instantáneo, como en cualquier API pública.

Las peticiones rechazadas con 429 **se registran en `Fact_LogLlamadaAPI`** con su código —para que el partner vea que le están limitando y ajuste su cliente— pero **no cuentan como llamada facturable** en `Fact_APIIntegracion`.

### RF-APM-011: Cálculo del excedente al cierre del período (CU-O54 / RF-O54.1, RF-O54.2)

Al cierre de cada mes, el sistema debe, por cada partner con credencial de producción:

1. Agregar `SUM(llamadas)` de `Fact_APIIntegracion` filtrado por `idpartner`, `entorno='Producción'` y el período cerrado.
2. Compararlo contra `Dim_Partner.limitellamadasmes`.
3. **Separar consumo incluido de consumo excedente**: el consumo dentro del cupo ya está pagado por la suscripción; solo se tarifica lo que lo supera.
4. Si hay excedente, calcular el importe como `llamadas_excedentes × Dim_Plan.precio_excedente_llamada` del plan vigente, y emitir en `Fact_Factura` con `tipo='excedente_api'`, `estado_pago='Pendiente'`, el `periodo` y el `id_cliente` del partner.

**La tarifa vive en `Dim_Plan.precio_excedente_llamada`** (DOUBLE, columna añadida 2026-08-08 — § 15 D1). La configura el Director de Estrategia al crear o editar el plan (CU-O26 / RF-O26.1), no es una constante del código.

**Si la tarifa vale el centinela `-1.0` («sin tarifa configurada»), el corte NO emite factura de importe cero: registra el partner como no tarificable y alerta**, igual que el camino de reintentos agotados (RF-APM-013). Facturar cero sería ingreso real no cobrado en silencio, que es justo lo que RN-APM-014 prohíbe.

### RF-APM-012: No duplicación de la factura de excedente (CU-O54 / RF-O54.3)

**Antes de emitir, el proceso debe verificar que no exista ya una factura de excedente para ese mismo partner y ese mismo período**, consultando `Fact_Factura` por `id_cliente` + `periodo` + `tipo='excedente_api'`.

Sin esta verificación, un reintento ejecutado sobre un proceso que sí alcanzó a emitir generaría un **doble cobro** — un error peor que no cobrar, porque afecta directamente la confianza del cliente.

Es la razón por la que existe la columna `Fact_Factura.tipo` (ya añadida, `decisiones-pendientes.md` #17): sin discriminador, esa consulta es imposible.

### RF-APM-013: Reintentos escalonados y emisión manual (CU-O54 / RF-O54.4)

**Si el cálculo o la emisión falla** —por ejemplo, si el servicio estuvo caído en el momento del corte— el proceso **no reintenta en silencio ni se abandona**. Ejecuta **tres reintentos con espera creciente: 1 hora, 6 horas y 24 horas**.

Cada intento actualiza `Fact_Factura.reintentos` y `resultado_ultimo_reintento`.

**Si se agotan los tres**, la factura queda en estado **pendiente de emisión manual** y se alerta al **Administrador y al Desarrollador de APIs**.

La regla de fondo es explícita: **una factura de excedente nunca debe quedar silenciosamente sin crearse**, porque eso ocultaría ingreso real no cobrado.

### RF-APM-014: Exclusión de facturas en disputa del cobro automático (CU-O54)

Una factura marcada como **en disputa** por `gestion-tickets-soporte` (CU-O83 / RF-O83.2) queda **excluida explícitamente de los intentos de cobro automático** mientras se resuelve. Al cerrarse el reclamo vuelve a su estado normal, pagada o con monto ajustado según la resolución.

Este módulo **no abre ni resuelve disputas**: solo respeta la exclusión.

## 5. Requisitos no funcionales

### RNF-APM-001: Exactitud del cálculo (RNF-02)

Los cálculos de consumo e importes son **exactos y deterministas ante las mismas entradas**. Dos ejecuciones del corte sobre el mismo período y los mismos datos producen el mismo importe. Es la base de la confianza en la facturación.

### RNF-APM-002: Latencia de la API de datos (RNF-04)

Los endpoints de consumo responden en **menos de 2 segundos en el percentil 95**. El registro de la llamada no debe añadir latencia perceptible: se publica de forma que no bloquee la respuesta al partner.

### RNF-APM-003: Capacidad de escritura (RNF-05)

El registro de consumo debe absorber el volumen del plan más alto sin degradar la respuesta: **decenas de escrituras por segundo sostenidas**. Es el flujo de mayor frecuencia de todo el departamento.

### RNF-APM-004: Confidencialidad de los datos entregados (RNF-13, Principio V)

Los datos de siniestralidad que se entregan al partner incluyen **geolocalización y potencialmente datos de personas involucradas**. Viajan cifrados, filtrados por zonas contratadas (RF-APM-003) y limitados por nivel de acceso (RF-APM-002). Todo acceso queda auditado con la credencial que lo originó.

### RNF-APM-005: Integridad del histórico (RNF-14)

`Fact_APIIntegracion` y `Fact_LogLlamadaAPI` son **append-only**: ninguna fila se modifica ni se elimina físicamente. El detalle del consumo es el respaldo de la tarificación (RF-O52.3) y debe poder auditarse.

### RNF-APM-006: Trazabilidad de la facturación (RNF-16)

Cada intento de emisión, su resultado y la alerta final quedan registrados con autor (`Sistema`), acción y fecha.

### RNF-APM-007: Configurabilidad (RNF-20)

Los umbrales de alerta, la tarifa de excedente y los tiempos de reintento son **parámetros de negocio configurables sin modificar código**.

### RNF-APM-008: Testabilidad (RNF-18)

Cobertura ≥ 80 %. Este módulo **no pertenece a la cadena crítica de despacho**, por lo que no le aplica el umbral reforzado del 95 %.

## 5.1 Declaración ISO/IEC 25010:2023 (Golden Rule de la constitución)

| Característica | Aplica | Justificación |
|---|---|---|
| **Functional Suitability** | ✅ | Trazable a CU-O51/O52/O53/O54. Es el componente sin el cual la línea de ingresos por consumo no es exigible. |
| **Reliability** | ✅ | **Muy relevante.** RF-APM-013 (reintentos escalonados) y RF-APM-004 (el fallo de medición no tumba la API) definen el comportamiento ante fallo antes de `/plan`, como exige el Principio II. |
| **Performance Efficiency** | ✅ | RNF-APM-002 y RNF-APM-003 declaran latencia y capacidad. Es el flujo de mayor frecuencia del departamento. |
| **Interaction Capability** | ⚠️ Parcial | Alcance BE limitado a RF-APM-007/008/009. El detalle de la consola vive en `../frontend/spec.md`. |
| **Security** | ✅ | **Dominante junto con Reliability.** Es la única superficie del sistema que entrega datos de siniestralidad a terceros: RF-APM-001 (autenticación por credencial), RF-APM-002 (nivel de acceso), RF-APM-003 (zonas), RNF-APM-004. |
| **Compatibility** | ✅ | La API de datos es el contrato versionado que consumen las aseguradoras (Principio VI); su documentación es CU-O50 del módulo #07. |
| **Maintainability** | ✅ | Propiedad de escritura repartida y documentada frente a #07 y #09 (§ 13). |
| **Flexibility** | ✅ | Cupo, tarifa y umbrales configurables (RNF-APM-007). |
| **Safety** | ❌ **No aplica** | Fuera de la cadena crítica registro → asignación → despacho → confirmación. Un fallo aquí impide cobrar o medir, pero **no retrasa la atención de ninguna víctima** ni influye en la clasificación de severidad o la asignación de unidades. La API es de solo lectura sobre datos ya cerrados. |

**Tie-breaker:** conflicto entre **Reliability** y **Functional Suitability** en RF-APM-004 — si la escritura del consumo falla, ¿se rechaza la petición del partner (medición exacta, servicio caído) o se responde igual (servicio disponible, medición con hueco)? Se prioriza **responder al partner** y registrar el fallo para reconciliación. No es Safety, así que aplica la regla 2 (Maintainability y Functional Suitability por defecto); aquí Functional Suitability se interpreta como «el partner recibe el dato que contrató». **Trade-off aceptado:** una medición perdida es ingreso potencialmente no cobrado, mitigado con registro de fallos y reconciliación; una API caída rompe la integración de una aseguradora en producción.

## 6. Reglas de negocio

### RN-APM-001

Todo consumo se califica por **entorno**. El de pruebas y el de producción **nunca se mezclan, ni siquiera para el mismo partner**. Todo reporte y todo cálculo de facturación se refiere exclusivamente a `Producción` (SRS L402).

### RN-APM-002

**Superar la cuota NO bloquea el servicio.** No hay corte automático. El exceso se resuelve después mediante facturación. Es una decisión de modelo comercial de pago por uso, documentada explícitamente en el SRS *«para que nadie la corrija asumiendo que debería bloquear»* (SRS L406, RN-11).

> **Divergencia documentada:** RF-O53.2 del catálogo dice «Restringir o degradar el servicio al superarse el límite, según la política configurada». **Manda el SRS.** El catálogo debería corregirse.

### RN-APM-003

**Cada llamada se registra en el instante en que ocurre, con el dato ya completo.** No existe job de agregación posterior ni tabla de agregados precalculados: reportes y facturación agregan sobre `Fact_APIIntegracion` en el momento de la consulta (SRS L396).

### RN-APM-004

Ninguna regla de este módulo puede depender de **leer en Pinot lo que se acaba de escribir**. La ingesta tarda 5–15 s y este módulo escribe decenas de filas por segundo. El patrón «consultar y luego escribir» aceptado en `partner-api-onboarding` **no es válido aquí**.

### RN-APM-005

El registro del consumo **no puede hacer fallar la petición del partner**. Si la publicación falla, se responde igualmente y el fallo se registra para reconciliación posterior.

### RN-APM-006

`Fact_APIIntegracion.idestadointegracion` es una **copia histórica** del estado del partner en el momento de la llamada, no la fuente de verdad del estado actual (esa es `Dim_Partner.activo` + el `entorno` vigente de la credencial).

### RN-APM-007

Una credencial **inválida, revocada o vencida** no obtiene datos; un partner **suspendido** tampoco; y un cliente **sin suscripción vigente** tampoco. La vigencia se deriva de los datos (`activo`, `fecha_expiracion < ahora`), no de que un job la haya marcado.

**Son tres condiciones independientes con tres dueños distintos** (D2 de `partner-access-management`): la credencial la invalida #09, el partner lo suspende #09 por mora de excedente, y la suscripción la suspende `subscriptions-and-billing` por su propia mora. El acceso exige **las tres**.

### RN-APM-008

El filtrado por zonas contratadas **falla hacia el lado cerrado**: un cliente sin zonas configuradas recibe conjunto vacío, nunca el conjunto completo.

### RN-APM-009

**Los errores de la propia integración se registran con su código** para que el partner pueda diagnosticar sus fallos sin escalar a un Administrador (SRS L410).

### RN-APM-010

Las alertas de cuota (al aproximarse y al alcanzar) **no se duplican dentro del mismo período**.

### RN-APM-011

El consumo **dentro del cupo ya está pagado por la suscripción**. Solo se tarifica lo que lo supera (SRS L408).

### RN-APM-012

**Regla de no duplicación, obligatoria.** Antes de emitir, verificar que no exista ya una factura de excedente para ese partner y período. Sin ella, un reintento sobre un proceso que sí emitió genera un **doble cobro** (SRS L416).

### RN-APM-013

Ante fallo del cálculo o la emisión: **tres reintentos con espera creciente de 1 h, 6 h y 24 h**. Agotados los tres, la factura queda **pendiente de emisión manual** con alerta al Administrador y al Desarrollador de APIs (SRS L414).

### RN-APM-014

**Una factura de excedente nunca debe quedar silenciosamente sin crearse**, porque eso ocultaría ingreso real no cobrado (SRS L418).

### RN-APM-015

`Fact_APIIntegracion` y `Fact_LogLlamadaAPI` son **append-only**. Ninguna fila se modifica ni se borra.

### RN-APM-016

Una factura **en disputa** queda excluida de los intentos de cobro automático mientras se resuelve. La disputa la gestiona `gestion-tickets-soporte`; este módulo solo respeta la exclusión.

### RN-APM-017

Un partner solo accede a **sus propias** métricas y logs. Un partner suspendido conserva el acceso de **lectura** a su historial.

### RN-APM-018

**Ninguna consulta usa `IS NULL`.** Pinot no almacena nulos: las guardas comparan contra centinelas explícitos.

## 7. Entradas

### Para consumir datos (CU-O51 / RF-APM-001)
- Credencial de API en la cabecera de autorización (`client_id` + `client_secret`).
- Parámetros de consulta del conjunto de datos solicitado (filtros de fecha, severidad, ubicación), siempre acotados por RF-APM-002 y RF-APM-003.

### Para consultar métricas propias (CU-O52 / RF-APM-007)
- `idpartner` (INT, path param — debe coincidir con el del token).
- `periodo` (STRING, opcional, `YYYY-MM`; por defecto el vigente).

### Para la consola de logs (CU-O52 / RF-APM-008)
- Filtros opcionales: `idpartner`, `idcredencialapi`, `endpoint`, `codigohttp`, `desde`, `hasta`.
- Paginación por cursor.

### Para el reporte mensual (CU-O52 / RF-APM-009)
- `periodo` (STRING, requerido, `YYYY-MM`).
- `idpartner` (INT, opcional; el Cliente solo puede consultar el suyo).

### Para el corte de facturación (CU-O54 / RF-APM-011)
- `periodo` (STRING, requerido, `YYYY-MM`) — proceso del sistema, no expuesto al partner.

## 8. Salidas

### Respuestas exitosas
- **200 OK — Datos consumidos:** `{ "data": [...], "meta": { "pagination": {...} } }` — filtrado por nivel de acceso y zonas contratadas.
- **200 OK — Métricas del partner:** `{ "data": { "periodo": "2026-08", "entorno": "Producción", "llamadas": 8421, "errores": 37, "latencia_promedio_ms": 142.5, "limite_mes": 10000, "porcentaje_consumido": 84.2 } }`
- **200 OK — Consola de logs:** `{ "data": [ { "endpoint": "...", "metodohttp": "GET", "codigohttp": 200, "latenciams": 118.0, "fechallamada": ... } ], "meta": { "pagination": {...} } }`
- **200 OK — Reporte mensual:** `{ "data": { "periodo": "2026-07", "llamadas": 0, "errores": 0, "latencia_promedio_ms": 0 } }` — ceros si no hubo consumo.
- **200 OK — Resultado del corte:** `{ "data": { "periodo": "2026-07", "partners_evaluados": 12, "facturas_emitidas": 3, "sin_excedente": 9, "pendientes_emision_manual": 0 } }`

### Respuestas de error
- **401 Unauthorized** — Credencial ausente, inválida, revocada o vencida (RF-APM-001).
- **403 Forbidden** — Partner suspendido; conjunto de datos fuera de su nivel de acceso (RF-APM-002); o intento de consultar métricas de otro partner (RN-APM-017).
- **400 Bad Request** — `periodo` con formato inválido.
- **404 Not Found** — `idpartner` inexistente.
- **422 Unprocessable Entity** — Corte solicitado sobre un período aún no cerrado.

Formato conforme a `api-standards.md`.

## 9. Estados

### Estado de la factura de excedente

| Estado | Origen | Significado |
|---|---|---|
| *(no emitida)* | RF-APM-011 | El consumo no superó el cupo. Resultado normal, no un fallo. |
| **Pendiente** | RF-APM-011 | Factura de excedente emitida, en circuito normal de cobro. |
| **En disputa** | `gestion-tickets-soporte` (CU-O83) | Excluida del cobro automático (RN-APM-016). Estado ajeno a este módulo. |
| **Pendiente de emisión manual** | RF-APM-013 | Agotados los tres reintentos. Alerta enviada. **Nunca se abandona en silencio.** |
| **Pagada** / con monto ajustado | `subscriptions-and-billing` | Cierre del circuito de cobro. |

### Ciclo del corte mensual

```
Cierre de período
   └─► por cada partner con credencial de producción:
          SUM(llamadas) vs limitellamadasmes
             ├── ≤ cupo ──► sin factura (consumo ya pagado por la suscripción)
             └── > cupo ──► ¿existe ya factura excedente de ese partner+período?
                               ├── sí ──► NO emitir (RN-APM-012, evita doble cobro)
                               └── no ──► emitir Fact_Factura tipo='excedente_api'
                                             └── si falla ──► reintento 1h → 6h → 24h
                                                                  └── agotados ──► pendiente
                                                                      de emisión manual
                                                                      + alerta
```

## 10. Escenarios

### Escenario A: Consumo exitoso dentro del cupo

Dado un partner con credencial de producción activa y zonas contratadas configuradas  
Cuando llama al endpoint de datos con su credencial  
Entonces el sistema debe validar la credencial y el estado del partner  
Y debe entregar solo los datos de sus severidades habilitadas y sus zonas contratadas  
Y debe escribir una fila en `Fact_LogLlamadaAPI` y otra en `Fact_APIIntegracion` con `llamadas=1`, `errores=0` y `entorno='Producción'`  
Y debe responder en menos de 2 s (p95).

### Escenario B: Credencial revocada

Dado un partner cuya credencial fue revocada (`activo=false`)  
Cuando intenta consumir datos  
Entonces el sistema debe rechazar con HTTP 401 **sin entregar dato alguno**  
Y no debe contabilizar la petición como consumo facturable.

### Escenario C: Partner suspendido por mora

Dado un partner con `Dim_Partner.activo=false`  
Cuando intenta consumir datos con una credencial que aún figura activa  
Entonces el sistema debe rechazar con HTTP 403  
Y ninguna llamada nueva debe generar consumo exitoso a partir de ese momento.

### Escenario D: Cliente sin zonas configuradas

Dado un partner cuyo cliente no tiene `zonas_geograficas` configuradas  
Cuando consume datos  
Entonces el sistema debe devolver **conjunto vacío**, no el conjunto completo  
Y la llamada debe registrarse igualmente como consumo.

### Escenario E: Superar la cuota no interrumpe el servicio

Dado un partner que ya superó su `limitellamadasmes`  
Cuando realiza más llamadas  
Entonces el sistema debe **atenderlas con normalidad** (RN-APM-002)  
Y debe registrarlas como consumo  
Y debe haber alertado al partner y al Desarrollador de APIs al aproximarse y al alcanzar el límite, sin duplicar avisos  
Y el exceso debe quedar disponible para tarificarse al cierre del período.

### Escenario F: Error de la integración, autodiagnóstico

Dado un partner que envía una petición mal formada  
Cuando el sistema responde con 4xx  
Entonces debe registrar la llamada con su `codigohttp` en `Fact_LogLlamadaAPI` y `errores=1` en `Fact_APIIntegracion`  
Y el partner debe poder ver ese error en sus métricas y diagnosticarlo sin escalar a un Administrador.

### Escenario G: Separación de entornos en el reporte

Dado un partner con consumo en pruebas y en producción en el mismo período  
Cuando se genera su reporte mensual o se calcula su excedente  
Entonces **solo debe considerarse el consumo de producción**  
Y el de pruebas no debe aparecer ni sumarse en ningún total.

### Escenario H: Corte mensual con excedente

Dado un partner con cupo de 10 000 llamadas que consumió 12 500 en producción  
Cuando se ejecuta el corte del período  
Entonces el sistema debe separar 10 000 incluidas de 2 500 excedentes  
Y debe verificar que no exista ya una factura de excedente para ese partner y período  
Y debe emitir `Fact_Factura` con `tipo='excedente_api'` y `estado_pago='Pendiente'`.

### Escenario I: Reintento que no duplica el cobro

Dado un corte que ya emitió la factura de excedente pero cuyo proceso falló después  
Cuando se ejecuta el reintento  
Entonces el sistema debe encontrar la factura existente por `id_cliente` + `periodo` + `tipo='excedente_api'`  
Y **no debe emitir una segunda** (RN-APM-012)  
Y debe cerrar el reintento como exitoso.

### Escenario J: Reintentos agotados

Dado un corte cuya emisión falla de forma persistente  
Cuando se agotan los tres reintentos de 1 h, 6 h y 24 h  
Entonces la factura debe quedar en estado **pendiente de emisión manual**  
Y debe alertarse al Administrador y al Desarrollador de APIs  
Y en ningún caso debe quedar silenciosamente sin crearse (RN-APM-014).

### Escenario K: Factura en disputa excluida del cobro

Dado que el partner abrió una disputa sobre su factura de excedente vía Soporte  
Cuando corre el proceso de cobro automático  
Entonces esa factura debe quedar **excluida** mientras la disputa siga abierta  
Y al cerrarse el reclamo debe volver a su estado normal según la resolución.

### Escenario L: El fallo de medición no tumba la API

Dado que la publicación del evento de consumo falla momentáneamente  
Cuando un partner realiza una llamada  
Entonces el sistema debe **responder igualmente al partner con sus datos**  
Y debe registrar el fallo de medición para reconciliación posterior (RN-APM-005).

## 11. Criterios de aceptación

### CA-APM-001 (CU-O51 / RF-O51.2)
Una credencial inexistente, revocada o vencida recibe HTTP 401 sin obtener datos. Un partner suspendido recibe HTTP 403. La vigencia se evalúa por comparación de datos, no por marca de un job.

### CA-APM-002 (CU-O51 / RF-O51.1)
El partner recibe únicamente conjuntos de datos habilitados por las severidades de su plan. Un conjunto no habilitado retorna 403, no una lista vacía.

### CA-APM-003 (CU-O51 / RF-O51.3)
El resultado se filtra por `Dim_Preferencias_Cliente.zonas_geograficas`. Un cliente sin zonas configuradas recibe conjunto vacío.

### CA-APM-004 (CU-O52 / RF-O52.1)
Cada llamada atendida escribe exactamente una fila en `Fact_LogLlamadaAPI` y una en `Fact_APIIntegracion`, en el mismo instante, con `errores` derivado del `codigohttp`.

### CA-APM-005 (CU-O52)
`Fact_APIIntegracion.idestadointegracion` refleja el estado del partner en el momento de la llamada, y no cambia si el partner cambia de estado después. `Dim_EstadoIntegracion` está sembrada.

### CA-APM-006 (CU-O52)
Ninguna agregación de reporte o facturación incluye consumo de `Sandbox`. Un partner con consumo en ambos entornos ve solo producción en su reporte y en su excedente.

### CA-APM-007 (CU-O52)
El partner consulta sus métricas del período (llamadas, errores, latencia promedio). Un partner que intenta consultar las de otro recibe 403. Un partner suspendido sí puede leer su historial.

### CA-APM-008 (CU-O52)
La consola del Desarrollador de APIs lista el detalle de cada llamada con filtros y paginación por cursor. Los errores 4xx/5xx aparecen con su código.

### CA-APM-009 (CU-O52 / RF-O52.2)
El reporte de un mes sin consumo devuelve cero en todas las métricas sin error.

### CA-APM-010 (CU-O53 / RF-O53.1, RF-O53.3)
El sistema alerta al aproximarse y al alcanzar el cupo, sin duplicar avisos en el mismo período. **Superar el cupo no interrumpe el servicio en ningún caso**: las llamadas posteriores se atienden y se registran con normalidad.

### CA-APM-011 (CU-O54 / RF-O54.1, RF-O54.2)
El corte separa consumo incluido de excedente y emite factura solo por el excedente, con `tipo='excedente_api'`. Un partner dentro del cupo no genera factura.

### CA-APM-012 (CU-O54 / RF-O54.3)
Un reintento sobre un período que ya tiene factura de excedente **no emite una segunda**. Verificado por `id_cliente` + `periodo` + `tipo`.

### CA-APM-013 (CU-O54 / RF-O54.4)
Ante fallo, se reintenta a 1 h, 6 h y 24 h, actualizando `reintentos` y `resultado_ultimo_reintento`. Agotados, la factura queda pendiente de emisión manual y se alerta al Administrador y al Desarrollador de APIs.

### CA-APM-014 (RN-APM-016)
Una factura en disputa queda excluida del cobro automático mientras el reclamo siga abierto.

### CA-APM-015 (RN-APM-005)
Si la escritura del consumo falla, la petición del partner se responde igualmente y el fallo queda registrado para reconciliación.

### CA-APM-016 (RNF-APM-002)
Los endpoints de consumo responden en p95 ≤ 2 s con el registro de la llamada activo.


### D3 — Las excepciones de facturación se exponen, no solo se avisan por correo

**Decidido 2026-08-10, al implementar el frontend de esta capa.**

**El problema.** RF-APM-013 y RN-APM-014 exigen que una factura de excedente
**nunca quede silenciosamente sin crearse**. El backend cumplía la mitad: los
dos casos de excepción se auditaban y se mandaba un correo, pero **no había
forma de consultarlos**. Un correo que se pierde es exactamente el silencio que
la regla prohíbe, y el caso `no_tarificable` ni siquiera dejaba rastro
persistido.

**La decisión.** `GET /api/v1/facturacion/excepciones` (BE-DELTA-04) devuelve
los dos tipos con un discriminador obligatorio:

| `tipo` | Hay factura | Acción |
|---|---|---|
| `reintentos_agotados` | Sí | Emitirla manualmente |
| `no_tarificable` | **No** | Configurar la tarifa del plan y reejecutar el corte |

Los no tarificables (BE-DELTA-05) se **derivan del mismo cálculo** que hace el
corte, sin emitir nada. Su `importe` va a `None` y **nunca a 0.0**: un cero
diría «se facturó nada», y la verdad es que no se pudo calcular.

**Sin cambios de esquema.** Expone datos que ya se escribían y un cálculo que ya
se hacía.

## 12. Dependencias

- **`partner-api-onboarding` (#07):** provee `Dim_Partner` con su cupo congelado y `Dim_CredencialAPI` con `activo` y `fecha_expiracion`. Sin partners incorporados no hay consumo.
- **`autenticacion-y-rbac`:** roles `DesarrolladorAPIs` (consola y alertas), `Administrador` (excepciones de facturación), `Cliente` (reporte) y `PartnerIntegracion` (métricas propias). La API de datos **no** usa JWT humano: autentica por credencial.
- **`subscriptions-and-billing`:** dueño de `Fact_Factura` (incluida la columna `tipo`) y de `Dim_Plan` (cupo y tarifa).
- **`incorporacion-clientes`:** provee `Dim_Preferencias_Cliente.zonas_geograficas`.
- **`seguimiento-cierre-de-casos`:** los expedientes cerrados son la materia prima que la API entrega. Este módulo **solo lee**.
- Es requerido por **`partner-access-management` (#09)**: la mora que dispara la suspensión nace de las facturas de excedente que emite este módulo.

## 13. Fuera de alcance

- **Emisión, rotación y nombrado de credenciales:** dueño = `partner-api-onboarding` (CU-O49). Este módulo **solo valida** la credencial en cada llamada.
- **Revocación por seguridad, avisos de mora, suspensión y reactivación:** dueño = `partner-access-management` (CU-O55). Este módulo solo lee `Dim_Partner.activo` para rechazar.
- **El documento de factura y su circuito de cobro:** dueño = `subscriptions-and-billing`. Este módulo calcula el excedente y dispara la emisión; el dunning y el cobro viven allá.
- **Apertura y resolución de disputas:** dueño = `gestion-tickets-soporte` (CU-O83 / RF-O83.2). Este módulo solo respeta la exclusión del cobro.
- **Documentación versionada del contrato de la API:** dueño = `partner-api-onboarding` (CU-O50).
- **Registro y cierre de los casos que la API expone:** dueños = `registro-accidente` y `seguimiento-cierre-de-casos`. Este módulo **nunca escribe** en `Fact_Accidente` ni en `Fact_Despacho`.
- **Pantallas y consola visual:** dueño = [`../frontend/spec.md`](../frontend/spec.md).

## 14. Supuestos

| Supuesto | Valor por defecto | Fundamento |
|---|---|---|
| Umbral del aviso «se aproxima al límite» | **80 % del cupo** | El SRS dice «se acerca» sin fijar porcentaje. Configurable (RNF-APM-007). |
| Momento del corte mensual | **Primer día del mes siguiente** | El SRS dice «al cierre de cada mes» sin precisar hora. |
| Período de facturación | **Mes natural** (`YYYY-MM`) | Coherente con `Fact_Factura.periodo` y con `Dim_Plan.periodicidad`. |
| Definición de «error» | `codigohttp` ≥ 400 | Convención estándar; el SRS solo dice «errores». |
| Retención del detalle de llamadas | **Sin purga automática** | RNF-14 prohíbe el borrado físico y RF-O52.3 exige conservar el detalle como respaldo de la tarificación. |
| Estados a sembrar en `Dim_EstadoIntegracion` | `Pruebas activo`, `Producción activa`, `Suspendido` | Alineados con los estados derivados de `partner-api-onboarding` § 9. |

## 15. Decisiones de esquema

### D1 — `Dim_Plan.precio_excedente_llamada`: la tarifa del excedente ✅ APLICADO 2026-08-08

**Decidido — opción A, aplicada y verificada contra Pinot.**

**El problema.** RF-O54.1 exige «calcular el importe del consumo según la **tarifa vigente del plan**», pero `Dim_Plan` no tenía dónde guardarla. Su columna `precio` es el importe de la **suscripción mensual**, no el precio unitario del excedente. Sin ese dato, **CU-O54 no podía calcular ningún importe** y la línea de ingresos por consumo seguía sin ser exigible — justo lo que este módulo viene a resolver.

**La decisión.** Columna nueva `precio_excedente_llamada` (DOUBLE) en `Dim_Plan`, **configurable por el Director de Estrategia** al crear o editar el plan (CU-O26 / RF-O26.1). Mismo actor, mismo formulario y mismo criterio con que se resolvió `api_calls_minuto`: es un parámetro de negocio, no una constante del código (RNF-20).

**Alternativas descartadas.** Una tabla `Dim_TarifaExcedente` con tramos por volumen (B) es más flexible, pero introduce una tabla y un cálculo por tramos que el negocio no ha pedido; queda como migración natural si algún día hacen falta precios escalonados. Derivar la tarifa del precio del plan (C) no requería esquema, pero haría que el excedente saliera **al mismo precio unitario que el consumo ya pagado**, sin margen comercial.

**Centinela `-1.0` = «sin tarifa configurada».** Deliberadamente **no** se usa `0.0` como defecto: un cero significa «excedente gratis» y el corte mensual emitiría facturas de importe cero sin que nadie lo note — ingreso real no cobrado en silencio, que es exactamente lo que RN-APM-014 prohíbe. Con `-1.0`, CU-O54 distingue «gratis» (decisión comercial legítima) de «sin configurar» (error) y **alerta en vez de facturar mal** (RF-APM-011). Mismo criterio que `Dim_Partner.limitellamadasmes = -1`.

**Cómo se calcularon los valores iniciales.** No por nivel de plan, sino a partir del **precio unitario real de cada plan** (`precio / api_calls_mes`) con un recargo del 25 %: el consumo dentro del cupo ya está pagado y tiene descuento por volumen, el excedente no.

> La primera versión sí derivaba la tarifa del nivel, y la simulación la descartó: el plan «Magnifico» es de nivel Empresarial pero con solo 100 llamadas/mes, así que por nivel le tocaba $0,005 cuando su consumo incluido cuesta $1,20 por llamada — el excedente habría salido **240 veces más barato que el cupo**, y al partner le habría convenido pasarse. Derivarla del unitario real garantiza que la tarifa siempre quede por encima del incluido, sea cual sea la coherencia interna del plan.

| Plan | Incluido | Excedente | Factor |
|---|---|---|---|
| Básico | $0,04900 | **$0,06** | ×1,22 |
| Profesional | $0,01490 | **$0,02** | ×1,34 |
| Empresarial | $0,00399 | **$0,005** | ×1,25 |
| Plan Remediation Demo | $0,19800 | **$0,25** | ×1,26 |
| Magnifico | $1,20000 | **$1,50** | ×1,25 |

Son valores **iniciales**: el Director de Estrategia los reconfigura desde el formulario de plan.

**Alcance de la implementación.** Esquema (`database/esquemas.json`) · validación en `CatalogoPlanService` (obligatorio al crear, validado al editar, rechaza negativos porque `-1.0` es centinela y no debe fijarse desde la UI) · campo «Excedente API (USD/llamada)» en el formulario de plan · tipos `Plan`, `PlanRequest` y `PlanPatchRequest` · seeds y doble de tests · los 5 planes migrados.

**Script:** `database/migra_tarifa_excedente.py` (idempotente, con `--dry-run` y respaldo releído antes de tocar nada). **Verificado:** 5/5 planes con tarifa en Pinot; backend 1042 passed / 2 skipped; frontend 316/316.

### D2 — El límite «por minuto»: throttle técnico, no cuota comercial ✅ DECIDIDO 2026-08-08

**Decidido — opción B.**

**La tensión.** El SRS exige que el plan defina un límite de llamadas **mensual y por minuto** (L376, L408), y `Dim_Partner.limitellamadasminuto` ya existe y se puebla. Pero el mismo SRS declara que **superar la cuota nunca bloquea** (RN-11, L406). Un tope por minuto que no corta y que solo se factura al mes no se distingue del tope mensual: quedaba decorativo.

**La decisión: son dos mecanismos distintos, y el SRS los mezcla.** `limitellamadasminuto` es el **throttle técnico del partner** y devuelve **HTTP 429**; el cupo mensual es el **compromiso comercial** y no bloquea nunca. Detalle completo en la tabla de RF-APM-010.

**Por qué esto no contradice RN-11.** Un `429` no es «aplicación de la cuota»: el cupo mensual sigue sin bloquear y sigue generando excedente facturable, que es lo que RN-11 protege. Lo que se limita es el *ritmo instantáneo*, como en cualquier API pública. La alternativa (A, solo alertar) dejaba la plataforma sin defensa ante un partner mal programado, y el proyecto ya declara throttling DRF como estándar en `api-standards.md`. La opción C (degradación) es la que insinúa RF-O53.2 del catálogo, pero es difícil de implementar, de explicar al partner y de testear de forma determinista.

**Consecuencia contable, importante:** una petición rechazada con 429 **no se atendió**, así que **no es consumo facturable**. Se registra en `Fact_LogLlamadaAPI` con su código —para que el partner vea que le están limitando— pero **no suma en `Fact_APIIntegracion`**. Facturar peticiones que nunca se sirvieron sería cobrar de más.

**Limitación declarada de infraestructura.** El proyecto **no tiene Redis ni caché distribuida**: Django usa `LocMemCache`, que es **por proceso**. Con un solo proceso el throttling de DRF es fiable; al escalar a varios, el límite efectivo se multiplicaría por el número de procesos. **No es bloqueante hoy** —el despliegue es de un proceso— pero debe recogerse como deuda en el `plan.md`: escalar horizontalmente exigirá un contador compartido.

**Pendiente derivado:** añadir un throttle rate por partner en `REST_FRAMEWORK.DEFAULT_THROTTLE_RATES` (hoy solo hay tres, ninguno de partners). Se resuelve en `/speckit-tasks`.

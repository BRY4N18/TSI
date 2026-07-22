# Especificación: Onboarding y Validación de Región Operativa

## 1. Objetivo

Asegurar que una nueva región operativa cumpla los requisitos de operatividad antes de recibir accidentes reales en producción, mediante un protocolo de validación ejecutado por el Administrador y el Director Tecnológico, con capacidad de re-evaluación, despublicación manual y despublicación automática por pérdida total de cobertura.

## Clarifications

### Session 2026-07-21
- Q: RF-REGON-001 dice que el Administrador "corre las validaciones automáticas" en CU-O55, pero la Sección 13 dice que no existe checklist técnico automatizado. ¿Qué significa "ejecutar el protocolo de validación"? → A: Revisión manual, sin checklist — el Administrador/Director Tecnológico evalúan criterios fuera del sistema; solo el resultado final (`'Aprobada'`/`'Rechazada'` + `motivo`) se registra en `Dim_ValidacionRegion`. No hay validaciones automáticas del sistema en este spec.
- Q: ¿Puede una región en `En_Alerta` o `Despublicada` volver a entrar al protocolo `CU-O55` para reactivarse? → A: Sí, puede reingresar — si el resultado es `Aprobada`, `estadoregion` vuelve a `Producción`. `CU-O55` es el único camino documentado hacia `Producción`, sin importar el estado previo (salvo `activo=false`).
- Q: Si dos ejecuciones de `CU-O55` ocurren casi simultáneamente para la misma región, ¿cómo debe comportarse `Dim_RegionOperativa.estadoregion`? → A: Último `INSERT` gana — ambas filas se insertan en `Dim_ValidacionRegion` (auditoría completa); `estadoregion` refleja el resultado de la última escritura procesada, sin bloqueo especial.

## 2. Contexto

Antes de que TSI pueda operar en una nueva zona geográfica, esa región debe pasar por un protocolo de validación de operatividad. Una vez en producción, la región puede degradarse (alerta) o despublicarse — manualmente por el Director Tecnológico, o automáticamente por el sistema si pierde toda cobertura de unidades activas. El modelo real es deliberadamente simple: el estado de la región vive en un campo directo (`Dim_RegionOperativa.estadoregion`), sin tabla de historial de transiciones — a diferencia del patrón usado para unidades de emergencia (`Fact_HistorialEstadoUnidad`), aquí no existe esa tabla equivalente.

**Casos de uso incluidos:**
- **CU-O55: Ejecutar protocolo de validación de operatividad** — El Administrador y el Director Tecnológico validan si una región cumple los criterios para pasar a producción.
- **CU-O60: Registrar resultado fallido de validación y definir remediación** — Camino negativo de `CU-O55`; gestión posterior al rechazo.
- **CU-O61: Re-evaluar/despublicar región habilitada** — El Director Tecnológico degrada o despublica una región que ya estaba en producción.
- **CU-O62: Ejecutar despublicación automática por pérdida total de cobertura** — El Sistema despublica una región sin intervención humana cuando no quedan unidades activas.

**Tablas de base de datos utilizadas** (verificadas contra `tablas.json`/`esquemas.json` — nombres reales, distintos de los que usa la narrativa de `ConfiguracionRedOperativa.md`):
- `Dim_RegionOperativa`: `idregionoperativa` (PK), `idestado` (FK a `Dim_EstadoRegion`), `nombreregion`, `estadoregion` (STRING — campo de estado **directo**, sobrescrito en cada transición, sin historial), `activo`, `fecha_actualizacion`.
- `Dim_ValidacionRegion`: `idvalidacionregion` (PK), `idregionoperativa` (FK), `idusuario`, `resultado` (STRING libre: 'Aprobada' | 'Rechazada' — **no** es FK a un catálogo, no existe tabla `Dim_Estado_Implementacion`), `motivo`, `fechahora`, `fecha_actualizacion`.
- `Dim_RegionOperativaEstadoRegion`: `idregionoperativaestadoregion` (PK), `idregionoperativa` (FK), `idestadoregion` (FK a `Dim_EstadoRegion`), `nombreregion`, `activo`, `fecha_actualizacion`. **Es una tabla puente geográfica** (qué estados/provincias cubre la región operativa), no un historial de ciclo de vida — reinterpretación necesaria respecto a la narrativa original.
- `Dim_EstadoRegion`: dimensión geográfica (estado/provincia, ej. "Jalisco"), no confundir con estado de ciclo de vida.
- `Fact_Accidente` (módulo Emergencias, solo lectura): usada para la regla de continuidad de casos activos al despublicar.
- `Dim_UnidadEmergencia` (módulo Red-Operativa, spec `alta-unidades`, solo lectura): el conteo de unidades activas dispara `CU-O62`.


## 3. Actores

| Actor | Rol en este spec | Interacción principal |
|---|---|---|
| **Administrador** | Ejecutor del protocolo | Corre las validaciones automáticas de una región nueva (`CU-O55`), gestiona la remediación tras un rechazo (`CU-O60`). |
| **Director Tecnológico** | Validador final y responsable de degradación | Queda registrado como `idusuario` en la aprobación final de `CU-O55`. Ejecuta `CU-O61` (re-evaluar/despublicar). |
| **Sistema** | Ejecutor automático | Ejecuta `CU-O62` sin intervención humana ante pérdida total de cobertura. |

## 4. Requisitos funcionales

### RF-REGON-001: Ejecutar protocolo de validación de operatividad (CU-O55)

El Administrador y el Director Tecnológico deben poder validar una región:

1. Si la región aún no existe en el sistema: insertar en `Dim_RegionOperativa` (`idestado`, `nombreregion`, `activo=true`), con `estadoregion = 'En_Validación'` desde el primer momento.
2. Insertar en `Dim_ValidacionRegion`: `idregionoperativa`, `idusuario` (quien ejecuta), `resultado` (`'Aprobada'` o `'Rechazada'`), `motivo` (obligatorio solo si `Rechazada`), `fechahora`.
3. **Si el resultado es `Aprobada`:** actualizar `Dim_RegionOperativa.estadoregion = 'Producción'`. Esto aplica sin importar el `estadoregion` previo de la región (`En_Validación`, `En_Alerta` o `Despublicada`) — `CU-O55` es el único camino documentado hacia `Producción`, incluyendo reactivación de regiones degradadas o despublicadas.
4. **Si el resultado es `Rechazada`:** `Dim_RegionOperativa.estadoregion` permanece en `'En_Validación'`; el flujo continúa en `CU-O60`.
5. **Actores duales, secuencial no indistinto:** el Administrador ejecuta el protocolo (recolecta los criterios y coordina la revisión); el Director Tecnológico es quien queda registrado como `idusuario` en `Dim_ValidacionRegion` cuando la aprobación requiere validación final. No existe un estado "pendiente de aprobación" separado — la región permanece en `En_Validación` hasta que se inserta la fila con `resultado='Aprobada'`.
6. **Naturaleza de la validación:** el protocolo es una revisión manual — el Administrador/Director Tecnológico evalúan los criterios de operatividad fuera del sistema (no hay checklist técnico automatizado de conectividad/healthcheck respaldado por tabla, ver Sección 13). El sistema únicamente registra el resultado final (`resultado`, `motivo`) en `Dim_ValidacionRegion`; no ejecuta validaciones automáticas propias.
7. **Concurrencia:** si dos ejecuciones de `CU-O55` ocurren casi simultáneamente para la misma región, ambas filas se insertan en `Dim_ValidacionRegion` (auditoría completa, sin pérdida de intentos) y `Dim_RegionOperativa.estadoregion` refleja el resultado de la última escritura procesada (último `INSERT` gana), sin bloqueo optimista ni mecanismo de versionado.

### RF-REGON-002: Gestionar resultado fallido y remediación (CU-O60)

Es el camino negativo de `CU-O55`, no una escritura nueva de tablas — el resultado fallido ya se registró dentro de `CU-O55` (`Dim_ValidacionRegion` con `resultado='Rechazada'` y `motivo`). Este requisito cubre la gestión posterior:

1. El reintento de validación tras resolver el motivo del rechazo es, simplemente, una nueva ejecución de `CU-O55`, generando una nueva fila en `Dim_ValidacionRegion`.
2. El historial completo de intentos (aprobados y rechazados) es consultable con un `SELECT` de todas las filas de `Dim_ValidacionRegion` para una `idregionoperativa`, ordenadas por `fechahora`.
3. **No existe una tabla de "plan de remediación"** (responsable + fecha estimada) en este modelo — se acordó que el campo `motivo` de `Dim_ValidacionRegion` es suficiente. *(Si a futuro se requiere trackear responsable y fecha de resolución como entidad propia, se necesitaría una tabla nueva con FK a `Dim_ValidacionRegion`; no existe hoy.)*
4. **Rechazo definitivo** (se decide no continuar con la región): `Dim_RegionOperativa.activo = false`. No se inserta ningún nuevo estado porque la región nunca llegó a `Producción`; queda simplemente inactiva desde `En_Validación`.

### RF-REGON-003: Re-evaluar/despublicar región habilitada (CU-O61)

El Director Tecnológico debe poder degradar o despublicar una región que ya está en `Producción`:

1. Actualizar `Dim_RegionOperativa.estadoregion` de `'Producción'` a `'En_Alerta'` o `'Despublicada'`.
2. **Regla de continuidad de casos activos:** si la región pasa a `Despublicada` mientras existen casos en curso dentro de esa zona (`Fact_Accidente` sin cierre, módulo Emergencias), esos casos **no se abandonan ni se cancelan** — se gestionan hasta su cierre natural (`CU-O28`, módulo Emergencias). La despublicación solo impide que la región reciba **casos nuevos**; esta validación se ejecuta en tiempo real al crear un nuevo `Fact_Accidente`, no requiere columna ni tabla adicional.

### RF-REGON-004: Despublicación automática por pérdida total de cobertura (CU-O62)

El Sistema debe despublicar automáticamente una región sin intervención humana:

1. Actualizar `Dim_RegionOperativa.estadoregion` de `'Producción'` (o `'En_Alerta'`, si ya venía degradada por `CU-O61`) a `'Despublicada'`.
2. El registro de la transición no tiene un actor humano — se documenta con `idusuario = NULL` conceptualmente (no hay tabla de historial donde insertar esta marca; el cambio es solo el `UPDATE` de `estadoregion`).
3. **Pendiente de confirmación:** el disparador exacto (qué evento evalúa el conteo de unidades activas y cómo se relaciona `zonacobertura` de `Dim_UnidadEmergencia` con `idregionoperativa`) no está definido a nivel de estructura de datos — **no existe FK entre `Dim_UnidadEmergencia` y `Dim_RegionOperativa`**. Se documenta la intención funcional (despublicar ante cero unidades activas en la región), sin mecanismo de disparo confirmado a nivel de esquema.

## 5. Requisitos no funcionales

### RNF-REGON-001: Trazabilidad de validaciones
Cada ejecución del protocolo de validación (`CU-O55`) debe quedar registrada de forma inmutable en `Dim_ValidacionRegion` — no se sobrescriben intentos previos, cada intento es una fila nueva.

### RNF-REGON-002: Consistencia de continuidad operativa
La despublicación de una región (`CU-O61`, `CU-O62`) no debe interrumpir casos de emergencia en curso — la validación contra `Fact_Accidente` debe ejecutarse en tiempo real, con latencia ≤100ms (p95), consistente con el umbral de "Consulta Pinot simple" de `.specify/docs/architecture/testing.md`.

## 6. Reglas de negocio

### RN-REGON-001
El estado de la región (`Dim_RegionOperativa.estadoregion`) es un campo **directo**, sin tabla de historial de transiciones — a diferencia de `Dim_UnidadEmergencia`, que deliberadamente no tiene estado directo. Esta asimetría es una decisión de modelo ya tomada, no un error a corregir.

### RN-REGON-002
`Dim_ValidacionRegion.resultado` es un `STRING` libre (`'Aprobada'` / `'Rechazada'`), no una FK a un catálogo de estados de implementación — dicho catálogo no existe en el esquema real.

### RN-REGON-003
Una región solo pasa a `Producción` cuando existe al menos una fila en `Dim_ValidacionRegion` con `resultado='Aprobada'` para esa `idregionoperativa`. Esta regla se cumple **por construcción**: `Producción` nunca se escribe salvo como efecto atómico de insertar una fila con `resultado='Aprobada'` (RF-REGON-001.3) — no existe un paso de "activación" independiente que pueda intentarse sin validación previa, por lo que no hay un caso de conflicto (409) asociado a esta regla.

### RN-REGON-004
La despublicación (`CU-O61`, `CU-O62`) nunca cancela casos de emergencia activos en la región — solo bloquea la creación de casos nuevos.

### RN-REGON-005 — Pendiente de confirmación
No existe FK entre `Dim_UnidadEmergencia` y `Dim_RegionOperativa`. El disparador de `CU-O62` (pérdida total de cobertura) no puede implementarse de forma confiable hasta que se defina cómo se relaciona `zonacobertura` (texto libre en `Dim_UnidadEmergencia`) con `idregionoperativa`.

## 7. Entradas

### Para validación de región (CU-O55)
`idregionoperativa` (si ya existe) o datos de alta (`idestado`, `nombreregion`, si es la primera validación), `resultado`, `motivo` (obligatorio si `Rechazada`), `idusuario`.

### Para remediación (CU-O60)
`idregionoperativa`, decisión: reintentar (dispara nueva ejecución de `CU-O55`) o rechazo definitivo (`activo=false`).

### Para re-evaluación/despublicación (CU-O61)
`idregionoperativa`, `estadoregion` nuevo (`'En_Alerta'` | `'Despublicada'`), `idusuario` (Director Tecnológico), motivo.

### Para despublicación automática (CU-O62)
Disparado por evento del sistema (conteo de unidades activas) — sin entrada de usuario. *(Mecanismo de disparo pendiente de confirmación, ver RN-REGON-005.)*

## 8. Salidas

- **200 OK — Validación registrada:** `{ idregionoperativa, resultado, estadoregion_actual }`.
- **200 OK — Región activada:** `{ idregionoperativa, estadoregion: 'Producción' }`.
- **200 OK — Región rechazada definitivamente:** `{ idregionoperativa, activo: false }`.
- **200 OK — Región degradada/despublicada:** `{ idregionoperativa, estadoregion }`.
- **409 Conflict** — Transición de `estadoregion` no permitida en `CU-O60` (rechazo definitivo sobre región que no está en `En_Validación`) o en `CU-O61`/`CU-O62` (estado origen distinto de `Producción`/`En_Alerta`). *(Nota de análisis 2026-07-21: el 409 "activar sin validación Aprobada" documentado en una versión previa de esta sección es estructuralmente inalcanzable — `Producción` solo se alcanza atómicamente al insertar `resultado='Aprobada'` en `CU-O55`, nunca como un paso de "activación" separado; RN-REGON-003 queda garantizada por construcción, no por una validación adicional.)*

## 9. Estados posibles

### Estados de `Dim_RegionOperativa.estadoregion`
| Estado | Significado |
|---|---|
| **En_Validación** | Región registrada, protocolo de validación en curso o con rechazos previos. |
| **Producción** | Al menos una validación `Aprobada`; la región recibe accidentes reales. |
| **En_Alerta** | Región en producción pero degradada (`CU-O61`). |
| **Despublicada** | Región retirada de operación, manual (`CU-O61`) o automáticamente (`CU-O62`). |

### Transiciones
```
En_Validación → Producción      (CU-O55, resultado='Aprobada')
En_Validación → [activo=false]  (CU-O60, rechazo definitivo — no es un estado, es baja lógica)
Producción → En_Alerta          (CU-O61)
Producción → Despublicada       (CU-O61 o CU-O62)
En_Alerta → Despublicada        (CU-O61 o CU-O62)
En_Alerta → Producción          (CU-O55, resultado='Aprobada' — reactivación)
Despublicada → Producción       (CU-O55, resultado='Aprobada' — reactivación)
```

## 10. Escenarios

### Escenario 1: Validación aprobada en primer intento (CU-O55)
Dado que una región nueva se registra en `Dim_RegionOperativa` con `estadoregion='En_Validación'`
Cuando el Director Tecnológico ejecuta la validación con `resultado='Aprobada'`
Entonces el sistema debe insertar en `Dim_ValidacionRegion`
Y debe actualizar `Dim_RegionOperativa.estadoregion='Producción'`.

### Escenario 2: Validación rechazada y reintento (CU-O55 + CU-O60)
Dado que la primera validación de una región resulta `Rechazada` con motivo "Latencia fuera de rango"
Cuando se corrige el problema y se re-ejecuta la validación
Entonces el sistema debe insertar una **nueva** fila en `Dim_ValidacionRegion` (no se sobrescribe la anterior)
Y si el nuevo resultado es `Aprobada`, la región pasa a `Producción`.

### Escenario 3: Rechazo definitivo (CU-O60)
Dado que una región acumula varios rechazos y se decide no continuar
Cuando el Administrador marca el rechazo como definitivo
Entonces el sistema debe actualizar `Dim_RegionOperativa.activo=false`
Y `estadoregion` permanece en `En_Validación` (nunca llegó a `Producción`).

### Escenario 4: Despublicación manual con casos activos (CU-O61)
Dado que una región en `Producción` tiene 3 casos de emergencia activos
Cuando el Director Tecnológico la despublica
Entonces el sistema debe actualizar `estadoregion='Despublicada'`
Y los 3 casos activos deben continuar hasta su cierre natural
Y la región no debe poder recibir accidentes nuevos a partir de ese momento.

### Escenario 5: Despublicación automática por pérdida de cobertura (CU-O62)
Dado que todas las unidades activas de una región pasan a inactivas
Cuando el sistema detecta cero unidades activas (mecanismo de disparo pendiente de confirmación)
Entonces debe actualizar `estadoregion='Despublicada'`
Sin ningún `idusuario` asociado a la transición.

## 11. Criterios de aceptación

### CA-REGON-001
El Administrador/Director Tecnológico puede ejecutar la validación de una región e insertar el resultado en `Dim_ValidacionRegion` (CU-O55).

### CA-REGON-002
Una región pasa a `Producción` solo si existe al menos una validación con `resultado='Aprobada'`.

### CA-REGON-003
Un resultado `Rechazada` no cambia `estadoregion`; la región permanece en `En_Validación`.

### CA-REGON-004
El historial completo de intentos de validación es consultable por `idregionoperativa`, ordenado por `fechahora` (CU-O60).

### CA-REGON-005
Un rechazo definitivo marca `Dim_RegionOperativa.activo=false` sin insertar un nuevo estado.

### CA-REGON-006
El Director Tecnológico puede degradar (`En_Alerta`) o despublicar (`Despublicada`) una región en producción (CU-O61).

### CA-REGON-007
La despublicación nunca cancela casos activos — solo bloquea casos nuevos.

### CA-REGON-008
El sistema puede despublicar automáticamente una región sin actor humano (CU-O62), aunque el disparador exacto está pendiente de confirmación.

## 12. Dependencias

- **`autenticacion-y-rbac`:** requiere autenticación JWT y roles "Administrador" y "Director Tecnológico".
- **`alta-unidades`:** el conteo de unidades activas de una región (para `CU-O62`) depende del catálogo gestionado en ese spec — aunque, como se documenta en RN-REGON-005, la relación no tiene FK real todavía.
- Es requerido por:
  - **`registro-accidente`** (módulo Emergencias): un accidente solo puede registrarse en una región con `estadoregion='Producción'`.

## 13. Fuera de alcance

- **Registro y gestión de unidades de emergencia:** eso corresponde a `alta-unidades` (este módulo).
- **Checklist de pruebas técnicas automatizadas (conectividad, healthcheck, notificaciones push/SMS):** no existe tabla que respalde esta funcionalidad en el esquema real; si se requiere, es una definición de alcance futura, no de este spec.
- **Cierre de casos de emergencia en regiones despublicadas:** eso corresponde a `seguimiento-cierre-de-casos` (módulo Emergencias).
- **Definición de la relación `zonacobertura` ↔ `idregionoperativa`:** pendiente de confirmación (RN-REGON-005), fuera de alcance hasta que se defina a nivel de estructura de datos.

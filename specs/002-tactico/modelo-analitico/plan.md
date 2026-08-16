# Implementation Plan: Modelo Analítico Táctico (esquema en estrella)

**Branch**: `modelo-analitico` | **Date**: 2026-08-14 | **Spec**: [`spec.md`](spec.md)

**Input**: Feature specification from `specs/002-tactico/modelo-analitico/spec.md`

**Módulos hermanos:** [`../infraestructura/`](../infraestructura/spec.md) define los contenedores y
el patrón de carga, que **no cambian**. [`../contrato-informes-simples.md`](../contrato-informes-simples.md)
es el contrato equivalente para los listados sobre el sistema operativo.

## Summary

Construir el **modelo dimensional del almacén analítico**: hechos con grano declarado, dimensiones
compartidas y versionadas, y un flujo de carga por hecho. Sustituye el diseño actual de una tabla y
un flujo por informe.

**Primera fase:** los hechos de **accidente** y **despacho** con sus cinco dimensiones. Cubren los
compuestos ya especificados de Emergencias, **sustituyen a los tres informes con tabla propia**, y
contienen el caso que justifica el modelo entero: la atribución unidad↔proveedor versionada.

## Traceability

- **Marco estratégico** §15.2 — el modelo Fact-Dim como capa de la que se sirven reportes, tableros e
  inteligencia.
- **Catálogo**: `informestacticos/TSI-Informes-Tacticos-Requeridos-por-OT.md`, ~105 informes
  compuestos que son los consumidores.
- **Defecto que resuelve**: la atribución de despachos al proveedor **actual** en lugar del vigente,
  limitación documentada en el propio código del informe de rendimiento por proveedor.
- **Infraestructura**: FR-012 de esta spec hereda el patrón de carga por ficheros intermedios sin
  cambiarlo.
- **Dependencias**: ninguna app de negocio. **El sistema operativo no se modifica** (FR-010).

## Technical Context

**Language/Version**: Python 3.11 en los flujos de carga (mismo entorno que los DAG existentes).

**Primary Dependencies**: el orquestador y el almacén analítico ya desplegados; las librerías de
`dags/lib/` —clientes de origen y destino, escritura de ficheros intermedios— que **se conservan**.
**Sin dependencias nuevas.**

**Storage**: almacén analítico columnar (`tsi_tactico`), de escritura por lotes. **Fuente**: el
sistema operativo, en solo lectura. **Ninguna tabla del origen se modifica.**

**Testing**: pruebas de las funciones puras de transformación —versionado, cálculo de hitos,
detección de huecos— más verificación de las propiedades del modelo declaradas en los criterios de
éxito: idempotencia, cifras coincidentes entre informes, historia estable.

**Target Platform**: el stack táctico ya desplegado, levantable de forma independiente del operativo.

**Project Type**: modelo de datos y flujos de carga. **No expone API ni interfaz.**

**Performance Goals**: que **al menos el 80 %** de los informes del catálogo se resuelva con una
consulta sobre el modelo, sin flujo propio (SC-001).

**Constraints**: los hechos se **particionan por mes** y la recarga descarta y repuebla la partición
(research D3); los atributos versionados se copian en el hecho **con su valor al momento del hecho**,
nunca como referencia mutable (research D4); un hito no alcanzado se guarda **ausente**, nunca como
cero ni fecha de carga (research D5); **prohibido que un informe cree su propia tabla** (FR-016).

**Scale/Scope**: 13 hechos y 12 dimensiones en el diseño; **2 hechos y 5 dimensiones en la primera
fase**.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Característica ISO 25010 | Estado | Justificación |
|---|---|---|
| **Functional Suitability** | PASS | El modelo se deriva del catálogo completo, no de una idea previa: cada hecho existe porque hay informes que lo reclaman. **Corrección reforzada por D1 y D2**: el grano de intento hace posibles informes que el grano de caso volvería imposibles, y el versionado impide reescribir el pasado. |
| **Reliability** | PASS | Fuera del camino crítico: es lectura por lotes del sistema operativo. La idempotencia por partición (D3) hace que una carga fallida se repita sin dejar rastro. Un hecho cuya dimensión no existe **se conserva** marcado como desconocido (FR-015): perder un accidente porque su calle no estaba cargada sería inaceptable. |
| **Performance Efficiency** | PASS | La desnormalización selectiva (D4) evita la unión en la mayoría de consultas. Descartar una partición es metadatos, no reescritura. |
| **Interaction Capability** | **N/A** | No hay superficie de usuario: los consumidores son informes. |
| **Security** | PASS | El almacén recibe **solo resultados analíticos por lotes**, como ya exige la spec de infraestructura. **Los hechos no copian identidad de personas ni coordenadas**: la geografía se guarda por nombre y jerarquía, coherente con lo decidido en los listados de Emergencias y Red Operativa. |
| **Compatibility** | PASS | **El sistema operativo no se toca.** El versionado se construye observando la fuente entre cargas. Las tres tablas actuales se retiran **cuando el modelo las cubra**, no antes (D7). |
| **Maintainability** | PASS | Un flujo por hecho en vez de uno por informe: ~13 frente a ~105. Una definición por concepto, así que dos informes no pueden discrepar sobre «severidad» o «condado». |
| **Flexibility** | PASS | FR-017 exige que añadir un hecho o una métrica no altere lo existente, y el diseño por particiones y dimensiones compartidas lo permite. Está asumido que el modelo se corregirá al avanzar por departamentos. |
| **Safety** | **N/A** | Lectura analítica por lotes, fuera del camino crítico. Ningún flujo escribe en el sistema operativo. |

### Tie-Breaker Mechanism

**Conflicto identificado: Functional Suitability vs. Performance Efficiency** en D1 (grano del hecho
de despacho).

- **En conflicto:** el grano de caso daría tablas más pequeñas y consultas más rápidas para las
  preguntas por caso; el grano de intento multiplica las filas.
- **Priorizado:** **Functional Suitability** — grano de intento.
- **Regla aplicada:** prioridad por defecto, al no estar Safety en juego. Y el argumento es
  categórico, no de grado: con grano de caso, *rechazo por unidad*, *despachos al primer intento* y
  *carga por unidad* **no son calculables**, no simplemente más lentos. Un modelo que impide
  responder preguntas del catálogo ha fallado en su única función.
- **Trade-off aceptado:** más filas, y que «cuántos casos se despacharon» sea un recuento de casos
  distintos en vez de filas. Se documenta en el contrato de consumo.

**Segundo conflicto: Functional Suitability vs. Maintainability** en D3 (motor de los hechos
acumulados).

- **En conflicto:** un solo motor para todos los hechos sería más simple; los acumulados necesitan
  actualizar filas y los de transacción no.
- **Priorizado:** **Functional Suitability** — dos motores según el tipo de hecho.
- **Regla aplicada:** prioridad por defecto. Usar el motor con deduplicación para **todo** haría que
  una consulta pudiera leer dos versiones de una fila mientras la deduplicación ocurre en segundo
  plano: cifras infladas de forma intermitente, que es el peor fallo posible en un informe.
- **Trade-off aceptado:** dos patrones de carga en vez de uno, y una regla de consumo que las
  consultas sobre hechos acumulados deben respetar. Se documenta en el contrato.

## Project Structure

### Documentation (this feature)

```text
specs/002-tactico/modelo-analitico/
├── spec.md · plan.md · research.md · data-model.md · quickstart.md
├── contracts/
│   ├── esquema-analitico.md          # hechos, dimensiones, columnas y granos
│   └── contrato-consumo.md           # cómo un informe consulta el modelo
├── checklists/requirements.md
└── tasks.md                          # Fase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
dags/
├── lib/                              # EXISTENTE — se conserva y se amplía
│   ├── clickhouse_http_client.py     # sin cambios
│   ├── pinot_http_client.py          # sin cambios
│   ├── parquet_io.py                 # sin cambios
│   ├── ddl.py                        # se REEMPLAZA: pasa de 3 tablas de informe al modelo
│   ├── dimensiones/                  # NUEVO
│   │   ├── versionado.py             # apertura y cierre de versiones (research D2)
│   │   ├── dim_tiempo.py
│   │   ├── dim_geografia.py
│   │   ├── dim_severidad.py
│   │   ├── dim_unidad.py             # versionada: unidad ↔ proveedor
│   │   └── dim_origen_despacho.py
│   └── hechos/                       # NUEVO
│       ├── hecho_accidente.py        # instantánea acumulada
│       └── hecho_despacho.py         # instantánea acumulada, grano intento
└── etl/
    ├── dag_etl_principal.py          # se conserva: es el ejemplo del patrón
    ├── dag_backfill.py               # se conserva
    ├── dag_dimensiones.py            # NUEVO — carga las dimensiones antes que los hechos
    ├── dag_hecho_accidente.py        # NUEVO
    ├── dag_hecho_despacho.py         # NUEVO
    ├── indice_calidad_dag.py         # se RETIRA cuando el modelo lo cubra (D7)
    ├── perdida_senal_dag.py          # ídem — su lógica pura se conserva
    └── rendimiento_proveedor_dag.py  # ídem
```

**Structure Decision.** Se separa `dimensiones/` de `hechos/` porque su ciclo es distinto: las
dimensiones se cargan **antes** y con menos frecuencia, y su versionado es una lógica compartida que
no debe repetirse por hecho. El patrón de ficheros intermedios se conserva tal cual en ambos.

**`ddl.py` se reemplaza, no se amplía**: hoy define tres tablas de informe; pasará a definir el
modelo. Es el fichero que materializa el cambio de diseño.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Dos motores de tabla según el tipo de hecho | Los hechos acumulados actualizan filas al avanzar el proceso; los de transacción no | Un solo motor con deduplicación haría que una consulta leyera dos versiones de la misma fila mientras la deduplicación ocurre en segundo plano — cifras infladas de forma intermitente |
| Lógica de versionado de dimensiones | Es lo que impide reescribir el pasado, y el defecto que justifica todo el módulo | Copiar el atributo actual en el hecho es más simple y **reproduce exactamente el defecto** que se quiere corregir |
| Desnormalización selectiva en los hechos | El almacén columnar rinde mucho mejor sin uniones; la mayoría de informes agrupa por los mismos pocos atributos | Un esquema en estrella normalizado obligaría a unir en casi toda consulta, con peor rendimiento que el diseño actual de tabla por informe — perdería la única ventaja que este tiene |

## Riesgo declarado

**La atribución histórica unidad↔proveedor empieza el día de la primera carga** (research D2). Nada
en el origen historiza ese cambio, así que **no hay forma de reconstruir el pasado**.

El modelo **no arregla los períodos ya transcurridos**; impide que se sigan rompiendo desde hoy. Cada
versión de dimensión declara si su fecha de inicio es real o significa «desde la primera carga», para
que un informe pueda decirlo en vez de presentar «no lo sabemos» como «siempre fue así».

**Es una limitación del dato, no del diseño**, y conviene que quede visible antes de que alguien
interprete las cifras de los primeros meses.

## Phase Status

- [x] **Phase 0 — Research**: [`research.md`](research.md), 7 decisiones, 0 NEEDS CLARIFICATION.
- [x] **Phase 1 — Design**: [`data-model.md`](data-model.md), [`contracts/`](contracts/), [`quickstart.md`](quickstart.md).
- [x] **Post-Design Constitution Check**: PASS. Dos conflictos resueltos vía Tie-Breaker; tres
  entradas de Complexity Tracking justificadas.
- [ ] **Phase 2 — Tasks**: pendiente de `/speckit-tasks`.

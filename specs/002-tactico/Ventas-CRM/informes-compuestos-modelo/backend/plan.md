# Implementation Plan: Informes Compuestos de Ventas y CRM sobre el Modelo Analítico

**Branch**: `002-tactico/Ventas-CRM/informes-compuestos-modelo/backend` | **Date**: 2026-08-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-tactico/Ventas-CRM/informes-compuestos-modelo/backend/spec.md`

## Summary

**13 informes agregados de Ventas y CRM, cada uno una consulta sobre el modelo analítico.**

| | |
|---|--:|
| Informes que ya existen | **0** |
| Informes cuyo sustrato ya está construido | **0** |
| Tablas nuevas en el modelo | **6** |

**Es el departamento más caro de los tres hechos hasta ahora, y por una razón concreta:** su dominio
no toca ninguna tabla del modelo actual. Emergencias construyó accidente y despacho; Red Operativa
reutilizó la unidad y añadió dos tablas. Aquí hacen falta seis.

Eso **no es un defecto del modelo**: es lo que cuesta incorporar un dominio entero por primera vez.
Lo que sí demuestra el patrón es que **la plomería no se toca**: cargador de consultas, repositorio,
período, permisos y versionado se reutilizan tal cual, igual que en Red Operativa.

### Las dos decisiones que dan forma al plan

**El desenlace de un prospecto no se lee de `activo`.** Esa columna cubre a la vez convertido y
perdido —resultados opuestos—, y el modelo lo resuelve **al cargar**: la dimensión de prospecto
guarda un desenlace de tres valores, derivado del motivo y de la etapa. Los informes no tienen que
acordarse de la trampa porque el dato ya llega desagregado.

**El CAC se entrega a medias y se dice.** Sin datos de coste, el informe devuelve clientes convertidos
por canal y **ninguna columna de coste, ni siquiera vacía** (FR-022): una columna así invita a
rellenarla desde fuera, y el tablero acabaría mostrando un CAC que el sistema no sostiene.

## Technical Context

**Language/Version**: Python 3.12 (Airflow) y Python 3.13 (Django)

**Primary Dependencies**: Django 5 + DRF, `requests` contra la interfaz HTTP del almacén. **Sin
dependencias nuevas.**

**Storage**: ClickHouse 24.8, base `tsi_tactico` — solo lectura desde el backend.

**Testing**: pytest. Suites actuales: backend 1 673, `dags/` 151.

**Target Platform**: Linux en contenedor; stack táctico con `docker/docker-compose.tactico.yml`.

**Project Type**: servicio web de lectura sobre un almacén analítico.

**Performance Goals**: irrelevantes por volumen —10 prospectos, 24 transiciones— pero las consultas
se escriben con el mismo particionado y las mismas reglas, porque el volumen que importa es el que
habrá.

**Constraints**:
- **Solo lectura**, sin tabla por informe.
- **Sin identidad ni contacto de prospectos**: ni nombre, ni correo, ni teléfono, ni cargo.
- **Sin notas ni texto libre** de las transiciones.
- **Sin ninguna columna de coste** en el informe de canales.
- Versión final obligatoria en dimensiones y hechos acumulados; prohibida en los de transacción.

**Scale/Scope**: 13 informes, 3 objetivos tácticos, 2 casos de uso tácticos que hoy no cubre nada.

## Constitution Check

*GATE: debe pasar antes de la fase 0 y volver a comprobarse tras la fase 1.*

| Principio | Cómo lo cumple | Estado |
|---|---|---|
| **I. Idoneidad funcional como contrato** | Los 13 salen del catálogo trazado a OT y origen. **Satisface CU-T03 y CU-T04**, los dos casos de uso tácticos que hoy no cubre ningún informe | ✅ |
| **II. Fiabilidad operativa** | Lectura sobre un almacén separado; no toca el camino crítico | ✅ |
| **III. Eficiencia en tiempo real** | No aplica | ✅ |
| **IV. Interacción inclusiva** | Frontend fuera de alcance | ⏭️ diferido |
| **V. Seguridad por diseño** | **Es el departamento con más dato personal de todo el sistema**: los prospectos son personas con nombre, correo, teléfono y cargo. **Nada de eso entra al modelo** (FR-027) | ✅ |
| **VI. Compatibilidad API-First** | REST de solo lectura sobre la app existente | ✅ |
| **VII. Mantenibilidad estructural** | Seis tablas nuevas, **cero piezas de plomería nuevas** | ✅ |
| **VIII. Flexibilidad multi-región** | Los prospectos se agregan por tipo de organización y canal, sin atarse a una geografía | ✅ |

**Mecanismo de desempate aplicado.** Dos choques, y ambos se resuelven a favor de la honestidad del
dato antes que de la completitud del catálogo:

1. **Idoneidad frente a Seguridad**: el catálogo pide «prospectos por ejecutivo asignado» y
   «carga por ejecutivo». El ejecutivo es una persona. Se resuelve identificándolo **por su función**
   en el único informe donde el desglose es el objeto del informe —la carga—, y prohibiéndolo en
   todos los demás (FR-028).
2. **Idoneidad frente a corrección**: el catálogo pide el CAC, que no es calculable. Se entrega la
   mitad medible **declarada como tal** en vez de completarla con un número de fuera.

**Sin violaciones que justificar.**

## Project Structure

### Documentation (this feature)

```text
specs/002-tactico/Ventas-CRM/informes-compuestos-modelo/
├── informes-compuestos-modelo.md
└── backend/
    ├── spec.md
    ├── plan.md
    ├── research.md
    ├── data-model.md
    ├── quickstart.md
    ├── contracts/
    │   ├── informes-compuestos-ventas-crm.openapi.yaml
    │   └── catalogo-consultas.md
    ├── checklists/requirements.md
    └── tasks.md
```

### Source Code (repository root)

```text
dags/lib/
├── consultas/
│   ├── emergencias/                            # ya existe
│   ├── red_operativa/                          # ya especificado
│   └── ventas_crm/                             # ← nuevo: los 13 de este módulo
│       ├── ot01_*.sql
│       ├── ot02_*.sql
│       └── ot03_*.sql
├── dimensiones/
│   ├── dim_prospecto.py                        # ← nuevo
│   └── dim_canal.py                            # ← nuevo
├── hechos/
│   ├── hecho_transicion_embudo.py              # ← nuevo
│   ├── hecho_asignacion_prospecto.py           # ← nuevo
│   ├── hecho_interaccion_demo.py               # ← nuevo (fuente vacía hoy)
│   └── hecho_notificacion_ventas.py            # ← nuevo (fuente vacía hoy)
├── ddl.py                                      # ← 2 dimensiones + 4 hechos
├── dimensiones_tasks.py                        # ← añadir las 2 dimensiones al flujo existente
└── hecho_*_tasks.py                            # ← 4 flujos

dags/etl/
└── dag_hecho_*.py                              # ← 4 DAGs

backend/apps/informes_tacticos/
├── services/ventas_crm_compuestos_service.py   # ← nuevo
├── views/ventas_crm_compuestos_views.py        # ← nuevo
└── urls.py                                     # ← añadir rutas
```

**Structure Decision**: se reutiliza **toda** la plomería construida para Emergencias. Lo propio del
departamento son sus consultas, dos dimensiones, cuatro hechos y sus endpoints.

**Los cuatro hechos se agrupan en dos flujos, no en cuatro.** Embudo y asignación comparten fuente
—el ciclo del prospecto— y se cargan juntos; demo y notificación, también. Un flujo por hecho
multiplicaría los DAG sin ganar nada: no hay dependencia entre los pares ni volumen que separe.

## Complexity Tracking

| Violación | Por qué es necesaria | Alternativa más simple, y por qué se rechazó |
|---|---|---|
| **Seis tablas nuevas** para 13 informes | El dominio no toca ninguna tabla del modelo actual: no hay nada que reutilizar | *Reutilizar dimensiones existentes* — no hay ninguna aplicable: un prospecto no es un cliente, ni una unidad, ni una región |
| **Dos hechos sobre fuentes vacías** —demo y notificación— | Sostienen 5 de los 13 informes; sus repositorios **sí publican a Kafka**, así que el vacío es de entorno | *Aplazarlos hasta que haya datos* — dejaría OT03 entero sin especificar, y el trabajo sería idéntico más tarde |
| **El informe #8 entrega la mitad del indicador** | El coste por canal no existe en ninguna tabla | *Parámetro de coste* — la cifra dependería de un número tecleado, presentado como dato del sistema. *Fuera de alcance* — descartaría también la mitad que sí es medible |
| **El desenlace del prospecto se deriva al cargar** | `activo` mezcla convertido con perdido | *Derivarlo en cada consulta* — trece consultas tendrían que acordarse de la trampa, y la primera que la olvide mezclará éxito con fracaso sin fallar |

# Implementation Plan: Informes Compuestos de Red Operativa sobre el Modelo Analítico

**Branch**: `002-tactico/Red-Operativa/informes-compuestos-modelo/backend` | **Date**: 2026-08-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-tactico/Red-Operativa/informes-compuestos-modelo/backend/spec.md`

## Summary

**15 informes agregados de Red Operativa, cada uno una consulta sobre el modelo analítico.**

Situación de partida, medida y no supuesta:

| | |
|---|--:|
| Informes que **ya existen** | **0** |
| Informes cuyo sustrato **ya está construido** | **8** |
| Informes que exigen ampliar el modelo | 7 |

A diferencia de Emergencias, aquí no hay endpoints previos que migrar ni cifras que contrastar: los
quince son construcción nueva. Y **la mitad ya tiene su sustrato**, porque `dim_unidad` versionada y
`hecho_estado_unidad` se construyeron con el modelo y son exactamente lo que pide el bloque de flota.

El enfoque es el mismo que en Emergencias, deliberadamente: **un catálogo de consultas SQL**, **un
repositorio de lectura compartido** y **endpoints en la app de informes tácticos ya existente**.
Ninguna de las tres piezas se inventa aquí — se reutilizan, y ese es el punto: el segundo
departamento debe costar menos que el primero, o el modelo no está cumpliendo su promesa.

### Las dos ampliaciones que importan

**Versionar la región** (FR-032 a FR-035) es la más delicada, y **no requiere código nuevo**: el
versionado de `dags/lib/dimensiones/versionado.py` ya resuelve exactamente este caso —estado actual
sin historial— y está probado con la unidad. Aquí se aplica a otra entidad.

**Es la segunda vez que se usa, y esa es la prueba real de que el mecanismo es genérico.** Si hubiera
que tocarlo para que sirviera a la región, no era un mecanismo: era una solución particular con
nombre general.

## Technical Context

**Language/Version**: Python 3.12 (contenedor Airflow) y Python 3.13 (backend Django)

**Primary Dependencies**: Django 5 + DRF, `requests` contra la interfaz HTTP del almacén. **Sin
dependencias nuevas.**

**Storage**: ClickHouse 24.8, base `tsi_tactico` — solo lectura desde el backend.

**Testing**: pytest. Suites actuales: backend 1 673, `dags/` 151.

**Target Platform**: Linux en contenedor; stack táctico con `docker/docker-compose.tactico.yml`.

**Project Type**: servicio web de lectura sobre un almacén analítico.

**Performance Goals**: irrelevantes por volumen —2 regiones, 18 unidades, 45 transiciones— pero las
consultas se escriben con el mismo particionado y las mismas reglas, porque el volumen que importa es
el que habrá, no el de hoy.

**Constraints**:
- **Solo lectura**, sin datos sensibles, sin tabla por informe.
- Versión final obligatoria en dimensiones y hechos acumulados; **prohibida** en los de transacción.
- **No depender del catálogo de estados de unidad**, que está incompleto.

**Scale/Scope**: 15 informes, 3 objetivos tácticos (OT11–OT13), sobre un departamento cuyos
volúmenes son hoy de dos dígitos.

## Constitution Check

*GATE: debe pasar antes de la fase 0 y volver a comprobarse tras la fase 1.*

| Principio | Cómo lo cumple | Estado |
|---|---|---|
| **I. Idoneidad funcional como contrato** | Los 15 salen del catálogo trazado a OT y origen, incluidos 3 BSC y 2 CU-T. Cada FR es verificable con una consulta | ✅ |
| **II. Fiabilidad operativa** | Lectura sobre un almacén separado; no toca el camino crítico | ✅ |
| **III. Eficiencia en tiempo real** | No aplica. Aun así, hechos particionados y atributos frecuentes copiados | ✅ |
| **IV. Interacción inclusiva** | Frontend fuera de alcance | ⏭️ diferido |
| **V. Seguridad por diseño** | Sin coordenadas ni identidad, sin excepción. **Alcanza al validador de región**, que el catálogo pedía como desglose (FR-021) | ✅ |
| **VI. Compatibilidad API-First** | REST de solo lectura sobre la app y convenciones existentes | ✅ |
| **VII. Mantenibilidad estructural** | El segundo departamento reutiliza catálogo, repositorio, permisos y versionado. **Cero piezas nuevas de infraestructura** | ✅ |
| **VIII. Flexibilidad multi-región** | **Es el departamento de este principio.** La dimensión de región versionada es su expresión directa | ✅ |

**Mecanismo de desempate aplicado.** Un choque, idéntico al de Emergencias: el catálogo pide «tasa de
aprobación por región **y validador**», y el validador es identidad de persona. Precedencia a
Seguridad: se entrega **por región** (FR-021). Registrado en *Complexity Tracking*.

**Sin violaciones que justificar.**

## Project Structure

### Documentation (this feature)

```text
specs/002-tactico/Red-Operativa/informes-compuestos-modelo/
├── informes-compuestos-modelo.md
└── backend/
    ├── spec.md
    ├── plan.md
    ├── research.md
    ├── data-model.md
    ├── quickstart.md
    ├── contracts/
    │   ├── informes-compuestos-red-operativa.openapi.yaml
    │   └── catalogo-consultas.md
    ├── checklists/requirements.md
    └── tasks.md
```

### Source Code (repository root)

```text
dags/lib/
├── consultas/
│   ├── emergencias/                            # ya existe
│   └── red_operativa/                          # ← nuevo: los 15 de este módulo
│       ├── ot11_*.sql
│       ├── ot12_*.sql
│       └── ot13_*.sql
├── dimensiones/
│   ├── versionado.py                           # ← se REUTILIZA sin tocar
│   ├── dim_region.py                           # ← nuevo, versionada
│   └── dim_condado_vecino.py                   # ← nuevo
├── hechos/
│   ├── hecho_baja_unidad.py                    # ← nuevo
│   └── hecho_validacion_region.py              # ← nuevo
├── ddl.py                                      # ← 2 dimensiones + 2 hechos
├── dimensiones_tasks.py                        # ← añadir las 2 dimensiones al flujo existente
├── hecho_baja_unidad_tasks.py                  # ← nuevo
└── hecho_validacion_region_tasks.py            # ← nuevo

dags/etl/
├── dag_dimensiones.py                          # ← sin cambios de estructura
├── dag_hecho_baja_unidad.py                    # ← nuevo
└── dag_hecho_validacion_region.py              # ← nuevo

backend/apps/informes_tacticos/
├── services/red_operativa_compuestos_service.py    # ← nuevo
├── views/red_operativa_compuestos_views.py         # ← nuevo
└── urls.py                                          # ← añadir rutas
```

**Structure Decision**: se **reutiliza todo lo construido para Emergencias** — el cargador de
consultas, `modelo_repository.py`, la envoltura de respuesta, la resolución de período y el
versionado de dimensiones. Lo único propio de este departamento son **sus consultas, sus dos
dimensiones, sus dos hechos y sus endpoints**.

**Las dos dimensiones nuevas entran en el flujo de dimensiones que ya existe**, no en uno propio.
Un flujo por dimensión reintroduciría, con otro nombre, el problema del flujo por informe.

## Complexity Tracking

| Violación | Por qué es necesaria | Alternativa más simple, y por qué se rechazó |
|---|---|---|
| **Versionar la región** para 2 informes | El origen guarda el estado actual y nunca cuándo cambió; sin versionado, #14 y #15 no existen | *Dejarlos fuera de alcance* — descartado por el usuario. *Guardar solo el estado actual* — es lo que hace el origen, y es la causa del problema |
| **Dos hechos nuevos** —baja de unidad y validación de región— para 6 informes | Ambos tienen instante propio y grano que no es el de ninguna entidad ya modelada | *Métricas en una dimensión* — perdería el instante, que es justo lo que miden la rotación y la tasa de aprobación |
| **El informe #11 entrega menos de lo que pide el catálogo** (por región, no por validador) | El validador es identidad de persona | *Entregarlo completo* — rompe una exclusión constitucional, igual que el técnico de campo en Emergencias |
| **Los estados de unidad se agrupan por texto**, no uniendo con su catálogo | El catálogo del origen **no define el estado 4**, usado en 6 de 45 transiciones | *Unir con el catálogo* — es lo correcto en teoría y aquí **pierde el 13 % de los datos en silencio** |

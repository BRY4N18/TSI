# Implementation Plan: Informes Compuestos de Partners y API sobre el Modelo Analítico

**Branch**: `002-tactico/Partners-API/informes-compuestos-modelo/backend` | **Date**: 2026-08-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-tactico/Partners-API/informes-compuestos-modelo/backend/spec.md`

## Summary

**13 informes agregados en alcance de los 14 del catálogo**, cada uno una consulta sobre el modelo.

| | |
|---|--:|
| Informes en catálogo | 14 |
| **En alcance** | **13** |
| Ya construidos, en la app de partners | **2** |
| Tablas nuevas en el modelo | **5** |
| Tablas que reutiliza de otros módulos | **2** |

**Es el primer departamento que reutiliza tablas de otro módulo compuesto**: `dim_cliente` y
`hecho_factura` los creó Suscripciones. No se recrean — se usan. Es la primera prueba de que las
dimensiones conformadas del modelo funcionan entre departamentos.

**Y cierra una dependencia abierta**: aquí se construye el hecho de llamadas API del que Suscripciones
se abstuvo deliberadamente, para no decidir por este departamento.

### Las tres decisiones que dan forma al plan

**Una sola fuente de consumo.** El sistema operativo tiene dos que difieren en un orden de magnitud;
manda el detalle, y **la preagregada no se carga al modelo**. Tenerla al lado sería una invitación a
usarla el día que el detalle diera un número incómodo.

**La p95 se calcula al consultar.** Es exactamente lo que una agregación previa impide, y el motivo
de que la métrica actual solo dé media.

**El motivo de inactividad de una credencial se deriva de la bitácora al cargar**, porque la
credencial no lo guarda: revocada, en cascada y expirada son indistinguibles en ella.

## Technical Context

**Language/Version**: Python 3.12 (Airflow) y Python 3.13 (Django)

**Primary Dependencies**: Django 5 + DRF, `requests` contra la interfaz HTTP del almacén. **Sin
dependencias nuevas.**

**Storage**: ClickHouse 24.8, base `tsi_tactico` — solo lectura desde el backend.

**Testing**: pytest. Suites actuales: backend 1 673, `dags/` 151.

**Target Platform**: Linux en contenedor; stack táctico con `docker/docker-compose.tactico.yml`.

**Project Type**: servicio web de lectura sobre un almacén analítico.

**Performance Goals**: el hecho de llamadas es el que más crecerá de todo el modelo —una fila por
petición—, así que su particionado mensual importa más aquí que en ningún otro departamento, aunque
hoy tenga 18 filas.

**Constraints**:
- **Solo lectura**, sin tabla por informe.
- ⚠️ **Sin secretos de autenticación, sin contacto técnico y sin IP de origen.**
- **Una sola fuente de consumo**: el detalle.
- Versión final obligatoria en dimensiones; **prohibida** en los dos hechos, ambos de transacción.

**Scale/Scope**: 13 informes, 3 objetivos tácticos, **4 indicadores BSC**, sobre 18 llamadas
registradas.

## Constitution Check

*GATE: debe pasar antes de la fase 0 y volver a comprobarse tras la fase 1.*

| Principio | Cómo lo cumple | Estado |
|---|---|---|
| **I. Idoneidad funcional como contrato** | 13 de los 14 del catálogo, con el que falta **declarado y justificado**. Corrige además el defecto documentado de las métricas actuales: latencia solo media | ✅ |
| **II. Fiabilidad operativa** | Lectura sobre un almacén separado; no toca el camino de la API productiva | ✅ |
| **III. Eficiencia en tiempo real** | No aplica al camino crítico. El hecho de llamadas es el de mayor crecimiento del modelo, y va particionado por mes | ✅ |
| **IV. Interacción inclusiva** | Frontend fuera de alcance | ⏭️ diferido |
| **V. Seguridad por diseño** | ⚠️ **Es el departamento con los secretos del sistema**: hash de credencial, contacto técnico e **IP de origen de cada llamada**. **Nada entra al modelo**. La IP identifica a un consumidor concreto y ningún informe la necesita | ✅ |
| **VI. Compatibilidad API-First** | Es el departamento **de** la API. Sus informes miden la adopción del contrato, que es el principio medido sobre sí mismo | ✅ |
| **VII. Mantenibilidad estructural** | Cinco tablas nuevas, **dos reutilizadas de otro módulo**, cero plomería nueva | ✅ |
| **VIII. Flexibilidad multi-región** | Los partners se agregan por plan y cliente, sin atarse a geografía | ✅ |

**Mecanismo de desempate aplicado.** Dos choques:

1. **Idoneidad frente a corrección**: el catálogo pide «alcance efectivo vs contratado», y el log no
   registra la zona. Se retira del alcance en vez de inferirla — una inferencia que **falla en
   silencio** no es idoneidad, es apariencia de ella.
2. **Idoneidad frente a Seguridad**: la bitácora registra **quién** ejecutó cada cambio de acceso, y
   el catálogo pide la tasa de rechazo «y sus motivos». Se entrega **por motivo, no por persona**.
   **Cuarta vez** que aparece este choque en la serie, y la cuarta con la misma resolución.

**Sin violaciones que justificar.**

## Project Structure

### Documentation (this feature)

```text
specs/002-tactico/Partners-API/informes-compuestos-modelo/
├── informes-compuestos-modelo.md
└── backend/
    ├── spec.md
    ├── plan.md
    ├── research.md
    ├── data-model.md
    ├── quickstart.md
    ├── contracts/
    │   ├── informes-compuestos-partners.openapi.yaml
    │   └── catalogo-consultas.md
    ├── checklists/requirements.md
    └── tasks.md
```

### Source Code (repository root)

```text
dags/lib/
├── consultas/
│   └── partners/                               # ← nuevo: los 13 de este módulo
│       ├── ot08_*.sql
│       ├── ot09_*.sql
│       └── ot10_*.sql
├── dimensiones/
│   ├── dim_partner.py                          # ← nuevo, sin contacto técnico
│   ├── dim_credencial_api.py                   # ← nuevo, sin secreto
│   └── dim_version_contrato.py                 # ← nuevo
├── hechos/
│   ├── hecho_llamada_api.py                    # ← nuevo, SIN IP de origen
│   └── hecho_cambio_acceso.py                  # ← nuevo, derivado de la bitácora
├── ddl.py                                      # ← 3 dimensiones + 2 hechos
├── dimensiones_tasks.py                        # ← añadir las 3 dimensiones al flujo existente
├── hecho_llamada_api_tasks.py                  # ← nuevo
└── hecho_cambio_acceso_tasks.py                # ← nuevo

dags/etl/
├── dag_hecho_llamada_api.py                    # ← nuevo
└── dag_hecho_cambio_acceso.py                  # ← nuevo

backend/apps/informes_tacticos/
├── services/partners_compuestos_service.py     # ← nuevo
├── views/partners_compuestos_views.py          # ← nuevo
└── urls.py                                     # ← añadir rutas
```

**Structure Decision**: se reutiliza toda la plomería de Emergencias, y **dos tablas de
Suscripciones** —`dim_cliente` y `hecho_factura`—.

⚠️ **Los dos informes ya construidos viven en la app de partners, no en la de informes tácticos.**
Este módulo **no los toca**: entrega sus equivalentes sobre el modelo y deja los originales
sirviendo. La unificación depende de la misma decisión pendiente que en Emergencias (#20), y hacerla
aquí por adelantado dejaría el tablero de consumo sin fuente mientras tanto.

**El hecho de llamadas se carga con su propio flujo**, separado del de cambios de acceso: es el hecho
que más crecerá del modelo —una fila por petición— y su cadencia de carga no tiene por qué ser la de
una bitácora que registra 15 eventos.

## Complexity Tracking

| Violación | Por qué es necesaria | Alternativa más simple, y por qué se rechazó |
|---|---|---|
| **Cinco tablas nuevas** | El dominio de integraciones no toca ninguna tabla del modelo | *Reutilizar `dim_cliente`* — se hace, pero un partner no es un cliente: es su área técnica, con plan y cupos propios |
| **No cargar la tabla preagregada del origen** | Difiere del detalle en un orden de magnitud y hace imposibles tres informes | *Cargar ambas y elegir por informe* — es tener dos verdades con un procedimiento para escoger cuál conviene |
| **Un informe del catálogo se retira** | El log no registra la zona consultada | *Inferirla del endpoint* — falla en silencio y no distingue «fuera de zona» de «no supe leerlo» |
| **Dos endpoints equivalentes conviven** con los ya construidos | Apagarlos dejaría el tablero de consumo sin fuente | *Migrarlos ya* — depende de una decisión de retirada que no es de este módulo |
| **La tasa de rechazo se entrega por motivo, no por persona** | La bitácora registra quién ejecutó cada cambio | *Entregarla por persona* — rompe una exclusión aplicada ya tres veces |

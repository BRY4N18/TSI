# Implementation Plan: Informes Compuestos de Soporte al Cliente sobre el Modelo Analítico

**Branch**: `002-tactico/Soporte-Cliente/informes-compuestos-modelo/backend` | **Date**: 2026-08-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-tactico/Soporte-Cliente/informes-compuestos-modelo/backend/spec.md`

## Summary

**9 informes agregados, cada uno una consulta sobre el modelo**, con el indicador **BSC de
cumplimiento de SLA** que hoy no tiene fuente.

| | |
|---|--:|
| Informes en catálogo | 9 |
| Ya construidos, con defectos | **1** |
| Tablas nuevas en el modelo | **5** |
| Tablas reutilizadas de otros módulos | **2** |

**Es el último departamento operativo, y el único que hereda un historial correcto.** Después de seis
departamentos donde el sistema operativo guardaba el estado actual y nunca cuándo cambió,
`Dim_SLAConfig` **sí versiona**: tiene vigencia desde y hasta, y una configuración cuyo tiempo de
resolución pasó de 86 400 a 7 200 segundos convive con su antecesora cerrada.

### Lo que eso cambia técnicamente

**La dimensión de SLA se carga versionada sin aplicar el mecanismo de versionado.** En `dim_unidad` y
`dim_region` hubo que **construir** la historia y marcarla como no real; aquí **ya existe y es real**.
No hace falta `inicio_es_real`: cada vigencia es un hecho registrado por la operación.

Es la primera vez en la serie que el modelo **solo tiene que respetar** una historia en vez de
inventarla — y respetarla importa: medir un ticket de hace un mes contra el SLA nuevo lo convertiría
de cumplido en **incumplido** sin que hubiera pasado nada.

## Technical Context

**Language/Version**: Python 3.12 (Airflow) y Python 3.13 (Django)

**Primary Dependencies**: Django 5 + DRF, `requests` contra la interfaz HTTP del almacén. **Sin
dependencias nuevas.**

**Storage**: ClickHouse 24.8, base `tsi_tactico` — solo lectura desde el backend.

**Testing**: pytest. Suites actuales: backend 1 673, `dags/` 151.

**Target Platform**: Linux en contenedor; stack táctico con `docker/docker-compose.tactico.yml`.

**Performance Goals**: el tablero que se sustituye **lee 100 000 tickets a memoria**. El del modelo
agrega en el almacén y **acepta corte temporal**, así que su coste depende del período pedido y no
del tamaño de la cola.

**Constraints**:
- **Solo lectura**, sin tabla por informe.
- ⚠️ **Sin asunto, descripción, mensajes ni notas internas.**
- **El agente se identifica por su clave**, nunca por su nombre.
- **El SLA vigente al ocurrir el ticket**, nunca el actual.
- Versión final obligatoria en dimensiones y en el hecho de ticket; prohibida en el de acciones.

**Scale/Scope**: 9 informes, 2 objetivos tácticos, **1 indicador BSC**, sobre 14 tickets y 34
acciones.

## Constitution Check

*GATE: debe pasar antes de la fase 0 y volver a comprobarse tras la fase 1.*

| Principio | Cómo lo cumple | Estado |
|---|---|---|
| **I. Idoneidad funcional como contrato** | Los 9 del catálogo, con el BSC de SLA que pasa a ser medible y el tablero corregido en sus dos defectos | ✅ |
| **II. Fiabilidad operativa** | Lectura sobre un almacén separado; no toca la cola real ni el escalado automático | ✅ |
| **III. Eficiencia en tiempo real** | ⚠️ **Es el principio que el tablero actual incumple**: lee 100 000 tickets a memoria. El del modelo agrega en el almacén y acota por período | ✅ |
| **IV. Interacción inclusiva** | Frontend fuera de alcance | ⏭️ diferido |
| **V. Seguridad por diseño** | Los tickets contienen **texto libre escrito por clientes y agentes**, incluidas **notas internas**. Nada de eso entra al modelo: se cuenta y se clasifica | ✅ |
| **VI. Compatibilidad API-First** | REST de solo lectura sobre la app existente | ✅ |
| **VII. Mantenibilidad estructural** | Cinco tablas nuevas, dos reutilizadas, cero plomería nueva. **Séptimo departamento consecutivo sin inventar infraestructura** | ✅ |
| **VIII. Flexibilidad multi-región** | El SLA se desglosa por plan, no por geografía | ✅ |

**Mecanismo de desempate aplicado.** Dos choques:

1. **Idoneidad frente a Seguridad en el rendimiento por agente.** El informe **necesita señalar a
   alguien** para ser accionable, igual que el de roles incompatibles en Cuentas. Se resuelve con la
   **clave del agente**, nunca su nombre. **Séptima vez** que aparece el choque, y la segunda con
   esta solución.

2. **Idoneidad frente a corrección en el denominador del BSC.** Excluir los tickets sin compromiso es
   correcto y **premia dejar tickets sin clasificar**. Se resuelve publicando la cobertura **en la
   misma fila** (FR-013): el incentivo no desaparece, pero deja de ser invisible.

**Sin violaciones que justificar.**

## Project Structure

### Documentation (this feature)

```text
specs/002-tactico/Soporte-Cliente/informes-compuestos-modelo/
├── informes-compuestos-modelo.md
└── backend/
    ├── spec.md
    ├── plan.md
    ├── research.md
    ├── data-model.md
    ├── quickstart.md
    ├── contracts/
    │   ├── informes-compuestos-soporte.openapi.yaml
    │   └── catalogo-consultas.md
    ├── checklists/requirements.md
    └── tasks.md
```

### Source Code (repository root)

```text
dags/lib/
├── consultas/
│   └── soporte/                                # ← nuevo: los 9 de este módulo
│       ├── ot19_*.sql
│       └── ot20_*.sql
├── dimensiones/
│   ├── dim_sla_config.py                       # ← nueva, VERSIONADA DESDE EL ORIGEN
│   ├── dim_servicio.py                         # ← nueva
│   └── dim_estado_soporte.py                   # ← nueva
├── hechos/
│   ├── hecho_ticket.py                         # ← nuevo, INSTANTÁNEA ACUMULADA
│   └── hecho_accion_ticket.py                  # ← nuevo, SIN mensajes ni notas
├── ddl.py                                      # ← 3 dimensiones + 2 hechos
├── dimensiones_tasks.py                        # ← añadir las 3 al flujo existente
└── hecho_soporte_tasks.py                      # ← nuevo, carga los dos hechos juntos

dags/etl/
└── dag_hecho_soporte.py                        # ← nuevo

backend/apps/informes_tacticos/
├── services/soporte_compuestos_service.py      # ← nuevo
├── views/soporte_compuestos_views.py           # ← nuevo
└── urls.py                                     # ← añadir rutas
```

**Structure Decision**: se reutiliza toda la plomería de Emergencias, y **`dim_cliente` y `dim_plan`
de Suscripciones** para el desglose por plan.

⚠️ **`dim_sla_config` se carga versionada, pero sin usar `versionado.py`.** Ese módulo **construye**
historia comparando el estado actual con el vigente; aquí la historia **ya viene en el origen**, con
sus fechas de vigencia. Aplicarle el mecanismo sería reconstruir lo que ya está — y, peor, produciría
versiones marcadas como no reales cuando sí lo son.

**Los dos hechos se cargan en un solo flujo**: comparten fuente —el ciclo del ticket— y su cadencia
es la misma. Separarlos multiplicaría los DAG sin ganar nada.

**El tablero actual no se toca.** Este módulo entrega su equivalente corregido y deja el original
sirviendo, como en Emergencias y Partners. Su retirada depende de la decisión pendiente #20.

## Complexity Tracking

| Violación | Por qué es necesaria | Alternativa más simple, y por qué se rechazó |
|---|---|---|
| **Cinco tablas nuevas** | El dominio de soporte no toca ninguna tabla del modelo | *Reutilizar dimensiones existentes* — se hace con cliente y plan; ticket, SLA, servicio y estado no tienen equivalente |
| **`hecho_ticket` es instantánea acumulada** | Un ticket es un proceso con hitos —creación, primera respuesta, resolución, cierre— que avanzan | *Hecho de transacción por acción* — obligaría a reconstruir el estado de cada ticket en cada consulta, que es lo que el tablero actual hace mal |
| **`dim_sla_config` versionada sin el mecanismo de versionado** | El origen ya guarda la vigencia | *Aplicar `versionado.py`* — reconstruiría una historia que ya existe y la marcaría como no real |
| **Un informe se entrega materialmente vacío** | `idservicio` es nulo en los 14 tickets | *Retirarlo del alcance* — el informe es correcto y el dato llegará; devolverá «sin servicio: 14» y lo declarará |
| **El agente se identifica por su clave** | El informe de rendimiento debe ser accionable | *Agregarlo sin identificar* — no serviría para gestionar un equipo. *Dar el nombre* — rompe la exclusión de identidad |

# Implementation Plan: Informes Compuestos de Cuentas y Clientes sobre el Modelo Analítico

**Branch**: `002-tactico/Cuentas-Clientes/informes-compuestos-modelo/backend` | **Date**: 2026-08-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-tactico/Cuentas-Clientes/informes-compuestos-modelo/backend/spec.md`

## Summary

**9 informes agregados, cada uno una consulta sobre el modelo**, con **dos indicadores BSC** que hoy
no tienen fuente: el churn por cohorte y el tiempo de onboarding.

| | |
|---|--:|
| Informes que ya existen | **0** |
| Tablas nuevas en el modelo | **4** |
| Tablas **ampliadas** de otro módulo | **1** |

**Es el módulo que cierra el experimento de las dimensiones conformadas.** `dim_cliente` la creó
Suscripciones porque fue quien primero la necesitó; su **dueño natural** llega el sexto y **la
amplía sin rehacer nada**. Si hubiera tenido que recrearla, el modelo compartido no habría
funcionado — habría producido dos verdades sobre el mismo cliente.

### Las tres decisiones que dan forma al plan

**El abandono se mide por ausencia.** El onboarding solo registra lo que se completó, así que el
embudo se deduce comparando contra un **catálogo explícito de etapas esperadas**. Es un patrón nuevo
en la serie, y su trampa está en el catálogo: si se infiriera de lo observado, **la etapa que nadie
ha completado nunca desaparecería del embudo** — y es justo la que hay que arreglar.

**Las sesiones son eventos, no intervalos.** 513 inicios frente a 195 cierres: la duración media se
calcula solo sobre las cerradas, y las abiertas se cuentan aparte.

**La pertenencia se usa con su cobertura declarada.** El 9,5 % de los usuarios tiene organización
conocida, y los informes lo dicen — sin ese número, «1 de 10 usuarios» se lee como ocupación real.

## Technical Context

**Language/Version**: Python 3.12 (Airflow) y Python 3.13 (Django)

**Primary Dependencies**: Django 5 + DRF, `requests` contra la interfaz HTTP del almacén. **Sin
dependencias nuevas.**

**Storage**: ClickHouse 24.8, base `tsi_tactico` — solo lectura desde el backend.

**Testing**: pytest. Suites actuales: backend 1 673, `dags/` 151.

**Target Platform**: Linux en contenedor; stack táctico con `docker/docker-compose.tactico.yml`.

**Project Type**: servicio web de lectura sobre un almacén analítico.

**Performance Goals**: `Fact_Session` es la mayor fuente de este departamento —718 filas— y la que
crecerá con cada inicio de sesión. El cálculo de **concurrencia por solape de intervalos** es el más
caro del módulo, y por eso su hecho va particionado por mes.

**Constraints**:
- **Solo lectura**, sin tabla por informe.
- ⚠️ **Sin token de sesión, sin identidad de usuario, sin identificador fiscal.**
- **Ampliar `dim_cliente`, nunca recrearla.**
- Versión final obligatoria en dimensiones; **prohibida** en los dos hechos, ambos de transacción.

**Scale/Scope**: 9 informes, 3 objetivos tácticos, **2 indicadores BSC**, sobre 4 clientes, 21
usuarios y 718 eventos de sesión.

## Constitution Check

*GATE: debe pasar antes de la fase 0 y volver a comprobarse tras la fase 1.*

| Principio | Cómo lo cumple | Estado |
|---|---|---|
| **I. Idoneidad funcional como contrato** | Los 9 del catálogo, con dos BSC que pasan a ser medibles. El embudo de abandono **mide lo que dice medir**, pese a que el origen no registre abandonos | ✅ |
| **II. Fiabilidad operativa** | Lectura sobre un almacén separado; no toca autenticación ni sesión real | ✅ |
| **III. Eficiencia en tiempo real** | No aplica. La concurrencia por solape va sobre un hecho particionado | ✅ |
| **IV. Interacción inclusiva** | Frontend fuera de alcance | ⏭️ diferido |
| **V. Seguridad por diseño** | ⚠️ **Es el departamento del control de acceso**: token de sesión, identidad completa —incluidos género y fecha de nacimiento— e identificador fiscal. **Nada entra al modelo.** El informe de roles incompatibles identifica al usuario **por su clave**, y quien deba actuar resuelve la identidad en el sistema operativo, con su propia auditoría | ✅ |
| **VI. Compatibilidad API-First** | REST de solo lectura sobre la app existente | ✅ |
| **VII. Mantenibilidad estructural** | Cuatro tablas nuevas, **una ampliada**, cero plomería nueva | ✅ |
| **VIII. Flexibilidad multi-región** | Las cuentas se agregan por tipo de organización y plan, sin atarse a geografía | ✅ |

**Mecanismo de desempate aplicado.** Un choque, y esta vez con un matiz que no se había dado:

**Idoneidad frente a Seguridad en el informe de roles incompatibles.** El informe **necesita señalar
a un usuario concreto** para ser accionable — no basta con decir «hay 3 combinaciones peligrosas».
Se resuelve identificándolo **por su clave y no por su nombre**: la combinación de roles es el
hallazgo, y quien deba actuar resuelve la identidad en el sistema operativo, **donde ese acceso queda
auditado**. Es la primera vez en la serie que la solución no es agregar, sino **seudonimizar con una
clave que el propio sistema ya usa**.

**Sin violaciones que justificar.**

## Project Structure

### Documentation (this feature)

```text
specs/002-tactico/Cuentas-Clientes/informes-compuestos-modelo/
├── informes-compuestos-modelo.md
└── backend/
    ├── spec.md
    ├── plan.md
    ├── research.md
    ├── data-model.md
    ├── quickstart.md
    ├── contracts/
    │   ├── informes-compuestos-cuentas.openapi.yaml
    │   └── catalogo-consultas.md
    ├── checklists/requirements.md
    └── tasks.md
```

### Source Code (repository root)

```text
dags/lib/
├── consultas/
│   └── cuentas/                                # ← nuevo: los 9 de este módulo
│       ├── ot04_*.sql
│       ├── ot17_*.sql
│       └── ot18_*.sql
├── dimensiones/
│   ├── dim_cliente.py                          # ← AMPLIAR el de Suscripciones, no recrear
│   ├── dim_rol.py                              # ← nuevo
│   ├── dim_etapa_onboarding.py                 # ← nuevo, catálogo EXPLÍCITO de etapas
│   └── dim_usuario_organizacion.py             # ← nuevo, pertenencia sin identidad
├── hechos/
│   ├── hecho_onboarding.py                     # ← nuevo
│   └── hecho_sesion.py                         # ← nuevo, SIN token
├── ddl.py                                      # ← 3 dimensiones + 2 hechos + ALTER de dim_cliente
├── dimensiones_tasks.py                        # ← añadir las 3 dimensiones al flujo existente
├── hecho_onboarding_tasks.py                   # ← nuevo
└── hecho_sesion_tasks.py                       # ← nuevo

dags/etl/
├── dag_hecho_onboarding.py                     # ← nuevo
└── dag_hecho_sesion.py                         # ← nuevo

backend/apps/informes_tacticos/
├── services/cuentas_compuestos_service.py      # ← nuevo
├── views/cuentas_compuestos_views.py           # ← nuevo
└── urls.py                                     # ← añadir rutas
```

**Structure Decision**: se reutiliza toda la plomería de Emergencias.

⚠️ **`dim_cliente` se amplía en su módulo de origen**, `dags/lib/dimensiones/dim_cliente.py`, que creó
Suscripciones. Las columnas nuevas —cohorte de alta, fecha y motivo de baja, etapa de onboarding
derivada— se añaden **sin tocar las que Suscripciones ya usa**, y una prueba comprueba que sus
informes siguen dando las mismas cifras.

**El catálogo de etapas de onboarding es una dimensión propia y explícita.** Podría parecer excesivo
para cinco etapas, y es lo que impide que el embudo se calcule sobre las etapas observadas — donde
**la etapa que nadie ha completado nunca no existiría**.

**Los dos hechos van en flujos separados**: el de sesión crece con cada inicio y el de onboarding con
cada alta. Sus cadencias no tienen por qué coincidir.

## Complexity Tracking

| Violación | Por qué es necesaria | Alternativa más simple, y por qué se rechazó |
|---|---|---|
| **Una dimensión solo para el catálogo de etapas** | El embudo debe mostrar etapas **que nadie ha completado** | *Inferir las etapas de lo observado* — la etapa donde todos abandonan **desaparecería del informe**, que es exactamente el fallo que el embudo existe para detectar |
| **Ampliar una dimensión de otro módulo** | `dim_cliente` es conformada y este departamento es su dueño | *Crear una propia* — dos verdades sobre el mismo cliente. *Dejarla como está* — faltarían cohorte, baja y motivo |
| **Una dimensión de pertenencia con 9,5 % de cobertura** | Dos informes la necesitan y es la única fuente que cuenta usuarios | *Usar el administrador del cliente* — conoce solo al administrador. *Combinar ambas* — mezcla dos conceptos distintos |
| **El usuario se identifica por su clave** en un informe | El informe de roles incompatibles **necesita ser accionable** | *Agregarlo sin identificar* — no sería accionable. *Dar el nombre* — rompe la exclusión de identidad |

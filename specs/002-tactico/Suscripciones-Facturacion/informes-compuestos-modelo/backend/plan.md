# Implementation Plan: Informes Compuestos de Suscripciones y Facturación sobre el Modelo Analítico

**Branch**: `002-tactico/Suscripciones-Facturacion/informes-compuestos-modelo/backend` | **Date**: 2026-08-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-tactico/Suscripciones-Facturacion/informes-compuestos-modelo/backend/spec.md`

## Summary

**13 informes agregados, cada uno una consulta sobre el modelo analítico**, y entre ellos **cinco
indicadores financieros del BSC que hoy no tienen ninguna fuente**.

| | |
|---|--:|
| Informes que ya existen | **0** |
| Tablas nuevas en el modelo | **5** |
| Indicadores BSC que pasan de no medibles a medibles | **5** |

**Es el departamento con el mayor salto de valor y el menor volumen de datos.** MRR, ingresos,
renovación, movimientos de plan y NRR pasan de no existir a estar definidos — y se calcularán sobre
**4 suscripciones y 6 facturas**.

### Lo que distingue técnicamente a este plan

**Su hecho central es una instantánea acumulada, no una transacción.** Una suscripción es un proceso
con hitos —alta, renovación, suspensión, cancelación— igual que un accidente o un despacho. Es el
tercer hecho de ese tipo del modelo, y el patrón ya está construido y probado.

**Y es el primero donde el trabajo importante ocurre al cargar, no al consultar.** Cinco defectos del
origen —estado que miente, motivo que no implica cancelación, vigencia invertida, centinela de plan y
tres formas de decir «sin motivo»— se resuelven **una vez en la carga**. Trece consultas no pueden
acordarse de cinco trampas.

## Technical Context

**Language/Version**: Python 3.12 (Airflow) y Python 3.13 (Django)

**Primary Dependencies**: Django 5 + DRF, `requests` contra la interfaz HTTP del almacén. **Sin
dependencias nuevas.**

**Storage**: ClickHouse 24.8, base `tsi_tactico` — solo lectura desde el backend.

**Testing**: pytest. Suites actuales: backend 1 673, `dags/` 151.

**Target Platform**: Linux en contenedor; stack táctico con `docker/docker-compose.tactico.yml`.

**Project Type**: servicio web de lectura sobre un almacén analítico.

**Performance Goals**: irrelevantes por volumen. Las consultas se escriben con el mismo particionado
porque el volumen que importa es el que habrá.

**Constraints**:
- **Solo lectura**, sin tabla por informe.
- ⚠️ **Sin medios de cobro**: ni token de pasarela, ni últimos dígitos, ni identificador fiscal.
- **Sin desglose por persona** ni textos libres.
- **Sin modelar llamadas API**: pertenecen a Partners.
- Versión final obligatoria en dimensiones y en el hecho de suscripción; prohibida en los otros dos.

**Scale/Scope**: 13 informes, 3 objetivos tácticos, **5 indicadores BSC**, sobre 4 suscripciones y 6
facturas.

## Constitution Check

*GATE: debe pasar antes de la fase 0 y volver a comprobarse tras la fase 1.*

| Principio | Cómo lo cumple | Estado |
|---|---|---|
| **I. Idoneidad funcional como contrato** | Los 13 salen del catálogo trazado. **Cinco indicadores BSC pasan de no medibles a medibles**, que es el mayor salto de idoneidad de la serie | ✅ |
| **II. Fiabilidad operativa** | Lectura sobre un almacén separado; no toca el camino crítico ni el cobro real | ✅ |
| **III. Eficiencia en tiempo real** | No aplica | ✅ |
| **IV. Interacción inclusiva** | Frontend fuera de alcance | ⏭️ diferido |
| **V. Seguridad por diseño** | ⚠️ **Es el departamento con el dato más sensible en términos financieros**: tokens de pasarela, últimos dígitos e identificadores fiscales. **Nada de eso entra al modelo** (FR-032). Se informa **si hay método vigente**, nunca cuál | ✅ |
| **VI. Compatibilidad API-First** | REST de solo lectura sobre la app existente | ✅ |
| **VII. Mantenibilidad estructural** | Cinco tablas nuevas, **cero piezas de plomería nuevas**. Tercer departamento consecutivo sin inventar infraestructura | ✅ |
| **VIII. Flexibilidad multi-región** | Los ingresos se desglosan por plan y tipo de cliente, sin atarse a geografía | ✅ |

**Mecanismo de desempate aplicado.** Dos choques, ambos ya resueltos igual en departamentos
anteriores:

1. **Idoneidad frente a Seguridad**: el catálogo pide el tiempo de resolución «por administrador».
   El administrador es una persona. Se entrega **agregado** (FR-033), como el técnico de campo en
   Emergencias y el validador en Red Operativa. **Tercera vez que aparece el mismo choque**, y la
   tercera con la misma resolución — señal de que la regla está asentada.
2. **Idoneidad frente a corrección**: el catálogo pide la utilización de límites completa, y una de
   sus tres dimensiones pertenece a otro departamento. Se entrega lo medible **declarando lo que
   falta** (FR-029 a FR-031).

**Sin violaciones que justificar.**

## Project Structure

### Documentation (this feature)

```text
specs/002-tactico/Suscripciones-Facturacion/informes-compuestos-modelo/
├── informes-compuestos-modelo.md
└── backend/
    ├── spec.md
    ├── plan.md
    ├── research.md
    ├── data-model.md
    ├── quickstart.md
    ├── contracts/
    │   ├── informes-compuestos-suscripciones.openapi.yaml
    │   └── catalogo-consultas.md
    ├── checklists/requirements.md
    └── tasks.md
```

### Source Code (repository root)

```text
dags/lib/
├── consultas/
│   └── suscripciones/                          # ← nuevo: los 13 de este módulo
│       ├── ot05_*.sql
│       ├── ot06_*.sql
│       └── ot07_*.sql
├── dimensiones/
│   ├── dim_plan.py                             # ← nuevo, con límites desplegados
│   └── dim_cliente.py                          # ← nuevo, sin identificador fiscal
├── hechos/
│   ├── hecho_suscripcion.py                    # ← nuevo, INSTANTÁNEA ACUMULADA
│   ├── hecho_factura.py                        # ← nuevo, transacción
│   └── hecho_solicitud_cambio_plan.py          # ← nuevo, transacción
├── ddl.py                                      # ← 2 dimensiones + 3 hechos
├── dimensiones_tasks.py                        # ← añadir las 2 dimensiones al flujo existente
├── hecho_suscripcion_tasks.py                  # ← nuevo
└── hecho_facturacion_tasks.py                  # ← nuevo (factura + solicitud, misma fuente)

dags/etl/
├── dag_hecho_suscripcion.py                    # ← nuevo
└── dag_hecho_facturacion.py                    # ← nuevo

backend/apps/informes_tacticos/
├── services/suscripciones_compuestos_service.py    # ← nuevo
├── views/suscripciones_compuestos_views.py         # ← nuevo
└── urls.py                                         # ← añadir rutas
```

**Structure Decision**: se reutiliza **toda** la plomería de Emergencias, como en los dos
departamentos anteriores.

**`dim_cliente` se crea aquí aunque el cliente «pertenezca» a Cuentas y Clientes.** Es una dimensión
**conformada**: la necesitan Suscripciones para los ingresos por tipo de cliente, Red Operativa para
los mercados activos y Ventas para cerrar el ciclo de conversión. Crearla en el primer módulo que la
necesita y compartirla es exactamente lo que un modelo en estrella hace; duplicarla por departamento
sería tener tres verdades sobre el mismo cliente.

⚠️ **Cuando se especifique Cuentas y Clientes, la ampliará — no la recreará.**

## Complexity Tracking

| Violación | Por qué es necesaria | Alternativa más simple, y por qué se rechazó |
|---|---|---|
| **Cinco tablas nuevas** para 13 informes | El dominio financiero no toca ninguna tabla del modelo actual | *Reutilizar dimensiones existentes* — ninguna aplica: un plan no es una unidad ni una región |
| **`hecho_suscripcion` es instantánea acumulada**, no transacción | Una suscripción es un proceso con hitos que avanzan; el estado de hoy debe poder actualizarse sin duplicar la fila | *Hecho de transacción por cambio de estado* — obligaría a reconstruir el estado vigente en cada consulta, que es justo lo que el modelo evita |
| **`dim_cliente` se crea en este departamento** y no en el que la «posee» | La necesitan tres departamentos y es la primera vez que hace falta | *Esperar a Cuentas y Clientes* — bloquearía los ingresos por tipo de cliente sin ganar nada. *Una dimensión por departamento* — tres verdades sobre el mismo cliente |
| **El informe #12 entrega dos de sus tres dimensiones** | Las llamadas API pertenecen a Partners | *Modelarlas aquí* — este módulo decidiría el diseño de otro. *Aplazar el informe* — renunciaría a dos dimensiones medibles |
| **El tiempo de resolución se entrega agregado**, no por administrador | Es identidad de persona | *Entregarlo por administrador* — rompería una exclusión constitucional aplicada ya dos veces |

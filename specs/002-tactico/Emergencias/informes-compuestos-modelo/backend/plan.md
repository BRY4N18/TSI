# Implementation Plan: Informes Compuestos de Emergencias sobre el Modelo Analítico

**Branch**: `002-tactico/Emergencias/informes-compuestos-modelo/backend` | **Date**: 2026-08-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-tactico/Emergencias/informes-compuestos-modelo/backend/spec.md`

## Summary

**26 informes agregados de Emergencias, cada uno una consulta sobre el modelo analítico.** Ninguna
tabla por informe, ningún flujo por informe.

El sustrato ya existe y está verificado: 5 dimensiones y 4 hechos cargados el 2026-08-14. **19 de los
26 se sostienen hoy tal cual**; 7 exigen ampliar el modelo con métricas y un hecho de evidencia,
siguiendo el procedimiento del §4.bis de su contrato de esquema.

> ## ⚠️ Corrección de alcance descubierta al planificar
>
> **16 de los 26 informes ya tienen endpoint construido y funcionando.** Los sirve el módulo
> `informes-tacticos-agregados` agregando **directamente contra Pinot** —13 endpoints con `GROUP BY`
> sobre el sistema operativo— más los 3 que ya usan el almacén analítico.
>
> El trabajo real de este módulo **no es construir 26 informes**, sino:
>
> | Bloque | Cuántos | Qué es |
> |---|--:|---|
> | **Construir nuevos** | **10** | No existen en ninguna forma |
> | **Migrar por defecto conocido** | **3** | Funcionan y **dan cifras equivocadas** |
> | **Migrar por consistencia** | **13** | Funcionan y dan cifras correctas |
>
> ### Recomendación: los 13 correctos **no se migran ahora**
>
> Migrar un endpoint que funciona y es correcto es **riesgo de regresión sin valor visible**. Los 13
> agregan sobre una sola tabla de Pinot, que es algo que Pinot hace bien; su límite es que no puede
> unir, y por eso resuelven las etiquetas con búsquedas en memoria.
>
> **Los 3 con defecto sí se migran**, porque el modelo es la única forma de arreglarlos:
>
> - **#3 completitud** — su condición es siempre cierta sobre Pinot, que no tiene nulos sino
>   centinelas. En el modelo la ausencia es ausencia.
> - **#12 ratio demanda/capacidad** — necesita la **capacidad de aquel período**. Pinot solo guarda
>   la flota de hoy; la dimensión versionada del modelo es la única fuente posible.
> - **#14 pérdida de señal** — analiza el 16,9 % de las posiciones por un truncamiento silencioso.
>
> ### El coste de no migrar los 13, dicho explícitamente
>
> Quedan **dos fuentes para la misma pregunta**: el endpoint de Pinot y la consulta del catálogo. Si
> divergen, nadie sabrá cuál creer. Se acota con una prueba de contraste que compara ambas y **falla
> si las cifras difieren** — convirtiendo la convivencia en algo vigilado en vez de en una bomba de
> relojería. Cuando el frontend se replantee, se migran de una vez y la prueba se retira.

El enfoque técnico tiene tres piezas y ninguna es nueva:

1. **Un catálogo de consultas** en `dags/lib/consultas/`, junto a las tres que ya escribió la fase 6
   del modelo. Son ficheros SQL parametrizados: la definición de cada informe vive en un sitio, no
   repartida entre un DAG y un repositorio.
2. **Un repositorio de lectura** que ejecuta esas consultas contra el almacén, con las reglas de
   consumo aplicadas de forma central — sobre todo la que obliga a forzar la versión final.
3. **Endpoints de solo lectura** en la app Django que ya sirve los informes tácticos, reutilizando su
   envoltura de respuesta, su resolución de período y sus permisos.

## Technical Context

**Language/Version**: Python 3.12 (contenedor Airflow) y Python 3.13 (backend Django)

**Primary Dependencies**: Django 5 + DRF (lectura HTTP), `requests` contra la interfaz HTTP nativa
del almacén. **Sin driver nuevo**: se reutiliza `core/clickhouse/client.py`, que ya existe y está
probado.

**Storage**: ClickHouse 24.8, base `tsi_tactico` — **solo lectura desde el backend**. La escritura es
exclusiva de los flujos del modelo.

**Testing**: pytest. Suite del backend (1 673 actuales) y suite de `dags/` (151 actuales).

**Target Platform**: Linux en contenedor; stack táctico levantado con
`docker/docker-compose.tactico.yml`.

**Project Type**: servicio web de lectura sobre un almacén analítico.

**Performance Goals**: cada informe responde con **al menos tres meses de datos** cargados, para que
el particionado se ejercite. Umbral operativo holgado: lo que se vigila es que no haya un recorrido
completo escondido, no milisegundos.

**Constraints**:
- **Solo lectura.** Ningún endpoint escribe en el almacén.
- **Sin datos sensibles**, para ningún rol: ni coordenadas, ni identidad, ni texto libre interno.
- **Sin tabla por informe.** Si falta un dato, se amplía el modelo.
- Toda consulta sobre hecho acumulado o dimensión **fuerza la versión final**.

**Scale/Scope**: 26 informes, 5 objetivos tácticos (OT21–OT25), sobre 4 hechos que hoy suman 67 656
filas y crecen a diario.

## Constitution Check

*GATE: debe pasar antes de la fase 0 y volver a comprobarse tras la fase 1.*

| Principio | Cómo lo cumple este plan | Estado |
|---|---|---|
| **I. Idoneidad funcional como contrato** | Los 26 informes salen del catálogo trazado a OT y a su origen (BSC, CU-T, OP, SRS). Cada FR es verificable con una consulta | ✅ |
| **II. Fiabilidad operativa** | El módulo **no toca el camino crítico**: es lectura sobre un almacén separado del operativo. Si el almacén cae, la operación de emergencias no se entera | ✅ |
| **III. Eficiencia en tiempo real** | No aplica al camino crítico. Aun así, los hechos van particionados por mes y las columnas más agrupadas están copiadas en el hecho | ✅ |
| **IV. Interacción inclusiva** | Capa de frontend fuera de alcance; se aplicará cuando se decida la ubicación en tableros | ⏭️ diferido |
| **V. Seguridad de la información por diseño** | Exclusión **constitucional** de coordenadas, identidad, secretos y texto libre, sin excepción ni para la autoridad departamental (FR-016, FR-034). El modelo ya no contiene esas columnas: no hay que filtrarlas, no existen | ✅ |
| **VI. Compatibilidad API-First** | Endpoints REST de solo lectura sobre la app y las convenciones ya existentes | ✅ |
| **VII. Mantenibilidad como prioridad estructural** | **Es el principio que justifica el módulo entero**: sustituye 26 tablas y 26 flujos por 26 consultas sobre un modelo compartido | ✅ |
| **VIII. Flexibilidad multi-región** | Los informes se desglosan por condado y región desde una dimensión geográfica compartida y conformada | ✅ |

**Mecanismo de desempate aplicado.** Un solo choque real: el informe #20 pedía desglose por técnico
de campo, lo que enfrenta **Idoneidad funcional** (el catálogo lo pide) contra **Seguridad por
diseño** (es identidad de una persona). La constitución da precedencia a Seguridad en su excepción de
dominio, y así se resolvió: el informe se entrega **por unidad** (FR-034). Registrado en
*Complexity Tracking*.

**Sin violaciones que justificar.**

## Project Structure

### Documentation (this feature)

```text
specs/002-tactico/Emergencias/informes-compuestos-modelo/
├── informes-compuestos-modelo.md    # índice del módulo
└── backend/
    ├── spec.md                      # qué y por qué
    ├── plan.md                      # este fichero
    ├── research.md                  # fase 0 — decisiones técnicas
    ├── data-model.md                # fase 1 — los 26 informes y lo que el modelo debe añadir
    ├── quickstart.md                # fase 1 — cómo verificarlo
    ├── contracts/
    │   ├── informes-compuestos-emergencias.openapi.yaml
    │   └── catalogo-consultas.md    # definición canónica de los 26 informes
    ├── checklists/requirements.md
    └── tasks.md                     # lo genera /speckit-tasks
```

### Source Code (repository root)

```text
dags/lib/
├── consultas/                                  # el catálogo de consultas
│   ├── perdida_senal.sql                       # ya existe (fase 6 del modelo)
│   ├── indice_calidad.sql                      # ya existe
│   ├── rendimiento_proveedor.sql               # ya existe
│   └── emergencias/                            # ← nuevo: los 26 de este módulo
│       ├── ot21_*.sql
│       ├── ot22_*.sql
│       ├── ot23_*.sql
│       ├── ot24_*.sql
│       └── ot25_*.sql
├── hechos/
│   ├── hecho_accidente.py                      # ← añadir métricas de FR-024, 026, 028
│   └── hecho_evidencia.py                      # ← nuevo, para FR-025 y FR-034
├── ddl.py                                      # ← columnas nuevas + tabla de evidencia
└── hecho_evidencia_tasks.py                    # ← nuevo flujo

dags/etl/dag_hecho_evidencia.py                 # ← nuevo DAG

backend/
├── core/repositories/informes_tacticos/
│   └── modelo_repository.py                    # ← nuevo: ejecuta las consultas del catálogo
├── apps/informes_tacticos/
│   ├── services/emergencias_compuestos_service.py   # ← nuevo
│   ├── views/emergencias_compuestos_views.py        # ← nuevo
│   └── urls.py                                      # ← añadir rutas
└── apps/informes_tacticos/tests/                    # pruebas por capa
```

**Structure Decision**: se **extiende la app `informes_tacticos` existente** en lugar de crear una
nueva. Ya tiene envoltura de respuesta (`envelope.py`), resolución de período (`periodo.py`),
permisos (`permissions.py`) y una base de vistas (`views/base.py`) construidas y probadas para
exactamente este tipo de informe. Crear una app paralela duplicaría las cuatro y garantizaría que
divergieran.

**Las consultas viven en `dags/lib/consultas/` y no en el backend** a propósito: son la definición
canónica de cada informe, y ahí quedan **junto al modelo que consultan**. Si vivieran en el
repositorio de Django, la definición del informe y el esquema que la sostiene evolucionarían en
repositorios mentales distintos — que es como se llega a que dos informes midan lo mismo y no
coincidan.

## Complexity Tracking

| Violación | Por qué es necesaria | Alternativa más simple, y por qué se rechazó |
|---|---|---|
| **Ampliar el modelo con 1 hecho y 5 métricas** para cubrir 7 informes | Sin ellas, 7 de los 26 informes no son calculables desde el modelo | *Crear una tabla por informe para esos 7* — es exactamente el diseño que este módulo sustituye. *Dejarlos fuera de alcance* — son informes del catálogo con origen trazado, incluido un BSC |
| **El informe #16 usa una estimación derivada** que el sistema operativo no guarda | El catálogo lo pide y el usuario decidió construirla (opción C) | *Dejarlo fuera de alcance* — se descartó explícitamente. El riesgo de presentar un cálculo propio como compromiso operativo se acota con FR-032 (etiquetado obligatorio) y FR-031 (sin referencia ⇒ sin dato, nunca cero) |
| **El informe #20 entrega menos de lo que pide el catálogo** (por unidad, no por técnico) | El desglose por persona es identidad, excluida sin excepciones | *Entregarlo completo* — rompería una exclusión constitucional. *Seudonimizar* — quien tenga acceso al sistema operativo puede reidentificar, así que solo aparenta resolverlo |

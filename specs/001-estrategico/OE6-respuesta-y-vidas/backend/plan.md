# Implementation Plan: OE6 — Reducción del Tiempo de Respuesta y Seguridad de Vidas

**Branch**: `001-estrategico/OE6-respuesta-y-vidas/backend` | **Date**: 2026-08-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-estrategico/OE6-respuesta-y-vidas/backend/spec.md`

---

## Summary

Doce informes estratégicos sobre el tiempo entre el reporte de una emergencia y la atención en sitio,
resueltos **con una consulta cada uno** sobre el modelo analítico existente. Es el módulo piloto de la
capa estratégica: la forma que fije la copian los otros cinco OE.

**El trabajo no es aritmética.** El módulo táctico de Emergencias ya construyó 26 consultas sobre el
mismo modelo, y **diez de los doce informes tienen una consulta de la que partir** (research D8). Lo
que esta capa añade son cuatro cosas que la táctica no hace: **percentil** en vez de promedio,
**ventana comparada**, **granularidad** configurable y **contraste contra la meta** del BSC.

**Dos correcciones de alcance salieron de la investigación**, ambas verificadas contra datos reales:

1. **El eje de región no es construible** y `FR-OE6-008` se corrige. No falta cargarlo: falta la
   relación región↔condado **en el sistema operativo**. Se agrupa por condado.
2. **Ningún informe de OE6 puede semaforizarse todavía.** Sus metas son todas `[CALIBRAR]`; las
   `[NORMATIVO]` pertenecen a OE3. Todos los `cumple` salen `null`, y la primera lectura de estos
   informes es lo que producirá la línea base que falta.

---

## Technical Context

**Language/Version**: Python 3.11 (Django) para la capa HTTP · SQL de ClickHouse para las consultas

**Primary Dependencies**: Django + DRF · `core/pinot` **no interviene** — esta capa lee solo el
almacén analítico · `clickhouse_http_client` desde los DAG, `ModeloRepository` desde Django

**Storage**: ClickHouse, base `tsi_tactico`, **13 tablas**. Se leen cinco: `hecho_accidente`,
`hecho_despacho`, `hecho_evidencia`, `dim_severidad`, `dim_geografia`. **No se crea ninguna.**

**Testing**: pytest. Pruebas de contrato por endpoint, de permisos, y **de contraste contra la capa
táctica** (`SC-007`), que es el mecanismo que ya encontró tres defectos reales en el módulo anterior

**Target Platform**: Contenedor `accidentes-django`, tras `docker compose -f docker/accidentes.yml`

**Project Type**: Servicio web de solo lectura — doce endpoints `GET`

**Performance Goals**: Toda consulta filtra por `fecha` para descartar particiones (Regla 7). Con
comparación son **dos ejecuciones** de la misma consulta, no una consulta el doble de compleja

**Constraints**:
- Período **obligatorio**; sin paginación por cursor
- Sin dato sensible, **tampoco para la autoridad departamental**
- Sin acotamiento por titularidad: `meta.acotado_a` no se emite
- `cumple` es `null` en todo objetivo `CALIBRAR`

**Scale/Scope**: 12 informes · 4 252 casos y 4 314 intentos de despacho hoy · histórico
2026-02-03 → 2026-08-13 (**~6 meses: `yoy` sin término de comparación**)

---

## Constitution Check

*GATE: debe pasar antes de Phase 0. Re-evaluado tras Phase 1.*

| Principio | Cómo se cumple | |
|---|---|:--:|
| **I. Idoneidad funcional como contrato** | Los doce salen del catálogo con origen trazado a **CU-E08** y al BSC. Las **cinco discrepancias** del catálogo se corrigieron contra el modelo real en vez de heredarse, y una sexta —el eje de región— se declaró no construible con su prerrequisito nombrado | ✅ |
| **II. Fiabilidad operativa** | No aplica a la cadena crítica: **este módulo no participa en el despacho**, solo lo mide. Su indisponibilidad no retrasa ninguna ambulancia | ⚪ |
| **III. Eficiencia en tiempo real** | Tampoco toca la ruta crítica. La Regla 7 (filtrar particiones) es la única exigencia, y es de degradación futura, no de latencia de emergencia | ✅ |
| **IV. Capacidad de interacción** | **No aplica en esta capa.** Frontend en `../frontend/` (implementado) | ⚪ |
| **V. Seguridad de la información** | `FR-OE6-009` y `FR-OE6-010`: exclusión constitucional aplicada **también a la autoridad**, y lista blanca de columnas en el repositorio. La comprobación 2.13 del quickstart se hace con el rol de máxima autoridad, no con uno acotado | ✅ |
| **VI. Compatibilidad API-first** | Contrato OpenAPI versionado, bajo el envelope común del contrato estratégico | ✅ |
| **VII. Mantenibilidad estructural** | Es el eje del plan: se reutiliza el lector de catálogo, el `ModeloRepository`, el envelope y el patrón `CATALOGO`/`PUBLICADOS`. **Ver el trade-off de abajo** | ⚠️ |
| **VIII. Flexibilidad multi-región** | ⚠️ **Aquí el módulo entrega menos de lo que el objetivo pide**, y no por decisión propia: el eje de región no existe en el modelo operativo. Se declara en vez de simularse | ⚠️ |
| **IX. Seguridad física (Safety)** | Es la razón de ser del OE. Tres decisiones de diseño salen directamente de aquí: **percentil y no promedio** (un promedio bueno esconde el uno de cada veinte que espera el triple), **un caso sin llegada no vale cero** (contarlo así haría instantáneos los casos que nadie atendió), y **descartados y fusionados fuera** de todo denominador | ✅ |

### Trade-off invocado — Mantenibilidad frente a riesgo de regresión

**Es el único conflicto real del plan**, y el Tie-Breaker exige documentarlo.

- **En conflicto:** *Mantenibilidad* —una sola definición de cada métrica— contra *Fiabilidad* de lo
  ya entregado: parametrizar las consultas tácticas para compartirlas tocaría **13 endpoints
  publicados y verificados** (T076, nueve comprobaciones en verde).
- **Qué se priorizó y bajo qué regla:** no hay Safety en juego —ninguno de los dos caminos afecta a
  una emergencia activa—, así que rige la regla 2: *Mantenibilidad y Idoneidad por defecto*. Pero
  aquí **las dos opciones son la mantenibilidad**: compartir el fichero la sirve a largo plazo;
  no romper trece informes correctos la sirve hoy.
- **Lo aceptado:** consultas propias en `estrategicos/oe6/`, con **prueba de contraste** que falla si
  las capas divergen (`SC-007`). Es el mismo mecanismo que el módulo táctico ya usa para sus 13
  informes vigilados, y **encontró tres defectos reales** (#34, #35, #36).
- **Impacto y regla de salida:** el coste es que una corrección futura hay que aplicarla en dos
  sitios. Si el contraste llega a fallar por eso, **la salida es promover la medida a fichero
  compartido, no ampliar la tolerancia de la prueba**.

### La limitación de Flexibilidad, declarada

`FR-OE6-008` pedía agrupación por región y **se corrige a condado**. No es una simplificación por
conveniencia: la relación región↔condado no existe en el sistema operativo, y las dos alternativas
—unir por estado, o tomar la primera región del estado— producen cifras **falsas que no fallan**
(research D1).

Es una excepción al Principio VIII y por tanto **lleva condición de revisión**: se levanta el día que
exista una tabla puente región↔condado. Afecta igual a OE3, cuyos E3-01 a E3-08 piden el mismo eje.

---

## Project Structure

### Documentation (this feature)

```text
specs/001-estrategico/OE6-respuesta-y-vidas/
├── OE6-respuesta-y-vidas.md          # Índice del módulo (no README)
└── backend/
    ├── spec.md                        # Qué y por qué
    ├── plan.md                        # Este fichero
    ├── research.md                    # Phase 0 — 9 decisiones, verificadas contra el stack
    ├── data-model.md                  # Phase 1 — los 12 informes: grano, fuente, medidas
    ├── quickstart.md                  # Phase 1 — 15 comprobaciones
    ├── contracts/
    │   └── informes-estrategicos-oe6.openapi.yaml
    ├── checklists/requirements.md
    └── tasks.md                       # Phase 2 — lo crea /speckit-tasks
```

### Source Code (repository root)

```text
backend/apps/informes_estrategicos/        # App nueva
├── periodo_estrategico.py                 # Ventanas, granularidad, comparación — TRANSVERSAL a los 6 OE
├── objetivo.py                            # Metas BSC, NORMATIVO vs CALIBRAR — TRANSVERSAL
├── envelope.py                            # meta.periodo / comparacion / objetivo / cobertura
├── permissions.py                         # DirectorOperaciones + Gerente, sin acotamiento
├── urls.py · apps.py
├── services/oe6_service.py                # CATALOGO + PUBLICADOS + parámetros por informe
└── views/oe6_views.py

backend/core/repositories/informes_estrategicos/
└── modelo_estrategico_repository.py       # Envuelve ModeloRepository con la doble ventana

dags/lib/consultas/estrategicos/oe6/       # Las 12 consultas
├── e6_01_tiempo_respuesta_global.sql      ← nueva
├── e6_02_tiempo_respuesta_por_severidad.sql
├── e6_03_tramos_del_ciclo.sql             ← nueva
├── e6_04_origen_de_asignacion.sql
├── e6_05_rechazo_y_timeout_por_unidad.sql
├── e6_06_abortos_y_misiones_fallidas.sql
├── e6_07_desviacion_de_llegada.sql
├── e6_08_impacto_humano.sql
├── e6_09_cierres_forzados.sql
├── e6_10_envejecimiento_casos_abiertos.sql
├── e6_11_escaladas_de_severidad.sql
└── e6_12_cobertura_de_evidencia.sql

backend/apps/informes_estrategicos/tests/
├── api/            # contrato por endpoint + permisos
├── unit/           # ventanas, granularidad, objetivo
└── contraste/      # SC-007: estratégico vs táctico
```

**Structure Decision**: app Django nueva, `informes_estrategicos`, espejo estructural de
`informes_tacticos`.

**No dentro de `informes_tacticos`** porque su nombre pasaría a mentir y su `permissions.py` resuelve
acotamiento por titularidad, que en esta capa no existe. **No repartida por app de departamento**
porque un OE cruza departamentos: OE6 no lo hace, pero es el piloto y OE1 cruza tres.

`periodo_estrategico.py` y `objetivo.py` viven en la **raíz de la app**, no bajo `oe6`: son
transversales a los seis objetivos y nacen aquí solo porque este es el primero.

Las consultas viven junto al modelo que consultan, en `dags/`, y Django las **lee** vía
`settings.CONSULTAS_DIR`. El único escritor del almacén sigue siendo Airflow.

---

## Constitution Re-Check (post-Phase 1)

Tras el diseño, **ningún gate cambió de estado**. Dos observaciones:

- **Principio V se reforzó** al escribir el contrato: `meta.alcance` obliga a E6-09 a declarar qué
  mide, lo que evita que una limitación derivada de la exclusión de identidad se lea como una cifra
  buena.
- **Principio I se reforzó** al medir: `retiro_forzado = 1` frente a los 451 de la definición pedida
  confirma que sin la declaración el informe sería engañoso, no solo incompleto.

---

## Complexity Tracking

| Violación | Por qué es necesaria | Alternativa más simple, y por qué se rechaza |
|---|---|---|
| **Consultas propias en vez de compartir fichero con la capa táctica** | Las tácticas fijan la granularidad a mes por diseño y no calculan percentiles. Compartirlas obliga a modificar 13 endpoints publicados y verificados | *Parametrizar las tácticas*: una regresión ahí es un informe en producción que empieza a mentir, para ganar algo que una prueba de contraste ya garantiza |
| **App Django nueva** | La capa no tiene acotamiento por titularidad y sus parámetros de período son otros | *Ampliar `informes_tacticos`*: su nombre dejaría de describir lo que contiene, y su módulo de permisos mezclaría dos modelos de acceso incompatibles |
| **Dos ejecuciones por petición cuando hay comparación** | Mantiene la consulta idéntica en forma a la táctica, que es lo que hace posible el contraste de `SC-007` | *Las dos ventanas en un `CASE`*: duplica cada expresión de percentil y rompe la comparabilidad fila a fila con la capa táctica |

---

## Riesgos

| Riesgo | Señal temprana | Mitigación |
|---|---|---|
| **Se reimplementan las consultas tácticas en vez de partir de ellas** | Una consulta estratégica que no se parece a su equivalente táctica | `SC-007` y las pruebas de `tests/contraste/` |
| **El p95 se publica con muestras diminutas** | Un p95 idéntico al máximo | Comprobación 2.3 del quickstart |
| **Alguien "arregla" el eje de región uniendo por estado** | Los totales se doblan y cada región muestra el total completo | Documentado en research D1, data-model §5 y en el contrato |
| **Se pinta un semáforo sobre un `[CALIBRAR]`** | Un `cumple` booleano en cualquier respuesta de OE6 | Comprobación 2.12: **ningún `cumple` booleano en todo el módulo** |

---

## Lo que este plan deja para después

1. **`retiro_manual` en `hecho_despacho`** — columna derivada de `idusuario IS NOT NULL` sin copiar el
   identificador. Resolvería E6-09 por completo. Toca el DAG de otro módulo.
2. **La tabla puente región↔condado** en el sistema operativo. Levanta el ⛔ del eje de región, aquí y
   en OE3.
3. **Sembrar el rol `Gerente`** en `Dim_Rol` y en las constantes del backend.
4. **La capa de presentación** (CU-E01) y la línea base que permitirá semaforizar.

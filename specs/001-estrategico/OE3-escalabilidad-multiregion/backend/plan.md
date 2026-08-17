# Implementation Plan: OE3 — Escalabilidad Multi-Región sin Degradación

**Branch**: `001-estrategico/OE3-escalabilidad-multiregion/backend` | **Date**: 2026-08-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-estrategico/OE3-escalabilidad-multiregion/backend/spec.md`

---

## Summary

Siete de los catorce informes de OE3, resueltos con una consulta cada uno sobre el modelo analítico,
más **una dimensión nueva** —la vecindad entre condados— que es la única ampliación del modelo.

**OE3 puede medir que el servicio no se degrada; no puede medir la escalabilidad.** Los siete
bloqueados no se publican, y cada uno nombra su prerrequisito.

**La investigación movió tres piezas**, y las tres estaban mal en la spec:

1. **E3-02 estaba mal especificado en el catálogo.** Mezcla la latencia técnica del algoritmo
   (≤100 ms) con el tiempo operativo del proceso. Se separa: el informe mide el tiempo operativo
   contra la meta real de `RNF-DES-001` —`<2 min p95`—, que **se cumple** (1,77 min medido).
2. **E3-12 no es construible.** 1 082 de 1 083 despachos manuales no siguen a ningún intento
   automático: el suceso que mide no se registra. Pasa a los bloqueados.
3. **E3-08 sí es construible.** `Dim_CondadoVecino` existe con datos. Se carga y se desbloquea.

El total de construibles no se mueve —siete—, pero el reparto entre historias sí.

---

## Technical Context

**Language/Version**: Python 3.11 (Django) para HTTP · SQL de ClickHouse para las consultas · Python
en los DAG para la dimensión nueva

**Primary Dependencies**: Django + DRF · `ModeloRepository` y el armazón de OE6 · lectura de Pinot
**solo desde el DAG** que carga la dimensión

**Storage**: ClickHouse, base `tsi_tactico`. Hoy 13 tablas; **14 tras este módulo**. Se leen seis y
**se crea una dimensión**: `dim_condado_vecino`

**Testing**: pytest. Contrato por endpoint, permisos **con exclusiones**, contraste contra la capa
táctica, y pruebas del catálogo de consultas

**Target Platform**: Contenedor `accidentes-django` · el DAG en `tactico-airflow-scheduler`

**Project Type**: Servicio web de solo lectura — siete endpoints `GET`

**Performance Goals**: Regla 7 en toda consulta. **E3-03 usa ventanas amplias**, así que es donde el
descarte de particiones más pesa

**Constraints**:
- Período obligatorio; sin paginación
- Sin dato sensible, tampoco para la autoridad
- **Autoridad repartida: el permiso es por informe, no por módulo**
- **`cumple` es booleano en dos informes** — único módulo de la capa que semaforiza

**Scale/Scope**: 7 informes publicados + 7 declarados no construibles · 4 252 casos, 4 314 intentos,
59 045 posiciones GPS · histórico 2026-02-03 → 2026-08-13

---

## Constitution Check

*GATE: debe pasar antes de Phase 0. Re-evaluado tras Phase 1.*

| Principio | Cómo se cumple | |
|---|---|:--:|
| **I. Idoneidad funcional como contrato** | Los siete construibles están trazados a CU-E05 y CU-E08. **Los siete bloqueados se declaran con su prerrequisito** en vez de publicarse vacíos. Y se corrige una incoherencia del propio catálogo: la meta de E3-02 | ✅ |
| **II. Fiabilidad operativa** | El módulo mide la fiabilidad, no participa en ella. Su indisponibilidad no retrasa ningún despacho | ⚪ |
| **III. Eficiencia en tiempo real** | No toca la ruta crítica. Regla 7 obligatoria, y E3-03 la necesita más que ningún otro informe de la capa | ✅ |
| **IV. Capacidad de interacción** | No aplica: frontend aplazado | ⚪ |
| **V. Seguridad de la información** | Exclusión constitucional aplicada también a las tres autoridades. **Y el permiso es por informe**, que es más restrictivo que por módulo | ✅ |
| **VI. Compatibilidad API-first** | Contrato OpenAPI bajo el envelope común | ✅ |
| **VII. Mantenibilidad estructural** | Reutiliza el armazón de OE6 y las consultas tácticas por contraste. La ampliación es **una dimensión compartida**, no una tabla de informe | ✅ |
| **VIII. Flexibilidad multi-región** | ⛔ **Es la característica que este objetivo existe para medir, y la que no puede medir.** Ver el trade-off | ⛔ |
| **IX. Seguridad física (Safety)** | E3-07 y E3-08 detectan **zonas donde una emergencia no tiene quién la atienda**: demanda sin capacidad, y sin vecino que respalde. Son los dos informes con consecuencia física más directa del módulo | ✅ |

### Trade-off invocado — Idoneidad frente a Safety y Fiabilidad

- **En conflicto:** *Idoneidad funcional* pedía publicar los catorce informes del catálogo. Publicar
  siete de ellos daría cifras falsas: E3-04 compararía contra 1970 y devolvería más de veinte mil días
  en rojo contra una meta `[NORMATIVO]`; E3-02 con la meta del catálogo estaría 1 060 veces por
  encima; E3-12 mediría un suceso que no ocurre.
- **Qué se priorizó y bajo qué regla:** **rige la regla 1 del Tie-Breaker, hay Safety en juego.** Este
  es el tablero que vigila la capacidad de despachar ambulancias, y una cifra falsa en él degrada la
  confianza en las que sí son ciertas.
- **Lo aceptado:** publicar siete y declarar siete. Se sacrifica cobertura aparente del catálogo.
- **Lo ganado:** ninguna cifra del tablero afirma algo que el sistema no sabe.
- **Condición de revisión:** cada bloqueado nombra su prerrequisito; se levantan uno a uno.

### La limitación de Flexibilidad, declarada

Es la única característica en ⛔ de todo el proyecto hasta ahora, y conviene no suavizarla: **el
objetivo cuyo propósito es demostrar que la operación escala no puede demostrarlo.** No por un
defecto de este módulo, sino porque el sistema operativo no historiza el estado de las regiones ni
declara qué condados cubre cada una.

**Excepción con condición de revisión:** se levanta cuando exista la tabla puente región↔condado y la
historización del estado de región (`decisiones-pendientes.md` #38).

---

## Project Structure

### Documentation (this feature)

```text
specs/001-estrategico/OE3-escalabilidad-multiregion/
├── OE3-escalabilidad-multiregion.md
└── backend/
    ├── spec.md · plan.md · research.md · data-model.md · quickstart.md
    ├── contracts/informes-estrategicos-oe3.openapi.yaml
    ├── checklists/requirements.md
    └── tasks.md                      # Phase 2 — lo crea /speckit-tasks
```

### Source Code (repository root)

```text
backend/apps/informes_estrategicos/        # Creada por OE6; aquí solo se añade
├── services/oe3_service.py                # CATALOGO + PUBLICADOS + parámetros
├── views/oe3_views.py
├── permissions.py                         # ← se AMPLÍA: autoridad por informe
└── urls.py                                # ← se amplía

core/repositories/informes_estrategicos/   # Reutilizado tal cual

dags/lib/dimensiones/
└── dim_condado_vecino.py                  # 🆕 la única ampliación del modelo

dags/lib/consultas/estrategicos/oe3/       # Las 7 consultas
├── e3_02_latencia_asignacion.sql
├── e3_03_evolucion_latencia.sql
├── e3_10_tasa_error_registro.sql
├── e3_11_primer_intento.sql
├── e3_07_ratio_demanda_capacidad.sql
├── e3_08_cobertura_de_respaldo.sql        ← depende de la dimensión nueva
└── e3_13_perdida_de_senal.sql

backend/apps/informes_estrategicos/tests/
├── api/ · unit/ · contraste/
```

**Structure Decision**: **no se crea app nueva.** OE3 se añade a `informes_estrategicos`, que OE6
creó. Es lo que justifica que las piezas transversales vivieran en la raíz de esa app y no bajo
`oe6`: este módulo es la primera prueba de que esa decisión era correcta.

Lo único que se **amplía** es `permissions.py`, porque OE3 introduce el primer acceso no uniforme de
la capa.

---

## Constitution Re-Check (post-Phase 1)

Ningún gate cambió de estado. Dos observaciones del diseño:

- **Principio I se reforzó al medir.** La incoherencia de E3-02 no se detectó leyendo el catálogo:
  salió de comparar 106 segundos contra una meta de 100 milisegundos. Sin esa medición, el informe se
  habría publicado en rojo permanente y el rojo habría parecido un problema de la operación.
- **Principio V se reforzó** con el permiso por informe: `DirectorExpansion` no accede a los de
  despacho, y la prueba comprueba la **exclusión**, no solo el acceso.

---

## Complexity Tracking

| Violación | Por qué es necesaria | Alternativa más simple, y por qué se rechaza |
|---|---|---|
| **Crear `dim_condado_vecino`** | E3-08 no es calculable sin la vecindad, y la tabla ya existe con datos en el operativo | *Derivar la vecindad de la geografía* (condados del mismo estado): sería una suposición sobre adyacencia física que el dato ya responde, y daría vecinos falsos en cuanto haya más de dos condados por estado |
| **Cambiar la meta de E3-02 respecto del catálogo** | La del catálogo mezcla dos métricas y produce un rojo falso 1 060× | *Conservarla y declarar el informe inmedible*: sacrificaría un informe construible, con meta escrita en `RNF-DES-001` y que **se cumple**, dejando a US1 sin indicador principal |
| **Permiso por informe y no por módulo** | La autoridad de OE3 está repartida entre tres cargos por materia | *Un permiso de módulo*: concedería de más justo en el caso donde el SRS advierte que la autoridad «no debe leerse como una cadena de mando única» |
| **Consultas propias en vez de compartir con la táctica** | Igual que en OE6: las tácticas fijan granularidad mensual y no calculan percentiles | *Parametrizar las tácticas*: tocaría endpoints publicados y verificados, para ganar algo que la prueba de contraste ya garantiza |

---

## Riesgos

| Riesgo | Señal temprana | Mitigación |
|---|---|---|
| **Se copia de OE6 la prueba «ningún `cumple` booleano»** | Fallan `latencia-asignacion` y `tasa-error-registro` | Documentado en data-model §5, contrato y quickstart 2.3. **Aquí la comprobación es la inversa** |
| **Se publica E3-02 con la meta de 100 ms** | Rojo permanente en el único informe que cumple su meta | `research.md` D1 y el `alcance` obligatorio en la respuesta |
| **El permiso se implementa por módulo** | `DirectorExpansion` entra en los informes de despacho | Quickstart 2.10 comprueba **exclusiones** |
| **E3-07 usa la flota actual** | Todos los períodos con la misma capacidad | Quickstart 2.5 |
| **E3-08 lee existencia en vez de disponibilidad** | Un vecino con todas sus unidades ocupadas cuenta como respaldo | Quickstart 2.7 |
| **Alguien "arregla" un bloqueado publicándolo vacío** | Un `200` en cualquiera de las siete rutas ausentes | Quickstart 2.9 |

---

## Lo que este plan deja para después

1. **Historizar el estado de región** en el sistema operativo. Desbloquea US3 entera (E3-04, E3-05,
   E3-06) y, con la tabla puente, el eje de región de toda la capa.
2. **Instrumentar el evento «asignación automática sin candidatas»** con su instante. Desbloquea E3-12.
3. **Integrar el monitoreo de infraestructura** como fuente del analítico. Desbloquea E3-01.
4. **Decidir si E3-14 sale del tablero de negocio**: mide el proceso de desarrollo, no la operación.

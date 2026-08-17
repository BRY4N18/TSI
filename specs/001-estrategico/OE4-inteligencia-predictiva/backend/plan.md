# Implementation Plan: OE4 — Registro Histórico e Inteligencia Predictiva

**Branch**: `001-estrategico/OE4-inteligencia-predictiva/backend` | **Date**: 2026-08-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-estrategico/OE4-inteligencia-predictiva/backend/spec.md`

---

## Summary

Nueve de los quince informes de OE4, resueltos con una consulta cada uno sobre el modelo analítico,
más **dos columnas nuevas en `hecho_accidente`** que completan los dos informes que se venden.

**La investigación movió tres piezas:**

1. **E4-13 se completa.** `distanciamillas` existe en el origen con **98,8 % de cobertura**; el modelo
   no la cargaba. El informe de impacto vial entregaba la mitad del producto.
2. **E4-06 se completa estructuralmente**, con la condición climática cargada — pero su dato son
   **3 casos de 4 252**, así que la mitad climática se entrega con la escasez declarada.
3. **E4-14 no es medible**, y no por falta de datos: **la regla de idempotencia del modelo lo impide
   por diseño**. Cada recarga reescribe `cargado_en` de la partición entera.

Construibles: **9, no 10**. Pero los dos que iban a entregar la mitad ahora entregan el producto
entero, y son precisamente los dos que se venden.

**Y se retira la última tabla legada de este dominio.** `indice_calidad_historico` deja de ser fuente.

---

## Technical Context

**Language/Version**: Python 3.11 (Django) para HTTP · SQL de ClickHouse para las consultas · Python
en el DAG de `hecho_accidente` para las dos métricas nuevas

**Primary Dependencies**: Django + DRF · el armazón de `informes_estrategicos` que creó OE6 ·
`ModeloRepository`

**Storage**: ClickHouse, base `tsi_tactico`. **El recuento de tablas no cambia**: las dos ampliaciones
son columnas de `hecho_accidente`. Se leen cuatro tablas

**Testing**: pytest. Contrato por endpoint, permisos con exclusiones, contraste contra la capa
táctica y **contra la tabla legada**, y pruebas del catálogo de consultas

**Target Platform**: Contenedor `accidentes-django` · el DAG en `tactico-airflow-scheduler`

**Project Type**: Servicio web de solo lectura — nueve endpoints `GET`

**Performance Goals**: Regla 7 en toda consulta. **E4-15 recorre el histórico entero**, así que es
donde más pesa

**Constraints**:
- Período obligatorio; sin paginación
- **Sin coordenadas ni identidad, reforzado: estos informes se venden a terceros**
- **Ningún `cumple` booleano** — todas las metas de OE4 son `[CALIBRAR]`
- Permiso por informe: `DirectorOperaciones` solo en los del expediente

**Scale/Scope**: 9 informes publicados + 6 declarados no construibles · 4 252 casos, 54 evidencias,
3 condiciones climáticas · 182 filas de tabla legada a retirar

---

## Constitution Check

*GATE: debe pasar antes de Phase 0. Re-evaluado tras Phase 1.*

| Principio | Cómo se cumple | |
|---|---|:--:|
| **I. Idoneidad funcional como contrato** | Los nueve están trazados a CU-E06 y CU-T14/T15. Los seis bloqueados se declaran con prerrequisito. Y se corrigen **tres errores de la propia spec**, dos a favor y uno en contra | ✅ |
| **II. Fiabilidad operativa** | El módulo mide la calidad del registro, no participa en la operación | ⚪ |
| **III. Eficiencia en tiempo real** | No toca la ruta crítica. Regla 7, con E4-15 como caso extremo | ✅ |
| **IV. Capacidad de interacción** | No aplica: frontend aplazado | ⚪ |
| **V. Seguridad de la información** | **Es el módulo donde más importa de todo el proyecto**: sus productos se venden a terceros. Un mapa con coordenadas o identidad sería una fuga **con destinatario comercial**. Exclusión aplicada también a `DirectorDatos` | ✅ |
| **VI. Compatibilidad API-first** | Contrato OpenAPI bajo el envelope común. ⚠️ E4-12 y E4-13 son candidatos a exponerse vía la API de partners, lo que hace su contrato **más sensible al cambio** que el del resto de la capa | ✅ |
| **VII. Mantenibilidad estructural** | Reutiliza el armazón de OE6, y **retira la última tabla legada** de este dominio. Las dos ampliaciones son columnas, no tablas | ✅ |
| **VIII. Flexibilidad multi-región** | ⚠️ E4-15 agrupa por condado: el eje de región no existe (#38) | ⚠️ |
| **IX. Seguridad física (Safety)** | Indirecta pero real: **E4-09 mide si las unidades se preposicionan según el modelo**, y un modelo mal evaluado desplaza ambulancias a las zonas equivocadas. Que esté bloqueado no lo hace menos crítico — lo hace más urgente | ✅ |

### Trade-off invocado — Idoneidad frente a Mantenibilidad, en la fórmula del índice

- **En conflicto:** la fórmula del legado es una **media sin ponderar**, así que la cobertura de
  evidencia pesa igual que la completitud de campos críticos. Es defendiblemente incorrecta: un
  expediente sin severidad es peor que uno sin foto.
- **Qué se priorizó:** **conservarla**. No hay Safety en juego, así que rigen Mantenibilidad e
  Idoneidad — y aquí apuntan a lo mismo: hay **182 días ya calculados** con la fórmula vieja, y
  cambiarla a la vez que se migra el informe produciría una serie que parece continua con un salto en
  medio, **sin forma de saber cuál de los dos cambios lo causó**.
- **Lo aceptado:** una ponderación discutible se mantiene un ciclo más.
- **Condición de revisión:** revisar la ponderación **después** de que la migración esté verificada,
  como cambio propio y aislado.

### La otra decisión que merece registro — cargar el clima con 3 filas

El proyecto tiene precedentes en las dos direcciones: Emergencias **no** creó un hecho para las
escaladas de severidad con 1 fila de origen, y OE3 **sí** cargó `dim_condado_vecino` con 2 filas.

Lo que los distingue es el **coste**, no el volumen: un hecho con su flujo y su DAG es caro; una
columna en una carga existente, no. Aquí el clima se resuelve como **columna desnormalizada**, así
que se carga — con la escasez declarada y una prueba que falla si la cardinalidad deja de ser 1:0..1.

---

## Project Structure

### Documentation (this feature)

```text
specs/001-estrategico/OE4-inteligencia-predictiva/
├── OE4-inteligencia-predictiva.md
└── backend/
    ├── spec.md · plan.md · research.md · data-model.md · quickstart.md
    ├── contracts/informes-estrategicos-oe4.openapi.yaml
    ├── checklists/requirements.md
    └── tasks.md                      # Phase 2 — lo crea /speckit-tasks
```

### Source Code (repository root)

```text
backend/apps/informes_estrategicos/        # Creada por OE6
├── services/oe4_service.py
├── views/oe4_views.py
├── permissions.py                         # ← se amplía con los conjuntos de OE4
└── urls.py                                # ← se amplía

dags/lib/hechos/hecho_accidente.py         # ← se amplía: 2 métricas nuevas
dags/lib/consultas/estrategicos/oe4/       # Las 9 consultas
├── e4_01_indice_calidad_historico.sql     ← migra la tabla legada
├── e4_02_completitud_campos_criticos.sql
├── e4_03_campos_mas_ausentes.sql
├── e4_04_calidad_por_origen.sql
├── e4_05_concentracion_siniestralidad.sql
├── e4_06_patron_horario_climatico.sql     ← usa condicion_clima
├── e4_12_impacto_humano_por_zona.sql
├── e4_13_impacto_vial_por_zona.sql        ← usa distancia_millas
└── e4_15_cobertura_del_historico.sql

backend/apps/informes_estrategicos/tests/
├── api/ · unit/ · contraste/
```

**Structure Decision**: **no se crea app nueva.** OE4 se añade a `informes_estrategicos`, como OE3.
Es el tercer módulo que confirma que poner las piezas transversales en la raíz de esa app fue
correcto.

Las dos ampliaciones del modelo van **en el flujo de carga que ya existe**
(`dags/lib/hechos/hecho_accidente.py`), no en uno nuevo. Es lo que las hace baratas.

⚠️ **La trampa conocida de ese flujo**, documentada en el changelog del módulo táctico: añadir una
fuente a `extraer()` y **olvidarla en `FUENTES`** hace que `datos.get(nombre, [])` la sustituya por
una lista vacía y **todos los recuentos salgan a cero, sin un solo error**. Las dos métricas nuevas
tienen que entrar en los dos sitios.

---

## Constitution Re-Check (post-Phase 1)

Ningún gate cambió de estado. Tres observaciones:

- **Principio I se reforzó dos veces al medir.** Ni la existencia de `distanciamillas` ni la
  imposibilidad de E4-14 se deducen del catálogo: la primera salió de consultar el origen y la
  segunda de mirar `cargado_en` y darse cuenta de que las 4 252 filas comparten valor.
- **Principio V se reforzó** al escribir el contrato: cada informe vendible declara explícitamente
  que la ubicación va por nombre.
- **Principio VII se reforzó**: al descifrar la fórmula del legado, la migración deja de ser un salto
  a ciegas y pasa a ser verificable contra 182 días.

---

## Complexity Tracking

| Violación | Por qué es necesaria | Alternativa más simple, y por qué se rechaza |
|---|---|---|
| **Añadir `distancia_millas`** | E4-13 entregaba la mitad de un producto que se vende, con el dato disponible al 98,8 % | *Dejarlo parcial*: renuncia a la mitad más valiosa del informe por no hacer un `ALTER TABLE` |
| **Añadir `condicion_clima` con 3 filas de dato** | La escasez se declara; la imposibilidad no. Y el pipeline queda listo para cuando el histórico crezca | *Dejarlo parcial*: coherente con el precedente de las escaladas, pero aquel exigía un hecho entero y esto es una columna |
| **Conservar una fórmula discutible** | 182 días ya calculados con ella | *Corregir la ponderación ahora*: haría imposible saber si un salto en la serie lo causó la migración o la fórmula |
| **Consultas propias en vez de compartir con la táctica** | Igual que OE6 y OE3 | *Parametrizar las tácticas*: toca endpoints verificados para ganar lo que el contraste ya garantiza |

---

## Riesgos

| Riesgo | Señal temprana | Mitigación |
|---|---|---|
| **Las métricas nuevas se añaden a `extraer()` y no a `FUENTES`** | `distancia_millas` y `condicion_clima` a cero en todas las filas, **sin error** | Quickstart 2.1 comprueba los recuentos reales (≈4 200 y 3), no que la columna exista |
| **Se rellenan las métricas nuevas con `0`** | La distancia media baja y la serie histórica se aplana | `Nullable` obligatorio, §4.bis. Quickstart 2.8: `casos_con_distancia` ≠ `casos` |
| **Se publica E4-14 porque `cargado_en` existe** | Una mediana de ~1 971 horas que parece una latencia | Quickstart 2.13. Es el bloqueado que más fácil se cuela |
| **El clima pasa a 1:N y la carga elige uno** | Nada visible: una condición plausible por caso | Quickstart 2.2 y su prueba automatizada |
| **Se cambia la fórmula del índice al migrarlo** | Un salto en la serie de 182 días | Quickstart 2.3 la reproduce exactamente |
| **Se publica una coordenada en un informe vendible** | — *(no hay señal: por eso la prueba es obligatoria)* | Quickstart 2.10, con `DirectorDatos` |

---

## Lo que este plan deja para después

1. **Las tres tablas del modelo predictivo** —`registro_predicciones`, `registro_modelos`,
   `catalogo_productos_inteligencia`—. Pertenecen al módulo operativo `predictive-ai-accident-rate`.
   Desbloquean US4 entera y **tres indicadores del BSC**.
2. **Una marca de primera aparición por fila** que sobreviva a la recarga idempotente. Desbloquea
   E4-14, y es una excepción deliberada a una regla del modelo.
3. **Revisar la ponderación del índice de calidad**, como cambio aislado y posterior a la migración.
4. **Retirar `indice_calidad_historico`** del almacén, una vez el contraste lleve un tiempo en verde.

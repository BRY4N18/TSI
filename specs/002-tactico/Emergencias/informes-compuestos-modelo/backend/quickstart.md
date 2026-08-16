# Quickstart — Informes Compuestos de Emergencias

**Fecha:** 2026-08-14 · **Plan:** [`plan.md`](plan.md)

Cómo verificar que los informes funcionan y **que dicen la verdad**, que no es lo mismo.

---

## 1. Prerrequisito: el modelo cargado

```bash
docker compose -f docker/docker-compose.tactico.yml up -d
```

```bash
docker exec -w /opt/airflow tactico-airflow-scheduler python -m pytest dags/tests -q
```

**Esperado:** verde. Si el modelo no está cargado, todo lo demás mide el vacío.

Comprobar que los cuatro hechos tienen datos y que el quinto —`hecho_evidencia`— existe tras
implementar OT24.

---

## 2. Comprobación por escenario

### 2.1 Un informe se resuelve con una consulta *(SC-001)*

Ejecutar cualquier fichero de `dags/lib/consultas/emergencias/` contra el almacén y comprobar que
devuelve filas **sin que se haya creado ninguna tabla**. Después:

```sql
SELECT name FROM system.tables WHERE database = currentDatabase()
```

**Esperado:** las mismas tablas que antes de ejecutar el informe. Ni una más.

### 2.2 La completitud deja de ser constante ⚠️ *(SC-002)*

Es el defecto que este módulo corrige, así que merece comprobarse en dos pasos:

1. Pedir el informe y anotar `pct_completitud`.
2. Cargar en la partición de prueba un caso **sin severidad** y volver a pedirlo.

**Esperado:** la segunda cifra es **menor**. Si sigue saliendo `1.0000`, la consulta heredó el
defecto: está comparando contra algo que nunca puede ser falso.

### 2.3 La capacidad es la de entonces, no la de hoy *(FR-006)*

1. Pedir el ratio demanda/capacidad de un período pasado y anotar `unidades_vigentes`.
2. Dar de baja una unidad en el sistema operativo y recargar las dimensiones.
3. Volver a pedir **el mismo período pasado**.

**Esperado:** `unidades_vigentes` **no cambia**. Si baja, el informe está usando la flota de hoy —el
defecto documentado— en vez de las versiones vigentes entonces.

### 2.4 El pasado no se reescribe *(SC-003)*

1. Pedir «retiros forzados por proveedor» de un período pasado.
2. Cambiar el proveedor de una unidad y recargar.
3. Volver a pedir **el mismo período**.

**Esperado:** el reparto por proveedor es **idéntico**. Es la propiedad que sostiene todo el modelo.

### 2.5 La pérdida de señal ve todas las posiciones *(SC-004)*

```sql
SELECT count() FROM hecho_ping_unidad
```

Comparar con el recuento del sistema operativo.

**Esperado:** iguales. Y el informe debe devolver **muchos más huecos** que la tabla anterior: 3 942
frente a 714 con los datos actuales. **Esa diferencia es el arreglo**, no una regresión.

### 2.6 Sin dato no es cero ⚠️ *(SC-011)*

Pedir la desviación de llegada con `muestra_minima` alto —por ejemplo 500—, de modo que ninguna
unidad tenga histórico suficiente.

**Esperado:** `segundos_referencia` y `desviacion_mediana` vienen **`null`**, no `0`. Un cero diría
«llegó justo a tiempo», que es exactamente lo contrario de lo que ocurre.

Repetir la idea con cualquier informe de porcentaje sobre un período vacío: el porcentaje sale
`null`, y `data` vuelve **vacío**, no con una fila de ceros.

### 2.7 Los trece que conviven dan la misma cifra ⚠️

**La comprobación que evita dos verdades.** Para cada uno de los 13 informes que siguen sirviéndose
desde el sistema operativo, pedir la cifra por ambos caminos —el endpoint actual y la consulta del
catálogo— y compararlas.

**Esperado:** coinciden. Si divergen, uno de los dos está mal y hay que averiguar cuál **antes** de
que alguien tome una decisión con la cifra equivocada.

⚠️ **Tres están excluidos de esta comparación a propósito**: completitud, ratio demanda/capacidad y
pérdida de señal **deben** diferir, porque el endpoint actual es el que está mal.

### 2.8 Nada sensible sale por la API *(SC-006)*

Pedir los 13 endpoints y comprobar que ninguna respuesta contiene coordenadas, nombres de personas
ni texto libre. Repetir **con un usuario que tenga la autoridad departamental**: la exención de
acotamiento no alcanza al dato sensible.

### 2.9 Ningún caso se pierde al clasificar *(SC-007)*

Para cada informe de distribución, sumar todas sus categorías y comparar con el total del período.

**Esperado:** iguales, con los casos sin ubicación o sin severidad resoluble bajo `Desconocido`.
**Si la suma es menor, alguien está desapareciendo del informe.**

---

## 3. Verificación de que nada se movió

```bash
cd backend && python -m pytest -q
```

**Esperado:** las suites existentes en verde y sin cambios de recuento salvo las pruebas nuevas de
este módulo. Los 13 endpoints que no se migran **no deben tocarse**.

---

## 4. Trampas conocidas

- **Olvidar la versión final** en un hecho acumulado o una dimensión devuelve filas duplicadas **de
  forma intermitente**. Es el fallo más difícil de diagnosticar del modelo: desaparece solo cuando el
  motor fusiona en segundo plano, así que quien lo reporte verá cifras normales al comprobarlo.
- **Pedirla en un hecho de transacción falla** con `ILLEGAL_FINAL`. `hecho_estado_unidad`,
  `hecho_ping_unidad` y `hecho_evidencia` no la admiten. No es una limitación: no hay versiones que
  reconciliar.
- **Contar filas no es contar casos.** El grano de despacho es el intento: 4 314 intentos son 3 651
  casos.
- **Cinco fuentes de OT24 y OT25 están casi vacías.** Un informe de evidencia que devuelva ~0 %
  probablemente esté **bien**: la operación apenas registra evidencia. Antes de depurar la consulta,
  comprobar el volumen del origen.
- **Los informes de OT24 se prueban con datos sintéticos**, no con los reales. Con las fuentes
  vacías, una consulta rota y un origen vacío se ven exactamente igual: ambos devuelven cero.

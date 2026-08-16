# Quickstart — Informes Compuestos de Red Operativa

**Fecha:** 2026-08-14 · **Plan:** [`plan.md`](plan.md)

---

## 1. Prerrequisitos

**Dos, y el segundo es fácil de olvidar:**

1. El modelo analítico cargado:

```bash
docker compose -f docker/docker-compose.tactico.yml up -d
```

2. **Las fases 1 y 2 de Emergencias implementadas.** Este módulo no crea plomería: reutiliza el
cargador de consultas, el repositorio de lectura, la resolución de período y los permisos. No depende
de ninguno de sus informes, solo de sus cimientos (research D6).

```bash
docker exec -w /opt/airflow tactico-airflow-scheduler python -m pytest dags/tests -q
```

---

## 2. Comprobación por escenario

### 2.1 «En Misión» aparece pese a no estar en el catálogo ⚠️ *(SC-002)*

```sql
SELECT estado_nuevo, count() FROM hecho_estado_unidad GROUP BY estado_nuevo
```

**Esperado:** aparecen cuatro estados, incluido `En Misión` con 6 filas. Pedir después el informe de
unidades por estado y comprobar que **también** lo muestra.

Si falta, la consulta está uniendo con el catálogo del sistema operativo — que solo define tres — y
**está perdiendo el 13 % de los datos sin que nada falle**.

### 2.2 La disponibilidad se mide en tiempo, no en transiciones ⚠️ *(SC-003)*

Es el error más fácil de cometer en este departamento, así que se comprueba en tres casos:

1. **Unidad activa todo el período, sin cambios** → `100 %`. ⚠️ No tiene **ninguna transición dentro
   del período**: si el informe cuenta transiciones, dará `0 %`.
2. **Unidad activa el 60 % del tiempo** → `60 %`, no «una de dos transiciones fue a Activa».
3. **Unidad sin ninguna transición conocida** → **ausente**, no `0 %`. No se sabe en qué estado
   estuvo, que es distinto de saber que estuvo parada.

### 2.3 El pasado de la región no se reescribe *(SC-010)*

1. Pedir «regiones en riesgo» de un período pasado y anotar el resultado.
2. Despublicar una región y recargar dimensiones.
3. Volver a pedir **el mismo período pasado**.

**Esperado:** el resultado **no cambia** — la región sigue apareciendo como publicada entonces. Es la
misma propiedad ya probada con la unidad y su proveedor, aplicada a otra entidad.

### 2.4 La región declara desde cuándo se mide *(SC-011)*

```sql
SELECT es_vigente, inicio_es_real, count() FROM dim_region FINAL GROUP BY es_vigente, inicio_es_real
```

**Esperado:** todas las versiones iniciales con `inicio_es_real = 0`. Y los informes #14 y #15 deben
devolver `medida_exacta_desde` en su respuesta.

⚠️ Con los datos actuales ambos devolverán **cero filas**, y eso es correcto: no ha habido
despublicaciones desde que empezó la medición. **Sin `medida_exacta_desde`, ese vacío se leería como
«nunca pasó»**, que es una afirmación que nadie puede hacer.

### 2.5 Una región que no llegó a producción no incumple nada *(SC-007)*

Pedir el tiempo de puesta en operación con una región aún en validación.

**Esperado:** `dias` y `cumple_objetivo` vienen **`null`**. Si sale `0` días o `false`, el informe
está declarando incumplido un plazo que aún corre.

### 2.6 Un condado sin vecinos aparece igualmente *(SC-008)*

**Esperado:** figura en cobertura crítica con `sin_alternativas: true`. Es la situación más grave, y
un informe que la omita por no tener vecinos que mostrar oculta justo el peor caso.

### 2.7 La suma de estados cuadra con la flota *(SC-005)*

Para cada condado, sumar sus unidades por estado y comparar con el número de unidades de ese condado
en el período.

**Esperado:** iguales. Si sobran, alguna unidad está contada en dos estados a la vez; si faltan,
alguna se perdió al clasificar.

### 2.8 La autoridad repartida se respeta

Pedir los informes con el **Director de Expansión** y con el **Director Tecnológico**.

**Esperado:** cada uno accede a su materia y **no a la del otro**. Este departamento no tiene
jefatura única, y un permiso que conceda todo a cualquiera de los dos incumple el §5.1 del SRS.

### 2.9 Nada sensible sale por la API *(SC-006)*

**Esperado:** ninguna respuesta trae coordenadas, contacto de proveedor ni **identidad del
validador** — que el catálogo pedía como desglose de la tasa de aprobación.

---

## 3. Verificación de que nada se movió

```bash
cd backend && python -m pytest -q
```

**Esperado:** verde, y **los informes de Emergencias devuelven las mismas cifras** (SC-009). Este
módulo añade dimensiones y hechos al mismo modelo: si algo de Emergencias se mueve, la ampliación no
fue aditiva.

---

## 4. Trampas conocidas

- **Unir con el catálogo de estados de unidad.** Es lo correcto en un modelo bien formado y aquí
  **pierde 6 de 45 transiciones**. Se agrupa por texto.
- **Medir disponibilidad contando transiciones.** Da 0 % justo a las unidades que nunca fallaron.
- **Olvidar el último tramo del período.** El estado vigente al final cuenta hasta el fin del
  período, no hasta el último cambio.
- **Leer un histórico vacío de despublicaciones como «nunca pasó».** Antes de la primera carga del
  modelo no hay historia porque nadie la guardaba.
- **Tratar `umbral_unidades` como una política de la empresa.** Es una convención de estos informes:
  el sistema operativo no define ningún umbral.
- **Volúmenes de dos dígitos.** 2 regiones, 3 validaciones, 2 bajas. Varios informes serán
  estadísticamente irrelevantes hoy; son correctos, simplemente aún no dicen mucho.

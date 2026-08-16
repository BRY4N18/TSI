# Quickstart — Informes Compuestos de Cuentas y Clientes

**Fecha:** 2026-08-14 · **Plan:** [`plan.md`](plan.md)

---

## 1. Prerrequisitos

1. El modelo analítico cargado y sus flujos corriendo.
2. **Las fases 1 y 2 de Emergencias implementadas** — la plomería.
3. ⚠️ **`dim_cliente` y `dim_plan` cargadas por Suscripciones.** Este módulo **amplía la primera**;
   si no existe, no hay nada que ampliar.

```bash
docker exec -w /opt/airflow tactico-airflow-scheduler python -m pytest dags/tests -q
```

---

## 2. Comprobación por escenario

### 2.1 La ampliación no rompió a Suscripciones ⚠️ *(SC-009)*

**Es la comprobación de fondo, y va primera por una razón**: si esto falla, da igual que los nueve
informes funcionen.

1. Anotar las cifras de MRR, ingresos y distribución de cartera **antes** de ampliar `dim_cliente`.
2. Aplicar la ampliación y recargar.
3. Volver a pedirlas.

**Esperado: idénticas.** Si se mueven, la ampliación no fue aditiva y hay **dos verdades sobre el
mismo cliente**.

### 2.2 El embudo muestra la etapa que nadie completó ⚠️ *(SC-004)*

```sql
SELECT etapa, orden FROM dim_etapa_onboarding FINAL ORDER BY orden
```

Pedir después el embudo.

**Esperado:** aparecen **todas** las etapas del catálogo, incluidas las que tienen cero clientes.

⚠️ Si el informe solo muestra las tres etapas que alguien completó, **está calculándose sobre lo
observado** — y mostraría 100 % de finalización describiendo un proceso perfecto. La etapa donde todo
el mundo se atasca sería justo la que falta.

### 2.3 La duración de sesión declara cuánto midió *(SC-006)*

```sql
SELECT desenlace, count() FROM hecho_sesion GROUP BY desenlace
```

**Esperado:** tres desenlaces —cerrada, abierta, expulsada— con la mayoría **sin cierre**.

El informe debe devolver `duracion_mediana` **y** `sesiones_sin_cierre`. Sin lo segundo, la mediana
describe **el 27 %** de las sesiones como si fueran todas — y precisamente las que terminaron bien.

### 2.4 La concurrencia no es un conteo de inicios

Cargar dos escenarios sintéticos: diez sesiones de un minuto repartidas por la hora, y diez
simultáneas.

**Esperado:** el mismo número de `sesiones_iniciadas` y **`concurrencia_maxima` muy distinta**. Si
ambas dan lo mismo, la consulta está contando inicios y no midiendo carga.

### 2.5 El churn agrupa por cohorte de alta *(SC-002)*

Dar de baja un cliente dado de alta en enero.

**Esperado:** aparece en la **cohorte de enero**, no en la del mes de baja.

### 2.6 La ocupación declara su cobertura ⚠️ *(SC-011)*

**Esperado:** `pct_cobertura_pertenencia` presente, hoy en torno a **0,095**.

Sin él, «1 de 10 usuarios» se lee como ocupación real cuando es **cobertura del dato**, y un cliente
parecería tener sitio de sobra cuando quizá esté lleno.

Comprobar también que los usuarios sin pertenencia **no se reparten** entre clientes (SC-012).

### 2.7 Nunca haber entrado no es haber entrado hoy *(SC-003)*

Un cliente sin ninguna sesión registrada.

**Esperado:** `sin_actividad_conocida = 1`, **no `0` días**.

### 2.8 Sin política, el informe de roles va vacío *(SC-007)*

Pedir roles incompatibles **sin parámetro**.

**Esperado: cero filas**, pese a que hay usuarios con dos roles activos. Acumular roles es el
**mecanismo previsto** del sistema; marcarlo denunciaría el funcionamiento normal.

Pedirlo después con un par declarado: **solo aparece esa combinación**, con `idusuario` y **ambos
roles nombrados**.

### 2.9 Nada sensible sale por la API ⚠️ *(SC-008)*

```sql
DESCRIBE TABLE hecho_sesion
```

**Esperado:** **ninguna columna de token**. Y en las dimensiones, ni nombre, ni correo, ni
identificación, ni teléfono, ni **género ni fecha de nacimiento**. No filtrados: **inexistentes**.

El único identificador de persona en todo el módulo es `idusuario`, y **solo en el informe de roles**.

### 2.10 La autoridad tiene un límite distinto aquí

Pedir los informes con el **Administrador** y con el **Director Tecnológico**.

**Esperado:** el Administrador accede a los nueve; el Director Tecnológico **solo a los dos de
acceso** (OT18). ⚠️ Su autoridad en este departamento **no cubre** el ciclo de vida ni la
incorporación.

---

## 3. Verificación de que nada se movió

```bash
cd backend && python -m pytest -q
```

**Esperado:** verde, y las cifras de los cinco departamentos anteriores sin cambios (SC-010).

---

## 4. Trampas conocidas

- ⚠️ **Recrear `dim_cliente` en vez de ampliarla.** Produce dos verdades sobre el mismo cliente, y
  los ingresos de Suscripciones dejan de cuadrar con las cuentas activas **sin que nada falle**.
- ⚠️ **Calcular el embudo sobre las etapas observadas.** Oculta exactamente la etapa que hay que
  arreglar.
- **Promediar la duración de todas las sesiones.** La mayoría no tiene cierre.
- **Contar inicios y llamarlo concurrencia.**
- **Olvidar que una sesión cruza la medianoche**: la suma de franjas supera el total, y parece un
  error de conteo.
- **Leer la ocupación sin su cobertura.** Hoy el 9,5 % de los usuarios tiene organización conocida.
- **Marcar el multi-rol como hallazgo.** Es el mecanismo previsto del sistema.
- **Volúmenes pequeños salvo en sesiones**: 4 clientes, 21 usuarios, 3 registros de onboarding — y
  718 eventos de sesión. Los dos BSC se calcularán sobre **un cliente con onboarding registrado**.

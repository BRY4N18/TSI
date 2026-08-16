# Quickstart — Informes Compuestos de Partners y API

**Fecha:** 2026-08-14 · **Plan:** [`plan.md`](plan.md)

---

## 1. Prerrequisitos

**Tres, y el tercero es nuevo en la serie:**

1. El modelo analítico cargado y sus flujos corriendo.
2. **Las fases 1 y 2 de Emergencias implementadas** — la plomería.
3. ⚠️ **`dim_cliente` y `hecho_factura` cargados por Suscripciones.** Dos informes de este módulo los
   usan, y **no los recrea**. Es la primera dependencia entre módulos compuestos.

```bash
docker exec -w /opt/airflow tactico-airflow-scheduler python -m pytest dags/tests -q
```

---

## 2. Comprobación por escenario

### 2.1 Hay una sola fuente de consumo ⚠️ *(SC-012)*

```sql
SELECT name FROM system.tables WHERE database = currentDatabase() AND name LIKE '%integracion%'
```

**Esperado: cero filas.** La tabla preagregada del sistema operativo **no está en el modelo**.

Si aparece, alguien la cargó «por completitud», y el departamento vuelve a tener dos verdades — con
la diferencia de que ahora ambas están en el almacén analítico, con apariencia de validadas.

### 2.2 La p95 existe, y declara sus muestras ⚠️ *(SC-002, SC-011)*

Pedir la latencia de un endpoint.

**Esperado:** `latencia_p95_ms` **y** `latencia_media_ms` **y** `muestras`. Con los datos actuales
—18 llamadas, 2 endpoints— `percentil_fiable` viene en `false` **y la fila igualmente se devuelve**.

⚠️ Comparar con el endpoint ya construido: **da solo media, y sus cifras diferirán**. Esa diferencia
es el arreglo.

### 2.3 Los cuatro motivos de credencial inactiva se distinguen *(SC-003)*

```sql
SELECT motivo_inactividad, count() FROM dim_credencial_api FINAL
WHERE esta_activa = 0 GROUP BY motivo_inactividad
```

**Esperado:** motivos distintos —revocada, cascada, expirada, suspensión manual—. En el sistema
operativo las cuatro son **el mismo `activo = false`**: si el modelo solo muestra uno, el motivo no
se derivó de la bitácora.

### 2.4 Los centinelas de fecha no son fechas ⚠️ *(SC-004)*

```sql
SELECT countIf(nunca_expira = 1) AS nunca, countIf(fecha_expiracion IS NOT NULL) AS con_fecha
FROM dim_credencial_api FINAL
```

**Esperado:** las credenciales del año 9999 tienen `fecha_expiracion` **ausente** y
`nunca_expira = 1`. **No aparecen** entre las próximas a vencer, y **no entran** en ningún promedio.

Comprobación rápida de que se hizo bien: si un promedio de días hasta la expiración da **millones**,
el centinela llegó al modelo.

Y lo mismo con la versión de contrato: `fecha_retiro` ausente en vez de la época cero. **Una versión
«retirada en 1970» ordenaría primera** en cualquier informe de versiones retiradas.

### 2.5 Las 429 no son errores del servicio *(SC-005)*

**Esperado:** la taxonomía separa `limite_cupo` (429), `autorizacion` (403) y `error_servicio` (5xx).
Con los datos actuales hay 3 llamadas 429, 2 con 403 y 1 con 500 — las tres clases deben aparecer
por separado.

Sumarlas diría «hay 6 errores» sin decir que **la mitad son de contrato y ninguno del servicio**.

### 2.6 Un partner sin llamadas no desaparece *(SC-006)*

**Esperado:** aparece con cero. Un partner que dejó de consumir es exactamente lo que hay que ver, y
omitirlo lo esconde.

### 2.7 El indicador de integración activa puede no cumplirse *(SC-007)*

**Esperado:** el denominador son **todos los clientes**. Si el porcentaje sale siempre 100 %, el
denominador está mal: se están contando solo los clientes que ya tienen partner.

### 2.8 La versión se declara derivada

**Esperado:** el informe de adopción devuelve `version_es_derivada` en verdadero y agrupa por
**(servicio, versión)**. Con los datos actuales, dos servicios comparten `'v1'`: si el informe
devuelve una sola fila `v1`, está mezclando servicios distintos.

### 2.9 Nada sensible sale por la API ⚠️ *(SC-008)*

```sql
DESCRIBE TABLE hecho_llamada_api
```

**Esperado:** ninguna columna de IP. Y en las dimensiones, ningún hash de secreto ni contacto
técnico. **No filtrados: inexistentes.**

Repetir con un usuario que tenga la autoridad departamental.

### 2.10 Un partner no ve estos informes

**Esperado:** un rol de partner recibe rechazo. Son cifras **comparadas de todos los partners**; su
propio consumo lo ve por el autoservicio ya existente.

---

## 3. Verificación de que nada se movió

```bash
cd backend && python -m pytest -q
```

**Esperado:** verde, **los dos endpoints ya construidos intactos**, y las cifras de los cuatro
departamentos anteriores sin cambios (SC-010).

---

## 4. Trampas conocidas

- ⚠️ **Cargar la tabla preagregada «por completitud».** Difiere del detalle en un orden de magnitud y
  hace imposibles tres informes.
- **Leer una p95 sobre 18 llamadas como si fuera estable.** Por eso `muestras` y `percentil_fiable`
  son obligatorios.
- **Agrupar el endpoint con su cadena de consulta.** Fragmenta el consumo en tantos grupos como
  combinaciones de parámetros haya, y ningún endpoint parece usado.
- **Sumar 429 con 5xx.** Son problemas de responsables distintos.
- **Dejar entrar el año 9999 o la época cero** en un cálculo de fechas.
- **Tomar `v1` como clave.** Dos servicios lo comparten.
- **Interpretar que la latencia del modelo «no cuadra» con la del endpoint actual.** No cuadra a
  propósito: aquel da media, este da p95.
- **Volúmenes de dos dígitos.** 18 llamadas y 2 endpoints: los informes son correctos y **sus cifras
  no significarán nada hasta que haya tráfico real**.

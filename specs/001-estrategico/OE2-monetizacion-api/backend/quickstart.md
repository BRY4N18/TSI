# Quickstart — Verificación de OE2

**Fecha:** 2026-08-18 · **Plan:** [`plan.md`](plan.md) · **Contrato:**
[`contracts/informes-estrategicos-oe2.openapi.yaml`](contracts/informes-estrategicos-oe2.openapi.yaml)

Cada comprobación existe porque su fallo sería silencioso (sobre todo: facturar con la fuente
equivocada, o publicar un p95 de dos llamadas).

---

## 1. Prerrequisitos

```powershell
docker ps --filter name=tactico-clickhouse --filter name=accidentes-django
docker exec tactico-clickhouse clickhouse-client --database tsi_tactico --query "EXISTS TABLE hecho_llamada_api"
```

**Esperado:** `1`. Si es `0`, el compuesto táctico de Partners no cargó el modelo.

```sql
SELECT count() FROM hecho_llamada_api;
SELECT count() FROM dim_partner FINAL;
```

**Medido 2026-08-16 en origen:** 18 llamadas, 4 partners.
**Medido 2026-08-18 en ClickHouse `tsi_tactico`:** tabla `hecho_llamada_api` existe; **0 / 0**
filas (ETL de Partners no ha cargado este entorno). Un p95 con `muestra_minima=20` saldrá
ausente: **es el resultado correcto** cuando haya muestras.

---

## 2. Comprobaciones

### 2.1 El detalle es la única fuente de consumo

Grep del catálogo `dags/lib/consultas/estrategicos/oe2/`: ninguna consulta nombra un hecho de
agregado de API.

**Fallo silencioso:** cuadrar contra 40 filas de agregado y facturar de más.

### 2.2 Adopción (E2-03)

`GET /api/v1/informes-estrategicos/oe2/integraciones-activas` como `DirectorTecnologico`.

**Esperado:** denominador = partners con acceso, no el catálogo. Un partner con credencial y
cero llamadas está en el denominador y no en el numerador.

### 2.3 p95 ausente (E2-05)

Mismo rol, `latencia-por-endpoint`, `muestra_minima=20`.

**Esperado:** `latencia_p95_ms` nulo y `percentil_fiable = 0` en endpoints con <20 muestras.
Bajar el umbral a 1 hace aparecer el p95 — no al revés.

### 2.4 4xx ≠ 5xx (E2-07)

**Esperado:** no hay un total «errores» que sume ambas clases.

### 2.5 Excedente facturable, no cobrado (E2-08)

Como `DirectorFinanciero`. Cada fila: llamadas, cupo, precio, importe. `alcance` dice que no
afirma cobro. Partners sin match a `dim_plan.precio_excedente_llamada` salen **declarados**, no
desaparecen.

### 2.6 Parciales de ingresos (E2-01, E2-02)

**Esperado:** `cobertura: "parcial"` y `falta` nombra el precio del plan de API.

### 2.7 Versión no es única (E2-09)

Dos servicios con `'v1'` → **dos** agrupaciones. `version_es_derivada` visible.

### 2.8 Crecimiento ≠ alta de credencial (E2-11)

Una credencial del mes sin llamadas 2xx **no** incrementa el ecosistema.

### 2.9 E2-06 no existe

`GET .../oe2/disponibilidad-api` → **404**. No está en el OpenAPI.

### 2.10 Un partner no entra

JWT con rol de partner → **403** en las diez, incluida `consumo-por-partner`.

### 2.11 Tecnológico no ve dinero; Finanzas sí

`DirectorTecnologico` en `excedente-facturable` → 403.
`DirectorFinanciero` en esa ruta → no 403.
`Gerente` en ambas familias → no 403.

---

## 3. Lo que este quickstart no cubre

- Frontend (aplazado).
- Uptime real (E2-06).
- Mix de ingresos al 100 % (falta precio de plan API).
- Semilla Pinot de `Gerente` si el entorno no la ha corrido.

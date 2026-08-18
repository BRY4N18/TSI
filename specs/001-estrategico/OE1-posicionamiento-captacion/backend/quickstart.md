# Quickstart — Verificación de OE1

**Fecha:** 2026-08-18 · **Plan:** [`plan.md`](plan.md) · **Contrato:**
[`contracts/informes-estrategicos-oe1.openapi.yaml`](contracts/informes-estrategicos-oe1.openapi.yaml)

Cada comprobación existe porque su fallo sería silencioso (sobre todo: MRR sin mensualizar, o
un CAC de 0 €).

---

## 1. Prerrequisitos

```powershell
docker ps --filter name=tactico-clickhouse --filter name=accidentes-django
docker exec tactico-clickhouse clickhouse-client --database tsi_tactico --query "EXISTS TABLE hecho_suscripcion"
```

**Esperado:** `1`. Si es `0`, el compuesto táctico de Suscripciones no cargó el modelo.

```sql
SELECT count() FROM hecho_suscripcion FINAL;
SELECT count() FROM dim_cliente FINAL;
SELECT count() FROM hecho_transicion_embudo;
SELECT count() FROM hecho_onboarding;
```

**Origen 2026-08-16:** 4 suscripciones, 4 clientes, transiciones de embudo, 3 onboardings.
**ClickHouse 2026-08-18 (implementación):** `hecho_suscripcion` 0 · `dim_cliente` 0 ·
`hecho_transicion_embudo` 0 · `hecho_onboarding` 0. Con n < 20, **todos** los GET salen
`cobertura: parcial`.

**Verificación 2026-08-18 (implementación):** las comprobaciones 2.1–2.10 viven en
`backend/apps/informes_estrategicos/tests/api/test_*oe1*` y `test_us1_*` / `test_us2_*` /
`test_us3_*`. El GET a `cac-por-canal` / `mercados-activos` / `cartera-mrr-por-mercado` es 404.

---

## 2. Comprobaciones

### 2.1 MRR mensualizado (E1-01)

`GET /api/v1/informes-estrategicos/oe1/mrr-mensual` como `DirectorFinanciero`.

**Esperado:** usa `precio_mensualizado`; el recuento de suscripciones viaja con la cifra;
`alcance` declara vigente al cierre. Una anual no vale 12× un mensual del mismo precio
anualizado.

### 2.2 ARR no es compromiso (E1-02)

**Esperado:** `alcance` dice extrapolación. Escenarios etiquetados.

### 2.3 Segmento = tipo, no país (E1-03)

**Esperado:** agrupación por `tipo`. Sin columna de mercado. Desconocidos visibles.

### 2.4 Embudo con ceros (E1-04)

Como `DirectorMarketing`. Etapa sin pasos **aparece** con 0. El volumen no crece entre etapas.

### 2.5 Onboarding contra catálogo (E1-10)

Como `Gerente`. Etapas del catálogo con cero completadas visibles. No es 100 % por omitirlas.

### 2.6 Churn sin muestra (E1-11)

Cohorte de 4 clientes: **sin porcentaje** o `parcial` explícito; no un 25 % como KPI.

### 2.7 Renovación (E1-06)

Denominador = vencidas en el período, no el stock de activas.

### 2.8 Los tres bloqueados

`GET .../oe1/cac-por-canal`, `mercados-activos`, `cartera-mrr-por-mercado` → **404**.
No están en el OpenAPI.

### 2.9 Exclusiones de permiso

| Quién | Ruta | Esperado |
|---|---|---|
| `DirectorMarketing` | `mrr-mensual` | 403 |
| `DirectorFinanciero` | `embudo-conversion` | 403 |
| `DirectorEstrategia` | `tiempo-onboarding` | 403 |
| `Gerente` | las diez | no 403 |
| rol partner | cualquiera | 403 |

### 2.10 Sin cobro ni persona

Ninguna clave de respuesta es medio de pago, hash, contacto o país.

---

## 3. Lo que este quickstart no cubre

- Frontend (aplazado).
- CAC real y mercados (E1-05/07/08).
- Mix de ingresos al 100 % (n de demostración).
- OE5 consumiendo estos cuatro (otro módulo).

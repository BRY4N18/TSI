# Quickstart — Verificación de OE5

**Fecha:** 2026-08-18 · **Plan:** [`plan.md`](plan.md) · **Contrato:**
[`contracts/informes-estrategicos-oe5.openapi.yaml`](contracts/informes-estrategicos-oe5.openapi.yaml)

Cada comprobación existe porque su fallo sería silencioso (sobre todo: SLA con tickets sin
plazo, NRR sin descomponer, o NPS de un accidente).

---

## 1. Prerrequisitos

```powershell
docker ps --filter name=tactico-clickhouse --filter name=accidentes-django
docker exec tactico-clickhouse clickhouse-client --database tsi_tactico --query "EXISTS TABLE hecho_ticket"
```

**Esperado:** `1`. Si es `0`, el compuesto táctico de Soporte no cargó el modelo.

```sql
SELECT count() FROM hecho_ticket FINAL;
SELECT count() FROM hecho_suscripcion FINAL;
SELECT count() FROM hecho_sesion;
SELECT count() FROM hecho_llamada_api;
```

**Origen 2026-08-16:** 14 tickets, 4 suscripciones, 747 sesiones, 18 llamadas API.
**ClickHouse 2026-08-18 (implementación):** `hecho_ticket` 0 · `hecho_suscripcion` 0 ·
`hecho_sesion` 0 · `hecho_llamada_api` 0. Con n < 20, **todos** los GET salen
`cobertura: parcial`.

Las comprobaciones 2.1–2.10 viven en `backend/apps/informes_estrategicos/tests/api/test_*oe5*`
y `test_us1_*` / `test_us2_*` / `test_us3_*` / `test_us4_*`.

---

## 2. Comprobaciones

### 2.1 SLA con denominador correcto (E5-04)

`GET /api/v1/informes-estrategicos/oe5/cumplimiento-sla` como `GerenteExitoCliente`.

**Esperado:** denominador = cerrados con `tiene_compromiso = 1`; `sin_compromiso` viaja
aparte. Un período sin cerrados-con-compromiso es `data: []`, no 0 %.

### 2.2 NRR descompuesto (E5-02)

Como `DirectorFinanciero`. Expansión, contracción y churn **visibles**. No hereda el stub
`expansion = 0` de OT07.

### 2.3 Movimiento pendiente no cuenta (E5-03)

Como `DirectorEstrategia`. Solo `aprobada`/`aplicada`. `delta_precio` del hecho, no
`dim_plan.precio`.

### 2.4 Una señal no marca riesgo (E5-12)

Como `Gerente`. Cuenta con una sola señal **ausente** de `data`. Si falta una fuente,
`cobertura: parcial` y `falta` la nombra.

### 2.5 Agente sin nombre (E5-06)

`idagente` sí; nombre/correo no. `alcance` dice carga de trabajo.

### 2.6 Reincidencia por cliente × servicio (E5-08)

Tres tickets de tres servicios ≠ reincidencia.

### 2.7 Antigüedad solo activas (E5-15)

Cerradas aparte.

### 2.8 Los bloqueados y las copias de OE1

`GET .../oe5/nps-satisfaccion`, `reportes-sin-correccion` → **404**.
`GET .../oe5/tasa-renovacion` (y `churn-por-cohorte` / `tiempo-onboarding` /
`abandono-onboarding`) → **404**.
No están en el OpenAPI. Ninguna respuesta lee `calificacion` de cierre.

### 2.9 Exclusiones de permiso

| Quién | Ruta | Esperado |
|---|---|---|
| `DirectorFinanciero` | `cumplimiento-sla` | 403 |
| `GerenteExitoCliente` | `retencion-neta-ingresos` | 403 |
| `DirectorEstrategia` | `cuentas-en-riesgo` | 403 |
| `Gerente` | las nueve | no 403 |
| rol partner | cualquiera | 403 |

### 2.10 Sin prosa ni cobro

Ninguna clave es asunto, mensaje, nota interna, medio de pago o calificación de accidente.

---

## 3. Lo que este quickstart no cubre

- Frontend: ver [`../frontend/quickstart.md`](../frontend/quickstart.md) (implementado).
- NPS real y entregas de informes (E5-01/11).
- Mix al 100 % (n de demostración).
- Consumo de E1-06/09/10/11 desde un tablero (otro módulo).

# Quickstart — Tres pantallas Z de OE2

**Fecha:** 2026-08-18 · **Spec:** [`spec.md`](spec.md) · **Contrato UI:** [`contracts/ui-contract.md`](contracts/ui-contract.md)

Cada comprobación existe porque su fallo sería silencioso.

## Prerrequisitos

- Backend OE2 en servicio (`../backend/quickstart.md`). Diez GET; `disponibilidad-api` → 404.
- `accidentes-django` (:8000) y `accidentes-frontend` (:4200) **Up**.
- ClickHouse: `hecho_llamada_api` existe (puede tener 0 filas en este entorno).

| Rol | Para qué |
|---|---|
| `DirectorTecnologico` | Entra a las tres |
| `Gerente` | Entra a las tres |
| `DirectorFinanciero` | Solo Dinero |
| `PartnerIntegracion` | Exclusión de las tres |

## 1. El Tecnológico entra a Uso; el Partner no

Abrir `/estrategico/oe2/uso` como Director Tecnológico.

**Esperado:** patrón Z (`zona-heroe`, `zona-periodo`, `zona-visual`, `zona-lectura`). Controles de período, granularidad y comparación. Sidebar grupo **Estratégico**. No hay recuadro de uptime. No hay botones de facturar.

Como Partner, la misma URL → access-denied. El sidebar **no** muestra Uso / Dinero / Ecosistema. `/partners/gestion/consumo` (si el rol táctico aplica) **no** es esta pantalla.

## 2. El trío de latencia no se rompe

En Uso, abrir el apoyo de latencia.

**Esperado:** p95, media y muestras **en el mismo bloque**. Si el percentil no es fiable, la fila sigue. Período 2019 → vacío, no 0 ms. Taxonomía: 4xx ≠ 5xx; **no** hay total «errores». Consumo: partner en cero **aparece**.

## 3. Esta pantalla no es el compuesto táctico

`/partners/gestion/consumo` **sigue** y **no** comparte disposición ni query `comparacion`. El Tecnológico ve **ambos** enlaces, en grupos distintos.

## 4. Dinero: facturable y parcial

`/estrategico/oe2/dinero` como Financiero **y** como Tecnológico.

**Esperado:** héroe con llamadas, cupo, precio e importe. Alcance «no cobrado». No tarificables visibles. Apoyo de participación/MRR con `zona-parcial` y el precio que falta.

Como Financiero, `/estrategico/oe2/uso` → access-denied. No ve esos enlaces.

Como Partner → access-denied.

## 5. Ecosistema: dos `'v1'` y primera 2xx

`/estrategico/oe2/ecosistema` como Tecnológico.

**Esperado:** adopción por (servicio, versión); dos `'v1'` = dos grupos; versión derivada declarada. Crecimiento no sube con una credencial sin 2xx. Comparativa con ceros. Financiero no entra.

## 6. No hay disponibilidad

Ninguna de las tres contiene uptime. No hay ruta UI para E2-06.

## 7. Un fallo no tumba la pantalla

Forzar error de red en un solo informe.

**Esperado:** esa zona en error; el héroe sigue.

## 8. Rebuild

Tras implementar:

```powershell
docker compose -f docker/accidentes.yml up -d --build django frontend
docker ps --filter name=accidentes-django --filter name=accidentes-frontend
```

Ambos **Up**.

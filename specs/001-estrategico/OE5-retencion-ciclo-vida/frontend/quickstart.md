# Quickstart — Cuatro pantallas Z de OE5

**Fecha:** 2026-08-18 · **Spec:** [`spec.md`](spec.md) · **Contrato UI:** [`contracts/ui-contract.md`](contracts/ui-contract.md)

Cada comprobación existe porque su fallo sería silencioso.

## Prerrequisitos

- Backend OE5 en servicio (`../backend/quickstart.md`). Nueve GET; NPS/reportes y refs OE1 → 404.
- `accidentes-django` (:8000) y `accidentes-frontend` (:4200) **Up**.
- ClickHouse: `hecho_ticket` existe (puede tener 0 filas).

| Rol | Para qué |
|---|---|
| `GerenteExitoCliente` | Solo Servicio |
| `DirectorFinanciero` | Solo Ingresos retenidos |
| `DirectorEstrategia` | Solo Planes |
| `Gerente` | Las cuatro |
| `PartnerIntegracion` | Exclusión de las cuatro |

## 1. El Éxito de Cliente entra a Servicio; Finanzas no

Abrir `/estrategico/oe5/servicio` como Gerente de Éxito de Cliente.

**Esperado:** patrón Z. Héroe con SLA **y recuento**. `zona-parcial` si n < 20. Tickets sin
compromiso en lectura. Sidebar grupo **Estratégico**. No hay NPS ni texto de ticket. No hay
botón de reabrir.

Como Financiero, la misma URL → access-denied. El sidebar **no** muestra Servicio.

## 2. Vacío no es 0 %

Período sin cerrados con compromiso.

**Esperado:** zona vacía, MUST NOT titular 0 % de cumplimiento.

## 3. Esta pantalla no es el compuesto táctico

El SLA táctico de Soporte **sigue** y **no** comparte disposición ni query `comparacion`.
El Éxito de Cliente ve **ambos** enlaces, en grupos distintos.

## 4. Ingresos: NRR descompuesto

`/estrategico/oe5/ingresos` como Financiero.

**Esperado:** neto + expansión/contracción/churn. Alcance de precio congelado. Sin stub OT07.

Como Éxito de Cliente → access-denied.

## 5. Planes: aprobados y activas

`/estrategico/oe5/planes` como Estrategia.

**Esperado:** SLA por plan; movimientos solo aprobados; antigüedad de activas. Financiero no entra.

## 6. Riesgo: solo Gerente; una señal no basta

`/estrategico/oe5/riesgo` como Gerente.

**Esperado:** cuentas con ≥2 señales; `meta.falta` visible si una fuente falta.

Como Financiero, Estrategia o Éxito de Cliente → access-denied.

## 7. No hay NPS, reportes ni ciclo OE1

Ninguna de las cuatro contiene NPS, reportes sin corrección, renovación, churn u onboarding.
No hay ruta UI para E5-01/11 ni recuadros de E5-09/10/13/14.

## 8. Un fallo no tumba la pantalla

Forzar error de red en un solo informe.

**Esperado:** esa zona en error; el héroe sigue.

## 9. Partner fuera

Como Partner, las cuatro URL → access-denied. El grupo Estratégico **no** le muestra OE5.

## 10. Rebuild

Tras implementar:

```powershell
docker compose -f docker/accidentes.yml up -d --build django frontend
docker ps --filter name=accidentes-django --filter name=accidentes-frontend
```

Ambos **Up**.

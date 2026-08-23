# Quickstart — Cuatro pantallas Z de OE1

**Fecha:** 2026-08-18 · **Spec:** [`spec.md`](spec.md) · **Contrato UI:** [`contracts/ui-contract.md`](contracts/ui-contract.md)

Cada comprobación existe porque su fallo sería silencioso.

## Prerrequisitos

- Backend OE1 en servicio (`../backend/quickstart.md`). Diez GET; CAC/mercados → 404.
- `accidentes-django` (:8000) y `accidentes-frontend` (:4200) **Up**.
- ClickHouse: `hecho_suscripcion` existe (puede tener 0 filas).

| Rol | Para qué |
|---|---|
| `DirectorFinanciero` | Solo Ingreso |
| `DirectorEstrategia` | Solo Cartera |
| `DirectorMarketing` | Solo Captación |
| `Gerente` | Las cuatro |
| `PartnerIntegracion` | Exclusión de las cuatro |

## 1. El Financiero entra a Ingreso; Marketing no

Abrir `/estrategico/oe1/ingreso` como Director Financiero.

**Esperado:** patrón Z. Héroe con MRR **y recuento**. `zona-parcial` si n < 20. ARR en lectura
con extrapolación. Sidebar grupo **Estratégico**. No hay CAC ni mapa. No hay botón de cobrar.

Como Marketing, la misma URL → access-denied. El sidebar **no** muestra Ingreso.

## 2. El ARR no se lee como compromiso

En Ingreso, zona de lectura.

**Esperado:** `meta.alcance` visible. MUST NOT titular «ingreso anual comprometido».

## 3. Esta pantalla no es el compuesto táctico

El MRR táctico de Suscripciones **sigue** y **no** comparte disposición ni query `comparacion`.
El Financiero ve **ambos** enlaces, en grupos distintos.

## 4. Cartera: tipo, no país

`/estrategico/oe1/cartera` como Estrategia.

**Esperado:** mezcla por plan; segmento por **tipo**; desconocidos visibles. Sin mapa.

Como Financiero → access-denied (el segmento HTTP existe; el menú no se lo da).

Como Marketing → access-denied.

## 5. Captación: ceros del embudo

`/estrategico/oe1/captacion` como Marketing.

**Esperado:** etapas en cero **aparecen**. Sin ficha de prospecto en velocidad. Financiero no entra.

## 6. Ciclo: solo Gerente; churn sin % si n bajo

`/estrategico/oe1/ciclo` como Gerente.

**Esperado:** catálogo de onboarding con ceros; `en_proceso` aparte; churn sin porcentaje
cerrado si n es bajo.

Como Financiero, Estrategia o Marketing → access-denied.

## 7. No hay CAC ni mercados

Ninguna de las cuatro contiene CAC, mercados ni mapa. No hay ruta UI para E1-05/07/08.

## 8. Un fallo no tumba la pantalla

Forzar error de red en un solo informe.

**Esperado:** esa zona en error; el héroe sigue.

## 9. Partner fuera

Como Partner, las cuatro URL → access-denied. El grupo Estratégico **no** le muestra OE1.

## 10. Rebuild

Tras implementar:

```powershell
docker compose -f docker/accidentes.yml up -d --build django frontend
docker ps --filter name=accidentes-django --filter name=accidentes-frontend
```

Ambos **Up**.

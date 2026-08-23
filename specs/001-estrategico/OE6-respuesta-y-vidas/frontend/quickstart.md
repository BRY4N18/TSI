# Quickstart — Cuatro pantallas Z de OE6

**Fecha:** 2026-08-18 · **Spec:** [`spec.md`](spec.md) · **Contrato UI:** [`contracts/ui-contract.md`](contracts/ui-contract.md)

Cada comprobación existe porque su fallo sería silencioso.

## Prerrequisitos

- Backend OE6 en servicio (`../backend/quickstart.md`). Doce GET.
- `accidentes-django` (:8000) y `accidentes-frontend` (:4200) **Up**.
- ClickHouse: `hecho_accidente` existe (puede tener 0 filas).

| Rol | Para qué |
|---|---|
| `DirectorOperaciones` | Las cuatro |
| `Gerente` | Las cuatro |
| `DirectorFinanciero` | Exclusión |
| `GerenteExitoCliente` | Exclusión |
| `PartnerIntegracion` | Exclusión |

## 1. Operaciones entra a Llegada; Finanzas no

Abrir `/estrategico/oe6/llegada` como Director de Operaciones.

**Esperado:** patrón Z. Héroe con **mediana, p95 y recuento**. `zona-parcial` si n bajo. Sin
mapa. Sin nombres. Sidebar grupo **Estratégico**. No hay botón de despacho.

Como Financiero, la misma URL → access-denied. El sidebar **no** muestra Llegada.

## 2. Vacío no es 0 min; p95 nulo no es el máximo

Período sin casos.

**Esperado:** zona vacía, MUST NOT titular 0 min.

Período con n menor al umbral de p95.

**Esperado:** p95 «sin dato»; la mediana puede seguir.

## 3. Esta pantalla no es el compuesto táctico

Los OT21–OT25 de Emergencias **siguen** y **no** comparten disposición ni query `comparacion`.
Operaciones ve **ambos** enlaces, en grupos distintos.

## 4. Diagnóstico: histórico, no ETA

`/estrategico/oe6/diagnostico` como Operaciones.

**Esperado:** tramos; automático vs manual; lectura de desviación **sin** la palabra ETA como
cifra. Partner no entra.

## 5. Ejecución: denominador y definición

`/estrategico/oe6/ejecucion`.

**Esperado:** tasas con denominador; abortos vacíos ≠ 0 %; cierres forzados declaran definición.

## 6. Personas: dato escaso ≠ 0 %

`/estrategico/oe6/personas`.

**Esperado:** impacto sin ceros fingidos; escaladas/evidencia declaran escasez si aplica; sin
identidad.

Como Partner o Éxito de Cliente → access-denied.

## 7. No hay mapa, ETA ni OE3

Ninguna de las cuatro contiene mapa, lat/lon, ETA como título ni informes de OE3.

## 8. Un fallo no tumba la pantalla

Forzar error de red en un solo informe.

**Esperado:** esa zona en error; el héroe sigue.

## 9. Rebuild

Tras implementar:

```powershell
docker compose -f docker/accidentes.yml up -d --build django frontend
docker ps --filter name=accidentes-django --filter name=accidentes-frontend
```

Ambos **Up**.

# Quickstart — Cuatro pantallas Z de OE3

**Fecha:** 2026-08-18 · **Spec:** [`spec.md`](spec.md) · **Contrato UI:** [`contracts/ui-contract.md`](contracts/ui-contract.md)

Cada comprobación existe porque su fallo sería silencioso.

## Prerrequisitos

- Backend OE3 en servicio (`../backend/quickstart.md`). Siete GET.
- `accidentes-django` (:8000) y `accidentes-frontend` (:4200) **Up**.
- ClickHouse: `hecho_accidente` existe (puede tener 0 filas).

| Rol | Para qué |
|---|---|
| `DirectorOperaciones` | Latencia, Calidad, Capacidad |
| `DirectorExpansion` | Capacidad, Respaldo |
| `Gerente` | Las cuatro |
| `DirectorTecnologico` | Exclusión |
| `DirectorFinanciero` | Exclusión |
| `PartnerIntegracion` | Exclusión |

## 1. Operaciones entra a Latencia; Expansión no

Abrir `/estrategico/oe3/latencia` como Director de Operaciones.

**Esperado:** patrón Z. Héroe con **p95, recuento y `cumple`**. Alcance de proceso (minutos), no
100 ms. `zona-parcial` si n bajo. Sin mapa. Sidebar grupo **Estratégico**. No hay botón de
despacho.

Como Expansión o Financiero, la misma URL → access-denied. El sidebar **no** muestra Latencia.

## 2. Vacío no es 0 min; p95 nulo no es el máximo

Período sin despachos.

**Esperado:** zona vacía, MUST NOT titular 0 min ni «meta cumplida».

Período con n menor al umbral de p95.

**Esperado:** p95 «sin dato»; el recuento puede seguir.

## 3. Esta pantalla no es OE6 Llegada ni el compuesto táctico

OE6 `/estrategico/oe6/llegada` **sigue** y **no** comparte disposición. Operaciones ve **ambos**
enlaces, en historias distintas (proceso vs persona). Los OT21–OT25 de Emergencias no cambian.

## 4. Calidad: campos a la vista; E3-11 sin semáforo

`/estrategico/oe3/calidad` como Operaciones.

**Esperado:** tasa de error con **lista de campos**; primer intento con denominador y grano de
intento; sin verde/rojo cerrado en E3-11. Expansión no entra.

## 5. Capacidad: sin capacidad ≠ infinito

`/estrategico/oe3/capacidad` como Expansión y como Operaciones.

**Esperado:** ratio por **condado**; condado con demanda y sin flota vigente se lee **sin
capacidad**; la lectura declara flota del período. Apoyo plegado = pérdida de señal con recuento.
Sin mapa. Tecnológico no entra.

## 6. Respaldo: denominador; Operaciones no lo ve

`/estrategico/oe3/respaldo` como Expansión.

**Esperado:** cobertura con denominador; vecino solo dado de alta ≠ respaldo. Vacío ≠ 0 %.

Como Operaciones, el sidebar **no** muestra Respaldo.

## 7. No hay mapa, región ni bloqueados

Ninguna de las cuatro contiene mapa, lat/lon, eje de región, uptime, puesta en marcha, margen,
pruebas ni reasignación cronometrada. No hay «20 000 días».

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

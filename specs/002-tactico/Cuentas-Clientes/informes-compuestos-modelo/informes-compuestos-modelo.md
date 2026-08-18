# Módulo: Informes Compuestos sobre el Modelo — Cuentas y Clientes

**Ubicación:** `specs/002-tactico/Cuentas-Clientes/informes-compuestos-modelo/`
**Departamento:** Cuentas y Clientes
**Feature paraguas:** `002-tactico`
**Sustrato:** [`specs/002-tactico/modelo-analitico/`](../../modelo-analitico/)

Índice global del módulo (no es una spec Speckit). La feature activa de Speckit es **una capa**,
apuntada por `.specify/feature.json`.

## Los 9 informes compuestos de OT04, OT17 y OT18

**Backend hecho.** Nueve GET sobre el modelo analítico (`/informes-tacticos/cuentas/<informe>`).
**Frontend hecho.** Tres pantallas Z (`ciclo`, `incorporacion`, `acceso`). Contienen **dos
indicadores BSC** que ahora tienen fuente: el churn por cohorte y el tiempo de onboarding.

## Es el dueño de `dim_cliente`, y llega el sexto

La dimensión la creó **Suscripciones**, porque fue el primer módulo que la necesitó. Este la
**amplía, no la recrea** — y es la prueba de que las dimensiones conformadas funcionan en la
dirección que más importaba: **el departamento dueño llega después y no tiene que rehacer nada**.

## Capas

| Capa | Ruta | Estado |
|------|------|--------|
| **Backend** | [`backend/`](./backend/) | hecha |
| **Frontend** | [`frontend/`](./frontend/) | hecha |

## Lo que hay que saber antes de tocar este departamento

**El onboarding solo registra lo completado.** No hay registro de abandono: se mide **por ausencia**,
contra un catálogo explícito de etapas esperadas. Un embudo mal diseñado mostraría **100 % de
finalización** y parecería un proceso perfecto.

**Las sesiones son eventos, no intervalos**: 513 inicios frente a 195 cierres.

**`Fact_Session` guarda el token de sesión** — no entra al modelo bajo ningún concepto.

⚠️ **Dos definiciones de pertenencia usuario↔cliente, y ninguna cubre el sistema**: 2 usuarios de 21.

## Autoridad, con un matiz ⚠️

El **Administrador** cubre todo el departamento. El **Director Tecnológico** cubre **solo la capa de
accesos técnicos** (OT18), no el ciclo de vida ni la incorporación — es la limitación del §5.1 del
SRS ya registrada en [`acceso-tactico.md`](../../acceso-tactico.md).

## Relación con los demás módulos del departamento

| Módulo | Qué es |
|---|---|
| [`../informes-tacticos-simples/`](../informes-tacticos-simples/) | Los 8 listados llanos |
| **`informes-compuestos-modelo/`** *(este)* | Los 9 informes agregados |

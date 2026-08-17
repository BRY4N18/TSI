# Módulo: Informes Compuestos sobre el Modelo — Red Operativa

**Ubicación:** `specs/002-tactico/Red-Operativa/informes-compuestos-modelo/`
**Departamento:** Red Operativa
**Feature paraguas:** `002-tactico`
**Sustrato:** [`specs/002-tactico/modelo-analitico/`](../../modelo-analitico/)

Índice global del módulo (no es una spec Speckit). La feature activa de Speckit es **una capa**,
apuntada por `.specify/feature.json`.

## Los 15 informes compuestos de OT11 a OT13

El backend **ya publica los quince**. A diferencia de Emergencias —donde 13 de 26 se vigilan y no
se vuelven a pintar—, aquí no hay vigilados: los quince entran en el frontend.

Ocho ya tenían sustrato (`dim_unidad` versionada y `hecho_estado_unidad`) cuando se especificó el
backend; los otros siete se construyeron ampliando el modelo (región versionada, baja, validación,
vecindad).

## Capas

| Capa | Ruta | Autoridad | Estado |
|------|------|-----------|--------|
| **Backend** | [`backend/`](./backend/) | Consultas sobre el modelo analítico y endpoints de lectura | hecha |
| **Frontend** | [`frontend/`](./frontend/) | Tres pantallas nuevas (patrón Z), **dos audiencias** | hecha — `/red-operativa/gestion/{flota,mercados,validacion}` |

**Pantallas (15 informes publicados, autoridad repartida):** Flota y cobertura · Mercados y
retirada *(Director de Expansión)* · Criterios de validación *(Director Tecnológico)*. El
Administrador ve las tres. Detalle en [`frontend/spec.md`](frontend/spec.md).

Rutas: `/red-operativa/gestion/flota` y `/mercados` (Expansión + Admin);
`/red-operativa/gestion/validacion` (Tecnológico + Admin). Sin tablero único de departamento.

No hay un tablero único de departamento: fusionar las dos materias anularía el §5.1. Los listados
simples (`../informes-tacticos-simples/` / `/red-operativa/informes`) no se tocan.

## Relación con los demás módulos del departamento

| Módulo | Qué es |
|---|---|
| [`../informes-tacticos-simples/`](../informes-tacticos-simples/) | Los 7 listados llanos, bajo el contrato común |
| **`informes-compuestos-modelo/`** *(este)* | Los 15 informes agregados |

## Autoridad repartida ⚠️

Este departamento **no tiene una jefatura única**: el §5.1 del SRS asigna el crecimiento al
**Director de Expansión** y los criterios de validación de región al **Director Tecnológico**. El
mapa exacto está en [`acceso-tactico.md`](../../acceso-tactico.md).

En pantalla eso significa **menús distintos**, no un ítem compartido con tarjetas filtradas. Solo
dos informes son de validación (tasa al primer intento y motivos de rechazo). El resto —incluida
la retirada y el tiempo de puesta en operación— es crecimiento.

# Módulo: Informes Compuestos sobre el Modelo — Red Operativa

**Ubicación:** `specs/002-tactico/Red-Operativa/informes-compuestos-modelo/`
**Departamento:** Red Operativa
**Feature paraguas:** `002-tactico`
**Sustrato:** [`specs/002-tactico/modelo-analitico/`](../../modelo-analitico/)

Índice global del módulo (no es una spec Speckit). La feature activa de Speckit es **una capa**,
apuntada por `.specify/feature.json`.

## Los 15 informes compuestos de OT11 a OT13

**Ninguno existe hoy.** A diferencia de Emergencias —donde 16 de 26 ya tenían endpoint—, la app de
informes tácticos no sirve nada de este departamento: los 15 son construcción nueva.

**Pero ocho ya tienen su sustrato listo.** `dim_unidad` versionada y `hecho_estado_unidad` se
construyeron con el modelo analítico y son justo lo que necesita el bloque de flota.

## Capas

| Capa | Ruta | Estado |
|------|------|--------|
| **Backend** | [`backend/`](./backend/) | activa |
| **Frontend** | *(pendiente)* | aplazada, como en todos los módulos tácticos |

## Relación con los demás módulos del departamento

| Módulo | Qué es |
|---|---|
| [`../informes-tacticos-simples/`](../informes-tacticos-simples/) | Los 7 listados llanos, bajo el contrato común |
| **`informes-compuestos-modelo/`** *(este)* | Los 15 informes agregados |

## Autoridad repartida ⚠️

Este departamento **no tiene una jefatura única**: el §5.1 del SRS asigna el crecimiento al
**Director de Expansión** y los criterios de validación de región al **Director Tecnológico**. El
mapa exacto está en [`acceso-tactico.md`](../../acceso-tactico.md).

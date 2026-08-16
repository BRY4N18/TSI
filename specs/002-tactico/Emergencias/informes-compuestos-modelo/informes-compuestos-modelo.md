# Módulo: Informes Compuestos sobre el Modelo — Emergencias

**Ubicación:** `specs/002-tactico/Emergencias/informes-compuestos-modelo/`
**Departamento:** Emergencias
**Feature paraguas:** `002-tactico`
**Sustrato:** [`specs/002-tactico/modelo-analitico/`](../../modelo-analitico/) — construido y verificado el 2026-08-14

Índice global del módulo (no es una spec Speckit). La feature activa de Speckit es **una capa**
(`backend` o `frontend`), apuntada por `.specify/feature.json`.

## Por qué este nombre y no `informes-tacticos-compuestos`

Ese nombre lo ocupa el módulo **sustituido**
([`../informes-tacticos-compuestos/`](../informes-tacticos-compuestos/)), cuyo diseño —una tabla y un
flujo por informe— es justo lo que el modelo analítico reemplaza. Renombrarlo costaría tocar 35
referencias en 19 ficheros, incluidas las URLs de Django, para un módulo que se va a borrar.

`informes-compuestos-modelo` marca la diferencia generacional de forma explícita, y será el nombre de
los módulos equivalentes en los otros siete departamentos.

## Los tres módulos de Emergencias, y qué es cada uno

| Módulo | Qué es | Estado |
|---|---|---|
| [`informes-tacticos-agregados/`](../informes-tacticos-agregados/) | El módulo **simples original**, renombrado. 16 endpoints implementados | 🟢 en producción |
| [`informes-tacticos-simples/`](../informes-tacticos-simples/) | Los 12 listados llanos pendientes, bajo el contrato común | ⚪ especificado, sin construir |
| [`informes-tacticos-compuestos/`](../informes-tacticos-compuestos/) | Diseño de una tabla por informe | ⛔ **sustituido** |
| **`informes-compuestos-modelo/`** *(este)* | Los 26 informes agregados, resueltos con consultas sobre el modelo | 🆕 |

## Capas

| Capa | Ruta | Autoridad | Estado |
|------|------|-----------|--------|
| **Backend** | [`backend/`](./backend/) | Consultas sobre el modelo analítico y endpoints de lectura | activa |
| **Frontend** | *(pendiente)* | Ubicación de cada informe en los tableros | aplazada, como en todos los módulos tácticos |

## Orden de trabajo

1. **Requiere el modelo analítico cargado.** Es prerrequisito duro: sin él no hay sustrato.
2. Backend primero: consultas y endpoints.
3. Frontend después, cuando se decida dónde vive cada informe.

## Lo que este módulo NO hace

**No crea una tabla por informe.** Si un informe necesita algo que el modelo no tiene, se **amplía el
modelo** siguiendo el procedimiento del
[§4.bis del contrato de esquema](../../modelo-analitico/contracts/esquema-analitico.md), y el informe
sigue siendo una consulta.

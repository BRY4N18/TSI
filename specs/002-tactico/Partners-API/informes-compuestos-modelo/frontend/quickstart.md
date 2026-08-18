# Quickstart — Tres pantallas Z de gestión (Partners y API)

**Fecha:** 2026-08-17 · **Spec:** [`spec.md`](spec.md) · **Contrato UI:** [`contracts/ui-contract.md`](contracts/ui-contract.md)

Cada comprobación existe porque su fallo sería silencioso.

## Prerrequisitos

- Backend de los 13 publicados en servicio (`../backend/quickstart.md`).
- `accidentes-django` (:8000) y `accidentes-frontend` (:4200) **Up**.
- Usuarios demo:

| Correo | Clave | Rol | Para qué |
|---|---|---|---|
| `director.tecnologico@demo.tsi.com` | `Tactico2026!` | DirectorTecnologico | Entra a las tres |
| `carlos.mendoza.admin@demo.tsi.com` | `password123` | Administrador | Entra a las tres |
| `partner.demo@demo.tsi.com` | `password123` | PartnerIntegracion | Exclusión |
| `maria.suarez.dev@demo.tsi.com` | `password123` | DesarrolladorAPIs | Exclusión (sigue en consola) |
| `sofia.castro.operador@demo.tsi.com` | `password123` | Operador | Exclusión |

## 1. El Director entra a Consumo; el Partner no

Abrir `http://localhost:4200/partners/gestion/consumo` como Director Tecnológico.

**Esperado:** patrón Z visible (`zona-heroe`, `zona-periodo`, `zona-visual`, `zona-lectura`). En
el héroe se ven **p95, media y muestras en el mismo bloque**. Declaración de que esta latencia
**no es** la del reporte operativo. No hay botones de revocar ni de cupo.

Como Partner, la misma URL → access-denied. El sidebar **no** muestra los tres enlaces de
gestión. «Estado de mi acceso» y «Mi consumo» siguen ahí para el Partner.

Como Desarrollador de APIs: «Registros de API» y «Reporte de consumo» siguen; las tres de
gestión **no**.

## 2. El trío no se puede romper

En Consumo, con un período que tenga llamadas (p. ej. el mes en curso) o uno pobre (pocas
filas).

**Esperado:** no existe un estado en el que se vea la p95 y no se vea, **en el mismo bloque**,
el número de muestras. Si `percentil_fiable` viene en 0, la fila **sigue** y se lee no fiable.
Un período 1999 → vacío, no 0 ms.

Taxonomía: tres clases distinguibles si hay 429, 403 y 500; **no** hay un total que las sume.
Comparativa: un partner sin llamadas **aparece en cero**.

## 3. Esta pantalla no es el reporte operativo

`/partners/consola/reportes` (como Administrador o Desarrollador) **sigue existiendo** y **no**
se parece a Consumo (otra disposición, sin las cuatro zonas Z, sin p95 con muestras).

`/partners/portal/consumo` (como Partner) sigue siendo «Mi consumo».

## 4. Incorporación: dos `'v1'` y cuatro motivos

`/partners/gestion/incorporacion` como Director.

**Esperado:** adopción por **(servicio, versión)**; si hay dos servicios con `'v1'`, **dos**
agrupaciones. Declaración de versión **derivada**. Motivos: revocada ≠ caducada. Tiempo: en
proceso **no** se lee como cero días. Rechazo, si se abre el detalle, por motivo, sin persona.

## 5. Entrega: el denominador son todos

`/partners/gestion/entrega`

**Esperado:** héroe = % con integración, total de clientes y meta ≥70 %. Si hay clientes sin
partner, el % es **menor que 100 %**. Visual = portal y API por separado. **Ninguna** zona de
mapa o «fuera de zona».

## 6. Un fallo no tumba la pantalla

Forzar error de red en un solo informe (p. ej. `comparativa`).

**Esperado:** esa zona en error; héroe y visual siguen.

## 7. Los listados, la consola y el portal no cambiaron

`/partners/informes` sigue siendo el índice de listados (el Partner entra a los suyos).
`/partners/consola/logs` sigue mostrando el detalle operativo. **No** hay tarjetas nuevas ahí.

## 8. Nada sensible

Recorrer las tres: ninguna IP, secreto, contacto técnico, ejecutor ni mapa. Ninguna fila abre
la consola de logs.

## Lo que este quickstart NO comprueba

- Exportar (no existe).
- Editor de percentil o mínimo de muestras (no existe en esta capa).
- Retirar métricas/reporte operativos (fuera de alcance).
- Frontend de Cuentas u otros departamentos.
- Ampliar el acceso a Partner o DesarrolladorAPIs (el backend no lo admite).

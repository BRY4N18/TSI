# Quickstart — Tres pantallas Z de gestión (Soporte al Cliente)

**Fecha:** 2026-08-17 · **Spec:** [`spec.md`](spec.md) · **Contrato UI:** [`contracts/ui-contract.md`](contracts/ui-contract.md)

Cada comprobación existe porque su fallo sería silencioso.

## Prerrequisitos

- Backend de los 9 publicados en servicio (`../backend/quickstart.md`).
- `accidentes-django` (:8000) y `accidentes-frontend` (:4200) **Up**.
- Usuarios demo:
  - Gerente de Éxito del Cliente: `gerente.exito@demo.tsi.com` / `Tactico2026!`
  - Agente: `lucia.vera.soporte@demo.tsi.com` / `password123`
- Un Cliente o un Operador de demo para la exclusión (`password123` si existen en este entorno;
  `director.tecnologico@demo.tsi.com` / `Tactico2026!` también sirve para comprobar que **no** entra).

## 1. El Gerente entra a Cumplimiento; el Cliente no

Abrir `http://localhost:4200/soporte-cliente/gestion/cumplimiento` como Gerente.

**Esperado:** patrón Z visible (`zona-heroe`, `zona-periodo`, `zona-alcance`, `zona-visual`,
`zona-lectura`). Alcance **todos**. En el héroe se ven **cumplimiento y % sin compromiso en el
mismo bloque**, con la meta ≥95 %. No hay botones de ticket.

Como Cliente (o Operador), la misma URL → access-denied. El sidebar **no** muestra los tres
enlaces de gestión. «Informes de soporte» y «Mis tickets» siguen ahí para el Cliente.

## 2. El par no se puede romper

En Cumplimiento, con un período que tenga tickets (p. ej. 2026).

**Esperado:** no existe un estado en el que se vea el % de cumplimiento y no se vea, **en el
mismo bloque**, el % sin compromiso. Un período 1999 → vacío, no 0 %. Si no hay tickets con
compromiso → **sin dato**, no 0 %.

Los tres motivos sin compromiso son distinguibles (pendiente / sin compromiso / sin config) en
el héroe, tamaño menor. Tickets por servicio están **plegados**; al abrirlos, «sin servicio» y
su declaración.

## 3. El agente ve lo mismo, acotado

La misma URL como agente de soporte.

**Esperado:** el mismo patrón Z. `zona-alcance` lee **propios**. Rendimiento, si hay filas,
muestra **clave** de agente, no nombre. Una reapertura no se lee como resolución extra.

## 4. Cola tiene período y no es el dashboard

`/soporte-cliente/gestion/cola` como Gerente.

**Esperado:** el tablero cambia al cambiar el período. La declaración de que **difiere del
tablero operativo** está visible. `/soporte-cliente/dashboard` sigue existiendo y **no** se
parece a esta pantalla (otra disposición, sin las cuatro zonas Z).

Evolución: un día sin tickets está en **cero**, no hay un hueco. Escalado: dos columnas;
**no** hay un total que las sume.

## 5. Un fallo no tumba la pantalla

Forzar error de red en un solo informe (p. ej. `rendimiento-agentes`).

**Esperado:** esa zona en error; héroe y visual siguen.

## 6. Tendencias: la cola que crece y el servicio que no se finge

`/soporte-cliente/gestion/tendencias`

**Esperado:** héroe = saldo/acumulado del último día. Visual = dos series diarias con días en
cero presentes. Lectura = reincidencia por clave de cliente. **Ninguna** zona se titula por
servicio ni muestra una columna de servicio. La declaración del eje está visible.

## 7. Los listados, la cola y el dashboard no cambiaron

`/soporte-cliente/informes` sigue siendo el índice de listados (el Cliente entra).
`/soporte-cliente/cola` sigue siendo la cola del agente. `/soporte-cliente/dashboard` sigue
siendo el tablero operativo. **No** hay tarjetas nuevas ahí.

`DesarrolladorAPIs` / `DirectorTecnologico` siguen viendo el dashboard operativo y **no** los
tres enlaces de gestión.

## 8. Nada sensible

Recorrer las tres: ningún asunto, mensaje, nota, nombre de agente, nombre de cliente ni mapa.
Ninguna fila abre el detalle de un ticket.

## Lo que este quickstart NO comprueba

- Exportar (no existe).
- Editor de `granularidad`, `eje` o `minimo` (no existe en esta capa).
- Retirar el tablero operativo (fuera de alcance).
- Frontend de Emergencias, Red, Ventas o Suscripciones.
- Ampliar el acceso a Cliente (el backend no lo admite).

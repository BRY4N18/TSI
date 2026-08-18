# Quickstart — Tres pantallas Z de gestión (Ventas y CRM)

**Fecha:** 2026-08-17 · **Spec:** [`spec.md`](spec.md) · **Contrato UI:** [`contracts/ui-contract.md`](contracts/ui-contract.md)

Cada comprobación existe porque su fallo sería silencioso.

## Prerrequisitos

- Backend de los 13 publicados en servicio (`../backend/quickstart.md`).
- `accidentes-django` (:8000) y `accidentes-frontend` (:4200) **Up**.
- Usuarios demo (clave `Tactico2026!`):
  - Director de Marketing: `director.marketing@demo.tsi.com`
  - Gerente de Ventas: `lucia.ramos.ventas@demo.tsi.com`
- Un Gerente de Cuentas Públicas o un Operador de demo para la exclusión.

## 1. El Director entra a Embudo, Cuentas Públicas no

Abrir `http://localhost:4200/ventas-crm/gestion/embudo` como Director.

**Esperado:** patrón Z visible (`zona-heroe`, `zona-periodo`, `zona-alcance`, `zona-visual`,
`zona-lectura`). Alcance **todos**. Convertido y perdido no son un solo grupo.

Como Gerente de Cuentas Públicas (o Operador), la misma URL → access-denied. El sidebar **no**
muestra los tres enlaces de gestión.

## 2. El ejecutivo ve lo mismo, acotado

La misma URL como Gerente de Ventas.

**Esperado:** el mismo patrón Z. `zona-alcance` lee **propios**. No hay botones de asignar ni de
mover etapa.

## 3. El estancado no parece el más rápido

Período con datos reales (p. ej. 2026) en Embudo.

**Esperado:** el visual de permanencia muestra `abiertos`. Quien no se ha movido no aparece como
el más veloz de su etapa. Un período 1999 → vacío, no 0 %.

## 4. Captación no es un CAC

`/ventas-crm/gestion/captacion`

**Esperado:** héroe = volumen (Desconocido suma si hay filas). Visual = tasa con denominador.
Lectura = convertidos **con** `nota_indicador` visible. Ninguna zona se llama CAC ni muestra
coste.

## 5. Un fallo no tumba la pantalla

Forzar error de red en un solo informe (p. ej. `motivos-perdida`).

**Esperado:** esa zona en error; héroe y visual siguen.

## 6. Nutrición vacía no es un tablero de ceros

`/ventas-crm/gestion/nutricion` en el entorno actual (fuentes de demo/aviso vacías).

**Esperado:** vacío explícito, distinguible de «hubo demo y no se usó». Si más adelante hay
datos: dos grupos con denominador; aviso ignorado fuera de la mediana; reglas de disparo
**plegadas**. Recuento de bloques de la vista principal ≤ 8.

## 7. Los listados y el pipeline no cambiaron

`/ventas-crm/informes` sigue siendo el índice de listados (Cuentas Públicas entra).
`/ventas-crm/pipeline` sigue siendo el tablero operativo. **No** hay tarjetas nuevas ahí.

## 8. Nada sensible

Recorrer las tres: ningún nombre, correo, teléfono ni mapa de prospecto. La carga, si se abre el
detalle, muestra **clave** de ejecutivo, no persona.

## Lo que este quickstart NO comprueba

- Exportar (no existe).
- Editor de `pesos_etapa` (no existe en esta capa).
- Frontend de Emergencias o Red Operativa.
- Ampliar el acceso a Gerente de Cuentas Públicas (el backend no lo admite).

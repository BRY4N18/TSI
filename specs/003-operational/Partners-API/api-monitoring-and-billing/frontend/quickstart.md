# Quickstart — Validación del frontend de Monitoreo y Facturación

Guía de validación end-to-end de la capa de presentación de #08. No contiene código de
implementación: eso vive en `tasks.md`.

## Prerrequisitos

- Backend de #08 implementado (71/71) **y los deltas `BE-DELTA-04`/`BE-DELTA-05` cerrados**, o la
  cuarta superficie no tendrá de dónde leer.
- Backend de #07 implementado: el portal y `GET /partners/me` son suyos.
- `frontend/` con dependencias instaladas.
- **No hay Chrome en esta máquina**: los tests usan Edge.
  ```bash
  CHROME_BIN="C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
  ```

> **`tsc --noEmit` NO valida las plantillas de Angular.** Un `@else if (cond; as x)` inválido o una
> comilla invertida dentro de un comentario HTML compilan en TypeScript y revientan en `ng test`.
> En #07 ocurrió cinco veces. **El gate real es `ng test`.**

## 1) Suite de la capa

```bash
cd frontend && npx ng test --watch=false --browsers=ChromeHeadless
```

Línea base sin regresiones: la que deje #07 frontend (**459 tests**, cobertura del módulo 91,6 %).

## 2) Escenarios de validación

### Escenario A — El partner ve su consumo (US-FE-1, FR-UI-101/104/105)

Entrar a `/partners/portal/consumo` como `PartnerIntegracion`.

Debe verse: llamadas, errores, latencia media, el badge **`Producción`** en texto y la marca del
último dato disponible. Ninguna cifra sin su contexto de período.

### Escenario B — 🎯 El exceso NO parece un fallo (FR-UI-103, RN-APM-002)

**El escenario que más importa de esta capa.** Partner con consumo por encima del 100 % del cupo.

Debe verse el excedente como **coste previsto** con su importe, y la frase de que el servicio no se
interrumpe.

**Debe fallar la validación si aparece**: el token `alerta-critica` o `alerta-media` en el bloque de
cupo, un icono de severidad, o cualquiera de las palabras «bloqueado», «cortado», «límite superado».

> Hay un test automático que lo comprueba sobre las plantillas. Existe porque este es el punto donde
> un desarrollador bienintencionado «arreglará» el medidor poniéndolo en rojo, creyendo que corrige
> un bug.

### Escenario C — Sin cupo configurado no hay porcentaje (FR-UI-102)

Partner con `limitellamadasmes` en el centinela.

Debe verse **«No aplica — sin cupo configurado»**. **Nunca `0 %`.**

### Escenario D — Sin tarifa no hay importe (FR-UI-107)

Partner con excedente cuyo plan no tiene `precio_excedente_llamada`.

Debe verse el número de llamadas excedentes y el importe como **«No aplica — sin tarifa
configurada»**. **Nunca `0,00`.**

### Escenario E — 🎯 Un mes sin consumo no es un error (FR-UI-123)

Reporte de un período sin llamadas.

Debe verse **ceros** con el copy «Este período no registró consumo. No es un error». Debe usar
`app-list-empty-state`, **no** `app-list-error-state`, y **no** debe ofrecer «Reintentar».

### Escenario F — El partner diagnostica sus errores (US-FE-2)

Partner con un `403`, un `429` y un `500` recientes.

Los tres deben distinguirse: el `429` como **«Límite de ritmo»** con token neutro, el `403` como
revisión de la petición, y el `500` como error de plataforma. El `429` debe indicar que **no cuenta
como consumo facturable**.

### Escenario G2 — 🎯 Los filtros consultan a la base, no a la memoria

Partner con 30 llamadas repartidas en 200, 429 y 500, y una página de 10.

Filtrar por `500` debe devolver **las 10** que hay en todo el historial, no las
3 que caben en la primera página. Con filtrado en memoria este escenario daría
3, y el usuario concluiría que su plataforma falla menos de lo que falla.

Verificar también que **«Cargar más» conserva el filtro** y que cambiar un
filtro **reinicia** la paginación.

### Escenario G — La consola exige elegir partner (contrato de UI)

Entrar a `/partners/consola/logs` como `DesarrolladorAPIs` sin partner seleccionado.

Debe verse un `empty-state` que pide elegir partner — **no** una tabla vacía ni un error 400 crudo.
El endpoint devuelve 400 sin `idpartner` y la UI se adelanta.

### Escenario H — 🎯 La cola de excepciones (US-FE-5, FR-UI-131/132)

Como `Administrador`, con una factura de reintentos agotados y un partner no tarificable.

Deben aparecer **los dos, distinguidos por tipo**. El no tarificable debe llevar la columna de
importe **vacía** (no `0,00`) y su acción sugerida debe apuntar a configurar la tarifa del plan, no
a emitir una factura que no existe.

**No debe haber ningún botón de emitir** (FR-UI-135).

### Escenario I — El suspendido sigue viendo su consumo (RN-APM-017)

Partner con `activo = false` en `/partners/portal/consumo`.

Debe cargar las métricas con normalidad, más un banner informativo de su situación. **No** debe
bloquearse: es lectura, y es lo que le permite entender qué pasó.

### Escenario J — Cada rol ve solo lo suyo (US-FE-6)

| Rol | Ve | No ve |
|---|---|---|
| `PartnerIntegracion` | Mi consumo | Consola, excepciones |
| `DesarrolladorAPIs` | Consola, reporte | Excepciones |
| `Administrador` | Reporte, excepciones | — |

Verificar en el sidebar **y** escribiendo la ruta a mano: el guard debe cortar en los dos casos.

### Validaciones transversales

| Comprobación | Esperado |
|---|---|
| Las cuatro superficies con datos asíncronos | Usan `app-list-loading-skeleton` / `app-list-error-state` / `app-list-empty-state` |
| Un 403 | `error-state` **sin** botón «Reintentar» |
| Identificadores y cifras | `JetBrains Mono` |
| Ningún PK tecleado por el usuario | Partners se eligen **por nombre** |
| Tablas de este módulo | Solo `eye` — sin `pencil` ni `trash` (append-only) |
| Auto-refresco | Existe y está **apagado** al entrar |
| Paginación en la consola | «Cargar más» por cursor, conservando los filtros |
| Filtros de la consola | **Todos** viajan al servidor; ninguno se resuelve en memoria |

## 3) Criterios de salida

- [ ] Escenarios A–J en verde, con **especial atención a B, E y H**.
- [ ] SC-001…007 de [`spec.md`](./spec.md) verificados.
- [ ] Test de invariante en verde: ningún token de severidad en el bloque de cupo.
- [ ] `ng test` completo sin regresiones sobre la línea base de #07.
- [ ] Las cuatro superficies en `nav-links.ts` con sus roles y en la matriz rol→navegación.

## 4) Verificación manual contra la app real

**Diferida hasta que se indique.** Los escenarios B, H e I merecen mirarse en pantalla aunque los
tests pasen: los tres dependen de que el **copy** comunique lo correcto, y un test comprueba que un
token no está, no que la frase se entienda.

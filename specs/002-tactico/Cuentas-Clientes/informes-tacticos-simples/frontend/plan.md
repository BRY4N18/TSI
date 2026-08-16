# Plan — Informes Tácticos Simples de Cuentas y Clientes (Frontend)

**Fecha:** 2026-08-15 · **Spec:** [`spec.md`](spec.md)
**Contrato común:** [`../../../contrato-informes-simples-frontend.md`](../../../contrato-informes-simples-frontend.md)

---

## 1. Stack y convenciones — se heredan, no se deciden

| Aspecto | Lo que ya usa el proyecto |
|---|---|
| Framework | Angular 19, componentes **standalone**, `ChangeDetectionStrategy.OnPush` |
| Estado | **Signals** (`signal`, `computed`), `inject()` |
| Estilos | Tailwind v4 con los tokens del design system (`bg-bg-surface`, `text-text-primary`…) |
| Pruebas | Karma + Jasmine, `.spec.ts` junto al fichero, `data-testid` para consultar |
| Rutas | `loadComponent` perezoso por módulo, con `canActivate` de rol |

Nada de esto se replantea aquí.

---

## 2. Lo que ya está construido y **no** se toca

`frontend/src/app/shared/informes/` — la capa compartida, con 42 pruebas:

| Pieza | Responsabilidad |
|---|---|
| `informes-listado.types.ts` | Envelope, columnas, filtros, error |
| `informes-listado.service.ts` | GET para los 32 endpoints; clasifica el error |
| `informes-listado.store.ts` | Filas, filtros, pila de cursores, error |
| `informes-listado.component.ts` | Tabla, estados, aviso de alcance, paginación |
| `informes-filtros.component.ts` | Barra de filtros desde la declaración |

> ⚠️ **Si al implementar hiciera falta modificarla, la generalización quedó incompleta** y la
> corrección va allí, no en una pantalla. Es la misma regla que gobernó `core/informes/` en backend.

---

## 3. Estructura a crear

```
frontend/src/app/modules/cuentas-clientes/informes/
    cuentas-clientes-informes.routes.ts
    guards/informes-cuentas.guard.ts
    guards/informes-accesos-tecnicos.guard.ts
    definiciones/                      ← columnas y filtros de los 8 listados
        informes-cuentas.definiciones.ts
    pages/informe/informe.page.ts      ← UNA página, parametrizada por definición
    pages/indice/indice-informes.page.ts
```

### 3.1 Una sola página, no ocho

Los ocho listados se diferencian **solo** en su declaración de columnas y filtros. Ocho ficheros de
página serían ocho copias del mismo `template` con distinto arreglo de columnas — y la novena copia
sería la que se olvidara del aviso de error.

La ruta lleva el identificador del informe, la página resuelve su definición y se la pasa a la capa
compartida. **Añadir un listado nuevo es añadir una entrada al catálogo de definiciones.**

### 3.2 Dos guards, porque los permisos son dos

El backend declara **Administrador** en siete listados y **Administrador o Director Tecnológico** en
`accesos-tecnicos`. Un guard único con la unión de roles daría al Director Tecnológico acceso a los
siete — justo lo que `acceso-tactico.md` §5 marca con ⚠️ como contradicción del SRS.

---

## 4. Decisiones de esta capa

### D1 — Las enumeraciones se copian del contrato, y eso es una deuda declarada

Los valores de `estado` en `cuentas-por-estado` los declara el OpenAPI del backend. La pantalla los
necesita para pintar el desplegable, y **no hay forma de leerlos en tiempo de ejecución**: el backend
no expone un endpoint de metadatos.

Se copian en la definición, **con el comentario de dónde vienen**. Es la misma clase de duplicación
que el backend evitó importando constantes del dominio, y aquí no se puede evitar — así que se hace
visible en vez de disimularla.

**Consecuencia:** si el backend añade un estado, el desplegable no lo ofrecerá hasta que alguien
actualice la definición. No es un fallo silencioso —el filtro seguiría funcionando escrito a mano—
pero sí una desactualización posible. Una prueba compara la definición contra el contrato OpenAPI
para que la divergencia salte.

### D2 — El estado vacío de transferencias dice por qué está vacío

`transferencias-propiedad` devolverá cero filas mientras la decisión **#28** siga abierta. Un «no hay
transferencias» genérico haría que alguien buscara el defecto en el código.

Su definición lleva un mensaje propio que dice que **la fuente aún no se alimenta**. Cuando #28 se
resuelva, se quita el mensaje y ya.

### D3 — El índice del departamento se genera del catálogo

La lista de informes de la pantalla índice sale del mismo catálogo de definiciones que las páginas.
Mantener una lista aparte garantizaría que algún día ofreciera un informe que ya no existe.

---

## 5. Riesgos

| Riesgo | Mitigación |
|---|---|
| La capa compartida no basta y hay que tocarla | Es **la señal que este piloto busca**. Si pasa, se corrige allí y se anota |
| El enum copiado se desactualiza (D1) | Prueba que lo compara contra el contrato OpenAPI |
| `acotado_a` no se ejercita | Declarado en la spec; se cierra con el siguiente departamento acotado |
| Alguien lee el vacío de transferencias como defecto | Mensaje propio (D2) |

---

## 6. Verificación

1. Pruebas de componente por definición y por comportamiento (columnas, filtros, errores, ausentes).
2. Suite completa del frontend verde.
3. **Recorrido en navegador contra el stack levantado** — es lo que este piloto tiene que probar y lo
   que ninguna prueba unitaria sustituye.

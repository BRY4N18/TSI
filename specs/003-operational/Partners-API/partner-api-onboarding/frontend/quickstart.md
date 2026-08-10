# Quickstart — Validación del frontend de Onboarding de Partners API

Escenarios que prueban la capa **end-to-end contra el backend real**. No sustituyen a los
`*.spec.ts`: estos verifican lo que un test de componente no puede — que la interfaz comunique lo
correcto a una persona.

## Prerrequisitos

```bash
docker compose -f docker/docker-compose.infraestructura.yml up -d
```

```bash
cd backend; python manage.py runserver
```

```bash
cd frontend; npm start
```

Datos base: un cliente con **suscripción vigente** y el rol `PartnerIntegracion` (idrol 15)
asignado al usuario de prueba. Si `Dim_VersionContratoAPI` está vacío, sembrar el catálogo:

```bash
python database/seed_versiones_contrato.py
```

---

## A. Registro sobre cliente sin suscripción → 422 explicado (FR-UI-006)

1. Entrar como Administrador → `/partners/consola` → «Registrar partner».
2. Elegir un cliente **sin** suscripción vigente y guardar.

**Esperado:** banner que explica que el cliente no tiene suscripción vigente y que se resuelve en
Suscripciones. **No** un «Error inesperado» ni un 422 crudo.

## B. Segundo partner sobre el mismo cliente → 409 con enlace (FR-UI-005)

1. Registrar un partner sobre un cliente válido.
2. Registrar otro sobre **el mismo cliente**.

**Esperado:** «Este cliente ya tiene un partner registrado» **con un enlace al partner existente**.
El enlace debe navegar a su detalle. Verifica que la UI usa el `idpartner_existente` que el backend
devuelve en el cuerpo del 409, en vez de descartarlo.

## C. Emitir sin plan → el CTA ni siquiera aparece (FR-UI-016)

1. Entrar como el partner recién registrado (aún sin plan) → `/partners/portal`.

**Esperado:** en lugar del botón «Emitir credencial», el copy que explica que un administrador debe
asignar el plan. **El escenario correcto es que el 409 `sin_plan` nunca llegue a ocurrir.**

## D. El secreto se entrega una sola vez (FR-UI-017) — **el escenario crítico**

1. Con el plan ya asignado, emitir una credencial de pruebas llamada `plataforma-siniestros`.

**Esperado, punto por punto:**
- Navega a una página dedicada, no a un modal ni a un toast.
- El aviso de irreversibilidad aparece **antes** del valor.
- El botón de salida está **deshabilitado** hasta marcar el checkbox de confirmación.
- `Esc` y el click fuera **no cierran nada**.

2. Con DevTools abiertas, comprobar que el secreto **no** está en `localStorage`, `sessionStorage`,
   la URL ni `document.title`.
3. **Recargar la página (F5).**

**Esperado:** estado vacío que explica que el secreto ya no está disponible y que puede emitirse
otra credencial sin interrumpir las existentes. **No** una pantalla en blanco ni un error.

## E. Reintento por red no duplica la credencial (FR-UI-018)

1. En DevTools → Network, activar throttling **Offline**.
2. Emitir una credencial. Esperar el error.
3. Volver a **Online** y pulsar «Reintentar».

**Esperado:** una **sola** credencial creada, y el secreto mostrado es el mismo. Verificar en
`/partners/portal` que no aparecen dos credenciales con el mismo nombre. Este escenario es la razón
de ser de la Decisión 7: sin `Idempotency-Key` se crearían dos y el primer secreto se perdería.

## F. Producción y pruebas coexisten (FR-UI-013)

1. Como partner en «Pruebas activo», solicitar producción.
2. Como **Administrador**, aprobar desde la cola de solicitudes.
3. Volver al portal del partner.

**Esperado:** dos grupos visibles, «Pruebas» y «Producción», **ambos con credenciales activas**. La
credencial de producción muestra «No expira» —nunca una fecha del año 9999— y la de pruebas
conserva su vencimiento. Ningún mensaje sugiere que lo de pruebas haya terminado.

## G. Solo el Administrador resuelve (FR-UI-011)

1. Entrar como **Desarrollador de APIs** → `/partners/consola/solicitudes`.

**Esperado:** la cola es visible (puede consultarla) pero **sin** acciones de aprobar/rechazar.

2. Escribir a mano `/partners/consola/solicitudes/{id}/resolver`.

**Esperado:** redirección a `access-denied`. **No** llegar al formulario y fallar al enviar.

## H. Rechazo con motivo redactado (FR-UI-010)

1. Como Administrador, rechazar una solicitud dejando el motivo vacío.

**Esperado:** error del **campo**, y la petición ni siquiera sale (el 422 `motivo_requerido` no
debería alcanzarse desde esta UI).

2. Escribir un motivo real y confirmar.

**Esperado:** el partner vuelve a **«Pruebas activo»** —no a «Registrado»— y puede volver a
solicitar. Comprobar en el buzón del contacto técnico que el motivo llegó **literal**.

## I. Dos administradores resuelven a la vez (contrato de consola)

1. Abrir la cola en dos sesiones de Administrador.
2. Aprobar la misma solicitud en ambas.

**Esperado en la segunda:** Alert modal «Esta solicitud ya fue resuelta por otro administrador» y
**refresco automático** de la cola. El copy no debe culpar al usuario: no hizo nada mal.

## J. Estados no felices (FR-UI-023)

1. Detener el backend (`Ctrl+C`) y recargar `/partners/consola`.

**Esperado:** `app-list-error-state` con botón «Reintentar» — no un spinner infinito ni una tabla
vacía. Al levantar el backend, «Reintentar» debe funcionar sin recargar la página.

2. Con el backend lento, observar el estado de carga.

**Esperado:** *skeleton* con la silueta de las filas. **Nunca** un spinner centrado (design-system
§ 5).

## K. Accesibilidad y responsividad

1. Reducir a **<640px**.

**Esperado:** las tablas colapsan a cards; el workpanel ocupa la página completa; el sidebar pasa a
hamburguesa.

2. Alternar tema claro/oscuro.

**Esperado:** ningún hex hardcodeado — todos los badges de estado y entorno cambian con el tema.

3. Simular daltonismo (DevTools → Rendering → Emulate vision deficiencies).

**Esperado:** pruebas y producción siguen siendo distinguibles **por ícono, etiqueta y agrupación**.
Este es el criterio real de la Decisión 5: si al quitar el color se vuelven indistinguibles, el
diseño está mal.

## L. Ningún PK visible (FR-UI-025)

Recorrer las seis páginas.

**Esperado:** en ningún formulario se teclea `idcliente`, `idpartner` ni `idcredencial`. El cliente
se elige por nombre y el servicio del contrato también.

---

## Tests automatizados

```bash
cd frontend; npm test
```

Cobertura esperada por `tasks.md`: cada página con su `*.spec.ts`, cada guard con el suyo, y el
servicio de API con tests de mapeo de errores. Los escenarios **D, E, G y K.3** deben tener además
su test automatizado — son los cuatro donde un fallo silencioso tiene consecuencias reales
(secreto perdido, credencial duplicada, control de acceso saltado, entorno confundido).

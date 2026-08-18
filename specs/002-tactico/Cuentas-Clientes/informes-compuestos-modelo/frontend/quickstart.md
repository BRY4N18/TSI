# Quickstart — Tres pantallas Z de gestión (Cuentas y Clientes)

**Fecha:** 2026-08-18 · **Spec:** [`spec.md`](spec.md) · **Contrato UI:** [`contracts/ui-contract.md`](contracts/ui-contract.md)

## Prerrequisitos

- Backend de los 9 publicados en servicio.
- Usuarios demo: Administrador, Director Tecnológico, Cliente, Operador.

## 1. El Administrador entra a Ciclo; el Tecnológico no

Abrir `/cuentas-clientes/gestion/ciclo` como Administrador.

**Esperado:** patrón Z. Churn por cohorte de alta. Ocupación con cobertura. Riesgo: sin actividad conocida ≠ 0 días. Antigüedad en detalle plegado. Sin botones de baja.

Como Director Tecnológico, la misma URL → access-denied. El sidebar **no** muestra Ciclo ni Incorporación. Sí muestra Acceso.

Como Cliente u Operador: ninguna de las tres.

## 2. Cobertura y vacío

Ocupación: usuarios, tope y cobertura en el mismo bloque. Cliente sin plan → sin dato, no 0 %. Período 1999 → vacío, no churn 0 %.

## 3. Incorporación: etapa fantasma

`/cuentas-clientes/gestion/incorporacion` como Administrador.

**Esperado:** héroe con mediana y `en_proceso` aparte. Embudo con etapas en cero. Nota de catálogo. El Tecnológico no entra.

## 4. Acceso: solape, no logins

`/cuentas-clientes/gestion/acceso` como Tecnológico o Administrador.

**Esperado:** `concurrencia_maxima` e inicios juntos. `sesiones_sin_cierre` a la vista. Roles: cero filas si no hay política; si hay, `idusuario` sin nombre.

## 5. Un fallo no tumba la pantalla

Forzar error de red en un solo informe. Esa zona en error; el resto sigue.

## 6. Los listados y la cuenta no cambiaron

`/cuentas-clientes/informes` sigue siendo el índice. `/cuentas-clientes/gestion-cuenta` intacto.

## Lo que este quickstart NO comprueba

- Exportar, editor de pares, rebuild Docker (aplazado a petición).

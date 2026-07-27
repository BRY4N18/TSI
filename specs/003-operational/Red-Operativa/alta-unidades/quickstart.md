# Quickstart - Validación de Alta y Configuración de Unidades de Emergencia

Guía de validación end-to-end contract-first para CU-O54, CU-O56, CU-O57, CU-O58.
**CU-O59 eliminado (2026-07-24):** disponibilidad solo vía **CU-O30** en `evidencia-unidad`.

## Prerequisitos

- Contrato: `contracts/alta-unidades.openapi.yaml` **v1.1.0**
- Spec y plan en `specs/003-operational/Red-Operativa/alta-unidades/`
- Proveedor con cuenta `Dim_Cliente.estado=Activo` y rol Cliente/Proveedor (admin_local)
- Un `Dim_Condado` existente para `idcondado`
- Migración cruzada de `despacho-inteligente` aplicada (`idcondado`)

## 1) Validar contrato REST (backend contract-first)

| Método | Ruta | UC | Rol |
|--------|------|-----|-----|
| POST | `/api/v1/red-operativa/unidades` | O54 | Proveedor |
| POST | `/api/v1/red-operativa/unidades/importacion-lote` | O56 | Proveedor |
| GET | `/api/v1/red-operativa/unidades/{id}` | — | Proveedor (propia) |
| PATCH | `/api/v1/red-operativa/unidades/{id}` | O57 | Proveedor |
| POST | `/api/v1/red-operativa/unidades/{id}/baja` | O58 | Proveedor |
| POST | `/api/v1/red-operativa/unidades/{id}/reactivar` | O58 | Proveedor |

**No existe** `POST .../disponibilidad` en este módulo (usar CU-O30).

Convenciones (`api-standards.md`): envelope `{data, meta}` / `{error, detail, code}`; `Idempotency-Key` en escritura.

## 2) Validar flujo backend

### Escenario A — Alta individual (O54)

1. Login como Proveedor (admin_local Activo) → JWT.
2. `POST /red-operativa/unidades` **sin** `idcliente` (se toma del JWT) → `201`.
3. Login Administrador → mismo POST → `403` (sin override).

### Escenario B — Lote + gmail (O56)

1. CSV con columnas: `idcondado,tipopropiedad,placa,contactoproveedor,unidademergencia,tipounidademergencia,gmail`.
2. Una fila con `gmail` inválido → `insertadas=0`, `usuarios_creados=0`.
3. Lote válido → N unidades + N usuarios/credenciales + invitación SMTP.

### Escenario C — Edición / Baja (O57/O58)

1. Solo unidades con `idcliente` del Proveedor; unidad ajena → `403`.
2. Despacho activo: edición crítica sin confirmación / baja sin `forzar` → `409`.

### Escenario D — Disponibilidad (solo O30)

1. Login como **Unidad** → módulo `evidencia-unidad` panel disponibilidad.
2. Confirmar que rutas `alta-unidades/disponibilidad-externa` ya no existen.

## 3) Frontend

1. Login Proveedor → `red-operativa/alta-unidades/catalogo` (`ProveedorFlotaGuard`).
2. Plantilla CSV documentada en UI con columna `gmail`.

## Criterios de éxito

- Escenarios A–D pasan contra OpenAPI 1.1.0.
- Admin no gestiona flota ajena; O59 fuera del producto.

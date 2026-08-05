# Quickstart: Validar los 3 workpanels de informes tácticos

## Prerrequisitos

- Backend con los 16 endpoints implementados y verificados (`../backend/quickstart.md`).
- Stack completo levantado (`docker/accidentes.yml` + `docker/docker-compose.infraestructura.yml`).
- Sesión iniciada como `sofia.castro.operador@demo.tsi.com` / `password123` (Operador) o `carlos.mendoza.admin@demo.tsi.com` / `password123` (Administrador).

## 1. Navegar al workpanel de Registro

Abrir `http://localhost:4200/emergencias/informes/registro`.

**Resultado esperado**: 7 tarjetas cargan (volumen, severidad, zona, completitud, descarte/fusión, ranking, impacto humano), cada una con su propio spinner mientras carga.

## 2. Cambiar el período

Cambiar el selector de período compartido (ej. últimos 7 días → últimos 90 días).

**Resultado esperado**: las 7 tarjetas se refrescan con el nuevo rango.

## 3. Navegar al workpanel de Despacho

Abrir `http://localhost:4200/emergencias/informes/despacho`.

**Resultado esperado**: 6 tarjetas cargan. Al elegir un condado en el filtro adicional, solo las tarjetas que lo soportan (asignación automática/manual, tiempo de respuesta) se recortan — las demás no cambian.

## 4. Navegar al workpanel de Seguimiento

Abrir `http://localhost:4200/emergencias/informes/seguimiento`.

**Resultado esperado**: 3 tarjetas cargan.

## 5. Verificar aislamiento de fallos (FR-UI-001)

Con el backend corriendo, detener temporalmente uno de los tres stacks de datos (o forzar un error de red en una tarjeta específica) y confirmar que solo esa tarjeta muestra su estado de error, sin bloquear las demás.

## 6. Verificar control de acceso (FR-UI-005)

Iniciar sesión con un rol distinto a Operador/Administrador (o cerrar sesión) e intentar navegar a `/emergencias/informes/registro`.

**Resultado esperado**: redirección a `/cuentas-clientes/auth/access-denied` (o `/login` si no hay sesión).

# Phase 0 Research: Informes Tácticos Simples de Emergencias (Frontend)

## 1. Sin librería de gráficas

**Decision**: Renderizar las 16 tarjetas con texto, badges y barras de distribución hechas con Tailwind (mismo patrón que `dashboard-soporte.page.ts::toDist`), no con una librería de charts.

**Rationale**: `package.json` no tiene `ngx-charts`/`chart.js`/`d3` — introducirla para 16 tarjetas simples (conteos, porcentajes, promedios) sería una dependencia nueva no justificada. El patrón `toDist()` ya resuelve exactamente esta forma de dato (distribución por categoría con % y barra proporcional).

**Alternatives considered**: `ngx-charts` para los informes de serie temporal (`volumen-casos`, `completitud-campos-criticos`, etc.) — descartado por ahora; si el negocio pide visualización más rica más adelante, se evalúa como spec aparte, no como parte de este MVP.

## 2. Componente base `InformeCardComponent`

**Decision**: Un componente `<app-informe-card>` reutilizable que recibe `loading`/`error`/`data` como `input()` y proyecta el contenido específico de cada informe vía `ng-content`, en vez de repetir la lógica de loading/error/empty 16 veces.

**Rationale**: FR-UI-001 exige que cada tarjeta tenga su propio estado independiente. Repetir el bloque `@if (loading) {...} @else if (error) {...} @else if (empty) {...} @else {...}` 16 veces violaría Maintainability. Los componentes compartidos ya existentes (`app-list-loading-skeleton`, etc.) están pensados para listados de filas, no para tarjetas de métrica — se necesita una variante nueva, no una reutilización directa.

## 3. Guard de rol

**Decision**: `emergenciasInformesGuard`, mismo patrón que `agenteSoporteGuard` (`CanActivateFn`, `AuthApiService.isAuthenticated()`/`hasRole()`), con `ROLES = ['Operador', 'Administrador']`.

**Rationale**: Ya es el mecanismo estándar del proyecto (research ya hecho en `agente-soporte.guard.ts`); FR-UI-005 ya corrigió la spec para usar los roles reales (no "Supervisor").

## 4. Un solo servicio API con 16 métodos

**Decision**: `InformesTacticosApiService` con 16 métodos (uno por endpoint), en vez de 3 servicios separados por módulo.

**Rationale**: Los 16 endpoints comparten el mismo prefijo base (`/api/v1/informes-tacticos/`) y el mismo shape de respuesta (`ApiEnvelope<T>`); dividir en 3 servicios (Registro/Despacho/Seguimiento) no aporta aislamiento real ya que las 3 páginas de workpanel son las que dan esa separación — el servicio es una capa de transporte fina.

**Alternatives considered**: 3 servicios — descartado por añadir 2 archivos extra sin beneficio (no hay lógica de negocio en el servicio, solo llamadas HTTP directas).

# Feature Specification: Monitoreo y Facturación de API — Frontend

**Feature Branch / capa**: `api-monitoring-and-billing/frontend`  
**Created**: 2026-08-08  
**Status**: 🚧 Stub — pendiente de especificar tras cerrar la capa `backend`  
**Depends-on**: [`../backend/spec.md`](../backend/spec.md) (RF-APM-*, RNF-APM-*, CA-APM-*, OpenAPI). Esta capa **MUST NOT** redefinir reglas de negocio, estados ni contratos REST.

## Alcance previsto

| Superficie | Actor | Cubre |
|---|---|---|
| **Consola de registros en tiempo real** | Desarrollador de APIs | Detalle de cada llamada (endpoint, método, código HTTP, IP, latencia) con filtros por partner, credencial, código y rango temporal · alertas de cuota (RF-APM-008, RF-APM-010) |
| **Panel de consumo del partner** | Partner de integración | Sus métricas del período: llamadas, errores, latencia promedio y porcentaje del cupo consumido (RF-APM-007) |
| **Reporte mensual** | Cliente / Administrador | Consumo del mes con posibilidad de comparar períodos (RF-APM-009) |
| **Excepciones de facturación** | Administrador | Facturas de excedente en «pendiente de emisión manual» tras agotar reintentos (RF-APM-013) |

## Interaction Capability — puntos críticos ya identificados

Derivan de reglas del backend y **no** son decisiones libres de esta capa:

1. **Superar la cuota no es un error.** La UI debe comunicar el exceso como **coste previsto**, no como fallo ni bloqueo (RN-APM-002). Un indicador rojo de «límite superado» daría a entender que el servicio se cortó, y no es así.
2. **Separación de entornos siempre visible.** Pruebas y producción nunca se mezclan (RN-APM-001); toda métrica debe indicar a qué entorno pertenece, y por más que el color (RNF-09).
3. **«Tiempo real» tiene un límite de 5–15 s** por la ingesta de Pinot. La consola no debe prometer latencia cero: conviene mostrar la marca temporal del último dato disponible.
4. **Los errores 4xx del partner son autodiagnóstico**, no incidencias del sistema (RN-APM-009). La UI debe presentarlos como información útil para el partner, no como alarma.
5. **«Pendiente de emisión manual» es un estado accionable**, no informativo: exige que un Administrador actúe (RF-APM-013).

## Pendiente

Esta capa se especifica cuando `backend/` tenga `spec.md`, `plan.md`, `tasks.md` y su contrato OpenAPI cerrados.

Referencia de estilo: [`../../partner-api-onboarding/frontend/`](../../partner-api-onboarding/frontend/) y `.specify/docs/design/design-system.md`.

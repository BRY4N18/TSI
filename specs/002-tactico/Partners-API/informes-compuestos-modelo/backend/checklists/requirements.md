# Specification Quality Checklist: Informes Compuestos de Partners y API

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-08-14
**Feature**: [spec.md](../spec.md)

## Content Quality

- [X] No implementation details (languages, frameworks, APIs)
- [X] Focused on user value and business needs
- [X] Written for non-technical stakeholders
- [X] All mandatory sections completed

## Requirement Completeness

- [X] No [NEEDS CLARIFICATION] markers remain
- [X] Requirements are testable and unambiguous
- [X] Success criteria are measurable
- [X] Success criteria are technology-agnostic (no implementation details)
- [X] All acceptance scenarios are defined
- [X] Edge cases are identified
- [X] Scope is clearly bounded
- [X] Dependencies and assumptions identified

## Feature Readiness

- [X] All functional requirements have clear acceptance criteria
- [X] User scenarios cover primary flows
- [X] Feature meets measurable outcomes defined in Success Criteria
- [X] No implementation details leak into specification

## Notes

### Las dos aclaraciones, resueltas el 2026-08-14

1. **Manda el detalle de llamadas** (FR-006 a FR-008), y la tabla preagregada **no se carga al
   modelo**. Es la única fuente que permite p95, desglose por endpoint y taxonomía de errores.

   **El precio está dicho**: las cifras serán bajas, y FR-008 obliga a devolver sobre cuántas
   llamadas se calculó cada medida para que nadie confunda **poco consumo** con **poco registrado**.
   FR-007 impide la recaída de tener las dos fuentes al lado.

2. **El alcance geográfico queda fuera** (FR-024 a FR-026). Derivar la zona de los parámetros del
   endpoint **falla en silencio**: no distinguiría «consulta fuera de zona» de «no supe leerla».
   Registrado como carencia del sistema operativo, no como informe pendiente.

**Alcance final: 13 informes construibles de los 14 del catálogo.**

### Verificado contra el sistema real, no supuesto

- **Las filas se contaron una a una**: **9 simples y 14 compuestos**, frente a los 9 y 13 del
  resumen. Es la **tercera discrepancia** del catálogo, y la fila reclasificada a compuesto es la
  causa más probable de las tres.
- **Ningún informe táctico de este departamento existe en la app de informes tácticos**: los tres
  construidos viven en la app de partners.
- **El defecto de la credencial está confirmado leyendo su esquema**: `Dim_CredencialAPI` tiene
  `activo` y ninguna columna de motivo.
- **Los dos centinelas están medidos**: `fecha_expiracion = 253402300799000` (año 9999) y
  `fecha_retiro = 0`.
- **La derivación de versión se comprobó**: el endpoint contiene `/api/v1/` y
  `Dim_VersionContratoAPI.version` vale `'v1'` — pero **dos servicios comparten ese valor**, así que
  la clave real es (servicio, versión).
- **Los volúmenes están medidos**: 18 llamadas, 4 partners, 6 credenciales, 15 cambios de acceso, 2
  versiones, 2 preferencias de cliente.

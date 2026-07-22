# Research — Onboarding y Validación de Región Operativa

Todos los `NEEDS CLARIFICATION` del Technical Context fueron resueltos durante `/speckit-clarify` (ver `spec.md` → `## Clarifications`) o por los documentos de arquitectura ya vigentes. No queda ningún unknown abierto para Phase 1.

## Decision 1 — Naturaleza de la validación en CU-O55

- **Decision**: la validación es una revisión manual del Administrador/Director Tecnológico; el sistema no ejecuta checklist técnico automatizado (conectividad, healthcheck). El backend solo persiste el resultado (`resultado`, `motivo`) en `Dim_ValidacionRegion`.
- **Rationale**: confirmado en `/speckit-clarify` (sesión 2026-07-21); consistente con Sección 13 del spec, que declara explícitamente que no existe tabla que respalde un checklist automatizado.
- **Alternatives considered**: validaciones de negocio in-app (ej. exigir ≥1 unidad activa antes de aprobar) — descartado porque el spec no define ese criterio como bloqueante, y RN-REGON-005 confirma que no hay FK confiable `Dim_UnidadEmergencia ↔ Dim_RegionOperativa` para calcularlo.

## Decision 2 — Reingreso a CU-O55 desde estados degradados

- **Decision**: una región en `En_Alerta` o `Despublicada` puede reingresar a `CU-O55`; si el resultado es `Aprobada`, `estadoregion` vuelve a `Producción`.
- **Rationale**: confirmado en `/speckit-clarify`; `CU-O55` es el único camino documentado hacia `Producción` en la Sección 9 del spec (transiciones), sin distinguir el estado previo salvo `activo=false`.
- **Alternatives considered**: tratar `Despublicada`/`En_Alerta` como terminales, requiriendo un caso de uso nuevo de "reactivación" — descartado por duplicar lógica ya cubierta por `CU-O55` sin necesidad real, y por no estar solicitado en el spec original.

## Decision 3 — Concurrencia en `Dim_RegionOperativa.estadoregion`

- **Decision**: último `INSERT` en `Dim_ValidacionRegion` gana; `estadoregion` se actualiza con el resultado de la escritura más reciente procesada, sin bloqueo optimista.
- **Rationale**: confirmado en `/speckit-clarify`; consistente con RN-REGON-001 (campo directo, sin tabla de historial de transiciones) y con el patrón ya aplicado en `Dim_UnidadEmergencia` de `alta-unidades` (last-write-wins en edición, RF-CAM-003).
- **Alternatives considered**: bloqueo optimista con versión/lock — descartado por sobre-ingeniería para un flujo administrativo de baja concurrencia real (onboarding de regiones no es alta frecuencia), y por romper el patrón last-write-wins ya establecido en el módulo.

## Decision 4 — Disparador de CU-O62 (despublicación automática)

- **Decision**: se implementa la lógica de negocio de `CU-O62` como servicio idempotente (`despublicacion_automatica_service.py`), invocable manualmente o por un job externo, pero **sin conectar un disparador automático real** en este ciclo.
- **Rationale**: RN-REGON-005 documenta que no existe FK entre `Dim_UnidadEmergencia` y `Dim_RegionOperativa`; el único campo disponible (`zonacobertura`, texto libre en `Dim_UnidadEmergencia`) no permite un match confiable. Priorizar Safety (Principio IX) sobre completar el disparador con una heurística de texto frágil, según el mecanismo de desempate de la constitución.
- **Alternatives considered**: (a) comparar `zonacobertura` contra `nombreregion` con normalización de texto — rechazado, alto riesgo de falso positivo; (b) esperar a una migración de esquema que agregue la FK — es la solución correcta pero está fuera de alcance de este spec (Sección 13); queda documentada como dependencia futura de `alta-unidades`/`incorporacion-regional`.

## Decision 5 — Reutilización de infraestructura de `alta-unidades`

- **Decision**: no se crea app Django ni módulo Angular nuevos; se extiende `red_operativa` (backend) y `red-operativa` (frontend), ya existentes y en estado "Implementado" según `module-map.md`.
- **Rationale**: `module-map.md` ya declara que la app `red_operativa` es compartida por `alta-unidades` e `incorporacion-regional` (mismo módulo de negocio Red-Operativa); `project-structure.md` fija la regla "1 app Django = 1 módulo de negocio".
- **Alternatives considered**: app separada `region_operativa` — rechazado, violaría la regla de organización de `project-structure.md` y fragmentaría innecesariamente un módulo de negocio único.

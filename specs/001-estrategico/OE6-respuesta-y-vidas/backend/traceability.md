# Trazabilidad: OE6 — Tiempo de Respuesta y Seguridad de Vidas (Backend)

**Fecha:** 2026-08-16 · **Spec:** [`spec.md`](spec.md) · **Tasks:** [`tasks.md`](tasks.md)

## Requisitos funcionales

| FR | Tareas | Prueba |
|---|---|---|
| FR-OE6-001 una consulta por informe | T025–T074 | `test_catalogo_estrategicos.py` (12 ficheros) |
| FR-OE6-002 versión final | T018 | `TestLaReglaDeVersionFinal` |
| FR-OE6-003 período obligatorio | T006, T022, T031 | `test_periodo_estrategico.py`, contrato US1 |
| FR-OE6-004 ventanas de comparación | T008, T035 | `test_us1_comparacion.py` |
| FR-OE6-005 período parcial | T009, T022 | `TestParcial` |
| FR-OE6-006 `cumple` null en CALIBRAR | T011, T023, T082 | `test_objetivo.py`, `test_ningun_cumple_booleano.py` |
| FR-OE6-007 porcentaje con denominador | T083 | `test_todo_porcentaje_con_denominador.py` |
| FR-OE6-008 agrupación por condado (no región) | T019, T089, T090 | `TestProhibicionDelEjeDeRegion` · changelog D1/#38 |
| FR-OE6-009 sin dato sensible | T021, T037, T052, T080 | catálogo + pruebas de autoridad |
| FR-OE6-010 sin `SELECT *` | T020 | `TestLaFormaDeLasConsultas` |
| FR-OE6-011 descartados y fusionados fuera | T026 | encabezado E6-01 + filtro SQL |
| FR-OE6-012 hito ausente ≠ cero | T027, T032 | `test_us1_sin_llegada.py` |
| FR-OE6-013 / 014 acceso | T013, T014, T024 | `test_permisos_oe6.py` |
| FR-OE6-015 sin `acotado_a` | T012 | `test_servicio_y_envelope.py` |
| FR-OE6-016 mediana y p95 | T025, T031 | contrato US1 |
| FR-OE6-017 p95 ausente bajo muestra | T027, T033 | `test_us1_percentil.py` |
| FR-OE6-018 / 019 por severidad | T028, T034 | `test_us1_suma_severidad.py` |
| FR-OE6-020 / 021 / 022 tramos | T038–T040, T047, T048 | población distinta; suma sin residuo |
| FR-OE6-023 origen | T041, T049 | `test_us2_origen.py` |
| FR-OE6-024 / 025 desviación | T042, T045, T050 | `test_us2_referencia_ausente.py` |
| FR-OE6-026 / 027 rechazo | T053–T055, T064, T065 | denominador intentos; tasas separadas |
| FR-OE6-028 abortos | T056 | contrato US3 |
| FR-OE6-029 cierres forzados | T057, T058, T066 | alcance + cobertura parcial |
| FR-OE6-030 envejecimiento | T059, T067 | `test_us3_envejecimiento.py` |
| FR-OE6-031 impacto humano | T069, T070, T076 | `test_us4_cero_vs_no_registrado.py` |
| FR-OE6-032 escaladas | T071, T072, T077 | `test_us4_escasez.py` |
| FR-OE6-033 evidencia | T073, T078 | `test_us4_evidencia.py` |

## Criterios de aceptación por historia

| Historia | Criterio | Prueba |
|---|---|---|
| US1 | SC-004: sin llegada no vale cero | `test_us1_sin_llegada.py` |
| US1 | SC-007: recuentos contra el hecho | `test_contraste_us1.py` |
| US2 | SC-003: cada tramo su población | `test_us2_tramos_poblacion.py` |
| US2 | SC-007: origen y desviación vs táctico | `test_contraste_us2.py` |
| US3 | SC-003: denominador = intentos (#34) | `test_us3_denominador_intentos.py` |
| US3 | SC-007: abortos coinciden; rechazo diverge | `test_contraste_us3.py` |
| US4 | SC-009: cero ≠ no registrado | `test_us4_cero_vs_no_registrado.py` |
| US4 | SC-007: impacto / escaladas / evidencia | `test_contraste_us4.py` |

## Hallazgos fuera de ciclo

| Código | Qué | Dónde |
|---|---|---|
| D1 / #38 | El eje de región no es construible; `FR-OE6-008` se corrige a condado | `research.md` D1, `.specify/docs/changelog.md` |

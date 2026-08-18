# Trazabilidad OE1 backend

**Fecha:** 2026-08-18

| FR | Tarea | Prueba |
|---|---|---|
| FR-OE1-001 armazón OE6 | T001, T005, T008–T010 | `test_oe1_us1_contract` |
| FR-OE1-002 una consulta | T014–T017, T028–T029, T035–T038 | `test_catalogo_estrategicos_oe1` |
| FR-OE1-003 sin cobro ni persona | T013, T023, T033 | `test_us1_sin_cobro`, `test_us2_sin_prospecto`, catálogo |
| FR-OE1-004 sin país | T013, T016 | `test_catalogo_estrategicos_oe1::test_sin_geografia_ni_cobro_ni_ddl` |
| FR-OE1-005 cobertura parcial | T008, T022 | `test_us1_cobertura_parcial`, `test_oe1_servicio` |
| FR-OE1-006 permiso partido | T006, T007, T011 | `test_permisos_oe1` |
| FR-OE1-007 ciclo solo Gerente | T006, T007, T011 | `test_permisos_oe1::test_ciclo_solo_gerente` |
| FR-OE1-008 MRR mensualizado | T014, T020 | `test_us1_mrr_mensualizado`, catálogo |
| FR-OE1-009 recuento con MRR | T014, T019 | `test_oe1_us1_contract` |
| FR-OE1-010 ARR extrapolación | T015, T021 | `test_us1_arr_extrapolacion` |
| FR-OE1-011 segmento = tipo | T016 | `e1_03_mrr_por_segmento.sql` |
| FR-OE1-012 cartera por plan | T017 | `e1_12_cartera_por_plan.sql` |
| FR-OE1-013 embudo con ceros | T028, T032 | `test_us2_embudo_ceros` |
| FR-OE1-014 velocidad sin ficha | T029, T033 | `test_us2_sin_prospecto` |
| FR-OE1-015 renovación = vencidas | T035, T041 | `test_us3_renovacion_vencidas` |
| FR-OE1-016 onboarding catálogo | T037, T042 | `test_us3_onboarding_catalogo` |
| FR-OE1-017 churn sin % si n bajo | T038, T043 | `test_us3_churn_sin_muestra` |
| FR-OE1-018 E1-05/07/08 sin ruta | T012, T025, T026 | `test_oe1_bloqueados`, `test_openapi_conforme_oe1` |
| Dueño OE5 (E1-06/09/10/11) | T039 | comentario en `oe1_service.py` |
| Cobertura ≥80 % | T048 | `oe1_service` 83 %, `oe1_views` 91 % |

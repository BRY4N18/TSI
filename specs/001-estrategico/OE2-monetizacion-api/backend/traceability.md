# Trazabilidad OE2 backend

**Fecha:** 2026-08-18

| FR | Tarea | Prueba |
|---|---|---|
| FR-OE2-001 armazón OE6 | T001, T008–T010 | `test_oe2_us1_contract` |
| FR-OE2-002 una consulta | T014–T017, T025–T027, T034–T036 | `test_catalogo_estrategicos_oe2` |
| FR-OE2-003 sin secretos | T013, T023 | `test_us1_sin_secretos`, catálogo |
| FR-OE2-005 sin agregado | T013 | `test_catalogo_estrategicos_oe2::test_no_usa_agregado_de_consumo` |
| FR-OE2-006 permiso partido | T006, T007, T011 | `test_permisos_oe2` |
| FR-OE2-007 partner fuera | T011, T047 | `test_permisos_oe2::test_partner_recibe_403_en_los_diez` |
| FR-OE2-008 denominador acceso | T014, T022 | `test_us1_denominador_acceso` |
| FR-OE2-009 p95 ausente | T016, T020 | `test_us1_p95_ausente` |
| FR-OE2-010 4xx ≠ 5xx | T017, T021 | `test_us1_4xx_vs_5xx` |
| FR-OE2-012/014 facturable | T025, T030 | `test_us2_alcance_facturable` |
| FR-OE2-013 no tarificables | T032 | `test_us2_no_tarificables` |
| FR-OE2-015 parciales | T026–T028, T031 | `test_us2_parciales` |
| FR-OE2-016/017 versión | T034, T039 | `test_us3_version_no_unica` |
| FR-OE2-018 primera 2xx | T036, T040 | `test_us3_crecimiento_primera_2xx` |
| FR-OE2-019 E2-06 sin ruta | T012, T043, T044 | `test_oe2_bloqueados`, `test_openapi_conforme_oe2` |
| Cobertura ≥80 % | T050 | `oe2_service` 84 %, `oe2_views` 85 % |

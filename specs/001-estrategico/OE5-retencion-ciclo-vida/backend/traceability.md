# Trazabilidad OE5 backend

**Fecha:** 2026-08-18

| FR | Tarea | Prueba |
|---|---|---|
| FR-OE5-001 armazón OE6 | T001, T008–T010 | `test_oe5_us1_contract` |
| FR-OE5-002 una consulta | T014–T016, T027–T028, T034–T037 | `test_catalogo_estrategicos_oe5` |
| FR-OE5-003 sin prosa de ticket | T013, T021 | `test_us1_sin_prosa`, catálogo |
| FR-OE5-004 sin cobro | T013 | `test_catalogo_estrategicos_oe5::test_sin_prosa_ni_cobro_ni_ddl` |
| FR-OE5-005 no reimplementar OE1 | T008, T012, T023 | `test_oe5_bloqueados` |
| FR-OE5-006 cobertura parcial | T008 | `test_oe5_servicio::test_sla_cobertura_parcial_bajo_umbral` |
| FR-OE5-007/008 permiso partido | T006, T007, T011 | `test_permisos_oe5` |
| FR-OE5-010 denominador SLA | T014, T019, T020 | `test_us1_sla_sin_compromiso`, `test_us1_sla_periodo_vacio` |
| FR-OE5-013 NRR descompuesto | T027, T031 | `test_us2_nrr_descompuesto` |
| FR-OE5-014/015 precio congelado, solo aprobados | T028, T032 | `test_us2_pendiente_no_cuenta` |
| FR-OE5-016 ≥2 señales | T036, T040 | `test_us3_una_senal_no_marca` |
| FR-OE5-017 falta nombra señal | T038 | `test_oe5_servicio::test_riesgo_falta_si_fuente_vacia` |
| FR-OE5-018 carga, no desempeño | T034, T041 | `test_us3_agente_sin_nombre` |
| FR-OE5-019 cliente × servicio | T035, T042 | `test_us3_reincidencia_servicio` |
| FR-OE5-020 solo activas | T037 | `e5_15_antiguedad_de_cuenta.sql` |
| FR-OE5-021/022 sin NPS | T012, T023, T025 | `test_oe5_bloqueados`, `test_us4_sin_nps_emergencia` |
| Cobertura ≥80 % | T047 | `oe5_service` 80 %, `oe5_views` 92 % |

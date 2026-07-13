# Trazabilidad — Seguimiento y Cierre de Casos

| ID | Requisito | Tareas | Estado |
|----|-----------|--------|--------|
| CA-SEG-001 | GPS cada 10s persiste Kafka + snapshot | T025–T032 | ✓ Validado (77 tests) |
| CA-SEG-002 | Mapa operador + SSE tiempo real | T034–T043 | ✓ Validado |
| CA-SEG-003 | Llegada manual En_sitio + EN_ATENCION | T026, T028, T030, T032 | ✓ Validado |
| CA-SEG-004 | Geofencing automático O26 | T029, T031 | ✓ Validado |
| CA-SEG-005 | Cierre valida todos Retirado | T044–T049 | ✓ Validado |
| CA-SEG-006 | Auto-retiro con idusuario ejecutor | T047 | ✓ Validado |
| CA-SEG-007 | horafin/duracionminutos inmutables SLA | T047 | ✓ Validado |
| CA-SEG-008 | Historial operador con filtros | T066–T078 | ✓ Validado |
| CA-SEG-009 | Expediente cliente por condado | T068, T071, T074–T077 | ✓ Validado |
| CA-SEG-010 | Cliente sin acceso mapa activo | T106 | ✓ Validado (403) |
| CA-SEG-011 | Job señal GPS perdida + depuración | T079–T087 | ✓ Validado |
| CA-SEG-012 | Abortar → DespachoAbortado_topic | T050–T057 | ✓ Validado |
| CA-SEG-013 | Cancelar falsa alarma solo motivo | T058–T065 | ✓ Validado |
| CA-SEG-014 | Forzar retiro unitario | T059, T061, T063 | ✓ Validado |

| CU/RF | Descripción | User Story |
|-------|-------------|------------|
| CU-O25 | Registrar posición GPS | US1 |
| CU-O26 | Llegada al sitio | US1 |
| CU-O28 | Cierre multi-despacho | US3 |
| CU-O29 | Historial emergencias | US6 |
| CU-O37 | Job señal GPS perdida | US7 |
| CU-O39 | Abortar misión | US4 |
| CU-O42 | Cancelar caso | US5 |
| CU-O44 | Forzar retiro | US5 |
| RF-SEG-004 | Evidencia cierre | US3 |
| RF-SEG-005 | Historial operador | US6 |
| RF-SEG-006 | Expediente cliente | US6 |
| RF-SEG-007 | Mapa + SSE | US2 |

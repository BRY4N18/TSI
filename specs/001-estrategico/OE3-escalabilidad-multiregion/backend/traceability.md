# Trazabilidad OE3 — Escalabilidad Multi-Región sin Degradación

**Feature:** `specs/001-estrategico/OE3-escalabilidad-multiregion/backend/`
**Fecha:** 2026-08-16

## Requisitos → tareas → pruebas

| FR | Tareas | Prueba |
|---|---|---|
| Armazón OE6 reutilizado | T001, T005, T016, T017 | `test_el_cargador_anidado` OE3 · rutas `/oe3/` |
| Línea base 14 tablas | T002, T006–T012 | `test_dim_condado_vecino.py` · quickstart §1 |
| Permiso por informe | T013, T014 | `test_permisos_oe3.py` · `TestOe3Permission` |
| `cumple` NORMATIVO | T015, T029, T030, T033, T062 | `test_us1_semaforo.py` · `test_oe3_semaforo_correcto.py` |
| E3-02 meta 2 min, no 100 ms | T021–T023, T032 | `test_us1_meta_correcta.py` |
| Sin asignación fuera de la mediana | T022, T034 | `test_us1_sin_asignacion.py` |
| E3-10 campos_comprobados | T025, T035 | `test_us1_campos_comprobados.py` |
| E3-11 grano de intento | T026, T037 | `test_contraste_oe3_us1.py` |
| Capacidad histórica | T039–T042, T047 | `test_oe3_us2_capacidad_del_periodo.py` |
| sin_capacidad | T041, T048 | `test_oe3_us2_sin_capacidad.py` |
| Respaldo = disponibilidad | T043, T049 | `test_oe3_us2_respaldo_disponibilidad.py` |
| Señal completa | T044, T050 | `test_oe3_us2_senal_completa.py` |
| Sin `dim_region` | T019, T065 | `TestProhibicionDelEjeDeRegionOe3` |
| Bloqueados 404 | T053, T057 | `test_oe3_bloqueados.py` |
| FINAL / SELECT * / fecha | T018, T020 | `test_catalogo_estrategicos.py` OE3 |

## Historias

| Historia | Criterio | Cómo se verifica |
|---|---|---|
| US1 | p95, meta 2 min, `cumple` booleano, dos ventanas | T031–T038 |
| US2 | capacidad del período; vecino ocupado no respalda | T046–T052 |
| US3 ⛔ | E3-04/05/06 → 404; prerrequisito único | T053–T056 |
| US4 ⛔ | E3-01/09/12/14 → 404; hallazgo E3-12 | T057–T060 |

## Hallazgos fuera de ciclo

| Código | Qué | Dónde |
|---|---|---|
| D1 / meta E3-02 | El catálogo mezclaba latencia técnica (100 ms) con tiempo operativo | `research.md` D1 · changelog |
| D2 / E3-12 | 1 082 de 1 083 manuales sin intento automático previo | `decisiones-pendientes.md` · changelog |
| D1 / #38 | Eje de región no construible; US3 comparte historización de estado | `research.md` D4 |

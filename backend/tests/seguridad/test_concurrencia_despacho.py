"""PG-NEG-001 y PG-NEG-002 — dos operadores, la misma unidad, el mismo instante.

**La única regla del plan cuyo fallo se mide en tiempo de respuesta a una
emergencia.** Una unidad asignada a dos accidentes no produce ningún error: los
dos despachos se crean, los dos operadores ven confirmación, y una de las dos
ambulancias no llega. Nadie se entera hasta que alguien pregunta por qué.

**Por qué la ventana aquí es enorme.** `asignar()` comprueba y luego actúa:

    if self.despachos.has_active_for_unidad(unidad):   # lee de Pinot
        raise ValueError("Unidad no disponible")
    ...
    self.asignacion.ejecutar(...)                      # escribe vía Kafka

Entre la lectura y la escritura no hay transacción — no puede haberla, porque
son dos sistemas distintos. Y la escritura **no es visible de inmediato**: viaja
por Kafka y Pinot la ingiere de forma asíncrona. La comprobación de la segunda
petición no ve el despacho que la primera acaba de crear aunque haya pasado un
segundo entero.

No es una carrera de milisegundos entre hilos: es una ventana del tamaño del
retraso de ingesta.
"""

from __future__ import annotations

import threading
from unittest.mock import patch

import pytest

pytestmark = [pytest.mark.unit, pytest.mark.seguridad, pytest.mark.critical_path]

UNIDAD = 2  # la 1 y la 999 ya tienen despacho activo en la siembra base
CASO_A = "ACC-CARRERA-A"
CASO_B = "ACC-CARRERA-B"


@pytest.fixture
def servicio(mock_pinot, mock_kafka):
    """Siembra los dos casos y la unidad **antes** de construir el servicio.

    Sin esto la prueba pasaba en vacio: ambas llamadas fallaban con
    «Accidente no encontrado» sin llegar nunca a la comprobacion de
    disponibilidad, y el aserto «como mucho una tuvo exito» se cumplia porque
    ninguna la tuvo. Se descubrio comprobandolo, no leyendolo.
    """
    from conftest import PINOT_STORE

    from apps.despacho.services.asignacion_manual_service import AsignacionManualService

    ahora = 1_756_000_000_000
    for caso in (CASO_A, CASO_B):
        PINOT_STORE.setdefault("Fact_Accidente", []).append({
            "idaccidente": caso, "idseveridad": 2, "idcalle": 1,
            "fechahoraaccidente": ahora, "idusuario": 2, "activo": True,
            "fecha_actualizacion": ahora,
        })
        PINOT_STORE.setdefault("Fact_AccidenteTipoEstadoAccidente", []).append({
            "idaccidente": caso, "idtipoestadoincidente": 2,  # REPORTADO
            "fechahoramodificado": ahora, "idusuario": 2, "activo": True,
            "fecha_actualizacion": ahora,
        })

    # Sin historial, `get_current_estado` devuelve ESTADO_DEFAULT — que es
    # «Fuera de servicio», no «Activa». La unidad se rechazaba por estado y la
    # carrera tampoco se ejercitaba.
    PINOT_STORE.setdefault("Fact_HistorialEstadoUnidad", []).append({
        "idhistorialestadosunidadesemergencias": 9001,
        "idunidademergencia": UNIDAD, "estadoanterior": "Fuera de servicio",
        "estadonuevo": "Activa", "fechahora": ahora, "idusuario": 2,
        "activo": True, "fecha_actualizacion": ahora,
    })

    return AsignacionManualService()


def _puede_asignar(servicio) -> bool:
    """Control de no-vacuidad: la siembra alcanza para una asignacion legitima."""
    try:
        servicio.asignar(idaccidente=CASO_A, idunidademergencia=UNIDAD, idusuario=2)
        return True
    except LookupError:
        return False
    except Exception:  # noqa: BLE001 - otro rechazo significa que si llego
        return True


def test_la_comprobacion_y_la_escritura_ocurren_dentro_de_la_reserva(servicio):
    """El arreglo, comprobado sobre la forma y no solo sobre el resultado.

    La comprobación **sigue** precediendo a la escritura —no puede ser de otro
    modo con dos sistemas separados— así que lo que elimina la carrera es que
    ambas queden bajo la misma reserva. Si alguien sacara la escritura fuera del
    bloque, la prueba de carrera volvería a fallar, pero esta lo dice antes y
    con el motivo.
    """
    import inspect

    from apps.despacho.services.asignacion_manual_service import AsignacionManualService

    externo = inspect.getsource(AsignacionManualService.asignar)
    assert "with reservar(idunidademergencia)" in externo, (
        "La asignación ya no toma la reserva: la ventana entre comprobar y "
        "escribir vuelve a estar abierta (PG-NEG-002)."
    )

    interno = inspect.getsource(AsignacionManualService._asignar_reservada)
    assert "has_active_for_unidad" in interno and "self.asignacion.ejecutar" in interno, (
        "La comprobación y la escritura ya no están juntas bajo la reserva."
    )


def test_dos_asignaciones_simultaneas_de_la_misma_unidad(servicio, mock_pinot):
    """El escenario real: dos operadores pulsan «asignar» a la vez.

    Se fuerza el entrelazado —ambas peticiones comprueban antes de que ninguna
    escriba— porque es exactamente lo que ocurre cuando la escritura tarda en
    ser visible. Con Kafka de por medio no hace falta que sean simultáneas: basta
    con que la segunda llegue antes de que Pinot ingiera la primera.
    """
    from core.repositories.despacho.despacho_repository import DespachoRepository

    # Timeout corto: con la reserva puesta, el segundo hilo **no llega** a la
    # barrera —lo rechaza antes— y el primero debe seguir en vez de quedarse
    # esperando. Que la barrera se rompa es aquí la señal de que el arreglo
    # funciona, no un fallo.
    barrera = threading.Barrier(2, timeout=1)
    original = DespachoRepository.has_active_for_unidad

    def comprobar_a_la_vez(self, idunidademergencia):
        resultado = original(self, idunidademergencia)
        try:
            barrera.wait()  # ninguna avanza hasta que ambas hayan comprobado
        except threading.BrokenBarrierError:  # pragma: no cover
            pass
        return resultado

    resultados: list[tuple[str, object]] = []

    def asignar(caso):
        try:
            resultados.append((caso, servicio.asignar(
                idaccidente=caso, idunidademergencia=UNIDAD, idusuario=2
            )))
        except Exception as exc:  # noqa: BLE001 - el rechazo es un resultado válido
            resultados.append((caso, exc))

    with patch.object(DespachoRepository, "has_active_for_unidad", comprobar_a_la_vez):
        hilos = [threading.Thread(target=asignar, args=(c,)) for c in (CASO_A, CASO_B)]
        for h in hilos:
            h.start()
        for h in hilos:
            h.join(timeout=10)

    # Si ninguna llego siquiera a la comprobacion, el aserto de abajo se
    # cumpliria sin haber ejercitado la carrera.
    assert resultados, "Ninguna de las dos llamadas termino."
    fallos = [str(r) for _c, r in resultados if isinstance(r, Exception)]
    assert not [f for f in fallos if "no encontrado" in f or "no elegible" in f], (
        f"Las llamadas fallan antes de la comprobacion de unidad: {fallos}. "
        "La siembra no alcanza y la carrera no se esta ejercitando."
    )
    assert len(fallos) < 2, (
        f"Ninguna de las dos asignaciones prospero ({fallos}): la unidad no esta "
        "disponible en la siembra, asi que el aserto de abajo se cumpliria en vacio."
    )

    exitos = [c for c, r in resultados if not isinstance(r, Exception)]

    assert len(exitos) <= 1, (
        f"La unidad {UNIDAD} quedó asignada a {len(exitos)} accidentes a la vez: "
        f"{exitos}.\n"
        "  Una de las dos ambulancias no llegará, y ninguno de los dos operadores "
        "recibió un error (PG-NEG-002)."
    )


def test_una_unidad_no_tiene_dos_despachos_activos(servicio, mock_pinot):
    """La invariante, comprobada sobre el estado y no sobre la respuesta.

    Aunque las dos llamadas devolvieran éxito por un fallo de la comprobación,
    el almacén no debería contener dos despachos activos para la misma unidad.
    Es el aserto que sobrevive a cualquier cambio en el manejo de errores.
    """
    from conftest import PINOT_STORE

    for caso in (CASO_A, CASO_B):
        try:
            servicio.asignar(idaccidente=caso, idunidademergencia=UNIDAD, idusuario=2)
        except Exception:  # noqa: BLE001 - el segundo debe fallar; da igual cómo
            pass

    activos = [
        d
        for d in PINOT_STORE.get("Fact_Despacho", [])
        if int(d.get("idunidademergencia", -1)) == UNIDAD and d.get("activo")
    ]

    assert len(activos) <= 1, (
        f"La unidad {UNIDAD} tiene {len(activos)} despachos activos: "
        f"{[d.get('idaccidente') for d in activos]}"
    )

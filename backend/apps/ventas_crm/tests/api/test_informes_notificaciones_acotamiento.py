"""T039 — las notificaciones se acotan por **destinatario**, y `estado_envio` no sale.

El eje de titularidad aquí **no es el ejecutivo asignado al prospecto** sino
`idusuariogerentenotificado`: el gerente ve aquellas de las que fue
destinatario. Son cosas distintas —un aviso sobre un prospecto puede dirigirse a
otra persona— y confundirlas le mostraría alertas que no eran para él.

Y `estado_envio` no se expone: la columna existe en el esquema y **ningún código
la escribe**. Devolverla sería presentar como dato algo que siempre está vacío, e
invitaría a construir encima un listado de «envíos fallidos» que no podría
funcionar.
"""

from __future__ import annotations

import json

import pytest

from apps.ventas_crm.tests.conftest import GERENTE_A, GERENTE_B

RUTA = "/api/v1/informes/ventas-crm/notificaciones-enviadas"


@pytest.mark.api
class TestAcotamientoPorDestinatario:
    def test_el_gerente_ve_las_suyas(
        self, api_client, gerente_a_headers, notificaciones_sembradas
    ):
        cuerpo = api_client.get(RUTA, **gerente_a_headers).json()

        assert [f["regla_disparada"] for f in cuerpo["data"]] == [
            "visita repetida a precios"
        ]

    def test_y_no_las_dirigidas_a_otro(
        self, api_client, gerente_a_headers, notificaciones_sembradas
    ):
        cuerpo = api_client.get(RUTA, **gerente_a_headers).json()

        reglas = {f["regla_disparada"] for f in cuerpo["data"]}
        assert "descarga de ficha tecnica" not in reglas

    def test_el_otro_gerente_ve_las_suyas(
        self, api_client, gerente_b_headers, notificaciones_sembradas
    ):
        cuerpo = api_client.get(RUTA, **gerente_b_headers).json()

        assert [f["regla_disparada"] for f in cuerpo["data"]] == [
            "descarga de ficha tecnica"
        ]

    def test_el_eje_es_el_destinatario_no_el_dueno_del_prospecto(
        self, api_client, gerente_b_headers, mock_pinot, notificaciones_sembradas
    ):
        """Una alerta sobre un prospecto de A, dirigida a B, la ve B."""
        from conftest import PINOT_STORE
        from apps.ventas_crm.tests.conftest import AHORA_MS

        PINOT_STORE["Fact_NotificacionVentas"].append(
            {
                "idnotificacion": 8699,
                "id_prospecto": 8101,  # prospecto del gerente A
                "idinteraccion": None,
                "idusuariogerentenotificado": GERENTE_B,  # aviso para B
                "regladisparada": "cruzada",
                "canal": "correo",
                "estado_envio": "NO-DEBE-SALIR",
                "fechahoranotificacion": AHORA_MS,
                "fecha_actualizacion": AHORA_MS,
            }
        )

        cuerpo = api_client.get(RUTA, **gerente_b_headers).json()

        assert "cruzada" in {f["regla_disparada"] for f in cuerpo["data"]}

    def test_declara_que_esta_acotado(
        self, api_client, gerente_a_headers, notificaciones_sembradas
    ):
        cuerpo = api_client.get(RUTA, **gerente_a_headers).json()

        assert cuerpo["meta"]["acotado_a"] == "propios"

    def test_el_rol_amplio_ve_las_de_todos(
        self, api_client, admin_auth_headers, notificaciones_sembradas
    ):
        cuerpo = api_client.get(RUTA, **admin_auth_headers).json()

        assert len(cuerpo["data"]) == 2
        assert cuerpo["meta"]["acotado_a"] == "todos"

    def test_pedir_las_de_otro_es_403(
        self, api_client, gerente_a_headers, notificaciones_sembradas
    ):
        respuesta = api_client.get(f"{RUTA}?ejecutivo={GERENTE_B}", **gerente_a_headers)

        assert respuesta.status_code == 403


@pytest.mark.api
class TestEstadoEnvioNoSeExpone:
    def test_no_aparece_como_clave(
        self, api_client, admin_auth_headers, notificaciones_sembradas
    ):
        cuerpo = api_client.get(RUTA, **admin_auth_headers).json()

        assert cuerpo["data"], "sin filas esta prueba no probaria nada"
        for fila in cuerpo["data"]:
            assert "estado_envio" not in fila

    def test_ni_su_valor(self, api_client, admin_auth_headers, notificaciones_sembradas):
        cuerpo = api_client.get(RUTA, **admin_auth_headers).json()

        assert "NO-DEBE-SALIR" not in json.dumps(cuerpo)

    def test_la_consulta_no_lo_selecciona(self):
        import inspect
        import re

        from core.repositories.ventas_crm import informes_nutricion_repository

        fuente = inspect.getsource(informes_nutricion_repository)
        consultas = re.findall(r'"(SELECT [^"]+)"', fuente, re.IGNORECASE)

        for consulta in consultas:
            assert "estado_envio" not in consulta


@pytest.mark.api
class TestFormaYFiltros:
    def test_los_campos_son_los_del_contrato(
        self, api_client, admin_auth_headers, notificaciones_sembradas
    ):
        cuerpo = api_client.get(RUTA, **admin_auth_headers).json()

        for fila in cuerpo["data"]:
            assert set(fila) == {
                "empresa", "ejecutivo_notificado", "regla_disparada", "canal", "fecha"
            }

    def test_filtra_por_canal(
        self, api_client, admin_auth_headers, notificaciones_sembradas
    ):
        cuerpo = api_client.get(f"{RUTA}?canal=push", **admin_auth_headers).json()

        assert all(f["canal"] == "push" for f in cuerpo["data"])

    def test_acepta_rango_opcional(
        self, api_client, admin_auth_headers, notificaciones_sembradas
    ):
        # Es de hechos del período: omitir el rango no es un error.
        assert api_client.get(RUTA, **admin_auth_headers).status_code == 200
        assert api_client.get(
            f"{RUTA}?desde=2026-08-01", **admin_auth_headers
        ).status_code == 200

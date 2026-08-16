"""T018 ⚠️ — estar de alta **no** es estar disponible (SC-003, research D2).

Es la prueba que protege el defecto de mayor consecuencia de toda la serie.

`activo` significa **existe**, no **puede acudir**. Los cuatro estados operativos
—`Activa`, `Ocupada`, `En Misión`, `Fuera de servicio`— viven **solo** en el
histórico, y este módulo no lo lee a propósito.

Un listado de flota presentado como disponibilidad llevaría a decidir cobertura
sobre unidades fuera de servicio, ocupadas o ya en camino a otro accidente. En
los módulos comerciales un error así infla una cifra; **aquí decide si alguien
acude**.

Tres defensas, y las tres se comprueban aquí:

1. la unidad `Fuera de servicio` **aparece** entre las dadas de alta —porque lo
   está—, lo que hace evidente que el listado no filtra por disponibilidad;
2. la respuesta **declara su alcance** en `meta`, para el consumidor que no leyó
   la spec;
3. **ningún campo** se llama disponibilidad ni estado operativo, para el que
   solo mira los nombres.
"""

from __future__ import annotations

import json

import pytest

RUTA = "/api/v1/informes/red-operativa/flota"

#: Palabras que no pueden aparecer como nombre de campo: prometerían un dato que
#: este listado no tiene.
PROHIBIDAS = (
    "disponible", "disponibilidad", "estado_operativo", "estado_unidad",
    "operativa", "ocupada", "en_mision",
)


def _claves(objeto, encontradas=None):
    encontradas = encontradas if encontradas is not None else set()
    if isinstance(objeto, dict):
        for clave, valor in objeto.items():
            encontradas.add(clave)
            _claves(valor, encontradas)
    elif isinstance(objeto, list):
        for elemento in objeto:
            _claves(elemento, encontradas)
    return encontradas


@pytest.mark.api
class TestLaUnidadFueraDeServicioAparece:
    def test_esta_entre_las_dadas_de_alta(
        self, api_client, admin_auth_headers, dos_flotas
    ):
        """Está de alta, así que sale. Su indisponibilidad no la filtra."""
        cuerpo = api_client.get(
            f"{RUTA}?dado_de_alta=true&limit=500", **admin_auth_headers
        ).json()

        assert "FUERA-01" in {f["placa"] for f in cuerpo["data"]}

    def test_su_indisponibilidad_existe_de_verdad(self, mock_pinot, dos_flotas):
        """Si no estuviera fuera de servicio, la prueba de arriba no probaría nada."""
        from conftest import PINOT_STORE

        historico = [
            h for h in PINOT_STORE["Fact_HistorialEstadoUnidad"]
            if h["idunidademergencia"] == 5002
        ]
        assert historico, "la unidad no tiene estado operativo sembrado"

    def test_y_el_listado_no_consulta_ese_historico(self):
        """research D2 — la decisión de diseño, fijada contra el código.

        Leerlo costaría una consulta por unidad, y además devolvería el estado
        del instante de la consulta, no el de cuando el consumidor lo lea.
        """
        import inspect

        from core.repositories.red_operativa import informes_flota_repository

        fuente = inspect.getsource(informes_flota_repository)

        assert "Fact_HistorialEstadoUnidad" not in fuente
        assert "get_current_estado" not in fuente


@pytest.mark.api
class TestLaRespuestaDeclaraSuAlcance:
    def test_meta_trae_alcance(self, api_client, admin_auth_headers, dos_flotas):
        cuerpo = api_client.get(RUTA, **admin_auth_headers).json()

        assert "alcance" in cuerpo["meta"]

    def test_y_dice_que_es_composicion_de_flota(
        self, api_client, admin_auth_headers, dos_flotas
    ):
        cuerpo = api_client.get(RUTA, **admin_auth_headers).json()

        assert cuerpo["meta"]["alcance"] == "composicion_de_flota"

    def test_lo_declara_tambien_cuando_no_hay_filas(
        self, api_client, admin_auth_headers
    ):
        # Es justo cuando más se puede malinterpretar: «no hay unidades
        # disponibles» y «no hay unidades» son cosas muy distintas.
        cuerpo = api_client.get(f"{RUTA}?condado=999999", **admin_auth_headers).json()

        assert cuerpo["data"] == []
        assert cuerpo["meta"]["alcance"] == "composicion_de_flota"

    def test_los_otros_listados_no_lo_declaran(self, api_client, admin_auth_headers):
        """Añadirlo a todos convertiría la advertencia en ruido."""
        cuerpo = api_client.get(
            "/api/v1/informes/red-operativa/regiones", **admin_auth_headers
        ).json()

        assert "alcance" not in cuerpo["meta"]


@pytest.mark.api
class TestNingunCampoPrometeDisponibilidad:
    def test_ninguna_clave_sugiere_disponibilidad(
        self, api_client, admin_auth_headers, dos_flotas
    ):
        cuerpo = api_client.get(f"{RUTA}?limit=500", **admin_auth_headers).json()

        assert cuerpo["data"], "sin filas esta prueba no probaria nada"
        claves = {c.lower() for c in _claves(cuerpo)}
        for prohibida in PROHIBIDAS:
            assert not any(prohibida in c for c in claves), (
                f"el campo '{prohibida}' prometeria un dato que este listado no tiene"
            )

    def test_el_campo_se_llama_dado_de_alta(
        self, api_client, admin_auth_headers, dos_flotas
    ):
        # El nombre dice exactamente lo que el dato significa.
        cuerpo = api_client.get(f"{RUTA}?limit=500", **admin_auth_headers).json()

        assert all("dado_de_alta" in f for f in cuerpo["data"])

    def test_ningun_valor_menciona_un_estado_operativo(
        self, api_client, admin_auth_headers, dos_flotas
    ):
        cuerpo = api_client.get(f"{RUTA}?limit=500", **admin_auth_headers).json()
        texto = json.dumps(cuerpo).lower()

        for estado in ("fuera de servicio", "en misión", "en mision"):
            assert estado not in texto


@pytest.mark.api
class TestElFiltroDeAltaFiltraExistencia:
    def test_las_dadas_de_baja_se_excluyen_con_false(
        self, api_client, admin_auth_headers, dos_flotas
    ):
        cuerpo = api_client.get(
            f"{RUTA}?dado_de_alta=false&limit=500", **admin_auth_headers
        ).json()

        assert "BAJA-01" in {f["placa"] for f in cuerpo["data"]}
        assert "GRUA-01" not in {f["placa"] for f in cuerpo["data"]}

    def test_sin_filtro_salen_las_dos_condiciones(
        self, api_client, admin_auth_headers, dos_flotas
    ):
        cuerpo = api_client.get(f"{RUTA}?limit=500", **admin_auth_headers).json()
        placas = {f["placa"] for f in cuerpo["data"]}

        assert {"GRUA-01", "BAJA-01"} <= placas

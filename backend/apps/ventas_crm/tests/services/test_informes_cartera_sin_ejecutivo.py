"""T023 — un prospecto sin ejecutivo asignado **aparece** (FR-020, research D7).

Es la anomalía que la supervisión busca: un prospecto sin dueño es un prospecto
que nadie está trabajando. Ocultarlo dejaría el listado consistente y con un
agujero, y nadie lo notaría — porque una ausencia solo se detecta si alguien
sabía que ese dato debía estar.

El cliente de Pinot ya convierte el centinela de entero en ausencia de valor, así
que el dato llega correctamente como «no hay». Lo que esta prueba fija es qué se
hace con ese «no hay»: mostrarlo, no filtrarlo.
"""

from __future__ import annotations

import pytest

from apps.ventas_crm.services.informes_cartera_service import InformesCarteraService
from core.informes.acotamiento import ACOTADO_TODOS, Acotamiento

SIN_ACOTAR = Acotamiento(titular=None, alcance=ACOTADO_TODOS)


@pytest.fixture
def servicio(mock_pinot):
    return InformesCarteraService()


class TestProspectoSinDueno:
    def test_aparece_en_el_listado(self, servicio, dos_carteras, prospecto_sin_ejecutivo):
        pagina = servicio.prospectos(acotamiento=SIN_ACOTAR, limit=500)

        assert any(f["empresa"] == "Huerfana S.A." for f in pagina.filas)

    def test_su_ejecutivo_se_marca_como_ausente(
        self, servicio, dos_carteras, prospecto_sin_ejecutivo
    ):
        pagina = servicio.prospectos(acotamiento=SIN_ACOTAR, limit=500)

        fila = next(f for f in pagina.filas if f["empresa"] == "Huerfana S.A.")
        # `None`, no cadena vacía ni «Sin asignar»: la ausencia es un hecho, no
        # una etiqueta que alguien pueda confundir con un nombre.
        assert fila["ejecutivo"] is None

    def test_la_clave_esta_presente_aunque_este_vacia(
        self, servicio, dos_carteras, prospecto_sin_ejecutivo
    ):
        pagina = servicio.prospectos(acotamiento=SIN_ACOTAR, limit=500)

        fila = next(f for f in pagina.filas if f["empresa"] == "Huerfana S.A.")
        assert "ejecutivo" in fila

    def test_el_resto_de_la_fila_llega_completo(
        self, servicio, dos_carteras, prospecto_sin_ejecutivo
    ):
        # No tener dueño no degrada el resto del dato.
        pagina = servicio.prospectos(acotamiento=SIN_ACOTAR, limit=500)

        fila = next(f for f in pagina.filas if f["empresa"] == "Huerfana S.A.")
        assert fila["etapa_actual"]
        assert fila["estado"] == "activo"


class TestElEjecutivoQueSiResuelve:
    def test_llega_como_nombre_no_como_identificador(self, servicio, dos_carteras):
        pagina = servicio.prospectos(acotamiento=SIN_ACOTAR, limit=500)

        fila = next(f for f in pagina.filas if f["empresa"] == "Alfa Seguros")
        assert fila["ejecutivo"] == "Lucia Ramos"


class TestMotivoDePerdida:
    def test_solo_aparece_cuando_el_estado_es_perdido(self, servicio, dos_carteras):
        pagina = servicio.prospectos(acotamiento=SIN_ACOTAR, limit=500)
        por_empresa = {f["empresa"]: f for f in pagina.filas}

        assert por_empresa["Beta Logistica"]["motivo_perdida"] == "eligio a un competidor"

    def test_no_aparece_en_un_convertido(self, servicio, dos_carteras):
        """Un prospecto ganado no tiene motivo de pérdida porque no se perdió.

        Devolver el campo, aunque fuera `null`, sugeriría que la pregunta tiene
        sentido para él.
        """
        pagina = servicio.prospectos(acotamiento=SIN_ACOTAR, limit=500)
        por_empresa = {f["empresa"]: f for f in pagina.filas}

        assert "motivo_perdida" not in por_empresa["Gamma Municipal"]

    def test_no_aparece_en_un_activo(self, servicio, dos_carteras):
        pagina = servicio.prospectos(acotamiento=SIN_ACOTAR, limit=500)
        por_empresa = {f["empresa"]: f for f in pagina.filas}

        assert "motivo_perdida" not in por_empresa["Alfa Seguros"]

    def test_un_perdido_sin_transicion_lo_devuelve_ausente_no_omite_la_fila(
        self, servicio, mock_pinot, gerentes_sembrados
    ):
        from conftest import PINOT_STORE
        from apps.ventas_crm.tests.conftest import GERENTE_A, _prospecto

        PINOT_STORE["Dim_Prospecto"].append(
            _prospecto(8900, empresa="Perdida Sin Motivo", idusuario=GERENTE_A,
                       activo=False, motivo="perdido", etapa="Perdido")
        )

        pagina = servicio.prospectos(acotamiento=SIN_ACOTAR, limit=500)
        fila = next(f for f in pagina.filas if f["empresa"] == "Perdida Sin Motivo")

        assert fila["estado"] == "perdido"
        assert fila["motivo_perdida"] is None


class TestElEstadoSeDecidePorElMotivo:
    """La misma regla que el filtro del repositorio, para que no discrepen."""

    def test_convertido_no_se_presenta_como_perdido(self, servicio, dos_carteras):
        pagina = servicio.prospectos(acotamiento=SIN_ACOTAR, limit=500)
        por_empresa = {f["empresa"]: f for f in pagina.filas}

        assert por_empresa["Gamma Municipal"]["estado"] == "convertido"

    def test_perdido_se_presenta_como_perdido(self, servicio, dos_carteras):
        pagina = servicio.prospectos(acotamiento=SIN_ACOTAR, limit=500)
        por_empresa = {f["empresa"]: f for f in pagina.filas}

        assert por_empresa["Beta Logistica"]["estado"] == "perdido"

    def test_filtrar_por_un_estado_devuelve_filas_de_ese_estado(
        self, servicio, dos_carteras
    ):
        # Si el filtro y la presentación usaran reglas distintas, un prospecto
        # podría filtrarse como perdido y presentarse como convertido.
        for estado in ("activo", "perdido", "convertido"):
            pagina = servicio.prospectos(
                acotamiento=SIN_ACOTAR, limit=500, estado=estado
            )
            assert pagina.filas, f"sin filas no se prueba nada para '{estado}'"
            assert all(f["estado"] == estado for f in pagina.filas)

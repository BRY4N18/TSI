import pytest

from apps.seguimiento.services.cerrar_caso_service import CerrarCasoService
from apps.seguimiento.services.expediente_pdf_service import ExpedientePdfService
from apps.seguimiento.services.finalizar_atencion_unidad_service import (
    FinalizarAtencionUnidadService,
)
from apps.seguimiento.services.registrar_llegada_service import RegistrarLlegadaService


@pytest.mark.service
class TestExpedientePdfService:
    def test_generar_bytes_when_cerrado_returns_pdf(
        self,
        mock_pinot,
        mock_kafka,
        accidente_activo,
        despacho_confirmado_unidad,
    ):
        # Arrange
        iddespacho = despacho_confirmado_unidad["iddespacho"]
        RegistrarLlegadaService().registrar(iddespacho=iddespacho, idunidademergencia=1, idusuario=6)
        # SRS 3.6.4: el caso no cierra hasta que la unidad se retira.
        FinalizarAtencionUnidadService().finalizar(
            iddespacho=iddespacho, idunidademergencia=1, idusuario=6
        )
        CerrarCasoService().cerrar(
            idaccidente=accidente_activo,
            idusuario=2,
            payload={"resultado_atencion": "PDF service test"},
        )
        svc = ExpedientePdfService()

        # Act
        pdf = svc.generar_bytes(accidente_activo, condados_permitidos={1})

        # Assert
        assert pdf is not None
        assert pdf.startswith(b"%PDF")
        assert accidente_activo.encode() in pdf

    def test_generar_bytes_when_activo_returns_none(
        self,
        mock_pinot,
        mock_kafka,
        accidente_activo,
        despacho_confirmado_unidad,
    ):
        # Arrange
        svc = ExpedientePdfService()

        # Act
        pdf = svc.generar_bytes(accidente_activo, condados_permitidos={1})

        # Assert
        assert pdf is None


@pytest.mark.service
class TestMinimalPdf:
    """El PDF tiene que ABRIRSE, no solo empezar por %PDF.

    El test de arriba solo comprobaba el prefijo, y por eso un PDF con la tabla
    `xref` desplazada y todo el texto encima del mismo renglon pasaba sin que
    nadie se enterara — hallazgo #21 de la revision del 24/08/2026 ("sale una
    pagina en blanco o se recorta").
    """

    def _leer(self, pdf: bytes):
        import io

        from pypdf import PdfReader

        return PdfReader(io.BytesIO(pdf))

    def test_startxref_apunta_a_la_tabla_real(self):
        # Arrange
        from apps.seguimiento.services.expediente_pdf_service import _minimal_pdf

        # Act
        pdf = _minimal_pdf("Una linea\nOtra linea")

        # Assert — los offsets se calculaban desde el cuerpo, ignorando los 9
        # bytes de la cabecera: todos quedaban cortos y el lector no encontraba
        # los objetos.
        posicion_real = pdf.find(b"\nxref") + 1
        declarado = int(pdf.split(b"startxref")[1].split()[0])
        assert declarado == posicion_real

    def test_cada_linea_ocupa_su_propio_renglon(self):
        # Arrange
        from apps.seguimiento.services.expediente_pdf_service import _minimal_pdf

        # Act
        pdf = _minimal_pdf("Primera\nSegunda\nTercera")
        texto = self._leer(pdf).pages[0].extract_text() or ""

        # Assert — un \n dentro de un string PDF no salta de renglon; hace falta
        # T*. Antes las tres lineas se pintaban encima del mismo renglon.
        renglones = [r.strip() for r in texto.strip().split("\n") if r.strip()]
        assert renglones == ["Primera", "Segunda", "Tercera"]

    def test_linea_larga_se_envuelve_en_vez_de_recortarse(self):
        # Arrange
        from apps.seguimiento.services.expediente_pdf_service import (
            _MAX_CARACTERES_LINEA,
            _minimal_pdf,
        )

        larga = "dato " * 60

        # Act
        pdf = _minimal_pdf(larga)
        texto = self._leer(pdf).pages[0].extract_text() or ""

        # Assert
        renglones = [r for r in texto.strip().split("\n") if r.strip()]
        assert len(renglones) > 1
        assert all(len(r.strip()) <= _MAX_CARACTERES_LINEA for r in renglones)

    def test_texto_largo_pagina_en_varias_hojas(self):
        # Arrange
        from apps.seguimiento.services.expediente_pdf_service import _minimal_pdf

        # Act
        pdf = _minimal_pdf("\n".join(f"Renglon {i}" for i in range(1, 120)))
        lector = self._leer(pdf)

        # Assert — antes todo iba a una sola pagina y lo que no cabia se perdia.
        assert len(lector.pages) > 1
        assert "Renglon 119" in (lector.pages[-1].extract_text() or "")

    def test_parentesis_no_rompen_el_documento(self):
        # Arrange
        from apps.seguimiento.services.expediente_pdf_service import _minimal_pdf

        # Act — los parentesis delimitan strings en PDF; sin escapar, el
        # documento queda corrupto.
        pdf = _minimal_pdf(r"Colision (curva) con \ barra")
        texto = self._leer(pdf).pages[0].extract_text() or ""

        # Assert
        assert "curva" in texto

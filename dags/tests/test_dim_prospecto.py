"""T008 y T009 — el desenlace de tres valores, y la ausencia de dato personal.

⚠️ **La trampa de este departamento es `activo`.** No dice si el prospecto sigue
en curso: cubre a la vez a los que se convirtieron y a los que se perdieron.
Medido sobre los datos reales: de los tres con `activo = false`, **dos son
convertidos y uno perdido**.

Un informe que agrupara por esa columna juntaría el mejor desenlace posible con
el peor y devolvería «3 inactivos» — una cifra que no significa nada y que nadie
cuestionaría, porque suena a lo que se esperaba.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.dimensiones.dim_canal import clave, normalizar  # noqa: E402
from lib.dimensiones.dim_prospecto import (  # noqa: E402
    CONSULTA_PROSPECTOS,
    construir,
    desenlace_de,
)

AHORA = datetime(2026, 8, 16, 12, 0, 0)


def _prospecto(idp: int, **campos) -> dict:
    base = {
        "idprospecto": idp,
        "empresa": "Empresa X",
        "tipo_organizacion": "Privada",
        "como_nos_conocio": "Web",
        "etapa_actual": "Contactado",
        "motivo_inactividad": None,
        "activo": True,
        "valor_estimado": 1000.0,
        "fecha_registro": 1786000000000,
    }
    base.update(campos)
    return base


class TestElDesenlaceTieneTresValores:
    """T008 — SC-002. `activo` solo distingue dos grupos, y hacen falta tres."""

    def test_un_convertido_y_un_perdido_quedan_en_grupos_distintos(self):
        """⚠️ Los dos comparten `activo = false` en el origen.

        Si el modelo solo distinguiera dos grupos, el desenlace habría salido de
        la columna equivocada — y el informe de conversión contaría las pérdidas
        como éxitos.
        """
        convertido = _prospecto(1, activo=False, motivo_inactividad="convertido",
                                etapa_actual="Ganado")
        perdido = _prospecto(2, activo=False, motivo_inactividad="perdido",
                             etapa_actual="Perdido")

        assert desenlace_de(convertido) == "convertido"
        assert desenlace_de(perdido) == "perdido"
        assert desenlace_de(convertido) != desenlace_de(perdido)

    def test_un_prospecto_vivo_esta_en_curso_y_no_perdido(self):
        # No hay evidencia de que terminara. Contarlo como perdido haría que el
        # embudo empeorara por el simple hecho de tener prospectos abiertos.
        assert desenlace_de(_prospecto(3, activo=True)) == "en_curso"

    def test_la_etapa_terminal_basta_cuando_no_hay_motivo(self):
        """Un prospecto en `Ganado` se convirtió aunque nadie escribiera el motivo.

        El respaldo importa: sin él, un hueco de registro convertiría un éxito en
        un prospecto eternamente en curso, y el embudo diría que nadie cierra.
        """
        assert desenlace_de(
            _prospecto(4, activo=False, motivo_inactividad=None, etapa_actual="Ganado")
        ) == "convertido"
        assert desenlace_de(
            _prospecto(5, activo=False, motivo_inactividad=None, etapa_actual="Perdido")
        ) == "perdido"

    def test_activo_no_participa_en_la_decision(self):
        """⚠️ Ni siquiera como respaldo.

        Es la columna que mezcla los dos desenlaces terminales, así que usarla
        para cualquier cosa reintroduciría el defecto por la puerta de atrás. Un
        prospecto inactivo del que no se sabe nada sigue **en curso**: no saber
        cómo acabó no es saber que acabó mal.
        """
        sin_pistas = _prospecto(6, activo=False, motivo_inactividad=None,
                                etapa_actual="Contactado")

        assert desenlace_de(sin_pistas) == "en_curso"

    def test_el_motivo_manda_sobre_la_etapa(self):
        # El motivo es lo que alguien **declaró**; la etapa es donde quedó el
        # prospecto. Si discrepan, gana la declaración explícita.
        raro = _prospecto(7, activo=False, motivo_inactividad="perdido",
                          etapa_actual="Ganado")

        assert desenlace_de(raro) == "perdido"

    @pytest.mark.parametrize("motivo", ["Convertido", "  convertido  ", "CONVERTIDO"])
    def test_el_motivo_se_compara_sin_mayusculas_ni_espacios(self, motivo):
        # El origen lo escribe a mano. Comparar literalmente dejaría fuera las
        # variantes y esos prospectos quedarían «en curso» para siempre.
        assert desenlace_de(_prospecto(8, activo=False, motivo_inactividad=motivo)) == "convertido"


class TestNingunDatoPersonalEntra:
    """T009 — SC-007. No filtradas: **inexistentes**."""

    PERSONALES = ("nombres", "apellidos", "gmail", "correo", "telefono", "cargo",
                  "idusuario", "usuario")

    def test_la_consulta_no_pide_ningun_campo_personal(self):
        """La primera mitad: no se traen.

        `Dim_Prospecto` es la tabla con más dato personal del sistema, así que un
        `SELECT *` aquí sacaría el teléfono de cada prospecto a un informe.
        """
        for campo in self.PERSONALES:
            assert campo not in CONSULTA_PROSPECTOS.lower(), (
                f"la consulta pide '{campo}', que es dato personal"
            )
        assert "SELECT *" not in CONSULTA_PROSPECTOS.upper()

    def test_ninguna_fila_construida_lleva_dato_personal(self):
        """La segunda mitad: aunque llegaran, no saldrían.

        Las dos hacen falta. Si solo se comprobara la consulta, un cambio en ella
        publicaría el dato; si solo se comprobara la fila, nadie notaría que el
        dato viaja por la red y queda en el fichero intermedio.
        """
        fila = construir(
            [_prospecto(1, nombres="Ana", gmail="ana@x.com", telefono="600")],
            [{"idcanal": 1, "canal": "Web"}],
            AHORA,
        )[0]

        for campo in self.PERSONALES:
            assert campo not in fila, f"la fila lleva '{campo}'"
        assert "Ana" not in str(fila) and "ana@x.com" not in str(fila)

    def test_lo_que_si_entra_hace_analizable_el_embudo(self):
        # La comprobación simétrica: excluir de más dejaría la dimensión sin nada
        # con lo que agrupar, y el departamento sin informes.
        fila = construir(
            [_prospecto(1)], [{"idcanal": 1, "canal": "Web"}], AHORA
        )[0]

        for campo in ("empresa", "tipo_organizacion", "canal", "desenlace", "valor_estimado"):
            assert campo in fila


class TestElCanal:
    def test_un_prospecto_sin_canal_cae_en_la_fila_desconocida(self):
        """Y **cuenta en los totales**: llegó igual.

        Dejarlo fuera haría que la suma de los canales fuera menor que el total
        del embudo, con los porcentajes sumando 100 % entre ellos — que es la
        forma en que ese fallo pasa inadvertido.
        """
        fila = construir(
            [_prospecto(1, como_nos_conocio=None)], [{"idcanal": 1, "canal": "Web"}], AHORA
        )[0]

        assert fila["idcanal"] == -1
        assert fila["canal"] == "Desconocido"

    def test_las_variantes_del_mismo_canal_convergen(self):
        """Sin esto, «Web» y «  WEB  » serían dos canales.

        El informe de rendimiento repartiría el mismo canal en varias filas con
        una fracción del volumen cada una, y ninguna parecería importante.

        ⚠️ Convergen por `clave`, no por `normalizar`. Hasta el 2026-08-19 las
        dos cosas eran la misma función, y para hacerlas converger forzaba el
        resto a minúscula: en pantalla salían «Linkedin» y «Referido tsi» con el
        origen diciendo «LinkedIn» y «Referido TSI». Agrupar y mostrar se
        separaron; lo que esta prueba protege —que no se partan— sigue igual.
        """
        assert clave("  WEB  ") == clave("web") == clave("Web")

    def test_la_grafia_del_origen_se_conserva_al_mostrar(self):
        """Lo que se agrupa sin mayúsculas no se muestra sin mayúsculas."""
        assert normalizar("  LinkedIn  ") == "LinkedIn"
        assert normalizar("Referido TSI") == "Referido TSI"

    def test_el_alias_junta_las_dos_variantes_que_hay_en_los_datos(self):
        # «Web / catálogo planes» y «Web / catálogo de planes» son el mismo canal
        # —falta un «de»— y partido en dos no aparece como el mayor.
        assert normalizar("Web / catálogo planes") == "Web / catálogo de planes"
        assert clave("Web / catálogo planes") == clave("Web / catálogo de planes")

    def test_dos_canales_distintos_no_se_juntan(self):
        """⚠️ El error simétrico, y peor.

        Juntar canales que alguien quiere ver por separado desaparece de la
        vista; partir uno se ve mirando la lista. «Referido institucional» y
        «Referido tsi» son cosas distintas.
        """
        assert normalizar("Referido institucional") != normalizar("Referido tsi")

    def test_una_fecha_ausente_no_se_convierte_en_la_epoca_cero(self):
        # Un prospecto registrado en 1970 tendría cincuenta y seis años y
        # encabezaría cualquier informe de prospectos estancados.
        fila = construir(
            [_prospecto(1, fecha_registro=None)], [{"idcanal": 1, "canal": "Web"}], AHORA
        )[0]

        assert fila["fecha_registro"] is None

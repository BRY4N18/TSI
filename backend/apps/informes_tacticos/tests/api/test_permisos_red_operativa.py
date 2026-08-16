"""T016 — la autoridad repartida de Red Operativa (FR-025).

Este departamento **no tiene una jefatura única**, y esta prueba existe porque el
error natural al escribir el permiso es admitir a las dos autoridades del
departamento y quedarse tranquilo. Eso daría a cada director acceso a la materia
del otro, **sin que nada fallara ni nadie se quejara** — un permiso demasiado
ancho no produce ningún síntoma, solo consecuencias.

Lo que se comprueba, entonces, no es que los directores entren: es que **cada uno
se queda fuera de la materia ajena**.
"""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from apps.informes_tacticos.services.red_operativa_compuestos_service import (
    CATALOGO,
    MATERIA_CRECIMIENTO,
    MATERIA_VALIDACION,
    MATERIAS,
)
from core.jwt_utils import create_access_token

BASE = "/api/v1/informes-tacticos/red-operativa"

DE_CRECIMIENTO = sorted(i for i, m in MATERIAS.items() if m == MATERIA_CRECIMIENTO)
DE_VALIDACION = sorted(i for i, m in MATERIAS.items() if m == MATERIA_VALIDACION)


def _concede(roles, informe):
    """¿El permiso deja pasar a estos roles para este informe?

    Se pregunta a la clase de permiso y no por HTTP, y es deliberado: las
    consultas del catálogo son de las fases siguientes, así que hoy un `GET`
    concedido termina en un error de consulta inexistente y la respuesta no
    distingue «entró» de «no entró». Aquí lo que se comprueba es **la decisión de
    acceso**, que es lo que esta prueba dice comprobar.

    Las comprobaciones de que alguien **no** entra sí van por HTTP: esas
    terminan en 403 antes de tocar ninguna consulta, así que prueban el camino
    completo — y son las que importan, porque un permiso demasiado ancho no
    produce ningún síntoma.
    """
    from types import SimpleNamespace

    from apps.informes_tacticos.permissions import RedOperativaCompuestosPermission

    usuario = SimpleNamespace(is_authenticated=True, roles=roles)
    peticion = SimpleNamespace(user=usuario)
    vista = SimpleNamespace(kwargs={"informe": informe})
    return RedOperativaCompuestosPermission().has_permission(peticion, vista)


def _cliente(roles):
    api = APIClient()
    api.credentials(
        HTTP_AUTHORIZATION=f"Bearer {create_access_token(user_id=1, roles=roles, session_id=1)}"
    )
    return api


class TestCadaDirectorSeQuedaFueraDeLaMateriaAjena:
    """⚠️ El corazón de FR-025."""

    @pytest.mark.parametrize("informe", DE_VALIDACION)
    def test_el_director_de_expansion_no_entra_a_validacion(self, informe):
        respuesta = _cliente(["DirectorExpansion"]).get(f"{BASE}/{informe}")

        assert respuesta.status_code == 403, (
            f"el Director de Expansión accede a '{informe}', que es de validación "
            f"de región: gobierna el crecimiento, no los criterios de validación"
        )

    @pytest.mark.parametrize("informe", DE_CRECIMIENTO)
    def test_el_director_tecnologico_no_entra_a_crecimiento(self, informe):
        respuesta = _cliente(["DirectorTecnologico"]).get(f"{BASE}/{informe}")

        assert respuesta.status_code == 403, (
            f"el Director Tecnológico accede a '{informe}', que es de crecimiento "
            f"de flota: gobierna la validación de región, no dónde se crece"
        )


class TestCadaDirectorEntraALaSuya:
    @pytest.mark.parametrize("informe", DE_CRECIMIENTO)
    def test_expansion_entra_a_crecimiento(self, informe):
        assert _concede(["DirectorExpansion"], informe)

    @pytest.mark.parametrize("informe", DE_VALIDACION)
    def test_tecnologico_entra_a_validacion(self, informe):
        assert _concede(["DirectorTecnologico"], informe)


class TestElResponsableOperativoNoEstaRepartido:
    @pytest.mark.parametrize("informe", sorted(CATALOGO))
    def test_el_administrador_entra_a_las_dos_materias(self, informe):
        # Su papel no está repartido: es el responsable operativo del
        # departamento entero, y entra con su acotamiento.
        assert _concede(["Administrador"], informe)


class TestQuienNoTieneNadaQueVer:
    @pytest.mark.parametrize(
        "roles",
        [["Operador"], ["Cliente"], ["Tecnico"], ["DirectorMarketing"], []],
    )
    def test_no_entra(self, roles):
        assert _cliente(roles).get(f"{BASE}/mercados-activos").status_code == 403

    def test_sin_credencial_es_401_y_no_403(self):
        assert APIClient().get(f"{BASE}/mercados-activos").status_code == 401


class TestElRegistroDeMaterias:
    def test_todo_informe_del_catalogo_declara_su_materia(self):
        """Un informe sin materia no lo ve nadie, y eso es lo correcto.

        La alternativa —una materia por defecto— dejaría accesible un informe
        nuevo a quien no le corresponde. Esta prueba obliga a decidir de quién es
        cada informe **antes** de publicarlo.
        """
        sin_materia = set(CATALOGO) - set(MATERIAS)

        assert not sin_materia, f"{sorted(sin_materia)} no declaran su materia"

    def test_un_informe_sin_materia_declarada_no_lo_ve_nadie(self):
        # La comprobación del comportamiento, no solo del registro.
        for roles in (["DirectorExpansion"], ["DirectorTecnologico"], ["Administrador"]):
            assert _cliente(roles).get(f"{BASE}/informe-que-no-existe").status_code == 403

    def test_las_dos_materias_tienen_informes(self):
        # Si una quedara vacía, la mitad de las pruebas de arriba pasaría sin
        # comprobar nada.
        assert DE_CRECIMIENTO and DE_VALIDACION

    def test_solo_son_de_validacion_los_que_miden_como_se_valida(self):
        """«Regiones en riesgo» suena a validación y no lo es.

        Habla de si el mercado aguanta, que es de quien decide dónde crecer. La
        distinción se equivoca sola, así que se fija aquí.
        """
        assert set(DE_VALIDACION) == {"tasa-aprobacion-primer-intento", "motivos-rechazo"}

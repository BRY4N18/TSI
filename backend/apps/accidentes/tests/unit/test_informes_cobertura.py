"""T010 y T011 — el eje de cobertura contratada, aislado.

**T010 es la prueba que decide un control de acceso.** De las dos lecturas
posibles de «este cliente no tiene zonas», una da acceso a todo el mapa de
siniestralidad a quien no contrató nada. La prueba fija la otra.

**T011 comprueba que la resolución es un filtro**, no una comprobación fila a
fila: un conjunto por petición, no una consulta por caso.
"""

from __future__ import annotations

import pytest

from core.informes.acotamiento import AccesoDenegado
from core.informes.cobertura import ACOTADO_ZONAS, resolver_cobertura

INTERNOS = frozenset({"Operador", "Administrador"})
CLIENTES = frozenset({"Cliente"})


def _resolver(roles, zonas=frozenset({10})):
    return resolver_cobertura(
        roles=roles,
        user_id=1,
        roles_internos=INTERNOS,
        roles_cliente=CLIENTES,
        resolver_ubicaciones=lambda _uid: zonas,
    )


class TestSinZonasEsCeroNoTodo:
    def test_un_cliente_sin_zonas_queda_acotado_a_conjunto_vacio(self):
        cobertura = _resolver(["Cliente"], zonas=frozenset())

        assert cobertura.ubicaciones == frozenset()
        assert cobertura.acotado is True
        assert cobertura.sin_cobertura is True

    def test_conjunto_vacio_no_es_lo_mismo_que_no_filtrar(self):
        """`None` significa «no filtres». Confundirlos es la fuga entera.

        Un `if zonas:` que se saltara el filtro cuando el conjunto está vacío
        caería justo en la lectura peligrosa, y sin ruido: la respuesta tendría
        la forma correcta y contendría todo el mapa.
        """
        sin_zonas = _resolver(["Cliente"], zonas=frozenset())
        interno = _resolver(["Operador"])

        assert sin_zonas.ubicaciones is not None
        assert interno.ubicaciones is None
        assert sin_zonas.ubicaciones != interno.ubicaciones

    def test_el_repositorio_devuelve_cero_filas_con_conjunto_vacio(self):
        """Y **sin ir a la base**: no hay consulta que pudiera equivocarse."""
        from core.repositories.accidentes.informes_casos_repository import (
            InformesCasosRepository,
        )

        class _PinotQueNoDebeLlamarse:
            def query(self, *_a, **_k):
                raise AssertionError("no debe consultarse con cobertura vacia")

        repo = InformesCasosRepository(pinot=_PinotQueNoDebeLlamarse())

        assert repo.casos(idcalles=frozenset()) == []


class TestQuienAccedeYConQueAlcance:
    def test_un_rol_interno_no_queda_acotado(self):
        cobertura = _resolver(["Operador"])

        assert cobertura.ubicaciones is None
        assert cobertura.alcance == "todos"
        assert cobertura.solo_cerrados is False

    def test_un_cliente_queda_acotado_y_solo_a_cerrados(self):
        cobertura = _resolver(["Cliente"])

        assert cobertura.ubicaciones == frozenset({10})
        assert cobertura.alcance == ACOTADO_ZONAS
        assert cobertura.solo_cerrados is True

    def test_un_rol_mixto_no_queda_acotado(self):
        """Misma regla que el rol mixto de Soporte: tener el rol interno saca
        del acotamiento."""
        cobertura = _resolver(["Cliente", "Operador"])

        assert cobertura.ubicaciones is None
        assert cobertura.alcance == "todos"

    def test_un_rol_ajeno_recibe_negativa_no_un_listado_vacio(self):
        """Un listado vacío le haría leer «no hay accidentes» donde debía leer
        «no puedes consultar esto»."""
        with pytest.raises(AccesoDenegado):
            _resolver(["PartnerIntegracion"])

    def test_las_zonas_no_se_resuelven_para_quien_no_accede(self):
        """El orden importa: primero se descarta el rol desconocido."""
        def _no_debe_llamarse(_uid):
            raise AssertionError("no debe resolverse la cobertura de un rol ajeno")

        with pytest.raises(AccesoDenegado):
            resolver_cobertura(
                roles=["Desconocido"],
                user_id=1,
                roles_internos=INTERNOS,
                roles_cliente=CLIENTES,
                resolver_ubicaciones=_no_debe_llamarse,
            )

    def test_declarar_un_rol_en_los_dos_conjuntos_falla_al_configurar(self):
        """Haría el resultado dependiente del orden de evaluación."""
        with pytest.raises(ValueError, match="internos y clientes"):
            resolver_cobertura(
                roles=["Cliente"],
                user_id=1,
                roles_internos=frozenset({"Cliente"}),
                roles_cliente=frozenset({"Cliente"}),
                resolver_ubicaciones=lambda _uid: frozenset(),
            )


@pytest.mark.django_db
class TestLaResolucionEsPorLotes:
    def test_condados_a_calles_cuesta_dos_consultas_sea_cual_sea_el_numero(
        self, geografia_sembrada
    ):
        """Un conjunto por petición, **no una consulta por condado**.

        Si el coste creciera con el número de zonas, el acotamiento volvería a
        ser lo que la spec descartó: trabajo proporcional en vez de un filtro.
        """
        from core.pinot.client import PinotClient
        from core.repositories.accidentes.informes_ubicacion_repository import (
            InformesUbicacionRepository,
        )
        from apps.accidentes.tests.informes_fixtures import (
            CONDADO_AJENO,
            CONDADO_CONTRATADO,
        )

        consultas: list[str] = []
        real = PinotClient()

        class _Contando:
            def query(self, sql, params=None):
                consultas.append(sql)
                return real.query(sql, params)

        repo = InformesUbicacionRepository(pinot=_Contando())

        consultas.clear()
        repo.calles_de_condados([CONDADO_CONTRATADO])
        con_uno = len(consultas)

        consultas.clear()
        repo.calles_de_condados([CONDADO_CONTRATADO, CONDADO_AJENO])
        con_dos = len(consultas)

        assert con_uno == con_dos == 2

    def test_sin_condados_no_consulta_nada(self, geografia_sembrada):
        from core.repositories.accidentes.informes_ubicacion_repository import (
            InformesUbicacionRepository,
        )

        class _PinotQueNoDebeLlamarse:
            def query(self, *_a, **_k):
                raise AssertionError("no debe consultarse sin condados")

        repo = InformesUbicacionRepository(pinot=_PinotQueNoDebeLlamarse())

        assert repo.calles_de_condados([]) == frozenset()

    def test_las_zonas_de_un_cliente_sin_preferencias_son_vacio(
        self, geografia_sembrada
    ):
        from core.repositories.accidentes.informes_ubicacion_repository import (
            InformesUbicacionRepository,
        )

        assert InformesUbicacionRepository().zonas_contratadas(999_999) == frozenset()

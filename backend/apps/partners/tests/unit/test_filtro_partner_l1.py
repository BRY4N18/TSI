"""El filtro «Partner» del listado L1 tiene que filtrar de verdad.

⚠️ **Esta prueba existe porque el filtro estaba en pantalla y no hacía nada.**

`PartnersView` leía `partner` de la query —para comprobar propiedad en
`acotar()`— y nunca lo pasaba al servicio. El resultado era el peor de los
posibles: el desplegable se pintaba, el parámetro viajaba, el backend respondía
`200`, y el listado devolvía **todos los partners igual**. Nada fallaba.

Además `meta.filtros.partner` publicaba `acotamiento.titular`, que en un gestor
es `None`: la respuesta decía «no se aplicó filtro de partner» y era cierto —
pero la pantalla afirmaba lo contrario.
"""

from core.informes.acotamiento import ACOTADO_TODOS, Acotamiento
from apps.partners.services.informes_acceso_service import InformesAccesoService


class _RepoEspia:
    def __init__(self):
        self.recibido = {}

    def partners(self, **kwargs):
        self.recibido = kwargs
        return []

    def credenciales_de(self, ids):
        return {}

    def eventos_de(self, ids, tipos):
        return {}

    def razones_sociales(self, ids):
        return {}


def _servicio():
    repo = _RepoEspia()
    servicio = InformesAccesoService()
    servicio.repo = repo
    return servicio, repo


class TestElFiltroLlegaAlRepositorio:
    def test_el_idpartner_pedido_se_empuja_a_la_consulta(self):
        servicio, repo = _servicio()
        servicio.partners(
            acotamiento=Acotamiento(titular=None, alcance=ACOTADO_TODOS), idpartner=7
        )
        assert repo.recibido["idpartner"] == 7

    def test_sin_pedirlo_no_se_filtra(self):
        servicio, repo = _servicio()
        servicio.partners(acotamiento=Acotamiento(titular=None, alcance=ACOTADO_TODOS))
        assert repo.recibido["idpartner"] is None

    def test_acotar_y_filtrar_viajan_por_separado(self):
        """⚠️ `cuenta` es a qué tiene derecho; `idpartner` es qué pidió.

        Mezclarlos haría que filtrar por un partner pareciera reducir el alcance
        —o, al revés, que pedir uno ajeno lo ampliara.
        """
        servicio, repo = _servicio()
        servicio.partners(
            acotamiento=Acotamiento(titular=42, alcance="propios"), idpartner=7
        )
        assert repo.recibido["cuenta"] == 42
        assert repo.recibido["idpartner"] == 7

"""Catálogos que pueblan los desplegables de los filtros.

⚠️ **Un catálogo no parece un control de acceso, y lo es.** `Cobertura` acota qué
*filas* ve un cliente; la lista de condados no es una fila, es metadato, y hay
que acotarla a mano. Publicarla entera diría dónde opera el sistema a quien
contrató una sola zona — con el listado devolviendo cero filas y ningún síntoma.
"""

from core.informes.cobertura import Cobertura
from apps.accidentes.services.informes_catalogos_service import (
    InformesCatalogosService,
    _desambiguar_ciudades,
)


class _RepoFalso:
    def catalogo_severidades(self):
        return [{"id": 1, "nombre": "Leve"}]

    def catalogo_tipos_reportados(self):
        return [{"id": 1, "nombre": "Llamada telefónica"}]


class _UbicacionesFalsas:
    def __init__(self):
        self.condados_pedidos = "no se llamó"
        self.ciudades_pedidas = "no se llamó"

    def catalogo_condados(self, contratados):
        self.condados_pedidos = contratados
        if contratados is not None and not contratados:
            return []
        return [{"id": 1, "nombre": "Cuauhtemoc"}, {"id": 2, "nombre": "Benito Juarez"}]

    def catalogo_ciudades(self, contratados):
        self.ciudades_pedidas = contratados
        if contratados is not None and not contratados:
            return []
        return [{"id": 1, "nombre": "Ciudad de Mexico", "idcondado": 1}]


def _servicio():
    ubic = _UbicacionesFalsas()
    return InformesCatalogosService(repo=_RepoFalso(), ubicaciones=ubic), ubic


class TestAcotamiento:
    def test_el_rol_interno_recibe_el_catalogo_completo(self):
        servicio, ubic = _servicio()
        servicio.catalogos(cobertura=Cobertura(ubicaciones=None, alcance="todos"))
        assert ubic.condados_pedidos is None
        assert ubic.ciudades_pedidas is None

    def test_el_cliente_solo_recibe_sus_condados_contratados(self):
        servicio, ubic = _servicio()
        servicio.catalogos(
            cobertura=Cobertura(ubicaciones=frozenset({2}), alcance="zonas_contratadas")
        )
        assert ubic.condados_pedidos == frozenset({2})
        assert ubic.ciudades_pedidas == frozenset({2})

    def test_sin_zonas_contratadas_el_catalogo_es_vacio_y_no_completo(self):
        """⚠️ La lectura peligrosa de «este cliente no tiene zonas».

        Un `if contratados:` que se salte el acotamiento con el conjunto vacío
        devolvería el mapa entero justo a quien no contrató nada.
        """
        servicio, ubic = _servicio()
        catalogos = servicio.catalogos(
            cobertura=Cobertura(ubicaciones=frozenset(), alcance="zonas_contratadas")
        )
        assert ubic.condados_pedidos == frozenset()
        assert catalogos["condado"] == []
        assert catalogos["ciudad"] == []

    def test_severidad_y_tipo_no_se_acotan(self):
        """Son catálogos de referencia: no dicen dónde opera nadie."""
        servicio, _ = _servicio()
        catalogos = servicio.catalogos(
            cobertura=Cobertura(ubicaciones=frozenset(), alcance="zonas_contratadas")
        )
        assert catalogos["severidad"] == [{"id": 1, "nombre": "Leve"}]
        assert catalogos["tipo_reportado"] == [{"id": 1, "nombre": "Llamada telefónica"}]


class TestDesambiguarCiudades:
    CONDADOS = [{"id": 1, "nombre": "Cuauhtemoc"}, {"id": 2, "nombre": "Benito Juarez"}]

    def test_las_homonimas_se_cualifican_con_su_condado(self):
        ciudades = [
            {"id": 1, "nombre": "Ciudad de Mexico", "idcondado": 1},
            {"id": 2, "nombre": "Ciudad de Mexico", "idcondado": 2},
        ]
        assert _desambiguar_ciudades(ciudades, self.CONDADOS) == [
            {"id": 1, "nombre": "Ciudad de Mexico · Cuauhtemoc"},
            {"id": 2, "nombre": "Ciudad de Mexico · Benito Juarez"},
        ]

    def test_una_ciudad_con_nombre_unico_se_deja_desnuda(self):
        # Repetir el condado en todas sería ruido en el caso que no lo necesita.
        ciudades = [{"id": 3, "nombre": "Toluca", "idcondado": 1}]
        assert _desambiguar_ciudades(ciudades, self.CONDADOS) == [
            {"id": 3, "nombre": "Toluca"}
        ]

    def test_no_se_inventa_condado_cuando_no_resuelve(self):
        """Mejor ambigua que cualificada con algo que no se sabe."""
        ciudades = [
            {"id": 1, "nombre": "Ciudad de Mexico", "idcondado": 99},
            {"id": 2, "nombre": "Ciudad de Mexico", "idcondado": 99},
        ]
        assert [c["nombre"] for c in _desambiguar_ciudades(ciudades, self.CONDADOS)] == [
            "Ciudad de Mexico",
            "Ciudad de Mexico",
        ]

    def test_el_idcondado_no_se_publica(self):
        """Es un detalle interno de la desambiguación, no parte del contrato."""
        ciudades = [{"id": 3, "nombre": "Toluca", "idcondado": 1}]
        assert "idcondado" not in _desambiguar_ciudades(ciudades, self.CONDADOS)[0]

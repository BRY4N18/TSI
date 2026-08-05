import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.rendimiento_proveedor_logic import agregar_por_proveedor  # noqa: E402


class TestAgregarPorProveedor:
    def test_dos_proveedores_con_distinto_pct_rechazo(self):
        # Arrange
        despachos = [
            {"iddespacho": 1, "idunidademergencia": 10, "periodo": "2026-07-01", "fechahoradespacho": 0, "fechahorallegada": 60_000},
            {"iddespacho": 2, "idunidademergencia": 20, "periodo": "2026-07-01", "fechahoradespacho": 0, "fechahorallegada": 120_000},
        ]
        historial = [
            {"iddespacho": 1, "estadonuevo": "Rechazado"},
            {"iddespacho": 2, "estadonuevo": "Confirmado"},
        ]
        unidades = [
            {"idunidademergencia": 10, "idcliente": 100},
            {"idunidademergencia": 20, "idcliente": 200},
        ]

        # Act
        result = agregar_por_proveedor(despachos, historial, unidades)

        # Assert
        por_cliente = {r["idcliente"]: r for r in result}
        assert por_cliente[100]["pct_rechazo"] == 1.0
        assert por_cliente[200]["pct_rechazo"] == 0.0
        assert por_cliente[100]["tiempo_llegada_promedio_seg"] == 60.0
        assert por_cliente[200]["tiempo_llegada_promedio_seg"] == 120.0

    def test_unidad_sin_proveedor_conocido_se_omite(self):
        despachos = [{"iddespacho": 1, "idunidademergencia": 99, "periodo": "2026-07-01", "fechahoradespacho": 0, "fechahorallegada": None}]
        result = agregar_por_proveedor(despachos, [], unidades=[])
        assert result == []

    def test_calcula_pct_abortos(self):
        despachos = [{"iddespacho": 1, "idunidademergencia": 10, "periodo": "2026-07-01", "fechahoradespacho": 0, "fechahorallegada": None}]
        historial = [{"iddespacho": 1, "estadonuevo": "Abortado"}]
        unidades = [{"idunidademergencia": 10, "idcliente": 100}]

        result = agregar_por_proveedor(despachos, historial, unidades)

        assert result[0]["pct_abortos"] == 1.0
        assert result[0]["total_despachos"] == 1

from unittest.mock import MagicMock

import pytest

from apps.red_operativa.services.importacion_lote_unidad_service import (
    ImportacionLoteUnidadService,
)

PROVEEDOR = {"user_id": 3, "roles": ["Cliente"]}


@pytest.mark.service
class TestImportacionLoteUnidadService:
    def _fila_valida(self, **overrides):
        fila = {
            "idcondado": 1,
            "tipopropiedad": "Externa",
            "placa": "LOTE-001",
            "contactoproveedor": "555",
            "unidademergencia": "Ambulancia Lote",
            "tipounidademergencia": "Ambulancia",
            "gmail": "lote001@test.com",
        }
        fila.update(overrides)
        return fila

    def test_importar_when_todas_validas_inserta_todas(self, mock_pinot, mock_kafka, pinot_store):
        # Arrange
        service = ImportacionLoteUnidadService()
        filas = [
            self._fila_valida(placa=f"LOTE-{i}", gmail=f"lote{i}@test.com") for i in range(3)
        ]

        # Act
        result = service.importar(filas, **PROVEEDOR)

        # Assert
        assert result["insertadas"] == 3
        assert result["usuarios_creados"] == 3
        assert result["fallidas"] == []
        for u in pinot_store["Dim_UnidadEmergencia"]:
            if str(u.get("placa", "")).startswith("LOTE-"):
                assert u.get("idusuario") is not None

    def test_importar_acepta_condado_por_nombre(self, mock_pinot, mock_kafka, pinot_store):
        """Hallazgo #16 — el CSV pedía `idcondado`, que el usuario no puede conocer."""
        # Arrange
        service = ImportacionLoteUnidadService()
        fila = self._fila_valida(placa="LOTE-NOM", gmail="lotenom@test.com")
        fila.pop("idcondado")
        fila["condado"] = "Cuauhtémoc"

        # Act
        result = service.importar([fila], **PROVEEDOR)

        # Assert
        assert result["fallidas"] == []
        assert result["insertadas"] == 1
        creada = next(
            u for u in pinot_store["Dim_UnidadEmergencia"] if u.get("placa") == "LOTE-NOM"
        )
        assert creada["idcondado"] == 1

    def test_importar_reporta_condado_inexistente_sin_insertar(self, mock_pinot, mock_kafka):
        # Arrange
        service = ImportacionLoteUnidadService()
        fila = self._fila_valida(placa="LOTE-BAD", gmail="lotebad@test.com")
        fila.pop("idcondado")
        fila["condado"] = "Condado Que No Existe"

        # Act
        result = service.importar([fila], **PROVEEDOR)

        # Assert — todo-o-nada: se reporta la fila, no se inserta nada.
        assert result["insertadas"] == 0
        assert "no existe en el catálogo" in result["fallidas"][0]["motivo"]

    def test_importar_sin_condado_reporta_campo_requerido(self, mock_pinot, mock_kafka):
        # Arrange
        service = ImportacionLoteUnidadService()
        fila = self._fila_valida(placa="LOTE-SIN", gmail="lotesin@test.com")
        fila.pop("idcondado")

        # Act
        result = service.importar([fila], **PROVEEDOR)

        # Assert
        assert result["insertadas"] == 0
        assert "condado es requerido" in result["fallidas"][0]["motivo"]

    def test_importar_when_plan_no_habilita_lote_raises_permission_error(
        self, mock_pinot, mock_kafka, pinot_store
    ):
        # Arrange — RF-O40.6/RF-O26.5 (2026-08-08): la carga en lote depende
        # del campo congelado en la suscripción activa, no de Dim_Plan en vivo.
        pinot_store["Fact_Suscripcion"][0]["carga_lote_habilitada"] = False
        service = ImportacionLoteUnidadService()
        filas = [self._fila_valida()]

        # Act & Assert
        with pytest.raises(PermissionError, match="no habilita"):
            service.importar(filas, **PROVEEDOR)

    def test_importar_when_una_fila_invalida_no_inserta_ninguna(self, mock_pinot, mock_kafka):
        # Arrange
        service = ImportacionLoteUnidadService()
        filas = [
            self._fila_valida(placa="LOTE-A", gmail="a@test.com"),
            self._fila_valida(placa="LOTE-A", gmail="b@test.com"),
        ]

        # Act
        result = service.importar(filas, **PROVEEDOR)

        # Assert
        assert result["insertadas"] == 0
        assert len(result["fallidas"]) == 1
        assert result["fallidas"][0]["fila"] == 2

    def test_importar_when_excede_500_filas_raises(self, mock_pinot, mock_kafka):
        # Arrange
        service = ImportacionLoteUnidadService()
        filas = [
            self._fila_valida(placa=f"LOTE-{i}", gmail=f"x{i}@t.com") for i in range(501)
        ]

        # Act & Assert
        with pytest.raises(ValueError):
            service.importar(filas, **PROVEEDOR)

    def test_importar_when_credencial_falla_revierte_lote(self, mock_pinot, mock_kafka, pinot_store):
        # Arrange
        service = ImportacionLoteUnidadService()
        service.credential_repo = MagicMock()
        service.credential_repo.create_temporary.side_effect = RuntimeError("smtp/cred fail")
        before = len(pinot_store["Dim_UnidadEmergencia"])
        filas = [
            self._fila_valida(placa="LOTE-C1", gmail="c1@test.com"),
            self._fila_valida(placa="LOTE-C2", gmail="c2@test.com"),
        ]

        # Act
        result = service.importar(filas, **PROVEEDOR)

        # Assert
        assert result["insertadas"] == 0
        assert result["usuarios_creados"] == 0
        assert result["fallidas"]
        activas_nuevas = [
            u
            for u in pinot_store["Dim_UnidadEmergencia"][before:]
            if u.get("placa", "").startswith("LOTE-C") and u.get("activo")
        ]
        assert activas_nuevas == []

    def test_importar_when_credencial_falla_y_pinot_aun_no_ingirio_igual_revierte(
        self, mock_pinot, mock_kafka, pinot_store
    ):
        # Arrange — en producción las escrituras van por Kafka y Pinot tarda en
        # ingerirlas, así que releer la unidad recién creada devuelve vacío. El
        # doble en memoria refleja la escritura al instante y esconde el caso;
        # aquí se fuerza el comportamiento real.
        service = ImportacionLoteUnidadService()
        service.credential_repo = MagicMock()
        service.credential_repo.create_temporary.side_effect = RuntimeError("smtp/cred fail")
        service.registro_service.unidad_repo.find_by_id = MagicMock(return_value=None)
        before = len(pinot_store["Dim_UnidadEmergencia"])
        filas = [
            self._fila_valida(placa="LOTE-L1", gmail="l1@test.com"),
            self._fila_valida(placa="LOTE-L2", gmail="l2@test.com"),
        ]

        # Act
        result = service.importar(filas, **PROVEEDOR)

        # Assert — el rollback no puede depender de leer lo recién escrito
        assert result["insertadas"] == 0
        activas_nuevas = [
            u
            for u in pinot_store["Dim_UnidadEmergencia"][before:]
            if str(u.get("placa", "")).startswith("LOTE-L") and u.get("activo")
        ]
        assert activas_nuevas == []

    def test_importar_when_credencial_falla_gmails_quedan_reutilizables(
        self, mock_pinot, mock_kafka, pinot_store
    ):
        # Arrange — compensación desactiva usuarios; reintento no debe chocar por gmail
        service = ImportacionLoteUnidadService()
        service.credential_repo = MagicMock()
        service.credential_repo.create_temporary.side_effect = RuntimeError("smtp/cred fail")
        filas = [
            self._fila_valida(placa="LOTE-R1", gmail="retry1@test.com"),
            self._fila_valida(placa="LOTE-R2", gmail="retry2@test.com"),
        ]

        # Act
        failed = service.importar(filas, **PROVEEDOR)
        service.credential_repo.create_temporary.side_effect = None
        service.credential_repo.create_temporary.return_value = {"idcredencial": 1}
        retried = service.importar(filas, **PROVEEDOR)

        # Assert
        assert failed["insertadas"] == 0
        assert retried["insertadas"] == 2
        assert retried["usuarios_creados"] == 2
        assert retried["fallidas"] == []

    def test_importar_when_rol_unidad_ausente_no_inserta(self, mock_pinot, mock_kafka):
        # Arrange
        service = ImportacionLoteUnidadService()
        service.role_repo = MagicMock()
        service.role_repo.find_role_by_name.return_value = None
        filas = [self._fila_valida(placa="LOTE-NR", gmail="nr@test.com")]

        # Act
        result = service.importar(filas, **PROVEEDOR)

        # Assert
        assert result["insertadas"] == 0
        assert result["usuarios_creados"] == 0
        assert "Unidad" in result["fallidas"][0]["motivo"]

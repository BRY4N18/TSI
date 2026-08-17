"""T061 — los siete publicados están en el YAML; los bloqueados no."""

from __future__ import annotations

from pathlib import Path

from apps.informes_estrategicos.services.oe3_service import BLOQUEADOS, PUBLICADOS
from apps.informes_estrategicos.tests.conftest import SENSIBLES

YAML = (
    Path(__file__).resolve().parents[5]
    / "specs/001-estrategico/OE3-escalabilidad-multiregion/backend/contracts/informes-estrategicos-oe3.openapi.yaml"
)


class TestOpenApiConformeOe3:
    def test_los_siete_publicados_estan_en_el_yaml(self):
        texto = YAML.read_text(encoding="utf-8")
        for informe in PUBLICADOS:
            assert f"/informes-estrategicos/oe3/{informe}:" in texto, (
                f"'{informe}' se publica y no está en el contrato"
            )

    def test_los_bloqueados_no_tienen_ruta(self):
        texto = YAML.read_text(encoding="utf-8")
        for informe in BLOQUEADOS:
            assert f"/informes-estrategicos/oe3/{informe}:" not in texto, (
                f"'{informe}' está bloqueado y el YAML lo publica"
            )

    def test_el_yaml_no_declara_campos_sensibles(self):
        import re

        texto = YAML.read_text(encoding="utf-8")
        for sensible in SENSIBLES:
            assert not re.search(rf"^\s+{sensible}:", texto, re.MULTILINE), (
                f"el contrato declara el campo '{sensible}'"
            )

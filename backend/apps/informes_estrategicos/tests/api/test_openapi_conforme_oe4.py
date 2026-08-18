"""Los nueve publicados están en el YAML; los bloqueados no; sin coordenadas."""

from __future__ import annotations

import re
from pathlib import Path

from apps.informes_estrategicos.services.oe4_service import BLOQUEADOS, PUBLICADOS

YAML = (
    Path(__file__).resolve().parents[5]
    / "specs/001-estrategico/OE4-inteligencia-predictiva/backend/contracts/"
    / "informes-estrategicos-oe4.openapi.yaml"
)

SENSIBLES = ("latitud", "longitud", "idusuario", "nombres", "apellidos")


class TestOpenApiConformeOe4:
    def test_los_nueve_publicados_estan_en_el_yaml(self):
        texto = YAML.read_text(encoding="utf-8")
        for informe in PUBLICADOS:
            assert f"/informes-estrategicos/oe4/{informe}:" in texto, informe

    def test_los_bloqueados_no_estan_en_el_yaml(self):
        texto = YAML.read_text(encoding="utf-8")
        for informe in BLOQUEADOS:
            assert f"/informes-estrategicos/oe4/{informe}:" not in texto, informe

    def test_el_yaml_no_declara_coordenadas(self):
        texto = YAML.read_text(encoding="utf-8")
        for sensible in SENSIBLES:
            assert not re.search(rf"^\s+{sensible}:", texto, re.MULTILINE), sensible

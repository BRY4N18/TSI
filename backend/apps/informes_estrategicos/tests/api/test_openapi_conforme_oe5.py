"""Los nueve publicados están en el YAML; bloqueados y refs OE1 no; sin prosa ni cobro."""

from __future__ import annotations

import re
from pathlib import Path

from apps.informes_estrategicos.services.oe5_service import (
    BLOQUEADOS,
    PUBLICADOS,
    REFERENCIAS_OE1,
)
from apps.informes_estrategicos.tests.conftest import SENSIBLES

YAML = (
    Path(__file__).resolve().parents[5]
    / "specs/001-estrategico/OE5-retencion-ciclo-vida/backend/contracts/"
    / "informes-estrategicos-oe5.openapi.yaml"
)

SECRETOS = SENSIBLES + (
    "asunto",
    "descripcion",
    "mensaje",
    "metodo_pago",
    "calificacion",
)


class TestOpenApiConformeOe5:
    def test_los_nueve_publicados_estan_en_el_yaml(self):
        texto = YAML.read_text(encoding="utf-8")
        for informe in PUBLICADOS:
            assert f"/informes-estrategicos/oe5/{informe}:" in texto, informe

    def test_bloqueados_y_referencias_no_estan_en_el_yaml(self):
        texto = YAML.read_text(encoding="utf-8")
        for informe in BLOQUEADOS | REFERENCIAS_OE1:
            assert f"/informes-estrategicos/oe5/{informe}:" not in texto, informe

    def test_el_yaml_no_declara_prosa_cobro_ni_nps(self):
        texto = YAML.read_text(encoding="utf-8")
        for sensible in SECRETOS:
            assert not re.search(rf"^\s+{sensible}:", texto, re.MULTILINE), sensible

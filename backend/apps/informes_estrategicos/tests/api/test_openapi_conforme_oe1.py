"""Los diez publicados están en el YAML; los tres bloqueados no; sin cobro ni país."""

from __future__ import annotations

import re
from pathlib import Path

from apps.informes_estrategicos.services.oe1_service import BLOQUEADOS, PUBLICADOS
from apps.informes_estrategicos.tests.conftest import SENSIBLES

YAML = (
    Path(__file__).resolve().parents[5]
    / "specs/001-estrategico/OE1-posicionamiento-captacion/backend/contracts/"
    / "informes-estrategicos-oe1.openapi.yaml"
)

SECRETOS = SENSIBLES + (
    "metodo_pago",
    "idpais",
    "idestado",
    "contacto",
    "hash",
)


class TestOpenApiConformeOe1:
    def test_los_diez_publicados_estan_en_el_yaml(self):
        texto = YAML.read_text(encoding="utf-8")
        for informe in PUBLICADOS:
            assert f"/informes-estrategicos/oe1/{informe}:" in texto, informe

    def test_los_bloqueados_no_estan_en_el_yaml(self):
        texto = YAML.read_text(encoding="utf-8")
        for informe in BLOQUEADOS:
            assert f"/informes-estrategicos/oe1/{informe}:" not in texto, informe

    def test_el_yaml_no_declara_cobro_pais_ni_contacto(self):
        texto = YAML.read_text(encoding="utf-8")
        for sensible in SECRETOS:
            assert not re.search(rf"^\s+{sensible}:", texto, re.MULTILINE), sensible

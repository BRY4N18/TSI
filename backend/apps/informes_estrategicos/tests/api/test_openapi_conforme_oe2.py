"""Los diez publicados están en el YAML; disponibilidad-api no; sin secretos."""

from __future__ import annotations

import re
from pathlib import Path

from apps.informes_estrategicos.services.oe2_service import BLOQUEADOS, PUBLICADOS
from apps.informes_estrategicos.tests.conftest import SENSIBLES

YAML = (
    Path(__file__).resolve().parents[5]
    / "specs/001-estrategico/OE2-monetizacion-api/backend/contracts/"
    / "informes-estrategicos-oe2.openapi.yaml"
)

SECRETOS = SENSIBLES + ("client_secret", "ip", "hash", "contacto")


class TestOpenApiConformeOe2:
    def test_los_diez_publicados_estan_en_el_yaml(self):
        texto = YAML.read_text(encoding="utf-8")
        for informe in PUBLICADOS:
            assert f"/informes-estrategicos/oe2/{informe}:" in texto, informe

    def test_los_bloqueados_no_estan_en_el_yaml(self):
        texto = YAML.read_text(encoding="utf-8")
        for informe in BLOQUEADOS:
            assert f"/informes-estrategicos/oe2/{informe}:" not in texto, informe

    def test_el_yaml_no_declara_secretos_ni_identidad(self):
        texto = YAML.read_text(encoding="utf-8")
        for sensible in SECRETOS:
            assert not re.search(rf"^\s+{sensible}:", texto, re.MULTILINE), sensible

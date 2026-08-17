"""T081 — los doce endpoints publicados están en el YAML, sin campos sensibles."""

from __future__ import annotations

from pathlib import Path

from apps.informes_estrategicos.services.oe6_service import PUBLICADOS

YAML = (
    Path(__file__).resolve().parents[5]
    / "specs/001-estrategico/OE6-respuesta-y-vidas/backend/contracts/informes-estrategicos-oe6.openapi.yaml"
)

SENSIBLES = (
    "latitud", "longitud", "idusuario", "nombres", "apellidos",
    "identificacion", "gmail", "observaciones", "client_secret",
)


class TestOpenApiConforme:
    def test_los_doce_publicados_estan_en_el_yaml(self):
        texto = YAML.read_text(encoding="utf-8")
        for informe in PUBLICADOS:
            assert f"/informes-estrategicos/oe6/{informe}:" in texto, (
                f"'{informe}' se publica y no está en el contrato"
            )

    def test_el_yaml_no_declara_campos_sensibles(self):
        import re

        texto = YAML.read_text(encoding="utf-8")
        for sensible in SENSIBLES:
            assert not re.search(rf"^\s+{sensible}:", texto, re.MULTILINE), (
                f"el contrato declara el campo '{sensible}': la implementación "
                f"tendría permiso escrito para publicarlo"
            )

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.indice_calidad_logic import combinar_indice  # noqa: E402


class TestCombinarIndice:
    def test_valores_perfectos_dan_indice_1(self):
        # completitud=1, descarte=0, fusion=0, cobertura=1 -> promedio de [1,1,1,1] = 1
        assert combinar_indice(1.0, 0.0, 0.0, 1.0) == 1.0

    def test_valores_pesimos_dan_indice_0(self):
        # completitud=0, descarte=1, fusion=1, cobertura=0 -> promedio de [0,0,0,0] = 0
        assert combinar_indice(0.0, 1.0, 1.0, 0.0) == 0.0

    def test_descarte_y_fusion_se_invierten_antes_de_promediar(self):
        # completitud=1, descarte=0.5(->0.5), fusion=0(->1), cobertura=1 -> [1,0.5,1,1]/4 = 0.875
        assert combinar_indice(1.0, 0.5, 0.0, 1.0) == 0.875

    def test_valores_intermedios_conocidos(self):
        assert combinar_indice(0.8, 0.1, 0.05, 0.9) == 0.8875

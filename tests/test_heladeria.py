import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from heladeria import Heladeria


class TestHeladeria(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.heladeria = Heladeria(RAIZ / "data")
   
    def test_los_cortes_de_luz_no_cuentan_en_la_tasa_de_merma(self):
        tasa = self.heladeria.tasa_merma()
        self.assertTrue(((tasa >= 0) & (tasa < 1)).all())
        self.assertEqual(tasa.idxmax(), "menta granizada")

    def test_modificar_la_copia_no_cambia_la_heladeria(self):
        copia = self.heladeria.ventas
        copia["kg"] = 0
        self.assertGreater(self.heladeria.ventas["kg"].sum(), 0)

    def test_un_sabor_sin_merma_tiene_tasa_cero(self):
        with tempfile.TemporaryDirectory() as carpeta:
            for archivo in ["ventas.csv", "recetas.json", "insumos.json"]:
                (Path(carpeta) / archivo).write_bytes((RAIZ / "data" / archivo).read_bytes())
            merma = pd.read_csv(RAIZ / "data" / "merma.csv")
            merma[merma["sabor"] != "limón"].to_csv(Path(carpeta) / "merma.csv", index=False)
            tasa = Heladeria(carpeta).tasa_merma()
        self.assertEqual(tasa["limón"], 0)
        self.assertFalse(tasa.isna().any())
        
if __name__ == "__main__":
    unittest.main()
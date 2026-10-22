import sys
import unittest
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "data"))

from generar_datos import generar_tablas


class TestGenerador(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.datos = generar_tablas(42)

    def test_misma_semilla_mismos_datos(self):
        otra_vez = generar_tablas(42)
        self.assertTrue(self.datos["ventas"].equals(otra_vez["ventas"]))
        self.assertTrue(self.datos["merma"].equals(otra_vez["merma"]))

    def test_otra_semilla_cambia_el_ruido_pero_no_las_reglas(self):
        otra = generar_tablas(7)
        self.assertFalse(self.datos["ventas"]["kg"].equals(otra["ventas"]["kg"]))
        self.assertEqual(list(self.datos["ventas"]["sabor"]), list(otra["ventas"]["sabor"]))
        self.assertEqual(self.datos["recetas"], otra["recetas"])

    def test_los_archivos_del_repositorio_salen_de_la_semilla_42(self):
        guardado = (RAIZ / "data" / "ventas.csv").read_text(encoding="utf-8")
        self.assertEqual(self.datos["ventas"].to_csv(index=False, lineterminator="\n"), guardado)

   
if __name__ == "__main__":
    unittest.main()
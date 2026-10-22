import json
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from fuentes import FuenteCSV, FuenteJSON, fuente_para

DATOS = RAIZ / "data"


class TestFuentes(unittest.TestCase):

    def test_csv_y_json_equivalentes_dan_la_misma_tabla(self):
        desde_csv = FuenteCSV(DATOS / "muestra_ventas.csv").cargar()
        desde_json = FuenteJSON(DATOS / "muestra_ventas.json").cargar()
        self.assertEqual(len(desde_csv), 60)
        self.assertTrue(desde_csv.equals(desde_json))

    def test_formato_no_soportado(self):
        with self.assertRaises(ValueError):
            fuente_para(DATOS / "ventas.xlsx")

    def test_json_que_no_es_una_lista_de_objetos(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "roto.json"
            ruta.write_text(json.dumps({"sabor": "limón"}), encoding="utf-8")
            with self.assertRaises(ValueError):
                FuenteJSON(ruta).cargar()

if __name__ == "__main__":
    unittest.main()
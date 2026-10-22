import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from heladeria import Heladeria
from main import App, elegir_app


class TestMenu(unittest.TestCase):

    def test_una_sesion_con_entradas_invalidas_no_rompe_la_app(self):
        respuestas = iter(["9", "1", "2", "3", "4", "13", "4", "abc", "4", "12", "5", "1",
                           "6", "1", "1", "6", "2", "0", "6", "3", "1", "6", "4", "6", "5", "1,5,6",
                           "6", "5", "1,2,3,4,5,6", "6", "9", "7", "0"])
        with tempfile.TemporaryDirectory() as carpeta:
            app = App(Heladeria(RAIZ / "data"), entrada=lambda mensaje: "" if "Enter" in mensaje else next(respuestas),
                      carpeta_salidas=carpeta, mostrar_graficos=False)
            salida = io.StringIO()
            with redirect_stdout(salida):
                app.ejecutar()
            archivos = sorted(ruta.name for ruta in Path(carpeta).iterdir())
        texto = salida.getvalue()
        self.assertIn("Opción inválida", texto)
        self.assertIn("El mes tiene que ser", texto)
        self.assertIn("Elegí hasta 5", texto)
        self.assertIn("Escribí un número del 1 al 5", texto)
        self.assertIn("¡Hasta luego!", texto)
        self.assertEqual(len(archivos), 8)

    def test_elegir_datos_rechaza_lo_invalido_y_carga_el_ejemplo(self):
        respuestas = iter(["7", "2", "carpeta_que_no_existe", "1"])
        with tempfile.TemporaryDirectory() as carpeta:
            salida = io.StringIO()
            with redirect_stdout(salida):
                app = elegir_app(entrada=lambda mensaje: next(respuestas), carpeta_salidas=carpeta)
        texto = salida.getvalue()
        self.assertIn("Opción inválida", texto)
        self.assertIn("No se pudieron usar esos datos", texto)
        self.assertEqual(app.heladeria.nombre, "Heladería de ejemplo")

    def test_elegir_datos_propios_con_un_año_incompleto(self):
        with tempfile.TemporaryDirectory() as carpeta:
            for archivo in ["merma.csv", "recetas.json", "insumos.json"]:
                (Path(carpeta) / archivo).write_bytes((RAIZ / "data" / archivo).read_bytes())
            ventas = pd.read_csv(RAIZ / "data" / "ventas.csv")
            ventas[~ventas["fecha"].str.startswith("2025-03")].to_csv(Path(carpeta) / "ventas.csv", index=False)
            respuestas = iter(["2", carpeta, "0"])
            salida = io.StringIO()
            with redirect_stdout(salida):
                app = elegir_app(entrada=lambda mensaje: next(respuestas), carpeta_salidas=carpeta)
        self.assertIsNone(app)
        self.assertIn("Faltan ventas de 2025 en: marzo", salida.getvalue())

if __name__ == "__main__":
    unittest.main()
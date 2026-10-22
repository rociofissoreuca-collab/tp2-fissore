import sys
import unittest
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from heladeria import Heladeria
from pronostico import Pronostico, calcular_crecimiento, error_porcentual


class TestPronostico(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.heladeria = Heladeria(RAIZ / "data")
        cls.pronostico = Pronostico(cls.heladeria, 2025)

    def test_caso_normal_produccion_de_diciembre(self):
        tabla = self.pronostico.produccion(12)
        self.assertGreater(tabla.loc["dulce de leche", "produccion"], 0)
        self.assertTrue((tabla["produccion"] >= tabla["demanda"]).all(), "La producción incluye la merma")

    def test_crecimiento_y_error_con_valores_conocidos(self):
        actual = pd.DataFrame({"limón": [110.0]})
        anterior = pd.DataFrame({"limón": [100.0]})
        self.assertAlmostEqual(calcular_crecimiento(actual, anterior)["limón"], 0.10)
        self.assertAlmostEqual(error_porcentual(pd.Series([90.0, 110.0]), pd.Series([100.0, 100.0])), 0.10)
        tabla, resumen = self.pronostico.validar()
        self.assertAlmostEqual((tabla["error"] * tabla["real"]).sum() / tabla["real"].sum(), resumen["error_metodo"])
        
    def test_mes_invalido(self):
        for mes in [0, 13, "julio", 7.5]:
            with self.assertRaises(ValueError):
                self.pronostico.demanda(mes)

    def test_sabor_sin_historial_queda_fuera_del_pronostico(self):
        self.assertEqual(self.pronostico.sabores_sin_historial(), ["maracuyá"])
        self.assertNotIn("maracuyá", self.pronostico.demanda(1).index)

    def test_avisa_el_cambio_de_tendencia_de_la_menta(self):
        cambios = self.pronostico.cambios_de_tendencia()
        self.assertEqual(list(cambios.index), ["menta granizada"])
        self.assertLess(cambios["menta granizada"], 0)

    def test_el_consumo_de_insumos_sale_de_las_recetas(self):
        produccion = self.pronostico.produccion(12)["produccion"]
        recetas = self.heladeria.recetas
        leche = recetas[recetas["insumo"] == "leche"].set_index("sabor")["cantidad_por_kg"]
        esperado = (produccion.reindex(leche.index).fillna(0) * leche).sum()
        self.assertAlmostEqual(self.pronostico.consumo_insumos(12)["leche"], esperado, places=1)

    def test_el_plan_de_compras_conserva_las_cantidades(self):
        plan = self.pronostico.plan_compras()
        self.assertTrue((plan["stock_final"] >= 0).all())
        for insumo, filas in plan.groupby("insumo"):
            stock_inicial = self.heladeria.insumos.loc[insumo, "stock_actual"]
            esperado = stock_inicial + filas["compra"].sum() - filas["consumo"].sum()
            self.assertAlmostEqual(filas["stock_final"].iloc[-1], esperado, delta=0.1)


if __name__ == "__main__":
    unittest.main()
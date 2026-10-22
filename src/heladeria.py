"""Clase Heladeria: los datos limpios de una heladería y las preguntas que responde sobre sus ventas."""
import pandas as pd

from pipeline import preparar_datos

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
MOTIVOS_ACCIDENTALES = ["corte de luz"]


class Heladeria:
    """Carga y limpia los datos de una carpeta al crearse. Los datos internos no se modifican desde afuera."""

    def __init__(self, carpeta, nombre="Heladería"):
        tablas, rechazos = preparar_datos(carpeta)
        self.nombre = nombre
        self._rechazos = rechazos
        ventas = tablas["ventas"]
        self._ventas = ventas.assign(año=ventas["fecha"].dt.year, mes=ventas["fecha"].dt.month)
        self._merma = tablas["merma"]
        self._recetas = tablas["recetas"]
        self._insumos = tablas["insumos"].set_index("insumo")

    @property
    def ventas(self):
        return self._ventas.copy()

    @property
    def rechazos(self):
        return self._rechazos.copy()

    @property
    def recetas(self):
        return self._recetas.copy()

    @property
    def insumos(self):
        return self._insumos.copy()

    def años(self):
        return sorted(int(año) for año in self._ventas["año"].unique())

    def sabores(self):
        return sorted(self._ventas["sabor"].unique())

    def kg_por_mes(self, año):
        """Tabla con una fila por mes (1 a 12) y una columna por sabor: kg vendidos."""
        if año not in self.años():
            raise ValueError(f"No hay ventas de {año}. Años disponibles: {self.años()}")
        del_año = self._ventas[self._ventas["año"] == año]
        tabla = del_año.groupby(["mes", "sabor"])["kg"].sum().unstack()
        return tabla.reindex(range(1, 13))

    def ventas_mensuales(self, sabor=None):
        """Kg vendidos por mes (filas) en cada año (columnas), de un sabor o del total si sabor es None."""
        if sabor is not None and sabor not in self.sabores():
            raise ValueError(f"No hay ventas del sabor {sabor}")
        columnas = {}
        for año in self.años():
            kg = self.kg_por_mes(año)
            columnas[año] = kg.sum(axis=1) if sabor is None else kg.reindex(columns=[sabor])[sabor]
        tabla = pd.DataFrame(columnas)
        tabla.index = MESES
        return tabla

    def ventas_por_sabor(self, sabores, año):
        """Kg vendidos por mes (filas) de varios sabores (columnas) en un año."""
        tabla = self.kg_por_mes(año).reindex(columns=sabores)
        tabla.index = MESES
        return tabla

    def estacionalidad(self):
        """Kg vendidos por mes en cada año y cuánto se aleja cada mes del promedio (1 = mes promedio)."""
        tabla = self.ventas_mensuales()
        promedio = tabla.mean(axis=1)
        tabla["indice"] = promedio / promedio.mean()
        return tabla

    def ranking_sabores(self, año):
        """Kg vendidos en el año por sabor, del que más vende al que menos."""
        kg = self.kg_por_mes(año).sum().sort_values(ascending=False)
        return pd.DataFrame({"kg": kg, "participacion": kg / kg.sum()})

    def tasa_merma(self):
        """Kg tirados sobre kg vendidos de cada sabor, sin contar accidentes (un corte de luz no es culpa del sabor)."""
        evitable = self._merma[~self._merma["motivo"].isin(MOTIVOS_ACCIDENTALES)]
        tirado = evitable.groupby("sabor")["kg"].sum()
        vendido = self._ventas.groupby("sabor")["kg"].sum()
        return tirado.reindex(vendido.index, fill_value=0) / vendido
    
    def __str__(self):
        return (f"{self.nombre}: {len(self._ventas)} registros de ventas válidos "
                f"({self.años()[0]}–{self.años()[-1]}), {len(self._rechazos)} filas rechazadas")
"""Lectura de datos: una interfaz común (FuenteDatos) y una implementación por formato."""
import json
from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd


class FuenteDatos(ABC):
    """Contrato común: toda fuente sabe cargar su archivo y devolver un DataFrame."""

    extension = ""

    def __init__(self, ruta):
        self.ruta = Path(ruta)
        if self.ruta.suffix != self.extension:
            raise ValueError(f"{self.ruta.name}: se esperaba un archivo {self.extension}")
        if not self.ruta.is_file():
            raise FileNotFoundError(f"No se encontró el archivo {self.ruta}")

    @abstractmethod
    def cargar(self):
        """Lee el archivo y devuelve una tabla con una fila por registro."""


class FuenteCSV(FuenteDatos):
    extension = ".csv"

    def cargar(self):
        try:
            return pd.read_csv(self.ruta, encoding="utf-8")
        except UnicodeDecodeError:
            raise ValueError(f"{self.ruta.name} no está guardado en UTF-8. En Excel: Guardar como → "
                             "CSV UTF-8 (delimitado por comas)")

class FuenteJSON(FuenteDatos):
    """El archivo debe ser una lista de objetos con los mismos campos (uno por registro)."""

    extension = ".json"

    def cargar(self):
        with open(self.ruta, encoding="utf-8") as archivo:
            registros = json.load(archivo)
        if not isinstance(registros, list) or not all(isinstance(r, dict) for r in registros):
            raise ValueError(f"{self.ruta.name}: el JSON tiene que ser una lista de objetos")
        return pd.DataFrame(registros)


FUENTES = {".csv": FuenteCSV, ".json": FuenteJSON}


def fuente_para(ruta):
    """Elige la fuente según la extensión del archivo."""
    extension = Path(ruta).suffix
    if extension not in FUENTES:
        raise ValueError(f"Formato no soportado: '{extension}'. Se aceptan: {', '.join(FUENTES)}")
    return FUENTES[extension](ruta)
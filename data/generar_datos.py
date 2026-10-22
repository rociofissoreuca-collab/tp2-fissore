"""Genera los datos simulados de la heladería (2024 y 2025).

Ejecutar desde la carpeta del proyecto:  python data/generar_datos.py
Las reglas de la simulación y las situaciones especiales están fijas en este archivo.
La semilla solo controla la variación aleatoria: con la misma semilla se obtienen los mismos datos.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

SEMILLA = 42
DESVIO_VENTAS = 0.15  # las ventas de un día varían ±15 % alrededor de lo esperado
DESVIO_MERMA = 0.2
CARPETA = Path(__file__).resolve().parent
INICIO, FIN = "2024-01-01", "2025-12-31"
DIAS_CERRADO = ["2024-01-01", "2024-12-25", "2025-01-01", "2025-12-25"]
AUMENTO_FIN_DE_SEMANA = 1.3
EXPONENTE_AGUA = 1.3  # los sabores al agua dependen más de la temporada
CORTES_DE_LUZ = ["2024-02-10", "2025-01-18"]
SABORES_EN_CORTE = 11
KG_POR_CORTE = (2, 4)

# Cuánto se vende en un mes respecto de un mes promedio (enero a diciembre)
ESTACIONALIDAD = [1.85, 1.6, 1.2, 0.8, 0.55, 0.4, 0.38, 0.45, 0.7, 1.0, 1.35, 1.9]

# sabor: (kg por día en 2024, crecimiento anual, tipo, proporción que se tira)
SABORES = {
    "dulce de leche": (7.0, 0.05, "crema", 0.02),
    "dulce de leche granizado": (6.0, 0.12, "crema", 0.03),
    "chocolate": (5.0, 0.02, "crema", 0.02),
    "chocolate amargo": (3.0, 0.15, "crema", 0.03),
    "crema americana": (3.0, -0.05, "crema", 0.03),
    "vainilla": (2.0, -0.08, "crema", 0.04),
    "sambayón": (2.0, -0.10, "crema", 0.08),
    "frutilla a la crema": (4.0, 0.04, "crema", 0.04),
    "banana split": (3.0, 0.20, "crema", 0.04),
    "tramontana": (4.0, 0.10, "crema", 0.03),
    "menta granizada": (2.5, -0.15, "crema", 0.12),
    "limón": (3.5, 0.06, "agua", 0.05),
    "frutilla al agua": (2.5, 0.08, "agua", 0.06),
    "maracuyá": (2.5, 0.0, "agua", 0.05),
}
MARACUYA_DESDE = "2025-03-01"
MENTA_CAE_DESDE, CAIDA_MENTA = "2025-07-01", 0.85

# Insumos por kg de helado
RECETAS = {
    "dulce de leche": {"leche": 0.5, "crema": 0.2, "azúcar": 0.08, "dulce de leche": 0.3},
    "dulce de leche granizado": {"leche": 0.45, "crema": 0.2, "azúcar": 0.08, "dulce de leche": 0.28, "chocolate": 0.08},
    "chocolate": {"leche": 0.55, "crema": 0.2, "azúcar": 0.17, "cacao": 0.08},
    "chocolate amargo": {"leche": 0.5, "crema": 0.2, "azúcar": 0.15, "cacao": 0.12},
    "crema americana": {"leche": 0.6, "crema": 0.25, "azúcar": 0.18},
    "vainilla": {"leche": 0.6, "crema": 0.22, "azúcar": 0.18, "esencia de vainilla": 0.004},
    "sambayón": {"leche": 0.5, "crema": 0.2, "azúcar": 0.2, "huevos": 4},
    "frutilla a la crema": {"leche": 0.4, "crema": 0.2, "azúcar": 0.17, "frutilla": 0.3},
    "banana split": {"leche": 0.45, "crema": 0.2, "azúcar": 0.15, "banana": 0.25, "dulce de leche": 0.08, "chocolate": 0.04},
    "tramontana": {"leche": 0.45, "crema": 0.2, "azúcar": 0.1, "dulce de leche": 0.2, "galletitas": 0.08},
    "menta granizada": {"leche": 0.55, "crema": 0.2, "azúcar": 0.17, "esencia de menta": 0.004, "chocolate": 0.08},
    "limón": {"azúcar": 0.25, "limón": 0.35},
    "frutilla al agua": {"azúcar": 0.22, "frutilla": 0.45},
    "maracuyá": {"azúcar": 0.24, "maracuyá": 0.4},
}

# insumo: (unidad, stock al 31/12/2025, días de entrega, vida útil en días)
INSUMOS = {
    "leche": ("litros", 60, 1, 10),
    "crema": ("litros", 25, 1, 12),
    "azúcar": ("kg", 150, 3, 365),
    "dulce de leche": ("kg", 40, 3, 60),
    "cacao": ("kg", 12, 5, 365),
    "chocolate": ("kg", 15, 5, 180),
    "frutilla": ("kg", 6, 1, 4),
    "banana": ("kg", 4, 1, 5),
    "limón": ("kg", 10, 2, 20),
    "maracuyá": ("kg", 3, 2, 6),
    "galletitas": ("kg", 8, 3, 120),
    "huevos": ("unidades", 120, 2, 21),
    "esencia de vainilla": ("litros", 0.5, 7, 365),
    "esencia de menta": ("litros", 0.3, 7, 365),
}


def simular_ventas(generador):
    """Kg vendidos de cada sabor por día, con estacionalidad, tendencia, fin de semana y ruido."""
    dias = pd.date_range(INICIO, FIN)
    dias = dias[~dias.isin(pd.to_datetime(DIAS_CERRADO))]
    filas = []
    for sabor, (kg_base, crecimiento, tipo, _) in SABORES.items():
        for dia in dias:
            if sabor == "maracuyá" and dia < pd.Timestamp(MARACUYA_DESDE):
                continue
            estacion = ESTACIONALIDAD[dia.month - 1]
            if tipo == "agua":
                estacion = estacion ** EXPONENTE_AGUA
            años = (dia - pd.Timestamp(INICIO)).days / 365
            tendencia = (1 + crecimiento) ** años
            if sabor == "menta granizada" and dia >= pd.Timestamp(MENTA_CAE_DESDE):
                tendencia *= CAIDA_MENTA
            finde = AUMENTO_FIN_DE_SEMANA if dia.dayofweek >= 5 else 1.0
            ruido = generador.normal(1, DESVIO_VENTAS)
            kg = kg_base * estacion * tendencia * finde * ruido
            filas.append({"fecha": dia.strftime("%Y-%m-%d"), "sabor": sabor, "kg": round(kg, 2)})
    return pd.DataFrame(filas).sort_values(["fecha", "sabor"]).reset_index(drop=True)


def simular_merma(ventas, generador):
    """Helado tirado: una fila por sabor y semana (cristalizado) y dos cortes de luz."""
    ventas = ventas.assign(semana=pd.to_datetime(ventas["fecha"]).dt.to_period("W").dt.end_time.dt.strftime("%Y-%m-%d"))
    por_semana = ventas.groupby(["semana", "sabor"])["kg"].sum().reset_index()
    filas = []
    for _, fila in por_semana.iterrows():
        proporcion = SABORES[fila["sabor"]][3]
        kg = fila["kg"] * proporcion * generador.normal(1, DESVIO_MERMA)
        filas.append({"fecha": min(fila["semana"], FIN), "sabor": fila["sabor"],
                      "kg": round(kg, 2), "motivo": "cristalizado"})
    for fecha in CORTES_DE_LUZ:
        for sabor in list(SABORES)[:SABORES_EN_CORTE]:
            filas.append({"fecha": fecha, "sabor": sabor, "kg": round(generador.uniform(*KG_POR_CORTE), 2), "motivo": "corte de luz"})
    return pd.DataFrame(filas).sort_values(["fecha", "sabor"]).reset_index(drop=True)


def agregar_errores(ventas, merma):
    """Errores de carga a propósito, para mostrar la validación y la limpieza."""
    ventas = ventas.astype({"kg": object})
    fila = ventas.index[ventas["sabor"] == "dulce de leche"][10]
    ventas.loc[fila, "sabor"] = "  Dulce de LECHE "         # se corrige al normalizar
    errores = [
        {"fecha": "2025-02-30", "sabor": "limón", "kg": 4.1},           # fecha que no existe
        {"fecha": "15/03/2024", "sabor": "chocolate", "kg": 3.2},       # formato de fecha inválido
        {"fecha": "2024-08-10", "sabor": "vainilla", "kg": -2.5},       # kg negativo
        {"fecha": "2024-09-14", "sabor": "tramontana", "kg": None},     # kg faltante
        {"fecha": "2025-06-21", "sabor": "chocolate suizo", "kg": 1.8}, # sabor sin receta
        {"fecha": "2025-11-08", "sabor": "banana split", "kg": 950},    # fuera de rango
    ]
    duplicado = ventas.iloc[[5000]].to_dict("records")                  # fila repetida
    ventas = pd.concat([ventas, pd.DataFrame(errores + duplicado)], ignore_index=True)
    merma = pd.concat([merma, pd.DataFrame([{"fecha": "2024-13-05", "sabor": "limón", "kg": 0.4, "motivo": "cristalizado"}])],
                      ignore_index=True)
    return ventas, merma


def guardar_json(registros, ruta):
    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(registros, archivo, ensure_ascii=False, indent=2)


def generar_tablas(semilla=SEMILLA):
    """Genera las cinco tablas de la heladería con la semilla indicada. No escribe archivos."""
    generador = np.random.default_rng(semilla)
    ventas = simular_ventas(generador)
    merma = simular_merma(ventas, generador)
    muestra = ventas.head(60)
    ventas, merma = agregar_errores(ventas, merma)
    recetas = [{"sabor": sabor, "insumo": insumo, "cantidad_por_kg": cantidad}
               for sabor, receta in RECETAS.items() for insumo, cantidad in receta.items()]
    insumos = [{"insumo": insumo, "unidad": unidad, "stock_actual": stock, "dias_entrega": entrega, "vida_util_dias": vida}
               for insumo, (unidad, stock, entrega, vida) in INSUMOS.items()]
    return {"ventas": ventas, "merma": merma, "muestra": muestra, "recetas": recetas, "insumos": insumos}


def guardar_tablas(tablas, carpeta=CARPETA):
    carpeta = Path(carpeta)
    tablas["ventas"].to_csv(carpeta / "ventas.csv", index=False)
    tablas["merma"].to_csv(carpeta / "merma.csv", index=False)
    tablas["muestra"].to_csv(carpeta / "muestra_ventas.csv", index=False)
    guardar_json(tablas["muestra"].to_dict("records"), carpeta / "muestra_ventas.json")
    guardar_json(tablas["recetas"], carpeta / "recetas.json")
    guardar_json(tablas["insumos"], carpeta / "insumos.json")


def main():
    tablas = generar_tablas(SEMILLA)
    guardar_tablas(tablas)
    print(f"Datos generados en {CARPETA} con semilla {SEMILLA}: "
          f"{len(tablas['ventas'])} ventas, {len(tablas['merma'])} registros de merma")
    
if __name__ == "__main__":
    main()
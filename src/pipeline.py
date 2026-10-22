"""Flujo de procesamiento: leer → validar el esquema → limpiar → registrar rechazos → guardar."""
import re
from datetime import datetime
from pathlib import Path

import pandas as pd

from fuentes import fuente_para

ARCHIVOS = {
    "ventas": "ventas.csv",
    "merma": "merma.csv",
    "recetas": "recetas.json",
    "insumos": "insumos.json",
}

COLUMNAS = {
    "ventas": ["fecha", "sabor", "kg"],
    "merma": ["fecha", "sabor", "kg", "motivo"],
    "recetas": ["sabor", "insumo", "cantidad_por_kg"],
    "insumos": ["insumo", "unidad", "stock_actual", "dias_entrega", "vida_util_dias"],
}

COLUMNAS_TEXTO = {
    "ventas": ["sabor"],
    "merma": ["sabor", "motivo"],
    "recetas": ["sabor", "insumo"],
    "insumos": ["insumo", "unidad"],
}
MARGEN_SEGURIDAD_DIAS = 2  # días de stock de seguridad, además de los que tarda el proveedor
TABLAS_OPCIONALES = ["merma"]  # pueden faltar o venir sin filas: una heladería puede no registrar merma
PATRON_FECHA = r"\d{4}-\d{2}-\d{2}"
VECES_LA_MEDIANA = 10


def tiene_formato_fecha(texto):
    """True si el texto tiene la forma AAAA-MM-DD (cuatro, dos y dos dígitos separados por guiones)."""
    return re.fullmatch(PATRON_FECHA, str(texto)) is not None


def es_fecha_existente(texto):
    """True si además la fecha existe en el calendario (la regex sola acepta 2025-02-30)."""
    try:
        datetime.strptime(str(texto), "%Y-%m-%d")
        return True
    except ValueError:
        return False


def leer_tablas(carpeta):
    """Lee los archivos de la carpeta con la fuente que corresponde a cada formato. Una tabla opcional que falta queda vacía."""
    carpeta = Path(carpeta)
    if not carpeta.is_dir():
        raise FileNotFoundError(f"No existe la carpeta de datos {carpeta}")
    tablas = {}
    for nombre, archivo in ARCHIVOS.items():
        if nombre in TABLAS_OPCIONALES and not (carpeta / archivo).exists():
            tablas[nombre] = pd.DataFrame(columns=COLUMNAS[nombre])
        else:
            tablas[nombre] = fuente_para(carpeta / archivo).cargar()
    return tablas

def validar_esquema(tabla, nombre):
    """Frena con un mensaje claro si a la tabla le faltan columnas o no tiene filas."""
    faltan = [columna for columna in COLUMNAS[nombre] if columna not in tabla.columns]
    if faltan:
        pista = ""
        if len(tabla.columns) == 1 and ";" in tabla.columns[0]:
            pista = ". Parece separado con punto y coma: guardalo separado con comas y con punto decimal"
        raise ValueError(f"A la tabla '{nombre}' le faltan las columnas: {', '.join(faltan)}{pista}")

def normalizar_encabezados(tabla):
    """Encabezados en minúscula y sin espacios en los extremos, sobre una copia: "Fecha " y "fecha" son lo mismo."""
    tabla = tabla.copy()
    tabla.columns = [str(columna).strip().lower() for columna in tabla.columns]
    return tabla

def normalizar_campos(tabla, columnas):
    """Pasa los textos a minúscula y sin espacios en los extremos, sobre una copia."""
    tabla = tabla.copy()
    for columna in columnas:
        tabla[columna] = tabla[columna].astype("string").str.strip().str.lower()
    return tabla


def separar(tabla, filas_validas, motivo, rechazos):
    """Se queda con las filas válidas y guarda las demás en rechazos, con su motivo."""
    filas_validas = filas_validas.astype(bool)
    rechazadas = tabla[~filas_validas].assign(motivo_rechazo=motivo)
    if len(rechazadas) > 0:
        rechazos.append(rechazadas)
    return tabla[filas_validas]


def limpiar_registros(tabla, sabores_validos, clave_duplicados):
    """Aplica las reglas de limpieza en orden. Devuelve (filas válidas, filas rechazadas con motivo)."""
    rechazos = []
    tabla = separar(tabla, tabla[["fecha", "sabor", "kg"]].notna().all(axis=1), "dato faltante", rechazos)
    tabla = separar(tabla, tabla["fecha"].map(tiene_formato_fecha), "fecha con formato inválido", rechazos)
    tabla = separar(tabla, tabla["fecha"].map(es_fecha_existente), "fecha inexistente", rechazos)
    kg = pd.to_numeric(tabla["kg"], errors="coerce")
    tabla = separar(tabla, kg > 0, "kg no numérico o no positivo", rechazos)
    kg = pd.to_numeric(tabla["kg"], errors="coerce")
    tope = tabla["sabor"].map(kg.groupby(tabla["sabor"]).median()) * VECES_LA_MEDIANA
    tabla = separar(tabla, kg <= tope, f"kg fuera de rango (más de {VECES_LA_MEDIANA} veces la mediana del sabor)", rechazos)
    tabla = separar(tabla, tabla["sabor"].isin(sabores_validos), "sabor sin receta", rechazos)
    tabla = separar(tabla, ~tabla.duplicated(clave_duplicados), "registro duplicado", rechazos)

    validas = tabla.assign(fecha=pd.to_datetime(tabla["fecha"], format="%Y-%m-%d"), kg=tabla["kg"].astype(float))
    rechazadas = pd.concat(rechazos) if rechazos else pd.DataFrame(columns=[*tabla.columns, "motivo_rechazo"])
    return validas.reset_index(drop=True), rechazadas
   

def verificar_catalogos(recetas, insumos):
    """Los catálogos no se limpian: si tienen errores, el pronóstico no se puede calcular y se frena."""
    sin_datos = sorted(set(recetas["insumo"]) - set(insumos["insumo"]))
    if sin_datos:
        raise ValueError(f"Insumos de las recetas que no están en insumos.json: {', '.join(sin_datos)}")
    if insumos["insumo"].duplicated().any():
        raise ValueError("insumos.json tiene insumos repetidos")
    if (recetas["cantidad_por_kg"] <= 0).any():
        raise ValueError("Hay recetas con cantidades que no son positivas")
    if (insumos["stock_actual"] < 0).any() or (insumos["dias_entrega"] < 0).any() or (insumos["vida_util_dias"] <= 0).any():
        raise ValueError("insumos.json tiene stock, días de entrega o vida útil fuera de rango")
    se_vencen = insumos[insumos["dias_entrega"] + MARGEN_SEGURIDAD_DIAS > insumos["vida_util_dias"]]["insumo"]
    if len(se_vencen) > 0:
        raise ValueError(f"El stock de seguridad de {', '.join(se_vencen)} se vence antes de usarse: los días de entrega "
                         f"más {MARGEN_SEGURIDAD_DIAS} de margen superan su vida útil")


def preparar_datos(carpeta):
    """El flujo completo. Devuelve las tablas limpias y una tabla con todas las filas rechazadas."""
    tablas = leer_tablas(carpeta)
    for nombre in tablas:
        tablas[nombre] = normalizar_encabezados(tablas[nombre])
        validar_esquema(tablas[nombre], nombre)
        tablas[nombre] = normalizar_campos(tablas[nombre], COLUMNAS_TEXTO[nombre])

    verificar_catalogos(tablas["recetas"], tablas["insumos"])
    sabores_validos = set(tablas["recetas"]["sabor"])
    tablas["ventas"], rechazos_ventas = limpiar_registros(tablas["ventas"], sabores_validos, ["fecha", "sabor"])
    tablas["merma"], rechazos_merma = limpiar_registros(tablas["merma"], sabores_validos, ["fecha", "sabor", "motivo"])
    if len(tablas["ventas"]) == 0:
        motivo = rechazos_ventas["motivo_rechazo"].value_counts()
        ejemplo = rechazos_ventas[rechazos_ventas["motivo_rechazo"] == motivo.index[0]].iloc[0]
        raise ValueError(f"Ninguna venta pasó la limpieza. Motivo más frecuente: {motivo.index[0]} "
                         f"({motivo.iloc[0]} filas). Ejemplo: fecha={ejemplo['fecha']}, sabor={ejemplo['sabor']}, kg={ejemplo['kg']}")
    rechazos = pd.concat([rechazos_ventas.assign(tabla="ventas", fila=rechazos_ventas.index + 2),
                          rechazos_merma.assign(tabla="merma", fila=rechazos_merma.index + 2)], ignore_index=True)
    columnas = ["tabla", "fila", "fecha", "sabor", "kg", "motivo", "motivo_rechazo"]
    return tablas, rechazos[columnas]

def guardar_tabla(tabla, ruta):
    """Guarda una tabla en CSV, creando la carpeta si hace falta."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    tabla.to_csv(ruta, index=True if tabla.index.name else False, encoding="utf-8")
    return ruta
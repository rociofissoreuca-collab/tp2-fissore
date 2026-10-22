"""Punto de entrada: python src/main.py

Pregunta si usar los datos de ejemplo o los de la persona, y muestra un menú.
"""
from pathlib import Path

import pandas as pd

import graficos
from heladeria import Heladeria
from pipeline import ARCHIVOS,guardar_tabla
from pronostico import Pronostico

RAIZ = Path(__file__).resolve().parents[1]
CARPETA_EJEMPLO = RAIZ / "data"
ARCHIVOS_PEDIDOS = ", ".join(ARCHIVOS.values())
CARPETA_SALIDAS = RAIZ / "outputs"
MAXIMO_SABORES = 5 

pd.set_option("display.width", 120)


class App:
    """Menú de consola. Ante una entrada inválida muestra un aviso y vuelve al menú en vez de cortarse."""

    def __init__(self, heladeria, entrada=input, carpeta_salidas=CARPETA_SALIDAS, mostrar_graficos=True):
        self.heladeria = heladeria
        self.pronostico = Pronostico(heladeria, heladeria.años()[-1])
        self.entrada = entrada
        self.carpeta_salidas = Path(carpeta_salidas)
        self.mostrar_graficos = mostrar_graficos
        self.opciones = {
            "1": ("Ver la carga de datos y las filas rechazadas", self.ver_carga),
            "2": ("Ver la estacionalidad y el ranking de sabores", self.ver_estacionalidad),
            "3": ("Validar el método de pronóstico", self.ver_validacion),
            "4": (f"Producción de cada sabor para un mes de {self.pronostico.año_objetivo}", self.ver_produccion),
            "5": (f"Compras de insumos para un mes de {self.pronostico.año_objetivo}", self.ver_compras),
            "6": ("Ver gráficos", self.ver_graficos),
            "7": ("Exportar las tablas a outputs/", self.exportar),
        }

    def mostrar_menu(self):
        print("\n" + "=" * 60)
        print(f"  PLANIFICADOR DE PRODUCCIÓN Y COMPRAS — {self.heladeria.nombre}")
        print("=" * 60)
        for clave, (texto, _) in self.opciones.items():
            print(f"  {clave}. {texto}")
        print("  0. Salir")

    def ejecutar(self):
        while True:
            self.mostrar_menu()
            opcion = self.entrada("Elegí una opción: ").strip()
            if opcion == "0":
                print("¡Hasta luego!")
                break
            self.atender(opcion)
            self.entrada("\n(Apretá Enter para volver al menú) ")

    def atender(self, opcion):
        if opcion not in self.opciones:
            print("⚠ Opción inválida: escribí un número del menú.")
            return
        try:
            self.opciones[opcion][1]()
        except ValueError as error:
            print(f"⚠ {error}")

    def pedir_mes(self):
        texto = self.entrada(f"¿Qué mes de {self.pronostico.año_objetivo}? (1 a 12): ").strip()
        if not texto.isdigit():
            raise ValueError("El mes tiene que ser un número del 1 al 12")
        return int(texto)
    
    def elegir(self, titulo, opciones, todos=None):
        """Muestra una lista numerada y devuelve la opción elegida. Si hay todos, el 0 devuelve None (todos)."""
        print(f"\n{titulo}")
        if todos:
            print(f"  0. {todos}")
        mostrar_lista(opciones)
        texto = self.entrada("Elegí un número: ").strip()
        if todos and texto == "0":
            return None
        if not texto.isdigit() or not 1 <= int(texto) <= len(opciones):
            raise ValueError(f"Escribí un número del {0 if todos else 1} al {len(opciones)}")
        return opciones[int(texto) - 1]

    def elegir_varios(self, titulo, opciones, maximo):
        """Muestra una lista numerada y devuelve las opciones elegidas, escritas separadas por comas (ej.: 1,5,6)."""
        print(f"\n{titulo} (hasta {maximo}, separados por comas)")
        mostrar_lista(opciones)
        numeros = [texto.strip() for texto in self.entrada("Elegí los números: ").split(",")]
        if not all(numero.isdigit() and 1 <= int(numero) <= len(opciones) for numero in numeros):
            raise ValueError(f"Escribí números del 1 al {len(opciones)} separados por comas")
        elegidas = []
        for numero in numeros:
            if opciones[int(numero) - 1] not in elegidas:
                elegidas.append(opciones[int(numero) - 1])
        if len(elegidas) > maximo:
            raise ValueError(f"Elegí hasta {maximo}")
        return elegidas

    def ver_carga(self):
        print(self.heladeria)
        rechazos = self.heladeria.rechazos
        if len(rechazos) == 0:
            print("No se rechazó ninguna fila.")
            return
        print("\nFilas rechazadas:")
        print(rechazos[["tabla", "fecha", "sabor", "kg", "motivo_rechazo"]].to_string(index=False))

    def ver_estacionalidad(self):
        print("Kg vendidos por mes (índice: 1 = mes promedio):")
        print(self.heladeria.estacionalidad().round(2).to_string())
        año = self.heladeria.años()[-1]
        print(f"\nRanking de sabores {año}:")
        print(self.heladeria.ranking_sabores(año).round(3).to_string())

    def ver_validacion(self):
        tabla, resumen = self.pronostico.validar()
        print(f"Pronóstico de {self.pronostico.año_base} usando solo los datos anteriores:")
        print(tabla.round(3).to_string())
        print(f"\nError del método: {resumen['error_metodo']:.1%} · "
              f"Error de repetir el año anterior: {resumen['error_ingenuo']:.1%}")

    def ver_produccion(self):
        mes = self.pedir_mes()
        tabla = self.pronostico.produccion(mes)
        print(tabla.round(1).to_string())
        print(f"\nTotal a producir: {tabla['produccion'].sum():,.1f} kg")
        sin_historial = self.pronostico.sabores_sin_historial()
        if sin_historial:
                print(f"Sin pronóstico (no vendieron en {self.pronostico.año_base - 1}, así que no se puede medir "
                  f"su crecimiento): {', '.join(sin_historial)}")
        for sabor, diferencia in self.pronostico.cambios_de_tendencia().items():
            sentido = "cae" if diferencia < 0 else "crece"
            print(f"⚠ {sabor}: en los últimos meses {sentido} más que en el resto del año "
                  f"({abs(diferencia) * 100:.0f} puntos de diferencia). Revisá su producción.")

    def ver_compras(self):
        mes = self.pedir_mes()
        print(self.pronostico.compras_del_mes(mes).round(2).to_string())
        print("\npedidos: en cuántas veces conviene comprar en el mes según la vida útil del insumo.")

    def ver_graficos(self):
        opciones = {
            "Ventas mensuales, un año contra el otro": self.grafico_ventas,
            f"Producción {self.pronostico.año_objetivo} contra lo vendido en {self.pronostico.año_base}": self.grafico_produccion,
            "Compras y stock de un insumo, mes a mes": self.grafico_compras,
            "Error de la validación por sabor": self.grafico_validacion,
            f"Comparar sabores en {self.pronostico.año_base}": self.grafico_comparacion,
        }
        elegido = self.elegir("¿Qué gráfico querés ver?", list(opciones))
        print(f"Gráfico guardado en {legible(opciones[elegido]())}")

    def grafico_ventas(self):
        sabor = self.elegir("¿De qué sabor?", self.heladeria.sabores(), todos="Todos los sabores")
        nombre = sabor or "todos los sabores"
        return graficos.grafico_lineas(self.heladeria.ventas_mensuales(sabor), f"Kg vendidos por mes: {nombre}", "kg",
                                       self.carpeta_salidas / f"ventas_{nombre_archivo(nombre)}.png", self.mostrar_graficos)

    def grafico_produccion(self):
        sabor = self.elegir("¿De qué sabor?", self.pronostico.sabores_con_pronostico(), todos="Todos los sabores")
        nombre = sabor or "todos los sabores"
        return graficos.grafico_lineas(self.pronostico.produccion_vs_vendido(sabor), f"Producción pronosticada: {nombre}",
                                       "kg", self.carpeta_salidas / f"produccion_{nombre_archivo(nombre)}.png",
                                       self.mostrar_graficos)

    def grafico_compras(self):
        insumos = self.heladeria.insumos
        insumo = self.elegir("¿De qué insumo?", list(insumos.index))
        return graficos.grafico_compras(self.pronostico.plan_de_insumo(insumo),
                                        f"Compras y stock de {insumo} en {self.pronostico.año_objetivo}",
                                        insumos.loc[insumo, "unidad"],
                                        self.carpeta_salidas / f"compras_{nombre_archivo(insumo)}.png", self.mostrar_graficos)

    def grafico_validacion(self):
        tabla, _ = self.pronostico.validar()
        return graficos.grafico_validacion(tabla, f"Error del pronóstico por sabor ({self.pronostico.periodo_validacion()})",
                                           self.carpeta_salidas / "validacion.png", self.mostrar_graficos)

    def grafico_comparacion(self):
        sabores = self.elegir_varios("¿Qué sabores querés comparar?", self.heladeria.sabores(), MAXIMO_SABORES)
        año = self.pronostico.año_base
        return graficos.grafico_lineas(self.heladeria.ventas_por_sabor(sabores, año), f"Kg vendidos por mes en {año}", "kg",
                                       self.carpeta_salidas / f"comparacion_{nombre_archivo('-'.join(sabores))}.png",
                                       self.mostrar_graficos)

    def exportar(self):
        año = self.pronostico.año_objetivo
        tabla_validacion, _ = self.pronostico.validar()
        rutas = [
            guardar_tabla(self.pronostico.produccion_anual().round(1), self.carpeta_salidas / f"produccion_{año}.csv"),
            guardar_tabla(self.pronostico.plan_compras().round(2), self.carpeta_salidas / f"compras_{año}.csv"),
            guardar_tabla(tabla_validacion.round(3), self.carpeta_salidas / "validacion.csv"),
        ]
        print("Archivos guardados:")
        for ruta in rutas:
            print(f"  {legible(ruta)}")

def legible(ruta):
    """La ruta relativa a la carpeta del proyecto, si está adentro; si no, completa."""
    return ruta.relative_to(RAIZ) if ruta.is_relative_to(RAIZ) else ruta


def mostrar_lista(opciones):
    for numero, opcion in enumerate(opciones, start=1):
        print(f"  {numero}. {opcion}")


def nombre_archivo(texto):
    return texto.replace(" ", "_")       

def elegir_app(entrada=input, carpeta_salidas=CARPETA_SALIDAS):
    """Pregunta qué datos usar. Si los datos propios tienen un problema, lo explica y vuelve a preguntar."""
    while True:
        print("\n¿Qué datos querés usar?")
        print("  1. Los datos de ejemplo (heladería simulada)")
        print(f"  2. Mis propios datos (una carpeta con {ARCHIVOS_PEDIDOS})")
        print("  0. Salir")
        opcion = entrada("Elegí una opción: ").strip()
        if opcion == "0":
            return None
        if opcion == "1":
            carpeta, nombre = CARPETA_EJEMPLO, "Heladería de ejemplo"
        elif opcion == "2":
            carpeta = Path(entrada("Ruta de la carpeta: ").strip().strip('"'))
            nombre = carpeta.name
        else:
            print("⚠ Opción inválida: escribí 1, 2 o 0.")
            continue
        try:
            app = App(Heladeria(carpeta, nombre), entrada, carpeta_salidas)
        except (FileNotFoundError, ValueError, TypeError, KeyError) as error:
            print(f"⚠ No se pudieron usar esos datos: {error}")
            continue
        if app.heladeria.tasa_merma().sum() == 0:
            print("⚠ No hay merma registrada (sin contar accidentes): la producción se calcula sin merma.")
        print(app.heladeria)
        guardar_tabla(app.heladeria.rechazos, app.carpeta_salidas / "rechazos.csv")
        return app


def main():
    app = elegir_app()
    if app is None:
        print("¡Hasta luego!")
        return
    app.ejecutar()

if __name__ == "__main__":
    main()
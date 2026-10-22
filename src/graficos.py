"""Gráficos de la aplicación. Cada uno se guarda como PNG y, si se pide, se abre en una ventana."""
from pathlib import Path

import matplotlib.pyplot as plt

TEXTO = "#52514e"


def preparar_ejes(titulo, etiqueta_y):
    figura, ejes = plt.subplots(figsize=(9, 5))
    ejes.set_title(titulo, loc="left", fontsize=13)
    ejes.set_ylabel(etiqueta_y, color=TEXTO)
    ejes.grid(axis="y", alpha=0.25)
    ejes.spines[["top", "right"]].set_visible(False)
    ejes.tick_params(colors=TEXTO)
    return figura, ejes


def terminar(figura, ruta, mostrar):
    """Guarda la figura y, si mostrar es True, la abre en una ventana: el programa sigue al cerrarla."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    figura.tight_layout()
    figura.savefig(ruta, dpi=120)
    if mostrar:
        plt.show()
    plt.close(figura)
    return ruta


def grafico_lineas(tabla, titulo, etiqueta_y, ruta, mostrar=False):
    """Una línea por columna de la tabla, con los meses en el eje horizontal."""
    figura, ejes = preparar_ejes(titulo, etiqueta_y)
    meses = [mes[:3] for mes in tabla.index]
    for numero, columna in enumerate(tabla.columns):
        ejes.plot(meses, tabla[columna], color=f"C{numero}", linewidth=2, marker="o", markersize=5, label=str(columna))
    ejes.set_ylim(bottom=0)
    ejes.legend(frameon=False)
    return terminar(figura, ruta, mostrar)


def grafico_compras(tabla, titulo, etiqueta_y, ruta, mostrar=False):
    """Barras con lo que se compra cada mes y una línea con el stock que queda a fin de mes."""
    figura, ejes = preparar_ejes(titulo, etiqueta_y)
    meses = [mes[:3] for mes in tabla.index]
    ejes.bar(meses, tabla["compra"], color="C0", label="compra del mes")
    ejes.plot(meses, tabla["stock_final"], color="C1", linewidth=2, marker="o", markersize=5, label="stock a fin de mes")
    ejes.legend(frameon=False)
    return terminar(figura, ruta, mostrar)


def grafico_validacion(tabla, titulo, ruta, mostrar=False):
    """Error del pronóstico por sabor, comparado con el método ingenuo (repetir el año anterior)."""
    tabla = tabla.sort_values("error")
    figura, ejes = preparar_ejes(titulo, "")
    posiciones = range(len(tabla))
    ejes.barh([p + 0.2 for p in posiciones], tabla["error"] * 100, height=0.4, color="C0", label="método con crecimiento")
    ejes.barh([p - 0.2 for p in posiciones], tabla["error_ingenuo"] * 100, height=0.4, color="C1", label="repetir el año anterior")
    ejes.set_yticks(list(posiciones), tabla.index)
    ejes.set_xlabel("error (% de lo vendido)", color=TEXTO)
    ejes.grid(axis="y", alpha=0)
    ejes.grid(axis="x", alpha=0.25)
    ejes.legend(frameon=False, loc="lower right")
    return terminar(figura, ruta, mostrar)
# Datos de ejemplo

## Fuente y procedimiento

Los datos se generan con el programa `data/generar_datos.py` y tienen **dos partes**:

- **Una parte diseñada**: las reglas de la heladería (qué sabores hay, cuánto vende cada uno, cómo crece, cómo cambia con la temporada, las recetas y el stock) y algunas situaciones puestas a propósito. Las definí yo, están escritas en el programa y son siempre las mismas.
- **Una parte aleatoria**: el ruido de un día a otro, que se sortea a partir de una semilla. Los archivos de esta carpeta usan la semilla 42.

Representan las ventas, la merma y los insumos de una heladería artesanal durante 2024 y 2025. No son de una heladería real ni de una heladería "promedio": están pensados para mostrar cómo responde la aplicación. Para volver a generarlos, desde la carpeta del proyecto:

    python data/generar_datos.py

- Responsable: Rocío Fissore
- Licencia: CC BY 4.0. No contienen información personal.
- Fecha de generación: octubre de 2026

## La parte diseñada

Los kg que se esperan vender de cada sabor en cada día salen de multiplicar estas reglas:

- los kg que vende el sabor en un día promedio de 2024;
- un factor por mes: en verano se vende más que en invierno, y los sabores al agua dependen más de la temporada;
- una tendencia anual propia de cada sabor: algunos crecen y otros caen;
- un aumento del 30 % los sábados y domingos.

La merma es una parte de lo vendido cada semana, distinta para cada sabor. La heladería cierra el 1 de enero y el 25 de diciembre.

Además, incluí a propósito algunas situaciones, para mostrar cómo las trata la aplicación:

| Situación | Para mostrar |
| --- | --- |
| El maracuyá empieza a venderse en marzo de 2025 | Qué pasa con un sabor sin historial |
| La menta granizada cae más desde julio de 2025 | El aviso de cambio de tendencia |
| Dos cortes de luz, el 10/2/2024 y el 18/1/2025 | Que la merma accidental no cuenta en la merma del sabor |
| 8 errores de carga: fechas inválidas, kg faltante, negativo y fuera de rango, un sabor inexistente y una fila repetida | La limpieza y el registro de rechazos |

## La parte aleatoria: la semilla

Sobre esas reglas se agrega un ruido, para que los datos no sean perfectos:

- cada día, los kg esperados se multiplican por un número sorteado de una distribución normal con media 1 y desvío 0,15: las ventas varían alrededor de ±15 % de lo esperado;
- la merma de cada semana se multiplica por una normal con media 1 y desvío 0,2;
- los kg que se tiran en cada corte de luz se sortean entre 2 y 4.

La semilla decide **solo** estos sorteos. Con la misma semilla se obtiene siempre el mismo ruido, y por lo tanto los mismos datos. Con otra semilla cambian los números de cada día, pero no los sabores, las recetas, las reglas ni las situaciones de la tabla.

La semilla es un parámetro de `generar_tablas(semilla)`, y una prueba comprueba que los archivos de esta carpeta son exactamente los que genera la semilla 42.

## Archivos y unidad de análisis

| Archivo | Unidad de análisis (una fila es) |
| `ventas.csv` | Los kg vendidos de un sabor en un día | 
| `merma.csv` | Una cantidad de helado que se tiró | 
| `recetas.json` | Un insumo de la receta de un sabor |
| `insumos.json` | Un insumo | 
| `muestra_ventas.csv` y `muestra_ventas.json` | Las primeras 60 ventas, iguales en los dos formatos, para comprobar que leer CSV y JSON da la misma tabla |

## Variables

- `fecha`: día de la venta o de la merma, con formato AAAA-MM-DD.
- `sabor`: nombre del sabor.
- `kg`: kilos de helado vendidos o tirados.
- `motivo`: por qué se tiró el helado (`cristalizado` o `corte de luz`).
- `insumo`: nombre del insumo.
- `cantidad_por_kg`: cantidad del insumo que lleva un kg de helado, en la unidad del insumo.
- `unidad`: unidad del insumo (kg, litros o unidades).
- `stock_actual`: stock del insumo al 31 de diciembre de 2025.
- `dias_entrega`: días que tarda el proveedor en entregar el insumo.
- `vida_util_dias`: días que dura el insumo antes de echarse a perder.

## Limitaciones

- Los valores (kg diarios, crecimiento, estacionalidad, recetas, stock, vida útil) son inventados con criterio, no tomados de una heladería ni de un proveedor reales.
- El ruido de cada día es independiente del de los demás, así que se compensa al sumar un mes. En datos reales, los días seguidos se parecen y los resultados variarían más.
- No hay precios, costos ni clima.
# Planificador de producción y compras para una heladería

- **Autora:** Rocío Fissore
- **Asignatura:** Programación Orientada a Datos con Python · Universidad Católica Argentina (UCA) · Trabajo Práctico 2
- **Repositorio:** https://github.com/rociofissoreuca-collab/tp2-fissore
- **Licencia:** datos de ejemplo bajo licencia CC BY 4.0

## Para qué sirve

En una heladería artesanal la demanda es muy estacional y muchos insumos son perecederos: producir o comprar de más genera pérdidas, y producir de menos deja sabores sin stock. Esta aplicación, pensada para el dueño o encargado de producción, estima **cuántos kilogramos de cada sabor producir y qué cantidad de cada insumo comprar en cada mes del año siguiente**, a partir de las ventas de los dos últimos años.

El cálculo parte de las ventas del mismo mes del año anterior, ajustadas por el crecimiento de cada sabor; suma la merma habitual, convierte la producción en insumos según las recetas y descuenta el stock disponible, dejando un stock de seguridad. Antes de usar los resultados, la aplicación valida el método contra las ventas reales.

**Fuera del alcance:** precios y costos, clima, sabores nuevos y pronóstico diario.

## Qué se obtiene

- Producción mensual recomendada por sabor.
- Plan de compras mensual por insumo, con la cantidad de pedidos según su vida útil.
- Error de validación del método, por sabor y total.
- Cinco gráficos a elección y las tablas exportadas en CSV.
- Registro de las filas de datos rechazadas, con su motivo.

**Archivos de salida**, en `outputs/<nombre de la heladería>/`:

| Archivo | Contenido | Se genera |
| --- | --- | --- |
| `rechazos.csv` | Filas descartadas, con su archivo, su fila y el motivo | Al cargar los datos |
| `produccion_<año>.csv` | Kg a producir por sabor y por mes | Al exportar (opción 7) |
| `compras_<año>.csv` | Consumo, stock de seguridad, compra, stock final y pedidos por insumo y por mes | Al exportar (opción 7) |
| `validacion.csv` | Ventas reales, pronóstico y error por sabor, del método y de repetir el año anterior | Al exportar (opción 7) |
| `ventas_<sabor>.png`, `produccion_<sabor>.png`, `compras_<insumo>.png`, `validacion.png`, `comparacion_<sabores>.png` | Cada gráfico elegido | Al ver un gráfico (opción 6) |

## Requisitos e instalación

Python 3.9 o superior, con las bibliotecas `pandas`, `numpy` y `matplotlib`:

```bash
pip install -r requirements.txt
```

## Uso

```bash
python src/main.py                     # aplicación
python -m unittest discover tests      # pruebas (28)
```

Las pruebas cubren casos normales, entradas inválidas y propiedades del resultado.

Al iniciar, se elige entre los **datos de ejemplo** o una **carpeta propia**. Luego, el menú ofrece:

| Opción | Muestra |
| --- | --- |
| 1 | Filas rechazadas en la carga |
| 2 | Estacionalidad y ranking de sabores |
| 3 | Validación del método |
| 4 | Producción de un mes (se ingresa el mes, de 1 a 12) |
| 5 | Compras de un mes (se ingresa el mes, de 1 a 12) |
| 6 | Gráficos (se elige el gráfico y el sabor o insumo) |
| 7 | Exportación de las tablas |

Ante una entrada inválida, la aplicación muestra un aviso y vuelve al menú.

## Datos necesarios

Una carpeta con estos archivos:

| Archivo | Una fila es | Columnas |
| --- | --- | --- |
| `ventas.csv` | Los kg vendidos de un sabor en un día | `fecha`, `sabor`, `kg` |
| `merma.csv` (opcional) | Una cantidad de helado descartada | `fecha`, `sabor`, `kg`, `motivo` |
| `recetas.json` | Un insumo de la receta de un sabor | `sabor`, `insumo`, `cantidad_por_kg` |
| `insumos.json` | Un insumo | `insumo`, `unidad`, `stock_actual`, `dias_entrega`, `vida_util_dias` |

**Condiciones obligatorias:**

- Ventas de los doce meses de los dos últimos años.
- CSV separados por comas, con punto decimal y codificación UTF-8; fechas con formato AAAA-MM-DD.
- Nombres de sabores e insumos idénticos entre archivos, incluidas las tildes.
- `stock_actual` corresponde al stock al 31 de diciembre del último año.

Las filas con errores se excluyen y quedan registradas; si un archivo no cumple el formato, la aplicación indica la corrección necesaria.

Los **datos de ejemplo** (`data/`) corresponden a una heladería simulada de 2024 y 2025, con reglas diseñadas y una variación diaria aleatoria generada con la semilla 42. Su procedencia se documenta en [`data/README.md`](data/README.md).

## Estructura del proyecto

```
src/       código de la aplicación (main.py, fuentes.py, pipeline.py, heladeria.py, pronostico.py, graficos.py)
tests/     pruebas con unittest
data/      datos de ejemplo, su generador y su documentación
outputs/   archivos de salida (no se incluyen en el repositorio)
```
## Resultados e interpretación

Con los datos de ejemplo, la aplicación muestra, entre otros, estos resultados:

**Validación del método (opción 3):**

```
Error del método: 3.7% · Error de repetir el año anterior: 8.6%
```

**Producción de diciembre de 2026 (opción 4):**

```
Total a producir: 3,583.6 kg
⚠ menta granizada: en los últimos meses cae más que en el resto del año (6 puntos de diferencia). Revisá su producción.
```

**Interpretación:**

- Al pronosticar el segundo semestre de 2025 con los datos anteriores, el método se equivocó un 3,7 % de lo vendido, menos de la mitad que repetir el año anterior (8,6 %). Ajustar cada sabor por su propio crecimiento mejora la planificación.
- Diciembre es el mes de mayor producción por la estacionalidad: vende 1,95 veces lo que un mes promedio. La planificación tiene que anticipar ese pico en la producción y en las compras.
- Los insumos perecederos se compran en varios pedidos. En enero, la frutilla, que dura 4 días, se pide 8 veces; la leche, que dura 10, 4 veces.
- Los avisos marcan dónde el método es menos confiable. La caída de la menta granizada se aceleró y su error fue del 14,9 %. El maracuyá no tiene pronóstico porque no se vendió en 2024.
- Por eso, los resultados son una guía para planificar y no una decisión automática. Conviene repetir el pronóstico cada mes, a medida que se suman datos nuevos.


## Limitaciones

- Supone que la tendencia de cada sabor se mantiene durante el año; si cambia, la aplicación lo advierte.
- Los sabores sin ventas en ambos años quedan fuera del pronóstico.
- Los resultados son una guía para planificar, no una decisión automática.
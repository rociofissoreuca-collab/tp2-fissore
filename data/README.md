# Datos

## Fuente y procedimiento

Los datos son simulados. Se generan con el programa `data/generar_datos.py`, con la semilla 42. La semilla es un parámetro de generar_tablas(semilla): con la misma semilla se obtienen exactamente los mismos datos y con otra, datos distintos:

    python data/generar_datos.py

Representan las ventas, la merma y los insumos de una heladería artesanal durante 2024 y 2025.

- Responsable: Rocío Fissore
- Licencia: CC BY 4.0. No contienen información personal.
- Fecha de generación: octubre de 2026

## Cómo se simularon

Los kg vendidos de cada sabor en cada día salen de multiplicar:

- los kg que vende el sabor en un día promedio,
- un factor por mes (en verano se vende más que en invierno),
- una tendencia anual propia de cada sabor (algunos crecen y otros caen),
- un aumento del 30 % los sábados y domingos,
- una variación aleatoria de un día a otro: una normal con media 1 y desvío 0,15 (en la merma, desvío 0,2).

La merma es una parte de lo vendido que se tira (distinta para cada sabor), más dos cortes de luz. Se agregaron a propósito algunos errores de carga (fechas inválidas, kilos negativos, un sabor inexistente, una fila repetida) para probar la limpieza.

## Archivos y unidad de análisis

- `ventas.csv`: cada fila son los kg vendidos de un sabor en un día. Tiene 9.763 filas.
- `merma.csv`: cada fila es una cantidad de helado que se tiró. Tiene 1.433 filas.
- `recetas.json`: cada registro es un insumo de la receta de un sabor.
- `insumos.json`: cada registro es un insumo.
- `muestra_ventas.csv` y `muestra_ventas.json`: las primeras 60 ventas, iguales en los dos formatos, para comprobar que la lectura de CSV y de JSON da el mismo resultado.

## Variables

- `fecha`: día de la venta o de la merma, con formato AAAA-MM-DD.
- `sabor`: nombre del sabor.
- `kg`: kilos de helado vendidos o tirados.
- `motivo`: por qué se tiró el helado (cristalizado o corte de luz).
- `insumo`: nombre del insumo.
- `cantidad_por_kg`: cantidad del insumo que lleva un kg de helado.
- `unidad`: unidad del insumo (kg, litros o unidades).
- `stock_actual`: stock del insumo al
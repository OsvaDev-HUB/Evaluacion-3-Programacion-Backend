"""Arma los archivos Excel (.xlsx) de los reportes con openpyxl.

Aquí no se calcula nada: las vistas entregan los datos ya resueltos con el ORM
y este archivo solo los ordena en hojas con un formato legible.
"""

from django.http import HttpResponse
from django.utils import timezone
from openpyxl import Workbook
from openpyxl.styles import Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

FORMATO_PESOS = '"$"#,##0'
FORMATO_PORCENTAJE = "0%"
# Mismos colores del sitio: panel de aluminio para el encabezado y grafito para el texto
RELLENO_ENCABEZADO = PatternFill("solid", fgColor="E8EBE7")
FUENTE_ENCABEZADO = Font(bold=True, color="222724")
LINEA_TOTAL = Border(top=Side(style="medium", color="A0A79F"))


def nuevo_libro():
    """Crea un libro de Excel vacío (se quita la hoja en blanco que trae por defecto)."""
    libro = Workbook()
    libro.remove(libro.active)
    return libro


def agregar_hoja(libro, titulo, encabezados, filas, columnas_pesos=(), columnas_porcentaje=(), fila_total=None):
    """Agrega una hoja con encabezado, filas y (opcional) una fila de total.

    columnas_pesos y columnas_porcentaje son números de columna, empezando en 1.
    """
    hoja = libro.create_sheet(titulo)

    hoja.append(encabezados)
    for celda in hoja[1]:
        celda.font = FUENTE_ENCABEZADO
        celda.fill = RELLENO_ENCABEZADO

    for fila in filas:
        hoja.append(fila)

    if fila_total:
        hoja.append(fila_total)
        for celda in hoja[hoja.max_row]:
            celda.font = Font(bold=True)
            celda.border = LINEA_TOTAL

    # Formato de pesos chilenos y de porcentaje en las columnas indicadas
    for columna in columnas_pesos:
        for celda in hoja[get_column_letter(columna)][1:]:
            celda.number_format = FORMATO_PESOS
    for columna in columnas_porcentaje:
        for celda in hoja[get_column_letter(columna)][1:]:
            celda.number_format = FORMATO_PORCENTAJE

    # Ancho de cada columna según su texto más largo
    for numero in range(1, len(encabezados) + 1):
        letra = get_column_letter(numero)
        largo = max(len(str(celda.value)) for celda in hoja[letra] if celda.value is not None)
        hoja.column_dimensions[letra].width = min(largo + 4, 50)

    # El encabezado queda fijo al bajar por la hoja
    hoja.freeze_panes = "A2"
    return hoja


def respuesta_excel(libro, nombre):
    """Devuelve el libro como archivo descargable, con la fecha de hoy en el nombre."""
    fecha = timezone.localdate().isoformat()
    respuesta = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    respuesta["Content-Disposition"] = f'attachment; filename="{nombre}-{fecha}.xlsx"'
    libro.save(respuesta)
    return respuesta

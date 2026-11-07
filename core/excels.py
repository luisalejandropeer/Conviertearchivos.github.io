"""Unir libros de Excel (.xlsx) conservando formato."""
import io
import re
from copy import copy

from openpyxl import Workbook, load_workbook
from openpyxl.utils import get_column_letter

from .common import UserError, clean_name

_BAD = re.compile(r"[\\/*?:\[\]]")


def _open(file_storage):
    nombre = file_storage.filename
    if nombre.lower().endswith(".xls"):
        raise UserError(
            f"«{nombre}» es un Excel antiguo (.xls). Ábrelo en Excel y guárdalo como .xlsx para poder unirlo."
        )
    try:
        return load_workbook(file_storage.stream, data_only=False)
    except Exception:
        raise UserError(f"No pude abrir «{nombre}». ¿Es un Excel (.xlsx) válido?")


def _unique(title, used):
    title = _BAD.sub("", title).strip() or "Hoja"
    title = title[:31]
    base, n = title, 2
    while title.lower() in used:
        suffix = f" ({n})"
        title = base[: 31 - len(suffix)] + suffix
        n += 1
    used.add(title.lower())
    return title


def _copy_cell(src, dst):
    dst.value = src.value
    if src.has_style:
        dst.font = copy(src.font)
        dst.border = copy(src.border)
        dst.fill = copy(src.fill)
        dst.number_format = src.number_format
        dst.protection = copy(src.protection)
        dst.alignment = copy(src.alignment)
    if src.hyperlink:
        dst.hyperlink = copy(src.hyperlink)
    if src.comment:
        dst.comment = copy(src.comment)


def _copy_sheet(src, dst, row_offset=0):
    for row in src.iter_rows():
        for c in row:
            if c.value is None and not c.has_style:
                continue
            _copy_cell(c, dst.cell(row=c.row + row_offset, column=c.column))
    for key, dim in src.column_dimensions.items():
        if dim.width:
            actual = dst.column_dimensions[key].width or 0
            dst.column_dimensions[key].width = max(actual, dim.width)
    for idx, dim in src.row_dimensions.items():
        if dim.height:
            dst.row_dimensions[idx + row_offset].height = dim.height
    for rango in src.merged_cells.ranges:
        dst.merge_cells(
            start_row=rango.min_row + row_offset,
            start_column=rango.min_col,
            end_row=rango.max_row + row_offset,
            end_column=rango.max_col,
        )


def merge(files, mode="hojas"):
    libros = [(f.filename, _open(f)) for f in files]
    salida_wb = Workbook()
    salida_wb.remove(salida_wb.active)
    usados = set()

    if mode == "una":
        hoja = salida_wb.create_sheet(_unique("Todo junto", usados))
        offset = 0
        for _, wb in libros:
            for ws in wb.worksheets:
                if ws.sheet_state != "visible":
                    continue
                _copy_sheet(ws, hoja, offset)
                offset += ws.max_row + 1  # una fila en blanco entre archivos
    else:
        for nombre, wb in libros:
            base = clean_name(nombre, "Libro")
            visibles = [ws for ws in wb.worksheets if ws.sheet_state == "visible"]
            for ws in visibles:
                titulo = base if len(visibles) == 1 else f"{base} - {ws.title}"
                nueva = salida_wb.create_sheet(_unique(titulo, usados))
                _copy_sheet(ws, nueva)
                if ws.freeze_panes:
                    nueva.freeze_panes = ws.freeze_panes

    if not salida_wb.worksheets:
        raise UserError("Los archivos no tienen hojas visibles para unir.")
    salida = io.BytesIO()
    salida_wb.save(salida)
    salida.seek(0)
    return salida

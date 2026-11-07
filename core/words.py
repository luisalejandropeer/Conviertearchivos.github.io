"""Unir documentos de Word (.docx)."""
import io

from docx import Document
from docxcompose.composer import Composer

from .common import UserError


def _open(file_storage):
    nombre = file_storage.filename
    if nombre.lower().endswith(".doc"):
        raise UserError(
            f"«{nombre}» es un Word antiguo (.doc). Ábrelo en Word y guárdalo como .docx para poder unirlo."
        )
    try:
        return Document(file_storage.stream)
    except Exception:
        raise UserError(f"No pude abrir «{nombre}». ¿Es un documento de Word (.docx) válido?")


def merge(files, page_break=True):
    docs = [_open(f) for f in files]
    maestro = docs[0]
    compositor = Composer(maestro)
    for d in docs[1:]:
        if page_break:
            maestro.add_page_break()
        compositor.append(d)
    salida = io.BytesIO()
    compositor.save(salida)
    salida.seek(0)
    return salida

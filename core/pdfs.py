"""Unir PDFs."""
import io

from pypdf import PdfReader, PdfWriter

from .common import UserError


def _reader(file_storage):
    try:
        r = PdfReader(file_storage.stream)
        if r.is_encrypted and not r.decrypt(""):
            raise UserError(
                f"«{file_storage.filename}» tiene contraseña. Quítale la contraseña y vuelve a intentarlo."
            )
        len(r.pages)  # fuerza a leerlo para detectar archivos dañados
        return r
    except UserError:
        raise
    except Exception:
        raise UserError(f"«{file_storage.filename}» no parece un PDF válido o está dañado.")


def page_count(file_storage):
    return len(_reader(file_storage).pages)


def merge(files):
    escritor = PdfWriter()
    for f in files:
        escritor.append(_reader(f))
    salida = io.BytesIO()
    escritor.write(salida)
    salida.seek(0)
    return salida

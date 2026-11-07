"""Utilidades compartidas."""
import os
import re


class UserError(Exception):
    """Error con un mensaje pensado para mostrarse tal cual a la persona."""


def get_files(request, exts, minimum=1, field="files"):
    """Devuelve la lista de archivos subidos validando extensión y cantidad."""
    files = [f for f in request.files.getlist(field) if f and f.filename]
    if len(files) < minimum:
        if minimum == 1:
            raise UserError("Primero elige al menos un archivo.")
        raise UserError(f"Elige al menos {minimum} archivos para poder unirlos.")
    if len(files) > 100:
        raise UserError("Son demasiados archivos a la vez (máximo 100).")
    for f in files:
        ext = os.path.splitext(f.filename)[1].lower()
        if ext not in exts:
            permitidos = ", ".join(sorted(exts))
            raise UserError(
                f"«{f.filename}» no es de un tipo permitido aquí. Tipos válidos: {permitidos}."
            )
    return files


def clean_name(name, default="archivo"):
    base = os.path.splitext(os.path.basename(name or ""))[0]
    base = re.sub(r"[^\w\- ]", "", base, flags=re.UNICODE).strip()
    return base or default

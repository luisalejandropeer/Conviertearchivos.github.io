"""Convierte Archivos: servidor web.

Ejecutar en tu compu:   python app.py      (abre http://localhost:5000)
En producción:          gunicorn -w 3 -t 120 app:app
"""
import json
import logging
import os

from flask import Flask, jsonify, request, send_file, send_from_directory
from werkzeug.exceptions import RequestEntityTooLarge

from core import excels, images, pdfs, qr, words
from core.common import UserError, get_files

app = Flask(__name__, static_folder="static", static_url_path="")
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024  # 200 MB por envío
log = logging.getLogger("convierte-archivos")

WORD_EXT = {".docx", ".docm"}
EXCEL_EXT = {".xlsx", ".xlsm", ".xls"}


@app.get("/")
def home():
    return send_from_directory(app.static_folder, "index.html")


def _send(buf, mimetype, name):
    return send_file(buf, mimetype=mimetype, as_attachment=True, download_name=name)


@app.post("/api/imagenes-a-pdf")
def imagenes_a_pdf():
    files = get_files(request, images.IMG_EXT, 1)
    try:
        rot = [int(x) for x in json.loads(request.form.get("rotations", "[]"))]
    except Exception:
        rot = []
    buf = images.build_pdf(files, rot, request.form.get("page", "auto"), request.form.get("margin", "0"))
    return _send(buf, "application/pdf", "mis-imagenes.pdf")


@app.post("/api/miniatura")
def miniatura():
    files = get_files(request, images.IMG_EXT, 1)
    return send_file(images.thumbnail(files[0]), mimetype="image/jpeg")


@app.post("/api/pdf-info")
def pdf_info():
    files = get_files(request, {".pdf"}, 1)
    return jsonify(pages=pdfs.page_count(files[0]))


@app.post("/api/unir-pdf")
def unir_pdf():
    files = get_files(request, {".pdf"}, 2)
    return _send(pdfs.merge(files), "application/pdf", "pdfs-unidos.pdf")


@app.post("/api/unir-word")
def unir_word():
    files = get_files(request, WORD_EXT | {".doc"}, 2)
    buf = words.merge(files, page_break=request.form.get("page_break", "1") == "1")
    return _send(
        buf,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "documentos-unidos.docx",
    )


@app.post("/api/unir-excel")
def unir_excel():
    files = get_files(request, EXCEL_EXT, 2)
    buf = excels.merge(files, request.form.get("mode", "hojas"))
    return _send(
        buf,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "excel-unido.xlsx",
    )


@app.post("/api/qr")
def make_qr():
    f = request.form
    buf, ok, nota = qr.make_qr(
        f.get("url", ""),
        shape=f.get("shape", "corazon"),
        fg=f.get("fg", "#1b1b1b"),
        bg=f.get("bg", "#ffffff"),
        deco=f.get("deco", f.get("fg", "#1b1b1b")),
        dots=f.get("dots", "cuadrados"),
        transparent=f.get("transparent", "1") == "1",
        shape_file=request.files.get("shape_image"),
        logo_file=request.files.get("logo"),
        use_image_colors=f.get("image_colors", "0") == "1",
    )
    resp = send_file(buf, mimetype="image/png")
    resp.headers["X-QR-Verified"] = "1" if ok else "0"
    resp.headers["X-QR-Note"] = json.dumps(nota)  # ASCII seguro (escapa acentos)
    resp.headers["Access-Control-Expose-Headers"] = "X-QR-Verified, X-QR-Note"
    resp.headers["Cache-Control"] = "no-store"
    return resp


@app.errorhandler(UserError)
def user_error(e):
    return jsonify(error=str(e)), 400


@app.errorhandler(RequestEntityTooLarge)
def too_large(e):
    return jsonify(error="Los archivos pesan demasiado (máximo 200 MB en total). Prueba con menos archivos."), 413


@app.errorhandler(Exception)
def unexpected(e):
    from werkzeug.exceptions import HTTPException

    if isinstance(e, HTTPException):
        return jsonify(error="No encontré eso."), e.code
    log.exception("Error inesperado")
    return jsonify(error="Algo salió mal de nuestro lado. Inténtalo otra vez; si sigue, prueba con otros archivos."), 500


@app.after_request
def headers(resp):
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    return resp


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)

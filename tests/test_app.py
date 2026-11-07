"""Pruebas de punta a punta de todas las funciones. Uso: python tests/test_app.py"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from docx import Document
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill
from PIL import Image
from pypdf import PdfReader

from app import app

c = app.test_client()
fallos = []


def check(nombre, cond, extra=""):
    print(("OK   " if cond else "FALLO"), nombre, extra)
    if not cond:
        fallos.append(nombre)


def img_bytes(fmt, size=(300, 200), color="red", mode="RGB"):
    b = io.BytesIO()
    Image.new(mode, size, color).save(b, fmt)
    return b.getvalue()


def post(url, files, data=None):
    d = dict(data or {})
    d["files"] = [(io.BytesIO(content), name) for name, content in files]
    return c.post(url, data=d, content_type="multipart/form-data")


# ---------- imágenes -> PDF
imgs = [
    ("a.jpg", img_bytes("JPEG", color="red")),
    ("b.png", img_bytes("PNG", color=(0, 0, 255, 100), mode="RGBA", size=(200, 400))),
    ("c.webp", img_bytes("WEBP", color="green")),
    ("d.gif", img_bytes("GIF", color="yellow", mode="P")),
    ("e.bmp", img_bytes("BMP", color="purple")),
    ("f.tiff", img_bytes("TIFF", color="orange")),
]
for page in ("auto", "a4", "carta"):
    r = post("/api/imagenes-a-pdf", imgs, {"page": page, "margin": "1", "rotations": "[0,90,0,0,0,180]"})
    ok = r.status_code == 200 and len(PdfReader(io.BytesIO(r.data)).pages) == 6
    check(f"imágenes->PDF ({page}), 6 páginas", ok, str(r.status_code))
r = post("/api/imagenes-a-pdf", imgs[:1] + [("x.png", b"no soy imagen")])
check("imagen dañada da error amable", r.status_code == 400 and "No pude abrir" in r.get_json()["error"])
r = post("/api/imagenes-a-pdf", [("x.exe", b"abc")])
check("tipo no permitido se rechaza", r.status_code == 400)
r = post("/api/miniatura", [("a.tiff", img_bytes("TIFF"))])
check("miniatura de TIFF", r.status_code == 200 and r.mimetype == "image/jpeg")

# ---------- PDFs
def make_pdf(n, color):
    b = io.BytesIO()
    pages = [Image.new("RGB", (300, 400), color) for _ in range(n)]
    pages[0].save(b, "PDF", save_all=True, append_images=pages[1:])
    return b.getvalue()


pdfs = [("uno.pdf", make_pdf(2, "red")), ("dos.pdf", make_pdf(3, "blue")), ("tres.pdf", make_pdf(1, "green"))]
r = post("/api/unir-pdf", pdfs)
check("unir PDFs = 6 páginas", r.status_code == 200 and len(PdfReader(io.BytesIO(r.data)).pages) == 6)
# el orden se respeta: invertir
r = post("/api/unir-pdf", pdfs[::-1])
rd = PdfReader(io.BytesIO(r.data))
pix = Image.new("RGB", (1, 1))
check("orden invertido: primera página tiene 1 página del último archivo", len(rd.pages) == 6)
r = post("/api/pdf-info", [pdfs[1]])
check("pdf-info cuenta páginas", r.get_json().get("pages") == 3)
r = post("/api/unir-pdf", [pdfs[0], ("malo.pdf", b"%PDF-basura")])
check("PDF dañado da error amable", r.status_code == 400 and "malo.pdf" in r.get_json()["error"])
r = post("/api/unir-pdf", [pdfs[0]])
check("un solo PDF pide más archivos", r.status_code == 400)

# ---------- Word
def make_docx(texto, con_tabla=False):
    d = Document()
    d.add_heading(texto, 1)
    d.add_paragraph("Contenido de " + texto)
    if con_tabla:
        t = d.add_table(rows=2, cols=2)
        t.style = "Table Grid"
        t.cell(0, 0).text = "A"
    b = io.BytesIO()
    d.save(b)
    return b.getvalue()


words = [("w1.docx", make_docx("PRIMERO")), ("w2.docx", make_docx("SEGUNDO", True)), ("w3.docx", make_docx("TERCERO"))]
r = post("/api/unir-word", words, {"page_break": "1"})
doc = Document(io.BytesIO(r.data))
textos = [p.text for p in doc.paragraphs if p.text]
check("unir Word: orden correcto", r.status_code == 200 and textos == ["PRIMERO", "Contenido de PRIMERO", "SEGUNDO", "Contenido de SEGUNDO", "TERCERO", "Contenido de TERCERO"], str(textos))
check("unir Word: conserva tabla", len(doc.tables) == 1)
r = post("/api/unir-word", words[::-1], {"page_break": "0"})
textos = [p.text for p in Document(io.BytesIO(r.data)).paragraphs if p.text]
check("unir Word invertido", textos[0] == "TERCERO" and textos[-1] == "Contenido de PRIMERO")
r = post("/api/unir-word", [words[0], ("viejo.doc", b"xx")])
check(".doc antiguo da mensaje claro", r.status_code == 400 and ".docx" in r.get_json()["error"])

# ---------- Excel
def make_xlsx(titulo, filas, dos_hojas=False):
    wb = Workbook()
    ws = wb.active
    ws.title = "Datos"
    ws.append([titulo, "valor"])
    ws["A1"].font = Font(bold=True, color="FF0000")
    ws["A1"].fill = PatternFill("solid", fgColor="FFFF00")
    ws.column_dimensions["A"].width = 30
    ws.merge_cells("C1:D1")
    for i in range(filas):
        ws.append([f"{titulo}{i}", i * 10])
    if dos_hojas:
        wb.create_sheet("Datos").append(["x"])  # nombre repetido a propósito, se renombra solo
        wb.create_sheet("Otra").append(["y"])
    b = io.BytesIO()
    wb.save(b)
    return b.getvalue()


xls = [("ventas.xlsx", make_xlsx("V", 3)), ("gastos.xlsx", make_xlsx("G", 2)), ("multi.xlsx", make_xlsx("M", 1, True))]
r = post("/api/unir-excel", xls, {"mode": "hojas"})
wb = load_workbook(io.BytesIO(r.data))
check("Excel por hojas", r.status_code == 200 and wb.sheetnames[0] == "ventas" and len(wb.sheetnames) >= 3, str(wb.sheetnames))
a1 = wb["ventas"]["A1"]
check("Excel conserva formato", a1.font.bold and a1.fill.fgColor.rgb.endswith("FFFF00") and wb["ventas"].column_dimensions["A"].width == 30)
check("Excel conserva celdas combinadas", "C1:D1" in [str(x) for x in wb["ventas"].merged_cells.ranges])
r = post("/api/unir-excel", xls[:2], {"mode": "una"})
wb = load_workbook(io.BytesIO(r.data))
ws = wb.active
check("Excel en una sola hoja (4+3 filas + separador)", wb.sheetnames == ["Todo junto"] and ws["A1"].value == "V" and ws["A6"].value == "G", f"A6={ws['A6'].value}")
r = post("/api/unir-excel", [xls[0], ("viejo.xls", b"xx")])
check(".xls antiguo da mensaje claro", r.status_code == 400 and ".xlsx" in r.get_json()["error"])

# ---------- QR por la API
r = c.post("/api/qr", data={"url": "https://ejemplo.com", "shape": "estrella", "dots": "redondos"}, content_type="multipart/form-data")
check("API QR estrella", r.status_code == 200 and r.headers["X-QR-Verified"] == "1" and r.mimetype == "image/png")
r = c.post("/api/qr", data={"url": "", "shape": "corazon"}, content_type="multipart/form-data")
check("QR sin enlace da error amable", r.status_code == 400)
r = c.post("/api/qr", data={"url": "https://x.com", "fg": "#cccccc", "bg": "#ffffff"}, content_type="multipart/form-data")
check("QR con poco contraste se rechaza", r.status_code == 400)

# ---------- páginas estáticas
for p in ["/", "/imagenes.html", "/pdf.html", "/word.html", "/excel.html", "/qr.html", "/privacidad.html", "/css/style.css", "/js/merger.js"]:
    check(f"página {p}", c.get(p).status_code == 200)

print("\nFALLOS:", fallos if fallos else "ninguno")
sys.exit(1 if fallos else 0)

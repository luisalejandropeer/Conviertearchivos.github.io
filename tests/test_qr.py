"""Prueba que el QR de cada forma se pueda leer. Uso: python tests/test_qr.py"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw
from werkzeug.datastructures import FileStorage

from core import qr

URL = "https://www.ejemplo.com/mi-pagina?id=12345"
OUT = sys.argv[1] if len(sys.argv) > 1 else "."


def fs(img, name="x.png"):
    b = io.BytesIO()
    img.save(b, "PNG")
    b.seek(0)
    return FileStorage(stream=b, filename=name)


# imagen propia: silueta de gato simple sobre fondo blanco (sin transparencia)
sil = Image.new("RGB", (500, 500), "white")
d = ImageDraw.Draw(sil)
d.ellipse((100, 150, 400, 450), fill="black")
d.polygon([(110, 220), (130, 80), (220, 170)], fill="black")
d.polygon([(390, 220), (370, 80), (280, 170)], fill="black")
d.ellipse((180, 250, 220, 290), fill="white")

logo = Image.new("RGB", (100, 100), "red")

fallos = 0
for shape in ["cuadrado", "corazon", "circulo", "estrella", "flor", "gota", "rombo", "redondeado", "imagen"]:
    for dots in ("cuadrados", "redondos"):
        kw = dict(shape=shape, dots=dots)
        if shape == "imagen":
            kw["shape_file"] = fs(sil)
        buf, ok, nota = qr.make_qr(URL, **kw)
        open(f"{OUT}/qr_{shape}_{dots}.png", "wb").write(buf.getvalue())
        print(f"{shape:12} {dots:10} verificado={ok} {nota}")
        fallos += 0 if ok else 1

# con logo y colores
buf, ok, nota = qr.make_qr(URL, shape="corazon", fg="#7a1fa2", deco="#c77dff", bg="#fff7fb", logo_file=fs(logo))
open(f"{OUT}/qr_corazon_logo.png", "wb").write(buf.getvalue())
print("corazon+logo+colores verificado=", ok, nota)
fallos += 0 if ok else 1

print("FALLOS:", fallos)
sys.exit(1 if fallos else 0)

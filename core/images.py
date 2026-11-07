"""Imágenes (cualquier formato común) -> un solo PDF."""
import io

from PIL import Image, ImageOps

try:  # HEIC/HEIF (fotos de iPhone)
    import pillow_heif

    pillow_heif.register_heif_opener()
except Exception:  # pragma: no cover
    pass

from .common import UserError

IMG_EXT = {
    ".jpg", ".jpeg", ".jfif", ".png", ".webp", ".gif", ".bmp", ".tif", ".tiff",
    ".heic", ".heif", ".ico", ".ppm", ".pgm", ".pbm", ".avif",
}

# tamaños a 150 puntos por pulgada (alcanza para imprimir bien)
PAGES = {"a4": (1240, 1754), "carta": (1275, 1650)}
MARGINS = {"0": 0, "1": 45, "2": 100}
MAX_SIDE = 4200  # evita PDFs gigantes con fotos enormes


def _open(file_storage):
    try:
        im = Image.open(file_storage.stream)
        im.seek(0)
        im.load()
    except Exception:
        raise UserError(f"No pude abrir «{file_storage.filename}». ¿Seguro que es una imagen?")
    try:
        im = ImageOps.exif_transpose(im)  # respeta la orientación de las fotos del celular
    except Exception:
        pass
    return im


def _flatten(im):
    """Pasa a RGB, poniendo fondo blanco donde haya transparencia."""
    if im.mode in ("I;16", "I;16B", "I;16L", "I"):
        im = im.point(lambda p: p / 256).convert("L")
    if im.mode == "P" and "transparency" in im.info:
        im = im.convert("RGBA")
    if im.mode in ("RGBA", "LA"):
        im = im.convert("RGBA")
        fondo = Image.new("RGB", im.size, "white")
        fondo.paste(im, mask=im.getchannel("A"))
        return fondo
    return im.convert("RGB")


def _limit(im):
    w, h = im.size
    big = max(w, h)
    if big > MAX_SIDE:
        k = MAX_SIDE / big
        im = im.resize((max(1, int(w * k)), max(1, int(h * k))), Image.LANCZOS)
    return im


def _layout(im, page, margin_px):
    if page == "auto":
        return _limit(im)
    w, h = PAGES[page]
    if im.width > im.height:  # foto horizontal -> hoja horizontal
        w, h = h, w
    hoja = Image.new("RGB", (w, h), "white")
    caja_w, caja_h = w - 2 * margin_px, h - 2 * margin_px
    k = min(caja_w / im.width, caja_h / im.height)
    nuevo = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)
    hoja.paste(nuevo, ((w - nuevo.width) // 2, (h - nuevo.height) // 2))
    return hoja


def build_pdf(files, rotations, page="auto", margin="0"):
    if page not in ("auto", *PAGES):
        page = "auto"
    margin_px = MARGINS.get(str(margin), 0)
    hojas = []
    for i, f in enumerate(files):
        im = _flatten(_open(f))
        grados = rotations[i] % 360 if i < len(rotations) else 0
        if grados:
            im = im.rotate(-grados, expand=True)  # sentido de las manecillas del reloj
        hojas.append(_layout(im, page, margin_px))
    salida = io.BytesIO()
    hojas[0].save(
        salida, "PDF", save_all=True, append_images=hojas[1:], resolution=150.0, quality=92
    )
    salida.seek(0)
    return salida


def thumbnail(file_storage, side=260):
    """Miniatura JPEG para formatos que el navegador no sabe mostrar (HEIC, TIFF...)."""
    im = _flatten(_open(file_storage))
    im.thumbnail((side, side))
    salida = io.BytesIO()
    im.save(salida, "JPEG", quality=80)
    salida.seek(0)
    return salida

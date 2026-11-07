"""Códigos QR con forma (corazón, estrella, tu propia imagen...) que siguen funcionando.

Idea: el QR real va completo, con su zona de silencio, en el centro de la forma. El resto de la
forma se rellena con puntos decorativos. Así el QR nunca pierde datos. Después se "escanea" el
resultado con un lector para confirmar que sí funciona.
"""
import hashlib
import io
import random
import re

import cv2
import numpy as np
import segno
from PIL import Image, ImageDraw, ImageOps

from .common import UserError

SHAPES = {"cuadrado", "corazon", "circulo", "estrella", "flor", "gota", "rombo", "redondeado", "imagen"}
_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


def _color(value, nombre):
    if not _HEX.match(value or ""):
        raise UserError(f"El color de {nombre} no es válido.")
    return tuple(int(value[i : i + 2], 16) for i in (1, 3, 5))


def _lum(rgb):
    r, g, b = (c / 255 for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


# ---------------------------------------------------------------- formas
def _polygon(nombre):
    t = np.linspace(0, 2 * np.pi, 600)
    if nombre == "corazon":
        x = 16 * np.sin(t) ** 3
        y = -(13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t))
    elif nombre == "flor":
        r = 0.80 + 0.20 * np.cos(8 * t)
        x, y = r * np.cos(t), r * np.sin(t)
    elif nombre == "gota":
        x = np.sin(t) * np.sin(t / 2) ** 1.3
        y = -np.cos(t)
    elif nombre == "estrella":
        ang = np.linspace(0, 2 * np.pi, 11)[:-1] - np.pi / 2
        r = np.where(np.arange(10) % 2 == 0, 1.0, 0.56)
        x, y = r * np.cos(ang), r * np.sin(ang)
    elif nombre == "rombo":
        x, y = np.array([0, 1, 0, -1.0]), np.array([-1, 0, 1, 0.0])
    else:
        raise UserError("Forma desconocida.")
    return x, y


def _builtin_mask(nombre, S):
    """Máscara suave (0-255) de la forma elegida, ocupando casi todo el lienzo SxS."""
    ss = 2
    img = Image.new("L", (S * ss, S * ss), 0)
    d = ImageDraw.Draw(img)
    pad = int(S * ss * 0.03)
    if nombre == "circulo":
        d.ellipse((pad, pad, S * ss - pad, S * ss - pad), fill=255)
    elif nombre == "redondeado":
        d.rounded_rectangle((pad, pad, S * ss - pad, S * ss - pad), radius=int(S * ss * 0.2), fill=255)
    else:
        x, y = _polygon(nombre)
        w, h = x.max() - x.min(), y.max() - y.min()
        k = (S * ss - 2 * pad) / max(w, h)
        px = (x - (x.max() + x.min()) / 2) * k + S * ss / 2
        py = (y - (y.max() + y.min()) / 2) * k + S * ss / 2
        d.polygon(list(zip(px.tolist(), py.tolist())), fill=255)
    return img.resize((S, S), Image.LANCZOS), None


def _image_mask(file_storage, S):
    """Forma sacada de la imagen de la persona (transparencia, o lo que no sea el fondo)."""
    try:
        im = Image.open(file_storage.stream)
        im.load()
        im = ImageOps.exif_transpose(im).convert("RGBA")
    except Exception:
        raise UserError("No pude abrir la imagen de la forma. Prueba con un PNG o JPG.")
    caja = S - 2 * int(S * 0.03)
    k = caja / max(im.size)  # se agranda o se achica para ocupar todo el lienzo
    im = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)
    lienzo = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    lienzo.paste(im, ((S - im.width) // 2, (S - im.height) // 2))
    arr = np.array(lienzo)
    alpha = arr[..., 3]
    region = np.zeros((S, S), bool)
    region[(S - im.height) // 2 : (S - im.height) // 2 + im.height, (S - im.width) // 2 : (S - im.width) // 2 + im.width] = True

    if (alpha[region] < 250).mean() > 0.02:  # tiene transparencia de verdad
        binaria = alpha > 128
    else:  # fondo sólido: la forma es lo que se distingue del fondo
        rgb = arr[..., :3].astype(np.int32)
        borde = np.concatenate([rgb[region][: im.width], rgb[region][-im.width :]])
        fondo = np.median(borde, axis=0)
        dist = np.abs(rgb - fondo).sum(axis=2)
        binaria = (dist > 90) & region

    # rellenar huecos interiores (ojos, letras) para obtener una silueta sólida
    u8 = (binaria * 255).astype(np.uint8)
    u8 = cv2.morphologyEx(u8, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    inv = cv2.bitwise_not(u8)
    flood = inv.copy()
    cv2.floodFill(flood, np.zeros((S + 2, S + 2), np.uint8), (0, 0), 0)
    u8 = cv2.bitwise_or(u8, flood)

    cobertura = (u8 > 0).mean()
    if cobertura < 0.04:
        raise UserError("No logré ver la forma en esa imagen. Usa una con fondo blanco o transparente.")
    soft = Image.fromarray(cv2.GaussianBlur(u8, (3, 3), 0))
    return soft, lienzo


# ---------------------------------------------------------------- colocación del QR
def _place(mask_bool, total_modules):
    """Busca el cuadrado (QR + zona de silencio) más grande que cabe dentro de la forma."""
    S = mask_bool.shape[0]
    ii = np.pad(mask_bool.astype(np.int64).cumsum(0).cumsum(1), ((1, 0), (1, 0)))

    def lleno(x0, y0, x1, y1):
        if x0 < 0 or y0 < 0 or x1 > S or y1 > S:
            return False
        s = ii[y1, x1] - ii[y0, x1] - ii[y1, x0] + ii[y0, x0]
        return s == (x1 - x0) * (y1 - y0)

    ys, xs = np.nonzero(mask_bool)
    cx, cy = int(xs.mean()), int(ys.mean())
    pasos = [int(S * f) for f in (0, 0.02, -0.02, 0.04, -0.04, 0.07, -0.07, 0.1, -0.1, 0.14, -0.14)]
    for m in range(S // total_modules, 3, -1):
        lado = total_modules * m
        for dy in pasos:
            for dx in (0, int(S * 0.02), -int(S * 0.02), int(S * 0.04), -int(S * 0.04)):
                x0, y0 = cx - lado // 2 + dx, cy - lado // 2 + dy
                if lleno(x0, y0, x0 + lado, y0 + lado):
                    return m, x0, y0
    raise UserError("La forma es demasiado pequeña para este enlace. Prueba otra forma o un enlace más corto.")


# ---------------------------------------------------------------- dibujo
def _draw_module(d, x, y, m, fill, redondo):
    if redondo:
        d.ellipse((x, y, x + m - 1, y + m - 1), fill=fill)
    else:
        d.rectangle((x, y, x + m - 1, y + m - 1), fill=fill)


def _is_finder(r, c, n):
    return (r < 8 and c < 8) or (r < 8 and c >= n - 8) or (r >= n - 8 and c < 8)


def _draw_qr(canvas, matrix, x0, y0, m, fg, dots):
    d = ImageDraw.Draw(canvas)
    n = len(matrix)
    for r in range(n):
        for c in range(n):
            if matrix[r][c]:
                _draw_module(d, x0 + c * m, y0 + r * m, m, fg, dots == "redondos" and not _is_finder(r, c, n))


def _logo(canvas, logo_file, x0, y0, side, bg):
    try:
        lg = Image.open(logo_file.stream)
        lg.load()
        lg = ImageOps.exif_transpose(lg).convert("RGBA")
    except Exception:
        raise UserError("No pude abrir la imagen del centro del QR.")
    lado = int(side * 0.2)
    lg.thumbnail((lado, lado), Image.LANCZOS)
    pad = max(4, lado // 8)
    cx, cy = x0 + side // 2, y0 + side // 2
    caja = (cx - lg.width // 2 - pad, cy - lg.height // 2 - pad, cx + lg.width // 2 + pad, cy + lg.height // 2 + pad)
    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle(caja, radius=pad, fill=bg)
    canvas.alpha_composite(lg, (cx - lg.width // 2, cy - lg.height // 2))


def _decorate(canvas, mask_bool, m, ox, oy, qr_box, rng, density, dots, color_fn):
    S = mask_bool.shape[0]
    ii = np.pad(mask_bool.astype(np.int64).cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    d = ImageDraw.Draw(canvas)
    qx0, qy0, qx1, qy1 = qr_box
    inset = max(1, int(m * 0.1))
    for y in range(oy, S - m + 1, m):
        for x in range(ox, S - m + 1, m):
            if x < qx1 and x + m > qx0 and y < qy1 and y + m > qy0:
                continue
            s = ii[y + m, x + m] - ii[y, x + m] - ii[y + m, x] + ii[y, x]
            if s < 0.98 * m * m:
                continue
            if rng.random() > density:
                continue
            fill = color_fn(x + m // 2, y + m // 2)
            box = (x + inset, y + inset, x + m - 1 - inset, y + m - 1 - inset)
            if dots == "redondos":
                d.ellipse(box, fill=fill)
            else:
                d.rectangle(box, fill=fill)


# ---------------------------------------------------------------- verificación
def verify(rgba_image, texto):
    """Intenta leer el QR como lo haría un teléfono. True si lee exactamente el enlace."""
    fondo = Image.new("RGB", rgba_image.size, "white")
    fondo.paste(rgba_image, mask=rgba_image.getchannel("A"))
    base = np.array(ImageOps.expand(fondo, border=fondo.width // 12, fill="white"))
    base = cv2.cvtColor(base, cv2.COLOR_RGB2BGR)
    detectores = [cv2.QRCodeDetector()]
    if hasattr(cv2, "QRCodeDetectorAruco"):
        detectores.append(cv2.QRCodeDetectorAruco())
    for escala in (1.0, 0.6, 0.4, 0.25):
        img = base if escala == 1.0 else cv2.resize(base, None, fx=escala, fy=escala, interpolation=cv2.INTER_AREA)
        for det in detectores:
            try:
                val, _, _ = det.detectAndDecode(img)
            except cv2.error:
                continue
            if val == texto:
                return True
    return False


# ---------------------------------------------------------------- principal
def _render(matrix, shape, size, fg, bg, dots, transparent, shape_file, logo_file, qz, density, deco_color, url_seed, use_image_colors):
    n = len(matrix)
    if shape == "cuadrado":
        m = max(3, size // (n + 8))
        lado = (n + 8) * m
        canvas = Image.new("RGBA", (lado, lado), bg + (255,))
        _draw_qr(canvas, matrix, 4 * m, 4 * m, m, fg + (255,), dots)
        if logo_file:
            _logo(canvas, logo_file, 4 * m, 4 * m, n * m, bg + (255,))
        return canvas

    S = size
    if shape == "imagen":
        if not shape_file:
            raise UserError("Sube primero la imagen que quieres usar como forma.")
        soft, color_img = _image_mask(shape_file, S)
    else:
        soft, color_img = _builtin_mask(shape, S)
    mask_bool = np.array(soft) > 200

    m, qx, qy = _place(mask_bool, n + 2 * qz)
    lado = (n + 2 * qz) * m
    canvas = Image.new("RGBA", (S, S), (255, 255, 255, 255) if not transparent else (0, 0, 0, 0))
    canvas.paste(Image.new("RGBA", (S, S), bg + (255,)), mask=soft)

    img_arr = np.array(color_img) if (color_img is not None and use_image_colors) else None

    def color_fn(cx, cy):
        if img_arr is not None:
            r, g, b, _ = (int(v) for v in img_arr[cy, cx])
            lum = _lum((r, g, b))
            if lum > 0.6:  # muy claro: oscurecer para que se vea
                k = 0.6 / max(lum, 1e-3)
                r, g, b = int(r * k), int(g * k), int(b * k)
            return (r, g, b, 255)
        return deco_color + (255,)

    if density > 0:
        rng = random.Random(url_seed)
        _decorate(
            canvas, mask_bool, m, qx % m, qy % m,
            (qx, qy, qx + lado, qy + lado), rng, density, dots, color_fn,
        )

    qr_x, qr_y = qx + qz * m, qy + qz * m
    _draw_qr(canvas, matrix, qr_x, qr_y, m, fg + (255,), dots)
    if logo_file:
        _logo(canvas, logo_file, qr_x, qr_y, n * m, bg + (255,))
    return canvas


def make_qr(url, shape="corazon", fg="#1b1b1b", bg="#ffffff", deco="#1b1b1b", dots="cuadrados",
            size=1400, transparent=True, shape_file=None, logo_file=None, use_image_colors=False):
    url = (url or "").strip()
    if not url:
        raise UserError("Escribe el enlace que quieres convertir en QR.")
    if len(url) > 900:
        raise UserError("Ese enlace es muy largo para un QR bonito. Acórtalo (por ejemplo con un acortador de enlaces).")
    if shape not in SHAPES:
        raise UserError("Forma desconocida.")
    if dots not in ("cuadrados", "redondos"):
        dots = "cuadrados"

    fg_c, bg_c, deco_c = _color(fg, "los puntos"), _color(bg, "el fondo"), _color(deco, "la decoración")
    if _lum(bg_c) - _lum(fg_c) < 0.45:
        raise UserError("Los puntos del QR deben ser bastante más oscuros que el fondo para que el celular los lea.")

    size = max(600, min(int(size), 2400))
    qr = segno.make(url, error="h", boost_error=False)
    matrix = [[bool(v) for v in row] for row in qr.matrix]
    seed = int(hashlib.sha256(url.encode()).hexdigest()[:12], 16)

    # Se prueba el QR decorado; si un lector no lo entiende, se va simplificando.
    intentos = [(3, 0.5), (4, 0.4), (5, 0.25), (6, 0.0)]
    for i, (qz, densidad) in enumerate(intentos):
        for f in (shape_file, logo_file):
            if f:
                f.stream.seek(0)
        img = _render(matrix, shape, size, fg_c, bg_c, dots, transparent, shape_file, logo_file,
                      qz, densidad, deco_c, seed, use_image_colors)
        ok = verify(img, url)
        if ok or shape == "cuadrado":
            break
    nota = ""
    if ok and shape != "cuadrado" and densidad < 0.5:
        nota = "Quité algo de decoración para que cualquier celular lo lea sin problemas."
    salida = io.BytesIO()
    img.save(salida, "PNG", optimize=True)
    salida.seek(0)
    return salida, ok, nota

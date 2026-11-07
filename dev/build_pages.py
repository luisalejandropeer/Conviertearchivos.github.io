"""Genera las páginas HTML de static/ (menú, 4 herramientas de unir, QR y privacidad).
Uso:  python dev/build_pages.py
Si quieres cambiar textos o colores de las páginas, edita este archivo y vuelve a ejecutarlo.
"""
import os

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
SITE = "Convierte Archivos"
# Pon aquí tu correo si quieres que aparezca en la página de privacidad (déjalo vacío para no mostrar ninguno).
CONTACT_EMAIL = ""
# ID de editor de Google AdSense (ca-pub-...). Si está vacío, no se agrega el código de AdSense a las páginas.
ADSENSE_CLIENT = "ca-pub-6011165604946199"
ADSENSE_SNIPPET = (
    f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={ADSENSE_CLIENT}"\n'
    '     crossorigin="anonymous"></script>\n'
    if ADSENSE_CLIENT else ""
)

HEAD = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="theme-color" content="#4f8cff">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E{fav}%3C/text%3E%3C/svg%3E">
<link rel="stylesheet" href="css/style.css">
{adsense}</head>
<body class="{theme}">
<header class="top"><div class="wrap">
  <a class="brand" href="index.html">🧰 {site}</a>
  {homebtn}
</div></header>
"""
HOMEBTN = '<a class="home-btn" href="index.html">🏠 Inicio</a>'

FOOT = """
<footer class="foot"><div class="wrap">
  <p>{site} · Gratis y fácil para todos 💙</p>
  <p><a href="index.html">Inicio</a> · <a href="privacidad.html">Privacidad</a></p>
</div></footer>
<script src="js/config.js"></script>
<script src="js/ads.js"></script>
{scripts}
</body>
</html>
"""


def page(filename, title, desc, theme, fav, body, scripts="", homebtn=HOMEBTN):
    html = HEAD.format(title=title, desc=desc, theme=theme, fav=fav, site=SITE, homebtn=homebtn, adsense=ADSENSE_SNIPPET)
    html += body + FOOT.format(site=SITE, scripts=scripts)
    with open(os.path.join(OUT, filename), "w", encoding="utf-8") as f:
        f.write(html)
    print("escrito", filename)


# ------------------------------------------------------------------ menú principal
TOOLS = [
    ("imagenes.html", "c-imagenes", "🖼️", "Fotos a PDF", "Junta tus fotos e imágenes en un solo PDF"),
    ("pdf.html", "c-pdf", "📕", "Unir PDF", "Junta varios PDF en uno solo"),
    ("word.html", "c-word", "📘", "Unir Word", "Junta varios documentos de Word en uno"),
    ("excel.html", "c-excel", "📗", "Unir Excel", "Junta varios archivos de Excel en uno"),
    ("qr.html", "c-qr", "🔳", "Crear QR", "Haz un QR con forma de corazón, estrella o tu dibujo"),
]
cards = "\n".join(
    f'    <a class="menu-card {c}" href="{href}"><span class="emoji">{e}</span><h2>{t}</h2><p>{d}</p><span class="go">¡Entrar!</span></a>'
    for href, c, e, t, d in TOOLS
)
page(
    "index.html",
    f"{SITE} – Unir PDF, Word, Excel, fotos a PDF y crear QR gratis",
    "Herramientas gratis y muy fáciles: convierte fotos a PDF, une PDF, Word y Excel, y crea códigos QR con formas.",
    "", "🧰",
    f"""
<div class="ad-slot" data-slot="top"></div>
<main class="wrap">
  <section class="hero">
    <h1>¿Qué quieres hacer hoy? 😊</h1>
    <p>Toca una de las cajas de colores</p>
  </section>
  <nav class="menu" aria-label="Herramientas">
{cards}
  </nav>
</main>
<div class="ad-slot spaced" data-slot="bottom"></div>
""",
    homebtn="",
)


# ------------------------------------------------------------------ páginas de unir
def merge_page(filename, theme, emoji, title, lead, desc, accept, accept_label, endpoint, out_name, icon,
               min_files, drop_text, options_html="", extra_js="", thumbs=False, rotate=False, show_pages=False,
               note="", ordering_hint="Arrastra las tarjetas para cambiarlas de lugar, o usa las flechas ⬅️ ➡️."):
    accept_js = "[" + ",".join(f'"{a}"' for a in accept) + "]"
    options = f'<section class="panel"><div class="options">{options_html}</div></section>' if options_html else ""
    body = f"""
<div class="ad-slot" data-slot="top"></div>
<main class="wrap tool">
  <h1>{emoji} {title}</h1>
  <p class="lead">{lead}</p>
  <ol class="steps">
    <li><b>1</b> Elige tus archivos</li>
    <li><b>2</b> Ponlos en orden</li>
    <li><b>3</b> ¡Toca el botón grande!</li>
  </ol>

  <div id="drop" class="dropzone" role="button" tabindex="0" aria-label="Elegir archivos">
    <div class="big-emoji">{emoji}</div>
    <button type="button" class="btn big" tabindex="-1">📂 Elegir archivos</button>
    <p>{drop_text}</p>
    <input id="file-input" type="file" multiple>
  </div>

  <section id="list-area" class="panel" hidden style="margin-top:18px">
    <div class="toolbar">
      <span id="count" class="count"></span>
      <button id="add-more" type="button" class="btn soft">➕ Agregar más</button>
      <button id="sort-az" type="button" class="btn soft">🔤 A → Z</button>
      <button id="sort-za" type="button" class="btn soft">🔤 Z → A</button>
      <button id="reverse" type="button" class="btn soft">🔃 Al revés</button>
      <button id="clear" type="button" class="btn soft">🗑️ Borrar todo</button>
    </div>
    <ul id="list" class="list"></ul>
    <p class="hint">{ordering_hint} El <b>1</b> es lo primero que saldrá.</p>
  </section>

  {options}
  {f'<div class="note">{note}</div>' if note else ''}

  <div class="go-row"><button id="go" type="button" class="btn big" disabled>✨ ¡Unir ahora!</button></div>
  <div id="status" class="status" role="status" aria-live="polite"></div>
</main>
<div class="ad-slot spaced" data-slot="bottom"></div>
"""
    scripts = f"""<script src="vendor/Sortable.min.js"></script>
<script src="js/merger.js"></script>
<script>
new FileMerger({{
  accept: {accept_js}, acceptLabel: "{accept_label}", endpoint: "{endpoint}", outName: "{out_name}",
  icon: "{icon}", minFiles: {min_files}, thumbs: {str(thumbs).lower()}, rotate: {str(rotate).lower()}, showPages: {str(show_pages).lower()},
  extraFields: function () {{ {extra_js} }}
}});
</script>"""
    page(filename, f"{title} gratis – {SITE}", desc, theme, emoji, body, scripts)


merge_page(
    "imagenes.html", "theme-imagenes", "🖼️", "Fotos a PDF",
    "Junta todas tus fotos e imágenes en un solo PDF.",
    "Convierte fotos e imágenes (JPG, PNG, WEBP, GIF, HEIC, TIFF...) a un solo PDF, gratis. Ordénalas y gíralas fácilmente.",
    [".jpg", ".jpeg", ".jfif", ".png", ".webp", ".gif", ".bmp", ".tif", ".tiff", ".heic", ".heif", ".ico", ".avif"],
    "fotos e imágenes (JPG, PNG, WEBP, GIF, HEIC, TIFF, BMP…)",
    "/api/imagenes-a-pdf", "mis-imagenes.pdf", "🖼️", 1,
    "o arrastra tus fotos hasta aquí. Sirven fotos de todo tipo: JPG, PNG, WEBP, GIF, HEIC del iPhone, TIFF…",
    options_html="""
      <label class="field">Tamaño de la hoja
        <select id="opt-page">
          <option value="auto">Igual que cada foto</option>
          <option value="a4">Hoja A4</option>
          <option value="carta">Hoja Carta</option>
        </select></label>
      <label class="field">Espacio en los bordes
        <select id="opt-margin">
          <option value="0">Sin espacio</option>
          <option value="1">Poquito</option>
          <option value="2">Mucho</option>
        </select></label>""",
    extra_js='return { page: document.getElementById("opt-page").value, margin: document.getElementById("opt-margin").value };',
    thumbs=True, rotate=True,
    ordering_hint="Arrastra las fotos para cambiarlas de lugar, usa ⬅️ ➡️ para moverlas y 🔄 para girarlas.",
)

merge_page(
    "pdf.html", "theme-pdf", "📕", "Unir PDF",
    "Junta varios PDF en un solo PDF.",
    "Une varios archivos PDF en uno solo, gratis y en el orden que tú quieras.",
    [".pdf"], "archivos PDF", "/api/unir-pdf", "pdfs-unidos.pdf", "📕", 2,
    "o arrastra tus PDF hasta aquí. Elige al menos 2.",
    show_pages=True,
)

merge_page(
    "word.html", "theme-word", "📘", "Unir Word",
    "Junta varios documentos de Word en uno solo.",
    "Une varios documentos de Word (.docx) en un solo documento, gratis y en el orden que quieras.",
    [".docx", ".docm", ".doc"], "documentos de Word (.docx)", "/api/unir-word", "documentos-unidos.docx", "📘", 2,
    "o arrastra tus documentos hasta aquí. Elige al menos 2.",
    options_html="""
      <label class="check"><input type="checkbox" id="opt-break" checked> Empezar cada documento en una hoja nueva</label>""",
    extra_js='return { page_break: document.getElementById("opt-break").checked ? "1" : "0" };',
    note="💡 Funciona con documentos <b>.docx</b>. Si tienes uno antiguo (.doc), ábrelo en Word y guárdalo como .docx.",
)

merge_page(
    "excel.html", "theme-excel", "📗", "Unir Excel",
    "Junta varios archivos de Excel en uno solo.",
    "Une varios archivos de Excel (.xlsx) en uno solo, conservando colores y formato, en el orden que quieras.",
    [".xlsx", ".xlsm", ".xls"], "archivos de Excel (.xlsx)", "/api/unir-excel", "excel-unido.xlsx", "📗", 2,
    "o arrastra tus archivos de Excel hasta aquí. Elige al menos 2.",
    options_html="""
      <fieldset>
        <legend>¿Cómo los junto?</legend>
        <label class="radio"><input type="radio" name="mode" value="hojas" checked> Cada archivo en su propia hoja</label>
        <label class="radio"><input type="radio" name="mode" value="una"> Todo junto en una sola hoja, uno debajo del otro</label>
      </fieldset>""",
    extra_js='return { mode: document.querySelector("input[name=mode]:checked").value };',
    note="💡 Se conservan los datos, colores, bordes y celdas combinadas. Las <b>gráficas e imágenes</b> dentro del Excel no se copian. Usa archivos <b>.xlsx</b> (si es .xls antiguo, guárdalo como .xlsx).",
)

# ------------------------------------------------------------------ QR
SHAPE_BTNS = [
    ("corazon", "❤️", "Corazón"), ("estrella", "⭐", "Estrella"), ("circulo", "⚪", "Círculo"),
    ("flor", "🌸", "Flor"), ("gota", "💧", "Gota"), ("rombo", "🔶", "Rombo"),
    ("redondeado", "🟦", "Redondo"), ("cuadrado", "⬛", "Normal"), ("imagen", "🖼️", "Mi imagen"),
]
shape_html = "\n".join(
    f'<button type="button" class="shape-btn" data-shape="{k}" aria-pressed="false"><span class="e">{e}</span>{n}</button>'
    for k, e, n in SHAPE_BTNS
)
qr_body = f"""
<div class="ad-slot" data-slot="top"></div>
<main class="wrap tool">
  <h1>🔳 Crear QR con forma</h1>
  <p class="lead">Escribe un enlace y elige la forma que quieras. ¡Tu QR seguirá funcionando!</p>
  <div class="qr-layout">
    <div class="qr-form">
      <section class="panel field-wide">
        <label for="url">1. El enlace de internet</label>
        <input id="url" type="url" inputmode="url" autocomplete="off" placeholder="Por ejemplo: www.mipagina.com">
      </section>

      <section class="panel">
        <div class="field-wide"><span>2. Elige la forma</span></div>
        <div class="shapes" style="margin-top:10px">{shape_html}</div>
        <div id="image-shape-box" hidden style="margin-top:14px">
          <div class="file-pick">
            <button id="pick-shape" type="button" class="btn soft">📂 Subir mi imagen</button>
            <span id="shape-name" class="picked"></span>
            <input id="shape-input" type="file" accept="image/*">
          </div>
          <p class="hint">Mejor si es un dibujo o silueta sobre fondo blanco o transparente (un corazón, un gatito, un logo…). El QR tomará esa forma.</p>
          <label class="check" style="display:flex;gap:10px;align-items:center;margin-top:8px;font-weight:700"><input id="image-colors" type="checkbox" style="width:24px;height:24px"> Pintar la decoración con los colores de mi imagen</label>
        </div>
      </section>

      <section class="panel">
        <div class="field-wide"><span>3. Elige colores</span></div>
        <div class="swatches" id="swatches" style="margin:10px 0 14px"></div>
        <div class="colors">
          <label class="field-wide">QR <input id="fg" type="color" value="#1b1b1b"></label>
          <label class="field-wide" id="deco-box">Decoración <input id="deco" type="color" value="#1b1b1b"></label>
          <label class="field-wide">Fondo <input id="bg" type="color" value="#ffffff"></label>
        </div>
        <p class="hint">El QR siempre debe ser más oscuro que el fondo para que el celular lo lea.</p>
        <fieldset style="margin-top:14px">
          <legend>Estilo de los puntos</legend>
          <label class="radio" style="display:flex;gap:10px;align-items:center;font-weight:700"><input type="radio" name="dots" value="cuadrados" checked style="width:24px;height:24px"> ▪️ Cuadrados</label>
          <label class="radio" style="display:flex;gap:10px;align-items:center;font-weight:700"><input type="radio" name="dots" value="redondos" style="width:24px;height:24px"> ⚫ Redondos</label>
        </fieldset>
        <label style="display:flex;gap:10px;align-items:center;margin-top:14px;font-weight:700"><input id="transparent" type="checkbox" checked style="width:24px;height:24px"> Sin fondo fuera de la forma (transparente)</label>
      </section>

      <section class="panel">
        <div class="field-wide"><span>4. ¿Quieres una imagen en el centro? (opcional)</span></div>
        <div class="file-pick" style="margin-top:10px">
          <button id="pick-logo" type="button" class="btn soft">📂 Subir imagen</button>
          <button id="clear-logo" type="button" class="btn soft">❌ Quitar</button>
          <span id="logo-name" class="picked"></span>
          <input id="logo-input" type="file" accept="image/*">
        </div>
        <p class="hint">Un logo o carita pequeña en medio del QR. Se hace chiquita para que siga funcionando.</p>
      </section>

      <div class="go-row" style="margin:6px 0"><button id="go" type="button" class="btn big">✨ ¡Crear mi QR!</button></div>
      <div id="status" class="status" role="status" aria-live="polite"></div>
    </div>

    <aside class="panel qr-result" aria-live="polite">
      <div id="badge" class="badge" hidden></div>
      <div id="stage" class="qr-stage"><div class="empty">Tu QR aparecerá aquí 👇<br>cuando toques «Crear mi QR»</div></div>
      <p id="qr-note" class="hint" style="margin:0 0 10px"></p>
      <a id="download" class="btn big" href="#" download="mi-qr.png" hidden>⬇️ Descargar mi QR</a>
    </aside>
  </div>
</main>
<div class="ad-slot spaced" data-slot="bottom"></div>
"""
page(
    "qr.html", f"Crear QR con forma de corazón, estrella o tu imagen – {SITE}",
    "Crea códigos QR gratis con forma de corazón, estrella, flor o de tu propia imagen, con colores y logo. Siguen funcionando.",
    "theme-qr", "🔳", qr_body, '<script src="js/qr.js"></script>',
)

# ------------------------------------------------------------------ privacidad
page(
    "privacidad.html", f"Privacidad – {SITE}", "Cómo cuidamos tus archivos y qué datos usa este sitio.", "", "🔒",
    f"""
<main class="wrap prose">
  <h1>🔒 Privacidad</h1>
  <p><b>Tus archivos son tuyos.</b> Cuando unes fotos, PDF, Word o Excel, o creas un QR, el archivo se envía a nuestro servidor, se procesa en la memoria y el resultado se te devuelve enseguida. <b>No guardamos tus archivos ni tus enlaces.</b></p>
  <h2>Anuncios</h2>
  <p>Este sitio es gratis gracias a los anuncios. Los anuncios los muestra Google AdSense, que puede usar cookies para mostrar anuncios. Puedes ver y cambiar tus preferencias en la configuración de anuncios de Google.</p>
  <h2>Datos</h2>
  <p>No pedimos nombre, correo ni registro.{f' Si tienes dudas, escríbenos a <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>.' if CONTACT_EMAIL else ''}</p>
  <p><a class="btn" href="index.html" style="text-decoration:none;display:inline-block">🏠 Volver al inicio</a></p>
</main>
""",
)

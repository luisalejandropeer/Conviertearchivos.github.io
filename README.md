# 🧰 Convierte Archivos

Sitio web con 5 herramientas muy sencillas (colores claros, botones grandes, pensado para que hasta un niño de primaria lo use):

| Página | Qué hace |
|---|---|
| `imagenes.html` | Fotos de cualquier tipo (JPG, PNG, WEBP, GIF, HEIC del iPhone, TIFF, BMP…) → **un solo PDF**. Se pueden ordenar (arrastrando o con flechas), girar y elegir hoja (igual que la foto / A4 / Carta) y márgenes. |
| `pdf.html` | Une varios **PDF** en uno (muestra cuántas páginas tiene cada uno). |
| `word.html` | Une varios **Word (.docx)** en uno, con opción de empezar cada documento en hoja nueva. Conserva estilos, tablas e imágenes. |
| `excel.html` | Une varios **Excel (.xlsx)**: cada archivo en sus hojas, o todo en una sola hoja. Conserva colores, bordes, anchos y celdas combinadas. |
| `qr.html` | **QR con forma** (corazón, estrella, flor, gota, círculo, rombo… o **tu propia imagen**), colores, puntos redondos/cuadrados y logo al centro. |

En todas las de unir se puede ordenar con: arrastrar, flechas ⬅️➡️, A→Z, Z→A, al revés, quitar, borrar todo.

## Cómo funciona el QR con forma (y por qué sigue funcionando)

El QR real va **completo** (con alta corrección de errores y su margen blanco) en el centro de la forma; el resto de la forma se rellena con puntos decorativos. Así nunca se pierden datos del QR. Además, **cada QR se "escanea" en el servidor antes de entregártelo** y la página muestra «✅ Probado». Si algún lector no lo entiende, el servidor simplifica la decoración automáticamente.

## Probarlo en tu computadora

```bash
pip install -r requirements.txt
python app.py            # abre http://localhost:5000
```

Pruebas automáticas:

```bash
python tests/test_app.py   # imágenes, PDF, Word, Excel, QR y páginas
python tests/test_qr.py .  # genera un QR de cada forma y comprueba que se lean
```

## Publicarlo en internet

Necesita un servidor con Python (no sirve un hosting solo de HTML como GitHub Pages o Netlify).

**Forma más fácil (Render, con plan gratis):**

1. Descomprime este ZIP y sube **el contenido de la carpeta** a un repositorio nuevo en [GitHub](https://github.com) (botón *Add file → Upload files*).
2. Entra a [render.com](https://render.com), crea cuenta con tu GitHub y elige **New → Blueprint**.
3. Selecciona tu repositorio. Render lee `render.yaml`, construye con el `Dockerfile` y te da un enlace `https://convierte-archivos-xxxx.onrender.com`.
4. (Opcional) En *Settings → Custom Domains* pon tu propio dominio. El HTTPS se activa solo.

En el plan gratis la página se "duerme" tras un rato sin visitas y la primera carga tarda ~1 minuto. Para que siempre responda rápido, pasa a un plan de pago.

Otras opciones: **Railway**, **Fly.io** o un VPS (con el `Dockerfile`, o sin Docker con `gunicorn -w 2 --threads 4 -t 120 app:app`).

Los archivos se procesan **en memoria** y no se guardan. El límite es 200 MB por envío (cámbialo en `app.py`, `MAX_CONTENT_LENGTH`).

## 💰 Anuncios (para ganar dinero)

1. Abre una cuenta en [Google AdSense](https://adsense.google.com) con tu dominio ya publicado. Google revisa el sitio y puede tardar días en aprobarlo (necesita una página de privacidad — ya incluida en `privacidad.html` — y contenido propio).
2. Crea 2 bloques de anuncios (arriba y abajo).
3. Edita **`static/js/config.js`** y pega tu `ca-pub-…` y los IDs de los bloques.

Mientras `adsenseClient` esté vacío no se muestra nada. Para ver dónde irán los anuncios: agrega `?ads=demo` al final de cualquier página. Los anuncios van arriba y abajo, **separados de los botones** para evitar clics accidentales (AdSense lo exige y más con niños). Importante: si el sitio va dirigido a menores de 13 años, AdSense exige marcarlo como "contenido dirigido a niños" y entonces solo muestra anuncios no personalizados (ganas menos por clic). Revisa sus políticas antes de decidir.

## Cambiar textos o colores

- Colores y estilo: `static/css/style.css` (variables al inicio).
- Textos de las páginas: `dev/build_pages.py`, y luego `python dev/build_pages.py` para regenerar los HTML.

## Límites conocidos

- Word: solo `.docx` (los `.doc` antiguos hay que guardarlos como `.docx`). Si dos documentos usan numeraciones/estilos muy distintos, Word puede acomodar la numeración de listas al estilo del primero.
- Excel: solo `.xlsx`. Se copian datos, fórmulas, formato, anchos y celdas combinadas; **no** se copian gráficas, imágenes ni macros. Si una fórmula apunta a otra hoja, revisa que sigan bien los nombres.
- PDF con contraseña: hay que quitarla antes.

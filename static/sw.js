/* Service worker de Convierte Archivos.
   Guarda las páginas, estilos e iconos para que la app abra al instante (aunque el servidor esté despertando)
   y no se vea en blanco sin internet. Los archivos que subes NUNCA se guardan: las herramientas siempre
   hablan con el servidor (/api/...) y los anuncios de Google no pasan por aquí.

   Si cambias algo del sitio, sube el número de VERSION para que todos reciban la versión nueva. */
const VERSION = "convierte-v1";
const SHELL = [
  "/", "/index.html", "/imagenes.html", "/pdf.html", "/word.html", "/excel.html", "/qr.html", "/privacidad.html",
  "/css/style.css", "/js/config.js", "/js/ads.js", "/js/merger.js", "/js/qr.js", "/js/pwa.js",
  "/vendor/Sortable.min.js", "/icons/icon-192.png", "/icons/icon-512.png", "/manifest.webmanifest",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(VERSION)
      .then((cache) => Promise.allSettled(SHELL.map((url) => cache.add(url))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== VERSION).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;                       // los envíos de archivos (POST) van directo al servidor
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;        // anuncios de Google y otros sitios: no los tocamos
  if (url.pathname.startsWith("/api/") || url.pathname === "/ads.txt" || url.pathname === "/sw.js") return;

  // Responde al instante con lo guardado y, en segundo plano, baja la versión más nueva para la próxima vez.
  event.respondWith(
    caches.open(VERSION).then((cache) =>
      cache.match(req, { ignoreSearch: true }).then((cached) => {
        const network = fetch(req)
          .then((res) => {
            if (res && res.ok && res.type === "basic") cache.put(req, res.clone());
            return res;
          })
          .catch(() => null);

        if (cached) { event.waitUntil(network); return cached; }
        return network.then((res) => {
          if (res) return res;
          // Sin internet y sin copia guardada: al menos mostramos el menú.
          return req.mode === "navigate" ? cache.match("/index.html") : Response.error();
        });
      })
    )
  );
});

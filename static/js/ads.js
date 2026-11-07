/* Muestra los anuncios de Google AdSense en los espacios <div class="ad-slot" data-slot="top|bottom|middle">. */
(function () {
  var cfg = window.SITE_CONFIG || {};
  var slots = document.querySelectorAll(".ad-slot");
  var demo = /[?&]ads=demo/.test(location.search);

  if (!cfg.adsenseClient) {
    slots.forEach(function (el) {
      if (demo) { el.classList.add("demo"); el.textContent = "📢 Aquí aparecerá un anuncio"; }
      else el.remove();
    });
    return;
  }
  // Si el código de AdSense ya está en el <head> de la página, no lo cargamos otra vez.
  if (!document.querySelector('script[src*="adsbygoogle.js"]')) {
    var s = document.createElement("script");
    s.async = true;
    s.crossOrigin = "anonymous";
    s.src = "https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=" + encodeURIComponent(cfg.adsenseClient);
    document.head.appendChild(s);
  }

  slots.forEach(function (el) {
    var id = (cfg.adSlots || {})[el.dataset.slot];
    if (!id) {
      // Aún sin ID de bloque: con ?ads=demo se muestra dónde irá el anuncio; si no, se quita el espacio.
      if (demo) { el.classList.add("demo"); el.textContent = "📢 Aquí aparecerá un anuncio"; }
      else el.remove();
      return;
    }
    var ins = document.createElement("ins");
    ins.className = "adsbygoogle";
    ins.style.display = "block";
    ins.setAttribute("data-ad-client", cfg.adsenseClient);
    ins.setAttribute("data-ad-slot", id);
    ins.setAttribute("data-ad-format", "auto");
    ins.setAttribute("data-full-width-responsive", "true");
    el.appendChild(ins);
    try { (window.adsbygoogle = window.adsbygoogle || []).push({}); } catch (e) {}
  });
})();

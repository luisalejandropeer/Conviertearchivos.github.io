/* Convierte Archivos como app: registra el service worker y muestra el botón "Instalar la app". */
(function () {
  // 1) Service worker (necesita HTTPS; en localhost también funciona)
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", function () {
      navigator.serviceWorker.register("/sw.js").catch(function () {});
    });
  }

  // 2) Botón de instalar (solo existe en el menú principal)
  var box = document.getElementById("install-box");
  if (!box) return;
  var btn = document.getElementById("install-btn");
  var iosHint = document.getElementById("install-ios");

  var standalone = (window.matchMedia && window.matchMedia("(display-mode: standalone)").matches) || window.navigator.standalone === true;
  if (standalone) return; // ya está abierta como app

  var deferred = null;
  window.addEventListener("beforeinstallprompt", function (e) {
    e.preventDefault();          // guardamos el aviso para mostrarlo con nuestro botón grande
    deferred = e;
    btn.hidden = false;
    iosHint.hidden = true;
    box.hidden = false;
  });
  btn.addEventListener("click", function () {
    if (!deferred) return;
    deferred.prompt();
    deferred.userChoice.then(function () { deferred = null; box.hidden = true; });
  });
  window.addEventListener("appinstalled", function () { box.hidden = true; });

  // iPhone / iPad: Safari no tiene botón automático, así que explicamos los pasos.
  var ua = navigator.userAgent || "";
  var isIOS = /iPhone|iPad|iPod/i.test(ua) || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
  if (isIOS) {
    btn.hidden = true;
    iosHint.hidden = false;
    box.hidden = false;
  }
})();

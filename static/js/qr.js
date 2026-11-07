/* Página del creador de QR con formas. */
(function () {
  "use strict";
  var $ = function (id) { return document.getElementById(id); };
  var state = { shape: "corazon", dots: "cuadrados", fg: "#1b1b1b", bg: "#ffffff", deco: "#1b1b1b", decoSame: true, blobUrl: null };
  var shapeFile = null, logoFile = null;

  /* ---------- formas ---------- */
  var shapeBtns = document.querySelectorAll(".shape-btn");
  function setShape(s) {
    state.shape = s;
    shapeBtns.forEach(function (b) { b.setAttribute("aria-pressed", b.dataset.shape === s ? "true" : "false"); });
    $("image-shape-box").hidden = s !== "imagen";
    $("deco-box").hidden = s === "cuadrado";
  }
  shapeBtns.forEach(function (b) { b.addEventListener("click", function () { setShape(b.dataset.shape); }); });
  setShape("corazon");

  /* ---------- colores ---------- */
  var PALETTES = [
    { fg: "#1b1b1b", deco: "#1b1b1b", bg: "#ffffff", name: "Clásico" },
    { fg: "#c2185b", deco: "#f06292", bg: "#fff5f8", name: "Rosa" },
    { fg: "#1565c0", deco: "#64b5f6", bg: "#f3f9ff", name: "Azul" },
    { fg: "#2e7d32", deco: "#81c784", bg: "#f4fbf4", name: "Verde" },
    { fg: "#6a1b9a", deco: "#ba68c8", bg: "#faf5ff", name: "Morado" },
    { fg: "#e65100", deco: "#ffb74d", bg: "#fffaf3", name: "Naranja" }
  ];
  var sw = $("swatches");
  PALETTES.forEach(function (p, i) {
    var b = document.createElement("button");
    b.type = "button"; b.className = "sw"; b.title = p.name; b.setAttribute("aria-label", "Colores " + p.name);
    b.style.background = "linear-gradient(135deg," + p.fg + " 50%," + p.deco + " 50%)";
    b.setAttribute("aria-pressed", i === 0 ? "true" : "false");
    b.addEventListener("click", function () {
      state.fg = p.fg; state.deco = p.deco; state.bg = p.bg;
      $("fg").value = p.fg; $("deco").value = p.deco; $("bg").value = p.bg;
      Array.prototype.forEach.call(sw.children, function (c) { c.setAttribute("aria-pressed", c === b ? "true" : "false"); });
    });
    sw.appendChild(b);
  });
  ["fg", "deco", "bg"].forEach(function (id) {
    $(id).addEventListener("input", function () {
      state[id] = $(id).value;
      Array.prototype.forEach.call(sw.children, function (c) { c.setAttribute("aria-pressed", "false"); });
    });
  });

  /* ---------- puntos redondos / cuadrados ---------- */
  document.querySelectorAll("input[name=dots]").forEach(function (r) {
    r.addEventListener("change", function () { state.dots = r.value; });
  });

  /* ---------- archivos ---------- */
  function picker(btnId, inputId, labelId, setter) {
    $(btnId).addEventListener("click", function () { $(inputId).click(); });
    $(inputId).addEventListener("change", function () {
      var f = $(inputId).files[0]; setter(f || null);
      $(labelId).textContent = f ? "✅ " + f.name : "";
    });
  }
  picker("pick-shape", "shape-input", "shape-name", function (f) { shapeFile = f; });
  picker("pick-logo", "logo-input", "logo-name", function (f) { logoFile = f; });
  $("clear-logo").addEventListener("click", function () { logoFile = null; $("logo-input").value = ""; $("logo-name").textContent = ""; });

  /* ---------- crear ---------- */
  var go = $("go"), status = $("status"), stage = $("stage"), badge = $("badge"), dl = $("download");

  function normalizeUrl(v) {
    v = v.trim();
    if (!v) return "";
    if (/^[a-z][a-z0-9+.-]*:/i.test(v)) return v;       // ya trae https:, mailto:, tel:...
    return "https://" + v;
  }
  function showError(msg) { status.className = "status error"; status.textContent = "😕 " + msg; }

  go.addEventListener("click", function () {
    var url = normalizeUrl($("url").value);
    if (!url) { showError("Escribe primero el enlace de internet que quieres convertir en QR."); $("url").focus(); return; }
    if (state.shape === "imagen" && !shapeFile) { showError("Elegiste «Mi imagen». Sube la imagen que quieres usar como forma."); return; }

    go.disabled = true;
    status.className = "status"; status.innerHTML = '<span class="spinner"></span>Creando tu QR y probando que funcione…';
    var fd = new FormData();
    fd.append("url", url);
    fd.append("shape", state.shape);
    fd.append("dots", state.dots);
    fd.append("fg", state.fg);
    fd.append("bg", state.bg);
    fd.append("deco", state.deco);
    fd.append("transparent", $("transparent").checked ? "1" : "0");
    fd.append("image_colors", $("image-colors").checked ? "1" : "0");
    if (shapeFile && state.shape === "imagen") fd.append("shape_image", shapeFile);
    if (logoFile) fd.append("logo", logoFile);

    fetch("/api/qr", { method: "POST", body: fd }).then(function (r) {
      if (!r.ok) return r.json().catch(function () { return {}; }).then(function (j) { throw new Error(j.error || "No se pudo crear el QR."); });
      var ok = r.headers.get("X-QR-Verified") === "1", note = "";
      try { note = JSON.parse(r.headers.get("X-QR-Note") || '""'); } catch (e) {}
      return r.blob().then(function (b) { return { blob: b, ok: ok, note: note }; });
    }).then(function (res) {
      if (state.blobUrl) URL.revokeObjectURL(state.blobUrl);
      state.blobUrl = URL.createObjectURL(res.blob);
      stage.innerHTML = ""; var img = document.createElement("img"); img.src = state.blobUrl; img.alt = "Tu código QR"; stage.appendChild(img);
      badge.hidden = false;
      badge.className = "badge " + (res.ok ? "ok" : "warn");
      badge.textContent = res.ok ? "✅ ¡Probado! Este QR sí se puede leer" : "⚠️ No logré comprobarlo: prueba con otra forma o colores más oscuros";
      $("qr-note").textContent = res.note || "";
      dl.href = state.blobUrl; dl.hidden = false;
      status.className = "status"; status.textContent = "";
    }).catch(function (e) {
      showError(e.message === "Failed to fetch" ? "No pude conectarme. Revisa tu internet e inténtalo otra vez." : e.message);
    }).then(function () { go.disabled = false; });
  });
})();

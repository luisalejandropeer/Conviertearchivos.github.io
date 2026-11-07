/* Lista de archivos que se puede ordenar (arrastrar, flechas, A-Z) y enviar al servidor para unirlos. */
(function () {
  "use strict";

  function fmtSize(b) {
    if (b < 1024) return b + " B";
    if (b < 1048576) return Math.round(b / 1024) + " KB";
    return (b / 1048576).toFixed(1) + " MB";
  }
  function extOf(name) { var i = name.lastIndexOf("."); return i < 0 ? "" : name.slice(i).toLowerCase(); }

  window.FileMerger = function (cfg) {
    var $ = function (id) { return document.getElementById(id); };
    var drop = $("drop"), input = $("file-input"), listArea = $("list-area"), list = $("list"),
        countEl = $("count"), goBtn = $("go"), status = $("status");
    var items = [];          // {id, file, rot, thumbUrl, pages}
    var nextId = 1, busy = false, lastBlob = null, lastName = "";
    var accept = cfg.accept.map(function (e) { return e.toLowerCase(); });

    input.setAttribute("accept", cfg.accept.join(","));
    input.multiple = true;

    /* ---------- agregar archivos ---------- */
    function addFiles(fileList) {
      var rejected = [];
      Array.prototype.forEach.call(fileList, function (f) {
        if (accept.indexOf(extOf(f.name)) < 0) { rejected.push(f.name); return; }
        var it = { id: nextId++, file: f, rot: 0, thumbUrl: null, pages: null };
        if (cfg.thumbs) it.thumbUrl = URL.createObjectURL(f);
        items.push(it);
        if (cfg.showPages) fetchPages(it);
      });
      if (rejected.length) {
        showError("Estos archivos no son del tipo correcto y no los agregué: " + rejected.join(", ") +
                  ".\nAquí puedes usar: " + cfg.acceptLabel + ".");
      } else clearStatus();
      render();
    }

    function fetchPages(it) {
      var fd = new FormData(); fd.append("files", it.file);
      fetch("/api/pdf-info", { method: "POST", body: fd }).then(function (r) { return r.json(); })
        .then(function (j) { it.pages = j.pages || null; it.pagesErr = j.error || null; render(); })
        .catch(function () {});
    }

    /* ---------- dibujar ---------- */
    function render() {
      list.innerHTML = "";
      items.forEach(function (it, i) {
        var li = document.createElement("li");
        li.className = "item"; li.dataset.id = it.id;

        var num = document.createElement("span"); num.className = "num"; num.textContent = i + 1;
        var th = document.createElement("div"); th.className = "thumb";
        if (it.thumbUrl) {
          var img = document.createElement("img"); img.alt = "Vista de " + it.file.name; img.src = it.thumbUrl;
          img.style.transform = "rotate(" + it.rot + "deg)" + (it.rot % 180 ? " scale(.75)" : "");
          img.onerror = function () { serverThumb(it, img, th); };
          th.appendChild(img);
        } else {
          var ic = document.createElement("span"); ic.className = "icon"; ic.textContent = cfg.icon; th.appendChild(ic);
        }
        var name = document.createElement("div"); name.className = "name"; name.textContent = it.file.name; name.title = it.file.name;
        var meta = document.createElement("div"); meta.className = "meta";
        meta.textContent = fmtSize(it.file.size) + (it.pages ? " · " + it.pages + (it.pages === 1 ? " página" : " páginas") : "");
        if (it.pagesErr) meta.textContent = "⚠️ " + it.pagesErr;

        var acts = document.createElement("div"); acts.className = "acts";
        acts.appendChild(mini("⬅️", "Mover antes", i === 0, function () { move(i, i - 1); }));
        acts.appendChild(mini("➡️", "Mover después", i === items.length - 1, function () { move(i, i + 1); }));
        if (cfg.rotate) acts.appendChild(mini("🔄", "Girar", false, function () { it.rot = (it.rot + 90) % 360; render(); }));
        var del = mini("❌", "Quitar", false, function () { remove(it.id); }); del.classList.add("del");
        acts.appendChild(del);

        li.append(num, th, name, meta, acts);
        list.appendChild(li);
      });
      var n = items.length;
      countEl.textContent = n === 0 ? "" : (n === 1 ? "1 archivo" : n + " archivos");
      listArea.hidden = n === 0;
      goBtn.disabled = busy || n < cfg.minFiles;
      var need = cfg.minFiles - n;
      goBtn.title = need > 0 ? "Agrega " + (need === 1 ? "1 archivo más" : need + " archivos más") : "";
    }

    function mini(emoji, label, disabled, fn) {
      var b = document.createElement("button");
      b.type = "button"; b.className = "mini"; b.textContent = emoji;
      b.title = label; b.setAttribute("aria-label", label); b.disabled = !!disabled;
      b.addEventListener("click", function (e) { e.stopPropagation(); fn(); });
      return b;
    }

    function serverThumb(it, img, th) {  // HEIC, TIFF... que el navegador no sabe mostrar
      if (it.serverTried) { img.remove(); var ic = document.createElement("span"); ic.className = "icon"; ic.textContent = "🖼️"; th.appendChild(ic); return; }
      it.serverTried = true;
      var fd = new FormData(); fd.append("files", it.file);
      fetch("/api/miniatura", { method: "POST", body: fd }).then(function (r) { if (!r.ok) throw 0; return r.blob(); })
        .then(function (b) { it.thumbUrl = URL.createObjectURL(b); render(); })
        .catch(function () { img.onerror = null; img.remove(); var ic = document.createElement("span"); ic.className = "icon"; ic.textContent = "🖼️"; th.appendChild(ic); });
    }

    /* ---------- ordenar ---------- */
    function move(from, to) {
      if (to < 0 || to >= items.length) return;
      items.splice(to, 0, items.splice(from, 1)[0]); render();
    }
    function remove(id) {
      items = items.filter(function (x) { if (x.id === id && x.thumbUrl && x.file) URL.revokeObjectURL(x.thumbUrl); return x.id !== id; });
      clearStatus(); render();
    }
    function sortBy(dir) {
      var cmp = function (a, b) { return a.file.name.localeCompare(b.file.name, "es", { numeric: true, sensitivity: "base" }); };
      items.sort(function (a, b) { return dir * cmp(a, b); }); render();
    }
    $("sort-az").onclick = function () { sortBy(1); };
    $("sort-za").onclick = function () { sortBy(-1); };
    $("reverse").onclick = function () { items.reverse(); render(); };
    $("clear").onclick = function () { items.forEach(function (x) { if (x.thumbUrl) URL.revokeObjectURL(x.thumbUrl); }); items = []; clearStatus(); render(); };

    if (window.Sortable) {
      Sortable.create(list, {
        animation: 160, ghostClass: "sortable-ghost", chosenClass: "sortable-chosen",
        delay: 120, delayOnTouchOnly: true, filter: ".mini", preventOnFilter: false,
        onEnd: function (e) { if (e.oldIndex !== e.newIndex) move(e.oldIndex, e.newIndex); else render(); }
      });
    }

    /* ---------- elegir / soltar archivos ---------- */
    drop.addEventListener("click", function () { input.click(); });
    drop.addEventListener("keydown", function (e) { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); input.click(); } });
    input.addEventListener("change", function () { addFiles(input.files); input.value = ""; });
    ["dragenter", "dragover"].forEach(function (ev) { drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.add("over"); }); });
    ["dragleave", "drop"].forEach(function (ev) { drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.remove("over"); }); });
    drop.addEventListener("drop", function (e) { if (e.dataTransfer && e.dataTransfer.files.length) addFiles(e.dataTransfer.files); });
    $("add-more").onclick = function () { input.click(); };
    // soltar archivos en cualquier parte de la página
    window.addEventListener("dragover", function (e) { if (e.dataTransfer && Array.prototype.indexOf.call(e.dataTransfer.types || [], "Files") >= 0) e.preventDefault(); });
    window.addEventListener("drop", function (e) { if (e.dataTransfer && e.dataTransfer.files.length && !drop.contains(e.target)) { e.preventDefault(); addFiles(e.dataTransfer.files); } });

    /* ---------- mensajes ---------- */
    function clearStatus() { status.className = "status"; status.innerHTML = ""; }
    function showError(msg) {
      status.className = "status error"; status.textContent = "";
      msg.split("\n").forEach(function (line, i) { if (i) status.appendChild(document.createElement("br")); status.appendChild(document.createTextNode("😕 " + (i ? "" : "") + line)); });
    }

    /* ---------- unir ---------- */
    goBtn.addEventListener("click", function () {
      if (busy || items.length < cfg.minFiles) return;
      busy = true; render();
      status.className = "status"; status.innerHTML = '<span class="spinner"></span>Trabajando… ¡un momentito!';
      var fd = new FormData();
      items.forEach(function (it) { fd.append("files", it.file, it.file.name); });
      if (cfg.rotate) fd.append("rotations", JSON.stringify(items.map(function (it) { return it.rot; })));
      var extra = (cfg.extraFields && cfg.extraFields()) || {};
      Object.keys(extra).forEach(function (k) { fd.append(k, extra[k]); });

      fetch(cfg.endpoint, { method: "POST", body: fd }).then(function (r) {
        if (r.ok) return r.blob();
        return r.json().catch(function () { return {}; }).then(function (j) { throw new Error(j.error || "No se pudo completar. Inténtalo otra vez."); });
      }).then(function (blob) {
        lastBlob = blob; lastName = cfg.outName;
        download();
        status.className = "status ok"; status.innerHTML = "";
        var t = document.createElement("div"); t.textContent = "🎉 ¡Listo! Tu archivo se está descargando."; status.appendChild(t);
        var a = document.createElement("div"); a.className = "actions";
        var again = document.createElement("button"); again.className = "btn"; again.textContent = "⬇️ Descargar otra vez"; again.onclick = download;
        var fresh = document.createElement("button"); fresh.className = "btn soft"; fresh.textContent = "🔁 Empezar de nuevo"; fresh.onclick = function () { $("clear").click(); window.scrollTo({ top: 0, behavior: "smooth" }); };
        a.append(again, fresh); status.appendChild(a);
      }).catch(function (e) {
        showError(e.message === "Failed to fetch" ? "No pude conectarme. Revisa tu internet e inténtalo otra vez." : e.message);
      }).then(function () { busy = false; render(); });
    });

    function download() {
      if (!lastBlob) return;
      var url = URL.createObjectURL(lastBlob), a = document.createElement("a");
      a.href = url; a.download = lastName; document.body.appendChild(a); a.click(); a.remove();
      setTimeout(function () { URL.revokeObjectURL(url); }, 4000);
    }

    render();
  };
})();

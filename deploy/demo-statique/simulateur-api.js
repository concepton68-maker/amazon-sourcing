(function () {
  var D = JSON.parse(document.getElementById("donnees-demo").textContent);
  function rep(status, corps) { return new Response(JSON.stringify(corps), { status: status, headers: { "content-type": "application/json" } }); }
  var natif = window.fetch.bind(window);
  window.fetch = async function (entree, init) {
    init = init || {};
    var url = typeof entree === "string" ? entree : entree.url;
    var i = url.indexOf("/api/");
    if (i < 0) return natif(entree, init);
    var chemin = url.slice(i).split("?")[0];
    var m = (init.method || "GET").toUpperCase();
    await new Promise(function (r) { setTimeout(r, 120); });
    if (m === "GET") {
      if (chemin in D.get) return rep(200, D.get[chemin]);
      if (chemin.indexOf("/api/sourcing/traitements/") === 0 && !/\.csv$/.test(chemin)) return rep(200, D.sourcing.suivi);
      return rep(404, { detail: "DEMO_LECTURE_SEULE" });
    }
    if (m === "POST" && chemin === "/api/analyse") {
      var b = JSON.parse(init.body);
      var k = String(b.code).trim().toUpperCase() + "|" + b.marketplace + "|" + b.prix_achat;
      if (D.analyse[k] && !b.achat_ttc && b.regime_tva === "assujetti") return rep(200, D.analyse[k]);
      return rep(404, { detail: "DEMO_EXEMPLE" });
    }
    if (m === "POST" && chemin === "/api/sourcing/fichiers") return rep(201, D.sourcing.fichier);
    if (m === "POST" && /^\/api\/sourcing\/fichiers\/[^/]+\/traitements$/.test(chemin)) return rep(201, { traitement_id: D.sourcing.traitement_id });
    if (m === "PUT" && chemin === "/api/parametres") return rep(409, { detail: { code: "DEMO_LECTURE_SEULE", champ: "" } });
    return rep(409, { detail: "DEMO_LECTURE_SEULE" });
  };
  // les liens vers l'API (export CSV) ne mènent nulle part dans la démo
  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("a[href*='/api/']");
    if (a) { e.preventDefault(); }
  }, true);
})();

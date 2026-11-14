import json, os, sys, time
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2] / "backend"))
os.environ["AMZ_MODE"] = "dev"
from fastapi.testclient import TestClient
from sourcing.api import app_depuis_environnement
cl = TestClient(app_depuis_environnement())
H = {"x-syllig-vente": "1"}
out = {"get": {}, "analyse": {}, "sourcing": {}}
def g(u):
    r = cl.get(u); assert r.status_code == 200, (u, r.text); out["get"][u] = r.json(); return r.json()
for u in ["/api/moi", "/api/places", "/api/lots", "/api/parametres", "/api/stock", "/api/fournisseurs", "/api/bons",
          "/api/remboursements", "/api/conformite"]:
    g(u)
for l in out["get"]["/api/lots"]["lots"]:
    g(f"/api/lots/{l['id']}")
EXEMPLES = [("B0DEMO0001", 8.5), ("B0DEMO0002", 6.2), ("B0DEMO0003", 9.8), ("B0DEMO0004", 6.4), ("B0DEMO0005", 14.2),
            ("3700000000017", 8.5), ("2000000000015", 11.49)]
for code, prix in EXEMPLES:
    for mp in ["FR", "DE", "IT", "ES", "US", "UK"]:
        d = {"code": code, "marketplace": mp, "prix_achat": prix, "achat_ttc": False, "regime_tva": "assujetti", "taux_tva": None}
        r = cl.post("/api/analyse", json=d, headers=H)
        if r.status_code == 200:
            out["analyse"][f"{code}|{mp}|{prix}"] = r.json()
        else:
            print("analyse", code, mp, r.status_code, r.text[:100])
out["exemples"] = [{"code": c, "prix": p} for c, p in EXEMPLES]
with open(str(__import__("pathlib").Path(__file__).resolve().parents[2] / "docs" / "demo" / "catalogue-fournisseur-demo.csv"), "rb") as f:
    fi = cl.post("/api/sourcing/fichiers", files={"fichier": ("catalogue-fournisseur-demo.csv", f, "text/csv")}, headers=H).json()
out["sourcing"]["fichier"] = fi
t = cl.post(f"/api/sourcing/fichiers/{fi['fichier_id']}/traitements", headers=H, json={"colonnes": fi["colonnes"],
        "marketplace": "FR", "regime_tva": "assujetti", "achat_ttc": False, "prix_par_carton": False}).json()
for _ in range(100):
    s = cl.get(f"/api/sourcing/traitements/{t['traitement_id']}").json()
    if s["statut"] not in ("EN_COURS", "EN_ATTENTE"): break
    time.sleep(0.1)
out["sourcing"]["traitement_id"] = t["traitement_id"]; out["sourcing"]["suivi"] = s
print("sourcing", s["statut"], s["total"], s["faits"], len(s["resultats"]))
print("analyses", len(out["analyse"]))
json.dump(out, open(sys.argv[1], "w"), ensure_ascii=False)

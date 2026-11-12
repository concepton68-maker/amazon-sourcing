import { useEffect, useState } from "react";
import { Stock, lireStock } from "./api";
import { dateCourte, message, monnaie, t } from "./i18n";

export function StockVue() {
  const [s, setS] = useState<Stock | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  useEffect(() => { lireStock().then(setS).catch((e) => setErreur(e.message)); }, []);
  if (erreur) return <p role="alert" className="alerte">{t(`erreur.${erreur}`)}</p>;
  if (!s) return <p>{t("chargement")}</p>;
  return (
    <div className="vue">
      <div className="entete-vue">
        <h1>{t("stock.titre")}</h1>
        <span className="meta">{s.jour ? t("stock.photo", { jour: dateCourte(s.jour) }) : t("stock.vide")}</span>
      </div>
      <div className="kpis">
        <div className="kpi"><span className="kpi-l">{t("stock.unites")}</span><span className="kpi-v">{s.compteurs.unites}</span></div>
        <div className="kpi"><span className="kpi-l">{t("stock.ruptures")}</span>
          <span className={`kpi-v ${s.compteurs.ruptures ? "negatif" : ""}`}>{s.compteurs.ruptures}</span></div>
        <div className="kpi"><span className="kpi-l">{t("stock.surstocks")}</span><span className="kpi-v">{s.compteurs.surstocks}</span></div>
      </div>
      <section className="carte" aria-labelledby="t-stock">
        <h3 id="t-stock">{t("stock.par_produit")}</h3>
        <div className="defile">
          <table>
            <thead><tr>
              <th scope="col">{t("col.produit")}</th><th scope="col">{t("col.place")}</th>
              <th scope="col" className="num">{t("col.disponible")}</th><th scope="col" className="num">{t("col.en_route")}</th>
              <th scope="col" className="num">{t("col.vendus")}</th><th scope="col" className="num">{t("col.couverture")}</th>
              <th scope="col">{t("col.rupture")}</th><th scope="col" className="num">{t("col.a_commander")}</th>
              <th scope="col">{t("col.fournisseur")}</th><th scope="col">{t("col.remarques")}</th>
            </tr></thead>
            <tbody>
              {s.lignes.map((l) => (
                <tr key={`${l.marketplace}-${l.sku}`}>
                  <td><div className="produit">{l.designation ?? l.sku}</div><div className="meta">{l.sku}{l.asin ? ` · ${l.asin}` : ""}</div></td>
                  <td>{l.marketplace}</td>
                  <td className="num">{l.disponible}</td><td className="num">{l.en_route}</td><td className="num">{l.vendus_30j}</td>
                  <td className="num">
                    <div className="jauge" aria-hidden="true"><div className={l.couverture === null ? "neutre" : l.alertes.some((a) => a.code === "S_RUPTURE") ? "negatif" : ""}
                      style={{ width: `${l.couverture === null ? 100 : Math.min(100, (l.couverture / 90) * 100)}%` }} /></div>
                    {l.couverture === null ? t("illimitee") : t("jours", { n: l.couverture })}
                  </td>
                  <td>{l.rupture_le ? dateCourte(l.rupture_le) : "—"}</td>
                  <td className="num"><strong>{l.a_commander || "—"}</strong></td>
                  <td>{l.fournisseur ?? "—"}</td>
                  <td className="remarques">{l.alertes.map((a, i) => <div key={i}>{message(a, l.devise)}</div>)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      <section className="carte" aria-labelledby="t-cmd">
        <h3 id="t-cmd">{t("stock.commandes")}</h3>
        {s.commandes.length === 0 ? <p className="meta">{t("stock.aucune_commande")}</p> : (
          <ul className="liste-cmd" role="list">
            {s.commandes.map((c, i) => (
              <li key={i}><strong>{c.fournisseur ?? t("stock.fournisseur_inconnu")}</strong>
                <span className="meta">{t("stock.ligne_cmd", { lignes: c.lignes, unites: c.unites })}</span>
                <span className="montant">{c.montant === null ? "—" : monnaie(String(c.montant), c.devise)}</span></li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

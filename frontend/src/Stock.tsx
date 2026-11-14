import { useEffect, useState } from "react";
import { PropositionRepricer, Stock, bonDepuisStock, envoyerRepricer, lireStock, preparerRepricer } from "./api";
import { dateCourte, message, monnaie, t } from "./i18n";

// [RM-AMZ-123] proposition puis envoi après validation
function Repricer({ props, fermer }: { props: PropositionRepricer[]; fermer: () => void }) {
  const [lignes, setLignes] = useState(props);
  const [res, setRes] = useState<{ sku: string; statut: string; probleme?: string; problemes?: string[] }[] | null>(null);
  const [envoi, setEnvoi] = useState(false);
  const maj = (i: number, k: keyof PropositionRepricer, v: string) => setLignes(lignes.map((l, j) => (j === i ? { ...l, [k]: k === "regle" ? v : Number(v.replace(",", ".")) } : l)));
  const valides = lignes.filter((l) => !l.erreur && l.minimum && l.maximum && l.regle);
  const envoyer = () => { setEnvoi(true); envoyerRepricer(valides.map((l) => ({ sku: l.sku, marketplace: l.marketplace, minimum: l.minimum!, maximum: l.maximum!, regle: l.regle! })))
    .then((r) => setRes(r.resultats)).finally(() => setEnvoi(false)); };
  return (
    <section className="carte">
      <div className="entete-vue"><h3>{t("repricer.titre")}</h3><button type="button" className="lien" onClick={fermer}>{t("fermer")}</button></div>
      <p className="meta">{t("repricer.info")}</p>
      <div className="defile"><table className="table-compacte">
        <thead><tr><th scope="col">SKU</th><th scope="col" className="num">{t("repricer.prix")}</th><th scope="col" className="num">{t("plancher.libelle")}</th>
          <th scope="col">{t("repricer.minimum")}</th><th scope="col">{t("repricer.maximum")}</th><th scope="col">{t("repricer.regle")}</th><th scope="col" /></tr></thead>
        <tbody>{lignes.map((l, i) => l.erreur ? <tr key={l.sku}><td>{l.sku}</td><td colSpan={6} className="meta">{l.erreur}</td></tr> : (
          <tr key={l.sku}>
            <td>{l.sku}<div className="meta">{l.asin} · {l.marketplace}</div></td>
            <td className="num">{l.prix == null ? "—" : monnaie(String(l.prix), l.devise)}</td>
            <td className="num">{l.plancher == null ? "—" : monnaie(String(l.plancher), l.devise)}</td>
            <td><input className="mini-saisie" inputMode="decimal" value={l.minimum ?? ""} onChange={(e) => maj(i, "minimum", e.target.value)} />
              {l.plancher != null && l.minimum != null && l.minimum < l.plancher && <div className="negatif">{t("repricer.sous_plancher")}</div>}</td>
            <td><input className="mini-saisie" inputMode="decimal" value={l.maximum ?? ""} onChange={(e) => maj(i, "maximum", e.target.value)} /></td>
            <td><select value={l.regle ?? ""} onChange={(e) => maj(i, "regle", e.target.value)}>
              {(l.regles ?? []).map((r) => <option key={r.id} value={r.id}>{r.nom}</option>)}</select></td>
            <td>{res?.find((x) => x.sku === l.sku)?.statut}</td>
          </tr>))}</tbody>
      </table></div>
      <div className="actions"><button type="button" className="principal" disabled={envoi || valides.length === 0 || !!res} onClick={envoyer}>
        {t("repricer.envoyer", { n: valides.length })}</button></div>
      {res && <ul className="msgs">{res.map((x) => <li key={x.sku}>{x.sku} : {x.statut}{x.probleme ? ` · ${x.probleme}` : ""}{(x.problemes ?? []).length ? ` · ${x.problemes!.join(" | ")}` : ""}</li>)}</ul>}
    </section>
  );
}

export function StockVue({ ouvrirBon }: { ouvrirBon: (id: string) => void }) {
  const [s, setS] = useState<Stock | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  const [choix, setChoix] = useState<string[]>([]);
  const [props, setProps] = useState<PropositionRepricer[] | null>(null);
  const [prep, setPrep] = useState(false);
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
      {props && <Repricer props={props} fermer={() => setProps(null)} />}
      <section className="carte" aria-labelledby="t-stock">
        <div className="entete-vue"><h3 id="t-stock">{t("stock.par_produit")}</h3>
          {choix.length > 0 && <button type="button" className="principal" disabled={prep} onClick={() => { setPrep(true);
            preparerRepricer(s.lignes.filter((l) => choix.includes(`${l.marketplace}-${l.sku}`)).map((l) => ({ sku: l.sku, asin: l.asin, marketplace: l.marketplace, cout_unitaire: l.cout_unitaire })))
              .then((r) => setProps(r.lignes)).catch((e) => setErreur(e.message)).finally(() => setPrep(false)); }}>
            {prep ? t("chargement") : t("repricer.preparer", { n: choix.length })}</button>}</div>
        <div className="defile">
          <table>
            <thead><tr>
              <th scope="col" className="case-suivi"><input type="checkbox" aria-label={t("annuaire.tout")} checked={s.lignes.length > 0 && choix.length === s.lignes.length}
                onChange={(e) => setChoix(e.target.checked ? s.lignes.map((l) => `${l.marketplace}-${l.sku}`) : [])} /></th>
              <th scope="col">{t("col.produit")}</th><th scope="col">{t("col.place")}</th>
              <th scope="col" className="num">{t("col.disponible")}</th><th scope="col" className="num">{t("col.en_route")}</th>
              <th scope="col" className="num">{t("col.vendus")}</th><th scope="col" className="num">{t("col.couverture")}</th>
              <th scope="col">{t("col.rupture")}</th><th scope="col" className="num">{t("col.a_commander")}</th>
              <th scope="col">{t("col.fournisseur")}</th><th scope="col">{t("col.remarques")}</th>
            </tr></thead>
            <tbody>
              {s.lignes.map((l) => (
                <tr key={`${l.marketplace}-${l.sku}`} className={`cliquable ${choix.includes(`${l.marketplace}-${l.sku}`) ? "choisie" : ""}`}
                  onClick={(e) => { if ((e.target as HTMLElement).closest("a, button, input")) return; const k = `${l.marketplace}-${l.sku}`;
                    setChoix((c) => (c.includes(k) ? c.filter((x) => x !== k) : [...c, k])); }}>
                  <td className="case-suivi"><input type="checkbox" aria-label={l.sku} checked={choix.includes(`${l.marketplace}-${l.sku}`)}
                    onChange={() => { const k = `${l.marketplace}-${l.sku}`; setChoix((c) => (c.includes(k) ? c.filter((x) => x !== k) : [...c, k])); }} /></td>
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
                <span className="montant">{c.montant === null ? "—" : monnaie(String(c.montant), c.devise)}</span>
                {c.fournisseur && <button type="button" className="secondaire"
                  onClick={() => bonDepuisStock(c.fournisseur!).then((b) => ouvrirBon(b.id)).catch((e) => setErreur(e.message))}>{t("stock.creer_bon")}</button>}</li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

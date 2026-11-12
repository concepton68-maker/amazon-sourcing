import { FormEvent, useEffect, useState } from "react";
import { Bon, FournisseurBilan, Place, actionBon, ajouterLigneBon, creerBon, creerFournisseur, listerBons,
  listerFournisseurs, listerPlaces, recevoirBon, retirerLigneBon } from "./api";
import { dateCourte, monnaie, pourcent, t } from "./i18n";

const n = (v: number | null) => (v === null ? null : String(v));
const STATUTS = ["TOUS", "BROUILLON", "ENVOYE", "RECU", "ANNULE"];

function DetailBon({ b, maj, voirLot }: { b: Bon; maj: (b: Bon) => void; voirLot: (id: string) => void }) {
  const [places, setPlaces] = useState<Place[]>([]);
  const [asin, setAsin] = useState(""); const [mp, setMp] = useState("FR"); const [qte, setQte] = useState("");
  const [recues, setRecues] = useState<Record<string, string>>({});
  const [erreur, setErreur] = useState<string | null>(null);
  useEffect(() => { listerPlaces().then(setPlaces).catch(() => undefined); }, []);
  useEffect(() => { setRecues(Object.fromEntries(b.lignes.map((l) => [l.id, String(l.quantite)]))); setErreur(null); }, [b]);
  const faire = async (p: Promise<Bon>) => { setErreur(null); try { maj(await p); } catch (x) { setErreur((x as Error).message); } };
  const d = b.devise ?? "EUR";
  const ajouter = (e: FormEvent) => { e.preventDefault(); faire(ajouterLigneBon(b.id, asin.trim(), mp, Number(qte))).then(() => { setAsin(""); setQte(""); }); };
  return (
    <section className="carte" aria-labelledby="titre-bon">
      <div className="entete-vue">
        <div>
          <h3 id="titre-bon">{b.reference} · {b.fournisseur?.nom}</h3>
          <p className="meta">{t("bon.cree_le", { date: dateCourte(b.cree_le) })}
            {b.envoye_le && ` · ${t("bon.envoye_le", { date: dateCourte(b.envoye_le) })}`}
            {b.recu_le && ` · ${t("bon.recu_le", { date: dateCourte(b.recu_le) })}`}</p>
        </div>
        <span className={`statut-bon ${b.statut}`}>{t(`statut_bon.${b.statut}`)}</span>
      </div>
      <div className="defile">
        <table>
          <thead><tr><th scope="col">{t("col.produit")}</th><th scope="col" className="num">{t("bon.quantite")}</th>
            <th scope="col" className="num">{t("bon.prix")}</th><th scope="col" className="num">{t("bon.montant")}</th>
            <th scope="col" className="num">{t("bon.roi")}</th>
            {b.statut === "ENVOYE" && <th scope="col" className="num">{t("bon.recue")}</th>}
            {b.statut === "RECU" && <th scope="col">{t("bon.lot")}</th>}
            {b.statut === "BROUILLON" && <th scope="col"><span className="masque">{t("bon.retirer")}</span></th>}</tr></thead>
          <tbody>
            {b.lignes.map((l) => (
              <tr key={l.id}>
                <td><div className="produit">{l.designation ?? l.asin}</div><div className="meta">{l.asin} · {l.marketplace}</div></td>
                <td className="num">{l.quantite}</td><td className="num">{monnaie(n(l.prix_unitaire), d)}</td>
                <td className="num">{monnaie(n(l.montant), d)}</td><td className="num">{pourcent(n(l.roi_prevu))}</td>
                {b.statut === "ENVOYE" && <td className="num"><input aria-label={`${t("bon.recue")} ${l.asin}`} className="etroit-num"
                  type="number" min={0} max={l.quantite} value={recues[l.id] ?? ""} onChange={(e) => setRecues({ ...recues, [l.id]: e.target.value })} /></td>}
                {b.statut === "RECU" && <td>{l.lot_id ? <button type="button" className="lien" onClick={() => voirLot(l.lot_id!)}>{t("bon.voir_lot")}</button> : "—"}</td>}
                {b.statut === "BROUILLON" && <td><button type="button" className="lien" onClick={() => faire(retirerLigneBon(b.id, l.id))}>{t("bon.retirer")}</button></td>}
              </tr>
            ))}
            <tr className="total"><th scope="row">{t("bon.montant")}</th><td /><td /><td className="num">{monnaie(n(b.montant), d)}</td>
              <td className="num">{pourcent(n(b.roi_prevu))}</td></tr>
          </tbody>
        </table>
      </div>
      {b.statut === "BROUILLON" && (
        <form className="formulaire nu" onSubmit={ajouter}>
          <label>{t("bon.asin")}<input type="text" required maxLength={20} value={asin} onChange={(e) => setAsin(e.target.value)} /></label>
          <label>{t("analyse.place")}<select value={mp} onChange={(e) => setMp(e.target.value)}>
            {places.map((p) => <option key={p.code} value={p.code}>{p.domaine}</option>)}</select></label>
          <label className="etroit">{t("bon.quantite")}<input type="number" min={1} required value={qte} onChange={(e) => setQte(e.target.value)} /></label>
          <button type="submit" className="secondaire">{t("bon.ajouter_ligne")}</button>
        </form>
      )}
      {erreur && <p role="alert" className="alerte">{t(`erreur.${erreur}`)}</p>}
      <div className="actions">
        {b.statut === "BROUILLON" && <button type="button" className="principal" onClick={() => faire(actionBon(b.id, "envoyer"))}>{t("bon.envoyer")}</button>}
        {b.statut === "ENVOYE" && <button type="button" className="principal"
          onClick={() => faire(recevoirBon(b.id, Object.fromEntries(Object.entries(recues).map(([k, v]) => [k, Number(v || 0)]))))}>{t("bon.recevoir")}</button>}
        {(b.statut === "BROUILLON" || b.statut === "ENVOYE") && <button type="button" className="secondaire" onClick={() => faire(actionBon(b.id, "annuler"))}>{t("bon.annuler")}</button>}
      </div>
    </section>
  );
}

export function FournisseursVue({ bonInitial, voirLot }: { bonInitial?: string; voirLot: (id: string) => void }) {
  const [fs, setFs] = useState<FournisseurBilan[]>([]);
  const [bons, setBons] = useState<Bon[]>([]);
  const [choisi, setChoisi] = useState<string | undefined>(bonInitial);
  const [filtre, setFiltre] = useState("TOUS");
  const [nom, setNom] = useState(""); const [delai, setDelai] = useState("7");
  const [erreur, setErreur] = useState<string | null>(null);
  const charger = () => Promise.all([listerFournisseurs().then(setFs), listerBons().then((b) => {
    setBons(b); setChoisi((c) => c ?? b[0]?.id);
  })]).catch((e) => setErreur(e.message));
  useEffect(() => { charger(); }, []);  // eslint-disable-line
  const maj = (b: Bon) => { setBons((x) => [b, ...x.filter((y) => y.id !== b.id)].sort((p, q) => q.reference.localeCompare(p.reference))); setChoisi(b.id); listerFournisseurs().then(setFs); };
  const ajouter = async (e: FormEvent) => {
    e.preventDefault(); setErreur(null);
    try { await creerFournisseur(nom, Number(delai)); setNom(""); charger(); } catch (x) { setErreur((x as Error).message); }
  };
  const bon = bons.find((b) => b.id === choisi);
  const visibles = bons.filter((b) => filtre === "TOUS" || b.statut === filtre);
  return (
    <div className="vue">
      <h1>{t("fournisseurs.titre")}</h1>
      <section className="carte" aria-labelledby="t-f">
        <h3 id="t-f">{t("fournisseurs.liste")}</h3>
        <div className="defile">
          <table>
            <thead><tr><th scope="col">{t("fournisseurs.nom")}</th><th scope="col" className="num">{t("fournisseurs.achete")}</th>
              <th scope="col" className="num">{t("fournisseurs.roi")}</th><th scope="col" className="num">{t("fournisseurs.delai_reel")}</th>
              <th scope="col"><span className="masque">{t("fournisseurs.nouveau_bon")}</span></th></tr></thead>
            <tbody>{fs.map((f) => (
              <tr key={f.id}>
                <td><div className="produit">{f.nom}</div><div className="meta">{t("fournisseurs.lots", { n: f.lots })} · {t("jours", { n: f.delai_jours })}</div></td>
                <td className="num">{monnaie(n(f.achete_12_mois), f.devise)}</td>
                <td className="num">{pourcent(n(f.roi_prevu))} → <span className={f.roi_reel !== null && f.roi_prevu !== null && f.roi_reel < f.roi_prevu ? "negatif" : ""}>{pourcent(n(f.roi_reel))}</span></td>
                <td className="num">{f.delai_reel_jours === null ? "—" : t("jours", { n: f.delai_reel_jours })}</td>
                <td><button type="button" className="lien" onClick={() => creerBon(f.id).then(maj).catch((e) => setErreur(e.message))}>{t("fournisseurs.nouveau_bon")}</button></td>
              </tr>))}</tbody>
          </table>
        </div>
        <form className="formulaire nu" onSubmit={ajouter}>
          <label>{t("fournisseurs.nom")}<input type="text" required maxLength={120} value={nom} onChange={(e) => setNom(e.target.value)} /></label>
          <label className="etroit">{t("fournisseurs.delai")}<input type="number" min={0} max={365} value={delai} onChange={(e) => setDelai(e.target.value)} /></label>
          <button type="submit" className="secondaire">{t("fournisseurs.ajouter")}</button>
        </form>
        {erreur && <p role="alert" className="alerte">{t(`erreur.${erreur}`)}</p>}
      </section>
      <div className="contenu sans-marge">
        <aside className="colonne" aria-labelledby="t-b">
          <h2 id="t-b" className="h-colonne">{t("bons.titre")}</h2>
          <div role="group" className="onglets" aria-label={t("bons.titre")}>
            {STATUTS.map((s) => <button key={s} type="button" aria-pressed={filtre === s} onClick={() => setFiltre(s)}>
              {s === "TOUS" ? t("bons.tous") : t(`statut_bon.${s}`)}</button>)}
          </div>
          {visibles.length === 0 ? <p className="meta">{t("bons.vide")}</p> : (
            <ul className="liste" role="list">{visibles.map((b) => (
              <li key={b.id}><button type="button" className={b.id === choisi ? "lot actif" : "lot"} aria-current={b.id === choisi} onClick={() => setChoisi(b.id)}>
                <span className="lot-nom">{b.reference} · {b.fournisseur?.nom}</span>
                <span className="lot-meta"><span>{monnaie(n(b.montant), b.devise ?? "EUR")}</span>
                  <span className={`statut-bon ${b.statut}`}>{t(`statut_bon.${b.statut}`)}</span></span>
              </button></li>))}</ul>
          )}
        </aside>
        <div className="detail">{bon && <DetailBon b={bon} maj={maj} voirLot={voirLot} />}</div>
      </div>
    </div>
  );
}

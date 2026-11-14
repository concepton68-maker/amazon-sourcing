import { useEffect, useState } from "react";
import { Activite, ajouterAuPlan, analyserTousCatalogues, EtatCorrespondance, ResultatPlan, ListeRentables, lireActivite, ProduitRentable, lancerCorrespondance, lireCorrespondance, lireRentables } from "./api";
import { FiltreMultiple } from "./Filtre";
import { monnaie, pourcent, t } from "./i18n";

// Produits rentables [RM-AMZ-105 à 108] : tout ce qui a été analysé, classé et filtré par le vendeur.
const NIVEAUX = ["VENDABLE", "PROBABLEMENT_VENDABLE", "PROBABLEMENT_NON_VENDABLE", "NON_VENDABLE", "INCONNU"];
const TON: Record<string, string> = { VENDABLE: "v", PROBABLEMENT_VENDABLE: "b", PROBABLEMENT_NON_VENDABLE: "a", NON_VENDABLE: "r", INCONNU: "n" };
const eur = (v: number | null) => (v === null ? "—" : monnaie(String(v), "EUR"));
const pc = (v: number | null) => (v === null ? "—" : pourcent(String(v)));

function Entete({ cle, tri, ordre, trier, num = true }: { cle: string; tri: string; ordre: string; trier: (c: string) => void; num?: boolean }) {
  const actif = tri === cle;
  return (
    <th scope="col" className={num ? "num" : undefined} aria-sort={actif ? (ordre === "desc" ? "descending" : "ascending") : "none"}>
      <button type="button" className={`tri ${actif ? "actif" : ""}`} onClick={() => trier(cle)}>
        {t(`rent.col.${cle}`)}{actif ? (ordre === "desc" ? " ↓" : " ↑") : ""}</button>
    </th>
  );
}

const cle = (p: ProduitRentable) => `${p.origine}|${p.marketplace}|${p.code}|${p.asin}`;

function Ligne({ p, analyser, nouveau, coche, basculer }: { p: ProduitRentable; analyser: (code: string, prix: number) => void;
  nouveau: boolean; coche: boolean; basculer: () => void }) {
  return (
    <tr className={`cliquable ${nouveau ? "arrivee" : ""} ${coche ? "choisie" : ""}`} onClick={basculer}>
      <td className="case"><input type="checkbox" checked={coche} onChange={basculer} onClick={(e) => e.stopPropagation()}
        aria-label={t("rent.choisir", { p: p.titre ?? p.asin })} /></td>
      <td><button type="button" className="lien produit" onClick={(e) => { e.stopPropagation(); analyser(p.asin, p.cout_achat ?? 0); }}>{p.titre ?? p.designation ?? p.asin}</button>
        {nouveau && <span className="nouveau">{t("vendable.nouveau")}</span>}
        <div className="meta">{p.asin} · {p.origine_nom}{p.unites_lot > 1 ? ` · ${t("rent.lot", { n: p.unites_lot })}` : ""}</div></td>
      <td className="num">{eur(p.cout_achat)}</td>
      <td className="num">{eur(p.prix_vente)}</td>
      <td className={`num ${p.profit !== null && p.profit > 0 ? "positif" : p.profit !== null ? "negatif" : ""}`}>{eur(p.profit)}</td>
      <td className="num">{pc(p.roi)}</td>
      <td className="num">{pc(p.marge)}</td>
      <td className="num">{eur(p.prix_achat_max)}</td>
      <td className="num">{p.historique_court ? <span className="meta">{t("sm.court")}</span> : p.rotation}</td>
      <td className="num">{p.bsr?.toLocaleString("fr-FR") ?? "—"}</td>
      <td className="num">{p.nb_vendeurs ?? "—"}{p.amazon_vend ? <span className="meta"> · {t("sm.amazon")}</span> : null}</td>
      <td><span className={`pill ${TON[p.vendabilite]}`}>{t(`vend.${p.vendabilite}`)}</span>
        {p.motif && <div className="meta">{t(`vend.motif.${p.motif}`)}</div>}</td>
      <td>{p.verdict && <span className={`verdict ${p.verdict}`}>{t(`verdict.${p.verdict}`)}</span>}</td>
    </tr>
  );
}

export function RentablesVue({ analyser, voirBon }: { analyser: (code: string, prix: number) => void; voirBon: (id: string) => void }) {
  const [l, setL] = useState<ListeRentables | null>(null);
  const [choix, setChoix] = useState<Set<string>>(new Set());
  const [plan, setPlan] = useState<ResultatPlan | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  const [corr, setCorr] = useState<EtatCorrespondance | null>(null);
  const [ouverture] = useState(() => new Date().toISOString());
  const [activites, setActivites] = useState<Activite[]>([]);
  const [rafraichir, setRafraichir] = useState(0);
  const [tri, setTri] = useState("profit"); const [ordre, setOrdre] = useState("desc");
  const [niveaux, setNiveaux] = useState<string[]>(NIVEAUX);
  const [roi, setRoi] = useState(""); const [profit, setProfit] = useState(""); const [marge, setMarge] = useState("");
  const [origine, setOrigine] = useState(""); const [verdict, setVerdict] = useState(""); const [sansAmazon, setSansAmazon] = useState(false);
  useEffect(() => {
    const q: Record<string, string> = { tri, ordre };
    if (niveaux.length < NIVEAUX.length) q.vendabilite = niveaux.join(",") || "AUCUN";
    const nb = (s: string, div = 1) => String(Number(s.replace(",", ".")) / div);
    if (roi) q.roi_min = nb(roi, 100);
    if (profit) q.profit_min = nb(profit);
    if (marge) q.marge_min = nb(marge, 100);
    if (origine) q.origine = origine;
    if (verdict) q.verdict = verdict;
    if (sansAmazon) q.amazon_absent = "true";
    if (q.vendabilite === "AUCUN") { setL((x) => x && { ...x, nombre: 0, produits: [] }); return; }
    lireRentables(q).then(setL).catch((x) => setErreur((x as Error).message));
  }, [tri, ordre, niveaux, roi, profit, marge, origine, verdict, sansAmazon, rafraichir]);
  const lireCorr = () => lireCorrespondance().then((x) => { setCorr((avant) => { if (avant?.en_cours && !x.en_cours) setRafraichir((n) => n + 1); return x; }); }).catch(() => undefined);
  useEffect(() => { lireCorr(); }, []);
  useEffect(() => {                                                       // [RM-AMZ-116] temps réel
    let actif = true;
    const tour = () => lireActivite().then((x) => {
      if (!actif) return;
      setActivites((avant) => {
        if (x.activites.length || avant.length) { setRafraichir((n) => n + 1); lireCorr(); }
        return x.activites;
      });
    }).catch(() => undefined);
    tour();
    const id = setInterval(tour, 3000);
    return () => { actif = false; clearInterval(id); };
  }, []);
  const analyserTout = () => { setErreur(null); analyserTousCatalogues().then(() => setRafraichir((n) => n + 1)).catch((x) => setErreur((x as Error).message)); };
  const occupe = activites.some((a) => a.type === "ANALYSE" || a.type === "ANALYSE_TOUT");
  const chercher = () => { setErreur(null); lancerCorrespondance().then(lireCorr).catch((x) => setErreur((x as Error).message)); };
  const trier = (c: string) => { if (c === tri) setOrdre(ordre === "desc" ? "asc" : "desc"); else { setTri(c); setOrdre("desc"); } };
  const visibles = l?.produits ?? [];
  const tous = visibles.length > 0 && visibles.every((p) => choix.has(cle(p)));
  const basculer = (k: string) => setChoix((s) => { const n = new Set(s); if (n.has(k)) n.delete(k); else n.add(k); return n; });
  const toutBasculer = () => setChoix((s) => { const n = new Set(s); visibles.forEach((p) => (tous ? n.delete(cle(p)) : n.add(cle(p)))); return n; });
  const choisis = visibles.filter((p) => choix.has(cle(p)));
  const versPlan = () => {                                             // [RM-AMZ-125]
    setErreur(null); setPlan(null);
    ajouterAuPlan(choisis.map((p) => ({ origine: p.origine, marketplace: p.marketplace, code: p.code, asin: p.asin })))
      .then((r) => { setPlan(r); setChoix(new Set()); }).catch((x) => setErreur((x as Error).message));
  };
  const e = (c: string, num = true) => <Entete cle={c} tri={tri} ordre={ordre} trier={trier} num={num} />;
  return (
    <div className="vue">
      <div className="entete-vue"><h1>{t("rent.titre")}</h1>
        <div className="actions">
          {l && <span className="meta">{t("rent.nombre", { n: l.nombre, total: l.total })}</span>}
          {l && l.catalogues > 0 && l.total > 0 && <button type="button" className="secondaire" disabled={occupe} onClick={analyserTout}
            title={t("rent.analyser_tout_info")}>{occupe ? t("rent.analyse_en_cours") : t("rent.analyser_tout")}</button>}
          <button type="button" className="principal" disabled={corr?.en_cours} onClick={chercher} title={t("corr.info")}>
            {corr?.en_cours ? t(corr.phase === "ANALYSE" ? "corr.analyse" : "corr.en_cours", { f: corr.progression?.[0] ?? 0, t: corr.progression?.[1] ?? 0 }) : t("corr.lancer")}</button>
        </div></div>
      {activites.length > 0 && <div className="bandeau-activite" role="status">
        <span className="point-pulse" aria-hidden="true" />
        {activites.map((a, i) => <span key={i}>{t(`activite.${a.type}`, { nom: a.nom ? t(`synchro.${a.nom}`) === `synchro.${a.nom}` ? a.nom : t(`synchro.${a.nom}`) : "", f: a.faits, t: a.total })}</span>)}
        <span className="meta">{t("activite.direct")}</span></div>}
      {corr?.bilan && !corr.en_cours && <p className="meta">{corr.bilan.erreur ? t("corr.erreur")
        : t(corr.bilan.correspondances ? "corr.bilan" : "corr.bilan_vide", { c: corr.bilan.candidats ?? 0, n: corr.bilan.correspondances ?? 0,
            f: corr.bilan.fournisseurs ?? 0, k: corr.bilan.catalogues_cherches ?? 0 })}</p>}
      {erreur && <p role="alert" className="alerte">{t(`erreur.${erreur}`)}</p>}
      {plan && <div className="bandeau-plan" role="status">
        <span>{t("plan.resultat", { n: plan.ajoutees, b: plan.bons.length })}{plan.deja ? ` · ${t("plan.deja", { n: plan.deja })}` : ""}</span>
        {plan.bons.length > 0 && <button type="button" className="lien" onClick={() => voirBon(plan.bons[0])}>{t("plan.voir")}</button>}
        {plan.refus.length > 0 && <span className="meta">{t("plan.refus", { n: plan.refus.length })} :{" "}
          {Object.entries(plan.refus.reduce<Record<string, number>>((a, r) => ({ ...a, [r.motif]: (a[r.motif] ?? 0) + 1 }), {}))
            .map(([m, n]) => `${t(`plan.motif.${m}`)} (${n})`).join(" · ")}</span>}
      </div>}
      {choisis.length > 0 && <div className="barre-selection" role="region" aria-label={t("rent.selection")}>
        <span>{t("rent.choisis", { n: choisis.length })}</span>
        <button type="button" className="principal" onClick={versPlan}>{t("plan.ajouter")}</button>
        <button type="button" className="lien" onClick={() => setChoix(new Set())}>{t("rent.tout_decocher")}</button>
      </div>}
      <div className="barre-filtres-rent">
        <FiltreMultiple libelle={t("rent.vendabilite")} changer={setNiveaux}
          options={NIVEAUX.map((n) => ({ code: n, libelle: `${t(`vend.${n}`)} (${l?.compteurs[n] ?? 0})`, coche: niveaux.includes(n) }))} />
        <label className="mini">{t("rent.roi_min")}<input inputMode="decimal" value={roi} onChange={(x) => setRoi(x.target.value)} placeholder="%" /></label>
        <label className="mini">{t("rent.profit_min")}<input inputMode="decimal" value={profit} onChange={(x) => setProfit(x.target.value)} placeholder="€" /></label>
        <label className="mini">{t("rent.marge_min")}<input inputMode="decimal" value={marge} onChange={(x) => setMarge(x.target.value)} placeholder="%" /></label>
        <label className="mini large">{t("rent.origine")}<select value={origine} onChange={(x) => setOrigine(x.target.value)}>
          <option value="">{t("rent.toutes")}</option>{l?.origines.map((o) => <option key={o.cle} value={o.cle}>{o.nom}</option>)}</select></label>
        <label className="mini">{t("rent.verdict")}<select value={verdict} onChange={(x) => setVerdict(x.target.value)}>
          <option value="">{t("rent.tous")}</option>{["ACHETER", "A_VERIFIER", "PASSER"].map((v) => <option key={v} value={v}>{t(`verdict.${v}`)}</option>)}</select></label>
        <label className="case-filtre"><input type="checkbox" checked={sansAmazon} onChange={(x) => setSansAmazon(x.target.checked)} />{t("rent.sans_amazon")}</label>
      </div>
      <section className="carte">
        {!l ? null : l.total === 0 ? (l.catalogues > 0
          ? <div className="vide-action"><p>{t("rent.vide_catalogues", { n: l.catalogues })}</p>
              <button type="button" className="principal" disabled={occupe} onClick={analyserTout}>{occupe ? t("rent.analyse_en_cours") : t("rent.analyser_tout")}</button></div>
          : <p className="meta">{t("rent.vide")} <a href="#fournisseurs">{t("nav.fournisseurs")}</a></p>)
          : <div className="defile"><table className="table-rent">
            <thead><tr><th scope="col" className="case"><input type="checkbox" checked={tous} onChange={toutBasculer}
              aria-label={tous ? t("rent.tout_decocher") : t("rent.tout_cocher")} title={tous ? t("rent.tout_decocher") : t("rent.tout_cocher")} /></th>
              <th scope="col">{t("rent.col.produit")}</th>{e("prix_achat")}{e("prix_vente")}{e("profit")}{e("roi")}{e("marge")}
              <th scope="col" className="num">{t("rent.col.achat_max")}</th>{e("rotation")}{e("bsr")}
              <th scope="col" className="num">{t("rent.col.vendeurs")}</th><th scope="col">{t("rent.col.vendabilite")}</th>
              <th scope="col">{t("rent.col.verdict")}</th></tr></thead>
            <tbody>{l.produits.map((p) => <Ligne key={cle(p)} p={p} analyser={analyser} nouveau={!!p.analyse_le && p.analyse_le > ouverture}
              coche={choix.has(cle(p))} basculer={() => basculer(cle(p))} />)}</tbody>
          </table></div>}
      </section>
    </div>
  );
}

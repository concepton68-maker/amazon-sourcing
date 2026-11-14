import { useEffect, useState } from "react";
import { EtatCorrespondance, ListeRentables, ProduitRentable, lancerCorrespondance, lireCorrespondance, lireRentables } from "./api";
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

function Ligne({ p, analyser }: { p: ProduitRentable; analyser: (code: string, prix: number) => void }) {
  return (
    <tr>
      <td><button type="button" className="lien produit" onClick={() => analyser(p.asin, p.cout_achat ?? 0)}>{p.titre ?? p.designation ?? p.asin}</button>
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

export function RentablesVue({ analyser }: { analyser: (code: string, prix: number) => void }) {
  const [l, setL] = useState<ListeRentables | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  const [corr, setCorr] = useState<EtatCorrespondance | null>(null);
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
  useEffect(() => {                                                       // [RM-AMZ-114] résultats au fil de l'eau
    if (!corr?.en_cours) return;
    const id = setTimeout(() => { lireCorr(); if (corr.phase === "ANALYSE") setRafraichir((n) => n + 1); }, 3000);
    return () => clearTimeout(id);
  }, [corr]);
  const chercher = () => { setErreur(null); lancerCorrespondance().then(lireCorr).catch((x) => setErreur((x as Error).message)); };
  const trier = (c: string) => { if (c === tri) setOrdre(ordre === "desc" ? "asc" : "desc"); else { setTri(c); setOrdre("desc"); } };
  const e = (c: string, num = true) => <Entete cle={c} tri={tri} ordre={ordre} trier={trier} num={num} />;
  return (
    <div className="vue">
      <div className="entete-vue"><h1>{t("rent.titre")}</h1>
        <div className="actions">
          {l && <span className="meta">{t("rent.nombre", { n: l.nombre, total: l.total })}</span>}
          <button type="button" className="principal" disabled={corr?.en_cours} onClick={chercher} title={t("corr.info")}>
            {corr?.en_cours ? t(corr.phase === "ANALYSE" ? "corr.analyse" : "corr.en_cours", { f: corr.progression?.[0] ?? 0, t: corr.progression?.[1] ?? 0 }) : t("corr.lancer")}</button>
        </div></div>
      {corr?.bilan && !corr.en_cours && <p className="meta">{corr.bilan.erreur ? t("corr.erreur")
        : t("corr.bilan", { c: corr.bilan.candidats ?? 0, n: corr.bilan.correspondances ?? 0, f: corr.bilan.fournisseurs ?? 0 })}</p>}
      {erreur && <p role="alert" className="alerte">{t(`erreur.${erreur}`)}</p>}
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
        {!l ? null : l.total === 0 ? <p className="meta">{t("rent.vide")} <a href="#fournisseurs">{t("nav.fournisseurs")}</a></p>
          : <div className="defile"><table className="table-rent">
            <thead><tr><th scope="col">{t("rent.col.produit")}</th>{e("prix_achat")}{e("prix_vente")}{e("profit")}{e("roi")}{e("marge")}
              <th scope="col" className="num">{t("rent.col.achat_max")}</th>{e("rotation")}{e("bsr")}
              <th scope="col" className="num">{t("rent.col.vendeurs")}</th><th scope="col">{t("rent.col.vendabilite")}</th>
              <th scope="col">{t("rent.col.verdict")}</th></tr></thead>
            <tbody>{l.produits.map((p) => <Ligne key={`${p.origine}|${p.asin}|${p.code}`} p={p} analyser={analyser} />)}</tbody>
          </table></div>}
      </section>
    </div>
  );
}

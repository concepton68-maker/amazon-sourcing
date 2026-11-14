import { useEffect, useState } from "react";
import { HistoriqueProduit, LigneMarche, Marche, Tendance, choisirFamilles, historiqueProduit, lireMarche, neplusSuivre,
  suivreProduit } from "./api";
import { monnaie, pourcent, t } from "./i18n";
import { FiltreMultiple } from "./Filtre";
import { EtatManuel, arreterTravaux, lancerSynchroManuelle, lireSynchroManuelle } from "./api";

// [RM-AMZ-141] relever maintenant (Buy Box, prix, classement, offres), avec avancement et arrêt
function ReleverMaintenant({ fini }: { fini: () => void }) {
  const [etat, setEtat] = useState<EtatManuel | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  const lireEtat = () => lireSynchroManuelle().then((x) => setEtat((avant) => { if (avant?.en_cours && x.etat && !x.etat.en_cours) fini(); return x.etat; })).catch(() => undefined);
  useEffect(() => { lireEtat(); }, []);
  useEffect(() => { if (!etat?.en_cours) return; const i = setTimeout(lireEtat, 2000); return () => clearTimeout(i); }, [etat]);
  const enCours = !!etat?.en_cours;
  const releve = etat?.terminees.find((x) => x.tache === "HISTORIQUE");
  return (
    <div className="releve-maintenant">
      {enCours ? <>
          <span className="en-cours"><span className="point-pulse" aria-hidden="true" /> {etat?.courante ? (etat.detail ?? t(`synchro.${etat.courante}`)) : t("manuel.attente")}</span>
          <button type="button" className="secondaire" disabled={!!etat?.arret} onClick={() => arreterTravaux().then(lireEtat)}>{etat?.arret ? t("arret.en_cours") : t("arret.bouton")}</button></>
        : <button type="button" className="principal" onClick={() => { setErreur(null); lancerSynchroManuelle(["HISTORIQUE"], true).then(lireEtat).catch((x) => setErreur((x as Error).message)); }}>{t("sm.relever")}</button>}
      {!enCours && releve && <span className="meta">{releve.ok ? "✓" : "✗"} {releve.message}</span>}
      {erreur && <span role="alert" className="alerte">{t(`erreur.${erreur}`)}</span>}
    </div>
  );
}

// Suivi de marché [RM-AMZ-086 à 090] : familles choisies, liste suivie, historique relevé chaque nuit.
const nb = (v: number | null | undefined) => (v === null || v === undefined ? "—" : v.toLocaleString("fr-FR"));
const pc = (v: number | null | undefined) => (v === null || v === undefined ? "—" : pourcent(String(v)));
const eur = (v: number | null | undefined) => (v === null || v === undefined ? "—" : monnaie(String(v), "EUR"));

function Variation({ v }: { v: number | null }) {
  if (v === null) return <span className="meta">—</span>;
  return <span className="pastille neutre">{new Intl.NumberFormat("fr-FR", { style: "percent", maximumFractionDigits: 1, signDisplay: "exceptZero" }).format(v)}</span>;
}

// Courbe : prix de la Buy Box (trait plein) et classement (pointillé, inversé : plus haut = mieux classé)
function Courbe({ h }: { h: HistoriqueProduit }) {
  const L = 1000, H = 160, M = 6;
  const pts = h.releves;
  if (pts.length < 2) return <p className="meta">{t("sm.releves")} : {pts.length}</p>;
  const x = (i: number) => M + (i * (L - 2 * M)) / (pts.length - 1);
  const bornes = (vals: (number | null)[]) => {
    const ok = vals.filter((v): v is number => v !== null);
    return ok.length ? [Math.min(...ok), Math.max(...ok)] : null;
  };
  const ligne = (vals: (number | null)[], inverse: boolean) => {
    const b = bornes(vals);
    if (!b) return "";
    const e = b[1] - b[0] || 1;
    return vals.map((v, i) => (v === null ? null : `${x(i)},${M + ((inverse ? v - b[0] : b[1] - v) / e) * (H - 2 * M)}`))
      .filter(Boolean).map((p, i) => `${i ? "L" : "M"}${p}`).join(" ");
  };
  const bp = bornes(pts.map((p) => p.prix)), bb = bornes(pts.map((p) => p.bsr));
  return (
    <figure className="courbe-bloc">
      <svg viewBox={`0 0 ${L} ${H}`} preserveAspectRatio="none" className="courbe" role="img" aria-label={t("sm.historique")}>
        <path d={ligne(pts.map((p) => p.bsr), true)} fill="none" stroke="var(--doux)" strokeWidth="1.5" strokeDasharray="4 4" vectorEffect="non-scaling-stroke" />
        <path d={ligne(pts.map((p) => p.prix), false)} fill="none" stroke="var(--accent)" strokeWidth="2.5" vectorEffect="non-scaling-stroke" />
      </svg>
      <figcaption className="legende meta">
        <span><i className="trait plein" />{t("sm.prix")} {bp ? `${eur(bp[0])} – ${eur(bp[1])}` : "—"}</span>
        <span><i className="trait pointille" />{t("sm.bsr")} {bb ? `${nb(bb[0])} – ${nb(bb[1])}` : "—"}</span>
        <span>{pts[0].jour.split("-").reverse().join("/")} → {pts[pts.length - 1].jour.split("-").reverse().join("/")}</span>
      </figcaption>
    </figure>
  );
}

function Tendances({ tr, titre }: { tr: Tendance; titre: string }) {
  return (
    <div className="kpi"><span className="kpi-l">{titre}{tr.court ? ` · ${t("sm.court")}` : ""}</span>
      <span className="kpi-v">{eur(tr.prix_moyen)}</span>
      <span className="kpi-s">{eur(tr.prix_min)} – {eur(tr.prix_max)} · {t("sm.baisses")} {nb(tr.jours_baisse_bsr)} · {t("sm.amazon")} {pc(tr.part_amazon_vend)}</span>
    </div>
  );
}

function Detail({ asin, analyser, changer }: { asin: string; analyser: (c: string) => void; changer: () => void }) {
  const [h, setH] = useState<HistoriqueProduit | null>(null);
  const lire = () => historiqueProduit(asin, "FR").then(setH);
  useEffect(() => { lire(); }, [asin]);
  if (!h) return null;
  const basculer = () => (h.suivi ? neplusSuivre(asin, "FR") : suivreProduit(asin, "FR")).then(() => { lire(); changer(); });
  return (
    <section className="carte detail-marche" aria-label={h.titre ?? asin}>
      <header className="detail-tete">
        <div><h2>{h.titre ?? asin}</h2><p className="meta">{asin} · {t("sm.historique")}</p></div>
        <div className="actions">
          <button type="button" className="secondaire" onClick={basculer}>{h.suivi ? t("sm.ne_plus_suivre") : t("sm.suivre")}</button>
          <button type="button" className="principal" onClick={() => analyser(asin)}>{t("sm.analyser")}</button>
        </div>
      </header>
      <Courbe h={h} />
      <div className="kpis">
        <Tendances tr={h.tendances["7"]} titre={t("sm.t7")} />
        <Tendances tr={h.tendances["30"]} titre={t("sm.t30")} />
        <div className="kpi"><span className="kpi-l">{t("sm.bb_amazon")}</span>
          <span className="kpi-v">{pc(h.tendances["30"].part_buybox_amazon)}</span>
          <span className="kpi-s">{t("sm.vendeurs")} {nb(h.tendances["30"].vendeurs_moyen)}</span></div>
      </div>
    </section>
  );
}

function Ligne({ p, choisi, choisir }: { p: LigneMarche; choisi: boolean; choisir: () => void }) {
  return (
    <tr className={choisi ? "choisie" : undefined} onClick={choisir} style={{ cursor: "pointer" }}>
      <td><button type="button" className="lien produit" onClick={choisir}>{p.titre ?? p.asin}</button>
        <div className="meta">{p.asin}{p.famille ? ` · ${t(`rayon.${p.famille}`)}` : ""}</div></td>
      <td className="num">{eur(p.prix)}</td>
      <td className="num"><Variation v={p.tendance.prix_variation} /></td>
      <td className="num">{nb(p.bsr)}</td>
      <td className="num">{nb(p.tendance.jours_baisse_bsr)}</td>
      <td className="num">{nb(p.vendeurs)}</td>
      <td className="num">{pc(p.tendance.part_amazon_vend)}</td>
      <td className="num">{p.tendance.releves}{p.tendance.court ? <span className="meta"> · {t("sm.court")}</span> : null}</td>
    </tr>
  );
}

export function MarcheVue({ analyser }: { analyser: (code: string) => void }) {
  const [groupe, setGroupe] = useState("SUIVI");
  const [m, setM] = useState<Marche | null>(null);
  const [choisi, setChoisi] = useState<string | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  const lire = () => lireMarche(groupe).then(setM).catch((x) => setErreur((x as Error).message));
  useEffect(() => { setChoisi(null); lire(); }, [groupe]);
  const suivies = m?.familles.filter((f) => f.suivie).map((f) => f.code) ?? [];
  const choisir = (l: string[]) => choisirFamilles(l).then(lire).catch((x) => setErreur((x as Error).message));
  const groupes = ["SUIVI", "ANALYSE", ...suivies];
  return (
    <div className="vue">
      <div className="entete-vue">
        <h1>{t("sm.titre")}</h1>
        <span className="meta">{t("sm.prochain")}</span>
        <ReleverMaintenant fini={lire} />
      </div>
      {erreur && <p role="alert" className="alerte">{t(`erreur.${erreur}`)}</p>}
      <div className="barre-filtres">
        <div className="onglets-ligne" role="tablist">
          {groupes.map((g) => (
            <button key={g} type="button" role="tab" aria-selected={g === groupe} onClick={() => setGroupe(g)}>
              {g === "SUIVI" || g === "ANALYSE" ? t(`sm.groupe.${g}`) : t(`rayon.${g}`)}
              {g === "SUIVI" && m ? <span className="compte">{m.suivis}</span> : null}</button>))}
        </div>
        {m && <FiltreMultiple libelle={t("sm.familles")} changer={choisir}
          options={m.familles.map((f) => ({ code: f.code, libelle: t(`rayon.${f.code}`), coche: f.suivie }))} />}
      </div>
      {choisi && <Detail asin={choisi} analyser={analyser} changer={lire} />}
      <section className="carte" aria-label={t("sm.titre")}>
        {!m ? null : m.produits.length === 0 ? <p className="meta">{groupe !== "SUIVI" && groupe !== "ANALYSE" ? t("sm.premier_releve") : t("sm.vide")}</p> : (
          <div className="defile"><table>
            <thead><tr>
              <th scope="col">{t("sm.produit")}</th><th scope="col" className="num">{t("sm.prix")}</th>
              <th scope="col" className="num">{t("sm.var30")}</th><th scope="col" className="num">{t("sm.bsr")}</th>
              <th scope="col" className="num"><abbr title={t("sm.baisses_info")}>{t("sm.baisses")} ⓘ</abbr></th>
              <th scope="col" className="num">{t("sm.vendeurs")}</th><th scope="col" className="num">{t("sm.amazon")}</th>
              <th scope="col" className="num">{t("sm.releves")}</th></tr></thead>
            <tbody>{m.produits.map((p) => <Ligne key={p.asin} p={p} choisi={p.asin === choisi} choisir={() => setChoisi(p.asin)} />)}</tbody>
          </table></div>)}
      </section>
    </div>
  );
}

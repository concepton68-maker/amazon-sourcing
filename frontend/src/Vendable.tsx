import { useEffect, useState } from "react";
import { Exploration, RayonSonde, choisirFamilles, explorationVue, lancerExploration, lireExploration, lireMarche, suivreProduit } from "./api";
import { t } from "./i18n";
import { EligibiliteVue } from "./Eligibilite";

const affiche = (r: RayonSonde) => (r.statut === "FERME" && r.approbation > 0 ? "APPROBATION" : r.statut);

// Ce que je peux vendre [RM-AMZ-084, 085] : sondage des rayons, produits autorisés d'abord.
function SuivreProduit({ asin }: { asin: string }) {
  const [fait, setFait] = useState(false);
  return <button type="button" className="lien" disabled={fait} onClick={() => suivreProduit(asin, "FR").then(() => setFait(true))}>
    {fait ? `✓ ${t("sm.suivi")}` : `+ ${t("sm.suivre")}`}</button>;
}

function Rayon({ r, analyser, suivi, basculer, nouveau, nouveaux }: { r: RayonSonde; analyser: (code: string) => void; suivi: boolean;
  basculer: () => void; nouveau: boolean; nouveaux: string[] }) {
  const [ouvert, setOuvert] = useState(false);
  const autorises = r.produits.filter((p) => p.statut === "AUTORISE");
  const part = r.testes ? r.autorises / r.testes : 0;
  return (
    <>
      <tr className={`cliquable ${suivi ? "choisie" : ""}`}
        onClick={(e) => { if (!(e.target as HTMLElement).closest("a, button, input")) basculer(); }}>
        <td className="case-suivi"><input type="checkbox" checked={suivi} onChange={basculer} aria-label={t("vendable.suivre_rayon", { rayon: t(`rayon.${r.code}`) })} /></td>
        <td><strong>{t(`rayon.${r.code}`)}</strong>{nouveau && <span className="nouveau">{t("vendable.nouveau")}</span>}</td>
        <td><span className={`statut-rayon ${affiche(r)}`}>{t(`rayon.statut.${affiche(r)}`)}</span></td>
        <td><div className="barre-part" title={`${r.autorises}/${r.testes}`}><div style={{ width: `${part * 100}%` }} /></div></td>
        <td className="num">{r.autorises} / {r.testes}</td>
        <td className="num">{r.approbation}</td>
        <td>{autorises.length > 0 && <button type="button" className="lien" aria-expanded={ouvert} onClick={() => setOuvert(!ouvert)}>
          {t("vendable.voir", { n: autorises.length })}</button>}</td>
      </tr>
      {ouvert && autorises.map((p) => (
        <tr key={p.asin} className="sous-ligne">
          <td />
          <td colSpan={3}><div className="produit">{p.titre ?? p.asin}{nouveaux.includes(p.asin) && <span className="nouveau">{t("vendable.nouveau")}</span>}</div><div className="meta">{p.asin}{p.categorie ? ` · ${p.categorie}` : ""}</div></td>
          <td className="num meta">{p.bsr ? `BSR ${p.bsr.toLocaleString("fr-FR")}` : "—"}</td>
          <td colSpan={2}><button type="button" className="lien" onClick={() => analyser(p.asin)}>{t("vendable.analyser")}</button>
            <SuivreProduit asin={p.asin} /></td>
        </tr>))}
    </>
  );
}

export function VendableVue({ analyser }: { analyser: (code: string) => void }) {
  const [e, setE] = useState<Exploration | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  const [nouv, setNouv] = useState<{ rayons: string[]; produits: string[] } | null>(null);
  const lire = () => lireExploration().then((x) => {
    setE(x);
    const n = x.resultat?.nouveautes;                                   // [RM-AMZ-113] affichées, puis marquées vues
    if (n && !n.vu && (n.rayons.length || n.produits.length)) { setNouv(n); explorationVue().catch(() => undefined); }
  }).catch((x) => setErreur((x as Error).message));
  const [suivies, setSuivies] = useState<string[]>([]);
  const lireSuivies = () => lireMarche("SUIVI").then((m) => setSuivies(m.familles.filter((f) => f.suivie).map((f) => f.code))).catch(() => undefined);
  const enregistrer = (l: string[]) => { setSuivies(l); choisirFamilles(l).catch((x) => { setErreur((x as Error).message); lireSuivies(); }); };
  useEffect(() => { lire(); lireSuivies(); }, []);
  useEffect(() => {
    if (!e?.en_cours) return;
    const id = setTimeout(lire, 2000);
    return () => clearTimeout(id);
  }, [e]);
  const lancer = () => { setErreur(null); lancerExploration().then(lire).catch((x) => setErreur((x as Error).message)); };
  const res = e?.resultat;
  const rayons = res ? [...res.rayons].sort((a, b) => Number(!!nouv?.rayons.includes(b.code)) - Number(!!nouv?.rayons.includes(a.code))
    || b.autorises / (b.testes || 1) - a.autorises / (a.testes || 1)) : [];
  return (
    <div className="vue">
      <div className="entete-vue">
        <h1>{t("vendable.titre")}</h1>
        <div className="formulaire nu">
          {res && <span className="meta">{t("vendable.le", { date: new Date(res.le).toLocaleString("fr-FR") })}</span>}
          <button type="button" className="principal" disabled={e?.en_cours} onClick={lancer}>
            {e?.en_cours ? t("vendable.en_cours", { f: e.progression?.[0] ?? 0, t: e.progression?.[1] ?? 0 }) : t("vendable.lancer")}</button>
        </div>
      </div>
      {erreur && <p role="alert" className="alerte">{t(`erreur.${erreur}`)}</p>}
      {res && (
        <div className="kpis">
          {["OUVERT", "PARTIEL", "APPROBATION", "FERME"].map((s) => (
            <div key={s} className="kpi"><span className="kpi-l">{t(`rayon.statut.${s}`)}</span>
              <span className="kpi-v">{res.rayons.filter((r) => affiche(r) === s).length}</span></div>))}
          <div className="kpi"><span className="kpi-l">{t("vendable.produits_autorises")}</span>
            <span className="kpi-v">{res.rayons.reduce((n, r) => n + r.autorises, 0)}</span></div>
        </div>)}
      {res && (() => {
        const accessibles = res.rayons.filter((r) => r.autorises > 0).map((r) => r.code);
        const manquants = accessibles.filter((c) => !suivies.includes(c));
        return (
          <div className="barre-actions">
            <span className="meta">{t(suivies.length === 1 ? "vendable.suivis_1" : "vendable.suivis", { n: suivies.length })}</span>
            {manquants.length > 0 && <button type="button" className="secondaire"
              onClick={() => enregistrer([...suivies, ...manquants])}>{t("vendable.suivre_accessibles", { n: accessibles.length })}</button>}
            {suivies.length > 0 && <a className="bouton-lien" href="#marche">{t("vendable.voir_marche")} →</a>}
          </div>);
      })()}
      <section className="carte" aria-label={t("vendable.titre")}>
        {!res ? <p className="meta">{e?.en_cours ? t("vendable.patience") : t("vendable.jamais")}</p> : (
          <div className="defile"><table>
            <thead><tr><th scope="col" className="case-suivi"><input type="checkbox" aria-label={t("vendable.suivre_tous")}
              checked={rayons.length > 0 && rayons.every((r) => suivies.includes(r.code))}
              ref={(el) => { if (el) el.indeterminate = suivies.length > 0 && !rayons.every((r) => suivies.includes(r.code)); }}
              onChange={(ev) => enregistrer(ev.target.checked ? rayons.map((r) => r.code) : [])} /></th><th scope="col">{t("vendable.rayon")}</th><th scope="col">{t("vendable.statut")}</th><th scope="col">{t("vendable.part")}</th>
              <th scope="col" className="num">{t("vendable.autorises")}</th><th scope="col" className="num">{t("vendable.approbation")}</th>
              <th scope="col"><span className="masque">{t("vendable.voir", { n: "" })}</span></th></tr></thead>
            <tbody>{rayons.map((r) => <Rayon key={r.code} r={r} analyser={analyser} suivi={suivies.includes(r.code)}
              nouveau={!!nouv?.rayons.includes(r.code)} nouveaux={nouv?.produits ?? []}
              basculer={() => enregistrer(suivies.includes(r.code) ? suivies.filter((c) => c !== r.code) : [...suivies, r.code])} />)}</tbody>
          </table></div>)}
      </section>
      <EligibiliteVue analyser={analyser} />
    </div>
  );
}

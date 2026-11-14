import { useEffect, useState } from "react";
import { Exploration, RayonSonde, lancerExploration, lireExploration } from "./api";
import { t } from "./i18n";

// Ce que je peux vendre [RM-AMZ-084, 085] : sondage des rayons, produits autorisés d'abord.
function Rayon({ r, analyser }: { r: RayonSonde; analyser: (code: string) => void }) {
  const [ouvert, setOuvert] = useState(false);
  const autorises = r.produits.filter((p) => p.statut === "AUTORISE");
  const part = r.testes ? r.autorises / r.testes : 0;
  return (
    <>
      <tr>
        <td><strong>{t(`rayon.${r.code}`)}</strong></td>
        <td><span className={`statut-rayon ${r.statut}`}>{t(`rayon.statut.${r.statut}`)}</span></td>
        <td><div className="barre-part" title={`${r.autorises}/${r.testes}`}><div style={{ width: `${part * 100}%` }} /></div></td>
        <td className="num">{r.autorises} / {r.testes}</td>
        <td className="num">{r.approbation}</td>
        <td>{autorises.length > 0 && <button type="button" className="lien" aria-expanded={ouvert} onClick={() => setOuvert(!ouvert)}>
          {t("vendable.voir", { n: autorises.length })}</button>}</td>
      </tr>
      {ouvert && autorises.map((p) => (
        <tr key={p.asin} className="sous-ligne">
          <td colSpan={3}><div className="produit">{p.titre ?? p.asin}</div><div className="meta">{p.asin}{p.categorie ? ` · ${p.categorie}` : ""}</div></td>
          <td className="num meta">{p.bsr ? `BSR ${p.bsr.toLocaleString("fr-FR")}` : "—"}</td>
          <td colSpan={2}><button type="button" className="lien" onClick={() => analyser(p.asin)}>{t("vendable.analyser")}</button></td>
        </tr>))}
    </>
  );
}

export function VendableVue({ analyser }: { analyser: (code: string) => void }) {
  const [e, setE] = useState<Exploration | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  const lire = () => lireExploration().then(setE).catch((x) => setErreur((x as Error).message));
  useEffect(() => { lire(); }, []);
  useEffect(() => {
    if (!e?.en_cours) return;
    const id = setTimeout(lire, 2000);
    return () => clearTimeout(id);
  }, [e]);
  const lancer = () => { setErreur(null); lancerExploration().then(lire).catch((x) => setErreur((x as Error).message)); };
  const res = e?.resultat;
  const rayons = res ? [...res.rayons].sort((a, b) => b.autorises / (b.testes || 1) - a.autorises / (a.testes || 1)) : [];
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
          {["OUVERT", "PARTIEL", "FERME"].map((s) => (
            <div key={s} className="kpi"><span className="kpi-l">{t(`rayon.statut.${s}`)}</span>
              <span className="kpi-v">{res.rayons.filter((r) => r.statut === s).length}</span></div>))}
          <div className="kpi"><span className="kpi-l">{t("vendable.produits_autorises")}</span>
            <span className="kpi-v">{res.rayons.reduce((n, r) => n + r.autorises, 0)}</span></div>
        </div>)}
      <section className="carte" aria-label={t("vendable.titre")}>
        {!res ? <p className="meta">{e?.en_cours ? t("vendable.patience") : t("vendable.jamais")}</p> : (
          <div className="defile"><table>
            <thead><tr><th scope="col">{t("vendable.rayon")}</th><th scope="col">{t("col.suivi")}</th><th scope="col">{t("vendable.part")}</th>
              <th scope="col" className="num">{t("vendable.autorises")}</th><th scope="col" className="num">{t("vendable.approbation")}</th>
              <th scope="col"><span className="masque">{t("vendable.voir", { n: "" })}</span></th></tr></thead>
            <tbody>{rayons.map((r) => <Rayon key={r.code} r={r} analyser={analyser} />)}</tbody>
          </table></div>)}
      </section>
    </div>
  );
}

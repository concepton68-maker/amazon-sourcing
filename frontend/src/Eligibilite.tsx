import { useEffect, useState } from "react";
import { EtatEligibilite, lancerEligibilite, lireEligibilite } from "./api";
import { t } from "./i18n";

// [RM-AMZ-121] vérifier une liste de produits, résultats au fil de l'eau, lien de demande d'autorisation
const STATUTS = ["AUTORISE", "APPROBATION", "INTERDIT", "INTROUVABLE", "INCONNU"];
const TON: Record<string, string> = { AUTORISE: "v", APPROBATION: "a", INTERDIT: "r", INTROUVABLE: "n", INCONNU: "n" };

export function EligibiliteVue({ analyser }: { analyser: (code: string) => void }) {
  const [texte, setTexte] = useState("");
  const [etat, setEtat] = useState<EtatEligibilite | null>(null);
  const [filtre, setFiltre] = useState<string | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  const lire = () => lireEligibilite().then((x) => setEtat(x.etat)).catch(() => undefined);
  useEffect(() => { lire(); }, []);
  useEffect(() => { if (!etat?.en_cours) return; const id = setTimeout(lire, 2000); return () => clearTimeout(id); }, [etat]);
  const fichier = (f?: File) => { if (f) f.text().then((x) => setTexte((avant) => (avant ? avant + "\n" : "") + x)); };
  const lancer = () => { setErreur(null); lancerEligibilite(texte, "FR").then(lire).catch((e) => setErreur((e as Error).message)); };
  const res = etat?.resultats ?? [];
  const visibles = filtre ? res.filter((r) => r.statut === filtre) : res;
  return (
    <section className="carte" aria-label={t("elig.titre")}>
      <div className="entete-vue"><h3>{t("elig.titre")}</h3>
        {etat && <span className="meta">{etat.en_cours ? t("elig.en_cours", { f: res.length, t: etat.total }) : t("elig.fini", { n: res.length })}</span>}</div>
      <div className="saisie-codes">
        <textarea rows={3} placeholder={t("elig.placeholder")} aria-label={t("elig.titre")} value={texte} onChange={(e) => setTexte(e.target.value)} />
        <div className="actions">
          <label className="bouton-lien fichier-bouton">{t("elig.fichier")}<input type="file" accept=".csv,.txt" className="masque" onChange={(e) => fichier(e.target.files?.[0])} /></label>
          <button type="button" className="principal" disabled={!texte.trim() || etat?.en_cours} onClick={lancer}>{t("elig.lancer")}</button>
          {etat && !etat.en_cours && res.length > 0 && <a className="bouton-lien" href="/api/eligibilite/export.csv">{t("sourcing.exporter")}</a>}
        </div>
      </div>
      {erreur && <p role="alert" className="alerte">{t(`erreur.${erreur}`)}</p>}
      {res.length > 0 && <>
        <div className="onglets" role="group">
          <button type="button" aria-pressed={filtre === null} onClick={() => setFiltre(null)}>{t("rent.tous")} · {res.length}</button>
          {STATUTS.map((s) => { const n = res.filter((r) => r.statut === s).length; return n ? (
            <button key={s} type="button" aria-pressed={filtre === s} onClick={() => setFiltre(s)}>{t(`elig.${s}`)} · {n}</button>) : null; })}
        </div>
        <div className="defile"><table className="table-compacte">
          <thead><tr><th scope="col">{t("role.code")}</th><th scope="col">ASIN</th><th scope="col">{t("vendable.statut")}</th><th scope="col" /></tr></thead>
          <tbody>{visibles.map((r) => (
            <tr key={r.code}>
              <td>{r.code}</td>
              <td>{r.asin ? <button type="button" className="lien" onClick={() => analyser(r.asin!)}>{r.asin}</button> : "—"}</td>
              <td><span className="statut-point"><i className={`point ${TON[r.statut]}`} />{t(`elig.${r.statut}`)}</span>
                {r.motifs && r.motifs.length > 0 && <abbr className="info-mini" title={r.motifs.join(" | ")}> ⓘ</abbr>}</td>
              <td>{(r.liens ?? []).map((l) => <a key={l.url} className="lien-externe" href={l.url} target="_blank" rel="noreferrer">{t("elig.demander")} ↗</a>)}</td>
            </tr>))}</tbody>
        </table></div></>}
    </section>
  );
}

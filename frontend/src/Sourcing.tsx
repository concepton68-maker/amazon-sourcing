import { ChangeEvent, FormEvent, useEffect, useState } from "react";
import { Colonnes, Fichier, Params, Place, Suivi, deposerFichier, lancerTraitement, lireParametres, listerPlaces, suivreTraitement, urlExport } from "./api";
import { message, monnaie, pourcent, t } from "./i18n";

const ROLES = ["code", "prix", "designation", "colisage", "minimum"];
const COMPTEURS = ["ACHETER", "A_VERIFIER", "PASSER", "INTROUVABLE", "REJETEE", "DOUBLON", "MEMOIRE"];
const FILTRES = ["TOUS", "ACHETER", "A_VERIFIER", "PASSER", "INTROUVABLE"];
const n = (v: number | null) => (v === null ? null : String(v));

export function SourcingVue({ analyser }: { analyser: (code: string, prix: number) => void }) {
  const [places, setPlaces] = useState<Place[]>([]);
  const [fichier, setFichier] = useState<Fichier | null>(null);
  const [colonnes, setColonnes] = useState<Colonnes>({});
  const [place, setPlace] = useState("FR");
  const [regime, setRegime] = useState("assujetti");
  const [ttc, setTtc] = useState(false);
  const [carton, setCarton] = useState(false);
  const [tid, setTid] = useState<string | null>(null);
  const [suivi, setSuivi] = useState<Suivi | null>(null);
  const [filtre, setFiltre] = useState("TOUS");
  const [erreur, setErreur] = useState<string | null>(null);

  const [params, setParams] = useState<Params | null>(null);
  useEffect(() => {
    listerPlaces().then(setPlaces).catch(() => setErreur("chargement"));
    lireParametres().then(setParams).catch(() => undefined);
  }, []);
  useEffect(() => {
    const r = params?.tva[place];
    if (r && r !== "hors_taxe") setRegime(r);
  }, [params, place]);

  useEffect(() => {
    if (!tid) return;
    let fini = false;
    const tour = () => suivreTraitement(tid).then((s) => {
      setSuivi(s);
      if (s.statut === "EN_COURS" && !fini) setTimeout(tour, 1000);
    }).catch((e) => setErreur(e.message));
    tour();
    return () => { fini = true; };
  }, [tid]);

  const deposer = async (e: ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setErreur(null); setFichier(null); setTid(null); setSuivi(null);
    try { const r = await deposerFichier(f); setFichier(r); setColonnes(r.colonnes); }
    catch (x) { setErreur((x as Error).message); }
  };

  const lancer = async (e: FormEvent) => {
    e.preventDefault();
    if (!fichier) return;
    setErreur(null); setSuivi(null);
    try {
      const r = await lancerTraitement(fichier.fichier_id, { colonnes, marketplace: place, regime_tva: regime,
        achat_ttc: ttc, prix_par_carton: carton });
      setTid(r.traitement_id);
    } catch (x) { setErreur((x as Error).message); }
  };

  const visibles = suivi?.resultats.filter((r) => filtre === "TOUS"
    || (filtre === "INTROUVABLE" ? r.statut === "INTROUVABLE" : r.statut === "ANALYSEE" && r.verdict === filtre)) ?? [];
  const d = suivi?.devise ?? "EUR";

  return (
    <div className="vue">
      <h1>{t("sourcing.titre")}</h1>
      <div className="formulaire">
        <label className="large">{t("sourcing.deposer")}
          <input type="file" accept=".csv,.txt,.xlsx" onChange={deposer} /></label>
        {fichier && <span className="meta">{fichier.nom} · {t("sourcing.lignes", { n: fichier.nb_lignes })}</span>}
      </div>
      {erreur && <p role="alert" className="alerte">{t(`erreur.${erreur}`)}</p>}

      {fichier && (
        <form className="carte" onSubmit={lancer}>
          <h3>{t("sourcing.colonnes")}</h3>
          <div className="formulaire nu">
            {ROLES.map((r) => (
              <label key={r}>{t(`role.${r}`)}
                <select value={colonnes[r] ?? ""} onChange={(e) => setColonnes({ ...colonnes, [r]: e.target.value === "" ? null : Number(e.target.value) })}>
                  <option value="">{t("sourcing.aucune")}</option>
                  {fichier.entetes.map((h, i) => <option key={i} value={i}>{h || `#${i + 1}`}</option>)}
                </select></label>
            ))}
          </div>
          <div className="defile">
            <table aria-label={t("sourcing.apercu")}>
              <thead><tr>{fichier.entetes.map((h, i) => <th key={i} scope="col">{h}</th>)}</tr></thead>
              <tbody>{fichier.apercu.map((l, k) => <tr key={k}>{l.map((c, i) => <td key={i}>{c}</td>)}</tr>)}</tbody>
            </table>
          </div>
          <div className="formulaire nu">
            <label>{t("analyse.place")}
              <select value={place} onChange={(e) => setPlace(e.target.value)}>
                {places.map((p) => <option key={p.code} value={p.code}>{p.domaine}</option>)}
              </select></label>
            <label>{t("analyse.regime")}
              <select value={regime} onChange={(e) => setRegime(e.target.value)}>
                {["assujetti", "non_assujetti"].map((r) => <option key={r} value={r}>{t(`regime.${r}`)}</option>)}
              </select></label>
            <div role="group" aria-label={t("analyse.base_prix")} className="segment">
              <button type="button" aria-pressed={!ttc} onClick={() => setTtc(false)}>{t("analyse.ht")}</button>
              <button type="button" aria-pressed={ttc} onClick={() => setTtc(true)}>{t("analyse.ttc")}</button>
            </div>
            <label className="case"><input type="checkbox" checked={carton} onChange={(e) => setCarton(e.target.checked)} />{t("sourcing.prix_carton")}</label>
            <button type="submit" className="principal" disabled={suivi?.statut === "EN_COURS"}>{t("sourcing.lancer")}</button>
          </div>
        </form>
      )}

      {suivi && (
        <section className="carte" aria-label={t("sourcing.titre")}>
          <div className="entete-resultats">
            <div className="progression" role="progressbar" aria-valuemin={0} aria-valuemax={suivi.total} aria-valuenow={suivi.faits}>
              <div style={{ width: `${suivi.total ? (suivi.faits / suivi.total) * 100 : 100}%` }} />
            </div>
            <span className="meta">{t("sourcing.progression", { faits: suivi.faits, total: suivi.total })}</span>
            {suivi.statut === "TERMINE" && tid && <a className="bouton-lien" href={urlExport(tid)} download>{t("sourcing.exporter")}</a>}
          </div>
          <ul className="compteurs" role="list">
            {COMPTEURS.map((c) => <li key={c} className={`compteur ${c}`}><strong>{suivi.compteurs[c] ?? 0}</strong> {t(`compteur.${c}`)}</li>)}
          </ul>
          <div role="group" className="onglets" aria-label={t("col.verdict")}>
            {FILTRES.map((f) => (
              <button key={f} type="button" aria-pressed={filtre === f} onClick={() => setFiltre(f)}>
                {f === "TOUS" ? t("sourcing.tous") : t(`compteur.${f}`)}</button>
            ))}
          </div>
          <div className="defile">
            <table className="resultats">
              <thead><tr>
                <th scope="col">{t("col.ligne")}</th><th scope="col">{t("col.produit")}</th>
                <th scope="col" className="num">{t("col.cout")}</th><th scope="col" className="num">{t("col.vente")}</th>
                <th scope="col" className="num">{t("col.profit")}</th><th scope="col" className="num">{t("col.roi")}</th>
                <th scope="col" className="num">{t("col.ventes")}</th><th scope="col">{t("col.verdict")}</th>
                <th scope="col">{t("col.remarques")}</th><th scope="col"><span className="masque">{t("action.analyser")}</span></th>
              </tr></thead>
              <tbody>
                {visibles.map((r) => {
                  const msgs = [...r.remarques, ...r.raisons, ...r.alertes];
                  return (
                    <tr key={`${r.ligne}-${r.asin ?? r.code}`}>
                      <td>{r.ligne}</td>
                      <td><div className="produit">{r.titre ?? r.designation ?? r.code}</div>
                        <div className="meta">{r.code}{r.asin ? ` · ${r.asin}` : ""}{r.unites_lot > 1 ? ` · ×${r.unites_lot}` : ""}</div></td>
                      <td className="num">{monnaie(n(r.cout_achat ?? r.prix_unitaire), d)}</td>
                      <td className="num">{monnaie(n(r.prix_vente), d)}</td>
                      <td className={`num ${r.profit !== null && r.profit <= 0 ? "negatif" : ""}`}>{monnaie(n(r.profit), d)}</td>
                      <td className="num">{pourcent(n(r.roi))}</td>
                      <td className="num">{r.ventes_mois ?? "—"}</td>
                      <td>{r.statut === "ANALYSEE" && r.verdict
                        ? <span className={`verdict ${r.verdict}`}>{t(`verdict.${r.verdict}`)}</span>
                        : <span className="verdict PASSER">{t(`statut.${r.statut}`)}</span>}</td>
                      <td className="remarques">{msgs.slice(0, 2).map((m, i) => <div key={i}>{message(m, d)}</div>)}</td>
                      <td>{r.statut === "ANALYSEE" && <button type="button" className="lien"
                        onClick={() => analyser(r.code, r.prix_unitaire)}>{t("action.analyser")}</button>}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          {suivi.rejets.length > 0 && (
            <div className="bloc-msgs"><h4>{t("rejets.titre")}</h4>
              <ul className="msgs discret" role="list">
                {suivi.rejets.map((x) => <li key={x.ligne}>{t("col.ligne")} {x.ligne} : {message(x.message, d)}</li>)}
              </ul></div>
          )}
        </section>
      )}
    </div>
  );
}

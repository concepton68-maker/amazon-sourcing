import { FormEvent, useEffect, useState } from "react";
import { Connexions, EtapeTest, TacheSynchro, lireJournalSynchro, SourceConnexion, ecrireConnexion, lireConnexions, retirerConnexion, testerConnexion } from "./api";
import { dateCourte, t } from "./i18n";

// Où trouver chaque code chez Amazon (adresses données par Sam et par la documentation Amazon)
const OU_TROUVER: Record<string, string> = {
  seller_id: "https://sellercentral.amazon.fr/global-dashboard/business-information",
  client_id: "https://solutionproviderportal.amazon.com/",
  client_secret: "https://solutionproviderportal.amazon.com/",
  refresh_token: "https://solutionproviderportal.amazon.com/",
};

function Source({ s, regions, maj }: { s: SourceConnexion; regions: string[]; maj: () => void }) {
  const vide = () => Object.fromEntries(s.champs.map((c) => [c, c === "region" ? "EU" : ""]));
  const [v, setV] = useState<Record<string, string>>(vide);
  const [ouvert, setOuvert] = useState(!s.enregistree_le);
  const [erreur, setErreur] = useState<string | null>(null);
  const [test, setTest] = useState<EtapeTest[] | null>(null);
  const [enTest, setEnTest] = useState(false);
  const tester = () => { setEnTest(true); setTest(null); setErreur(null);
    testerConnexion("FR").then((r) => setTest(r.etapes)).catch((x) => setErreur((x as Error).message)).finally(() => setEnTest(false)); };
  const envoyer = (e: FormEvent) => {
    e.preventDefault();
    ecrireConnexion(s.source, v).then(() => { setV(vide()); setOuvert(false); setErreur(null); maj(); })
      .catch((x) => setErreur((x as Error).message));
  };
  return (
    <div className="carte">
      <h3>{t(`connexion.${s.source}`)}</h3>
      <p className="meta">{s.enregistree_le ? t("connexion.enregistree", { date: dateCourte(s.enregistree_le) }) : t("connexion.absente")}</p>
      {ouvert ? (
        <form onSubmit={envoyer} autoComplete="off">
          {s.champs.map((c) => c === "region"
            ? <label key={c} className="ligne-reglage">{t("connexion.champ.region")}
                <select value={v.region} onChange={(e) => setV({ ...v, region: e.target.value })}>
                  {regions.map((r) => <option key={r} value={r}>{t(`connexion.region.${r}`)}</option>)}</select></label>
            : <label key={c} className="ligne-reglage"><span>{t(`connexion.champ.${c}`)}
                {s.source === "SPAPI" && OU_TROUVER[c] && <> · <a href={OU_TROUVER[c]} target="_blank" rel="noreferrer">{t("connexion.ou_trouver")}</a></>}</span>
                <input type={c === "seller_id" ? "text" : "password"} autoComplete="new-password" spellCheck={false} maxLength={2000}
                  required={!s.enregistree_le && c !== "seller_id"}
                  placeholder={s.enregistree_le ? t("connexion.inchange") : undefined}
                  value={v[c]} onChange={(e) => setV({ ...v, [c]: e.target.value })} /></label>)}
          <div className="formulaire nu">
            <button type="submit" className="principal">{t("connexion.enregistrer")}</button>
            {s.enregistree_le && <button type="button" className="secondaire" onClick={() => setOuvert(false)}>{t("connexion.annuler")}</button>}
          </div>
        </form>
      ) : (
        <div className="formulaire nu">
          {s.source === "SPAPI" && <button type="button" className="principal" disabled={enTest} onClick={tester}>
            {enTest ? t("connexion.test_en_cours") : t("connexion.tester")}</button>}
          <button type="button" className="secondaire" onClick={() => setOuvert(true)}>{t("connexion.remplacer")}</button>
          <button type="button" className="lien" onClick={() => retirerConnexion(s.source).then(maj).catch((x) => setErreur((x as Error).message))}>{t("connexion.retirer")}</button>
        </div>
      )}
      {test && <ul className="test-connexion">{test.map((e) => (
        <li key={e.etape} className={e.ok === null ? "neutre" : e.ok ? "ok" : "ko"}>
          <strong>{e.ok === null ? "—" : e.ok ? "✓" : "✗"} {t(`connexion.etape.${e.etape}`)}</strong>
          {e.ok === false && <div className="meta">{e.statut ?? ""} {e.message}{e.requete ? ` · ${t("connexion.requete")} ${e.requete}` : ""}</div>}
          {e.ok !== false && e.message && <div className="meta">{e.message}</div>}
        </li>))}</ul>}
      {erreur && <p role="alert" className="alerte">{t(`erreur.${erreur}`)}</p>}
    </div>
  );
}

function JournalSynchro() {
  const [j, setJ] = useState<TacheSynchro[] | null>(null);
  useEffect(() => { lireJournalSynchro().then(setJ).catch(() => setJ([])); }, []);
  if (!j) return null;
  return (
    <section className="carte" aria-label={t("synchro.titre")}>
      <h3>{t("synchro.titre")}</h3>
      {j.length === 0 ? <p className="meta">{t("synchro.vide")}</p> : (
        <ul className="test-connexion">{j.map((x, i) => (
          <li key={i} className={x.ok ? "ok" : "ko"}>
            <strong>{x.ok ? "✓" : "✗"} {t(`synchro.${x.tache}`)}</strong> <span className="meta">{new Date(x.le).toLocaleString("fr-FR")}</span>
            {x.message && <div className="meta">{x.message}</div>}
          </li>))}</ul>)}
    </section>
  );
}

export function ConnexionsVue() {
  const [c, setC] = useState<Connexions | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  const maj = () => lireConnexions().then(setC).catch((e) => setErreur((e as Error).message));
  useEffect(() => { maj(); }, []);
  if (erreur) return <p role="alert" className="alerte">{t(`erreur.${erreur}`)}</p>;
  if (!c) return null;
  return (
    <section aria-label={t("connexion.titre")}>
      <h2>{t("connexion.titre")}</h2>
      {!c.chiffrement && <p role="alert" className="alerte">{t("erreur.CHIFFREMENT_NON_CONFIGURE")}</p>}
      <JournalSynchro />
      <div className="grille trois">{c.sources.map((s) => <Source key={s.source + (s.enregistree_le ?? "")} s={s} regions={c.regions} maj={maj} />)}</div>
    </section>
  );
}

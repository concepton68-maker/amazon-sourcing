import { FormEvent, useEffect, useState } from "react";
import { Connexions, EtapeTest, EtatMessagerie, deconnecterMessagerie, demarrerMessagerie, lireMessagerie, EtatManuel, TacheSynchro, lancerSynchroManuelle, lireJournalSynchro, lireSynchroManuelle, SourceConnexion, ecrireConnexion, lireConnexions, retirerConnexion, testerConnexion } from "./api";
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
            : <label key={c} className="ligne-reglage"><span>{t(s.source === "MICROSOFT" ? `connexion.ms.${c}` : `connexion.champ.${c}`)}
                {s.source === "SPAPI" && OU_TROUVER[c] && <a className="info" href={OU_TROUVER[c]} target="_blank" rel="noreferrer"
                  title={t("connexion.ou_trouver")} aria-label={`${t("connexion.ou_trouver")} : ${t(`connexion.champ.${c}`)}`}>i</a>}</span>
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

// Où voir les données de chaque tâche, une fois finie [RM-AMZ-134]
const DESTINATION: Record<string, string> = { VENTES: "#tableau", STOCK: "#stock", REMBOURSEMENTS: "#remboursements",
  PRIX: "#stock", EXPLORATION: "#vendable", HISTORIQUE: "#marche", CORRESPONDANCE: "#rentables" };
const duree = (s: number) => (s < 60 ? `${s} s` : `${Math.floor(s / 60)} min ${String(s % 60).padStart(2, "0")} s`);

// [RM-AMZ-115] lancer les travaux de nuit maintenant, avancement réel
function TravauxManuels({ fini }: { fini: () => void }) {
  const [taches, setTaches] = useState<string[]>([]);
  const [choix, setChoix] = useState<string[]>([]);
  const [etat, setEtat] = useState<EtatManuel | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  const [maintenant, setMaintenant] = useState(Date.now());
  useEffect(() => { if (!etat?.en_cours) return; const id = setInterval(() => setMaintenant(Date.now()), 1000); return () => clearInterval(id); }, [etat?.en_cours]);
  const lire = () => lireSynchroManuelle().then((x) => {
    setTaches(x.taches); setChoix((c) => (c.length ? c : x.taches));
    setEtat((avant) => { if (avant?.en_cours && x.etat && !x.etat.en_cours) fini(); return x.etat; });
  }).catch(() => undefined);
  useEffect(() => { lire(); }, []);
  useEffect(() => { if (!etat?.en_cours) return; const id = setTimeout(lire, 2000); return () => clearTimeout(id); }, [etat]);
  const lancer = () => { setErreur(null); lancerSynchroManuelle(choix).then(lire).catch((e) => setErreur((e as Error).message)); };
  const basculer = (x: string) => setChoix((c) => (c.includes(x) ? c.filter((y) => y !== x) : [...c, x]));
  const statut = (x: string) => {
    if (!etat || !etat.taches.includes(x)) return null;
    const r = etat.terminees.find((y) => y.tache === x);
    if (r) return <span className={r.ok ? "positif" : "negatif"}>{r.ok ? "✓" : "✗"} {r.message}
      {r.ok && DESTINATION[x] && <> · <a href={DESTINATION[x]}>{t("manuel.voir")}</a></>}</span>;
    if (etat.courante !== x) return <span className="meta">{etat.en_cours ? t("manuel.attente") : ""}</span>;
    const depuis = etat.debut_tache ? Math.max(0, Math.round((maintenant - Date.parse(etat.debut_tache)) / 1000)) : null;
    const vu = etat.vu ? Math.max(0, Math.round((maintenant - Date.parse(etat.vu)) / 1000)) : null;
    return <span className="en-cours"><span className="point-pulse" aria-hidden="true" /> {etat.detail ?? t("manuel.en_cours")}
      {depuis !== null && <span className="meta"> · {t("manuel.depuis", { d: duree(depuis) })}</span>}
      {vu !== null && <span className="meta"> · {t("manuel.vu", { d: duree(vu) })}</span>}</span>;
  };
  return (
    <section className="carte" aria-label={t("manuel.titre")}>
      <div className="entete-vue"><h3>{t("manuel.titre")}</h3>
        <button type="button" className="principal" disabled={etat?.en_cours || choix.length === 0} onClick={lancer}>
          {etat?.en_cours ? t("manuel.en_cours_n", { f: etat.terminees.length, t: etat.taches.length }) : t("manuel.lancer", { n: choix.length })}</button></div>
      {erreur && <p role="alert" className="alerte">{t(`erreur.${erreur}`)}</p>}
      <table className="table-compacte"><tbody>
        <tr className="cliquable" onClick={(e) => { if (!(e.target as HTMLElement).closest("input")) setChoix(choix.length === taches.length ? [] : taches); }}>
          <td className="case-suivi"><input type="checkbox" aria-label={t("annuaire.tout")} checked={choix.length === taches.length}
            onChange={() => setChoix(choix.length === taches.length ? [] : taches)} /></td><td colSpan={2}><strong>{t("annuaire.tout")}</strong></td></tr>
        {taches.map((x) => (
          <tr key={x} className={`cliquable ${choix.includes(x) ? "choisie" : ""}`} onClick={(e) => { if (!(e.target as HTMLElement).closest("input")) basculer(x); }}>
            <td className="case-suivi"><input type="checkbox" aria-label={t(`synchro.${x}`)} checked={choix.includes(x)} onChange={() => basculer(x)} /></td>
            <td>{t(`synchro.${x}`)}</td><td className="etat-tache">{statut(x)}</td>
          </tr>))}
      </tbody></table>
      {etat?.fin && !etat.en_cours && <p className="meta">{t("manuel.fini", { date: new Date(etat.fin).toLocaleString("fr-FR") })}</p>}
    </section>
  );
}

function JournalSynchro({ version }: { version: number }) {
  const [j, setJ] = useState<TacheSynchro[] | null>(null);
  useEffect(() => { lireJournalSynchro().then(setJ).catch(() => setJ([])); }, [version]);
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

// Ma messagerie [RM-AMZ-129] : l'adresse de retour à déclarer chez Microsoft, puis la connexion de la boîte.
function Messagerie() {
  const [m, setM] = useState<EtatMessagerie | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  const [copie, setCopie] = useState(false);
  const retour = new URLSearchParams(window.location.search);
  const resultat = retour.get("messagerie");
  useEffect(() => { lireMessagerie().then(setM).catch((x) => setErreur((x as Error).message)); }, []);
  if (!m) return null;
  const copier = () => navigator.clipboard?.writeText(m.adresse_retour).then(() => setCopie(true)).catch(() => undefined);
  const connecter = () => demarrerMessagerie().then((r) => { window.location.href = r.url; }).catch((x) => setErreur((x as Error).message));
  return (
    <div className="carte">
      <h3>{t("messagerie.titre")}</h3>
      {resultat === "ok" && <p role="status" className="succes">{t("messagerie.connectee_ok")}</p>}
      {resultat === "erreur" && <p role="alert" className="alerte">{t(`messagerie.cause.${retour.get("cause") ?? "inconnue"}`)}</p>}
      <div className="ligne-reglage"><span>{t("messagerie.adresse_retour")}</span>
        <span className="code-copie"><code>{m.adresse_retour}</code>
          <button type="button" className="lien" onClick={copier}>{copie ? t("messagerie.copiee") : t("messagerie.copier")}</button></span></div>
      {!m.configuree ? <p className="meta">{t("messagerie.non_configuree")}</p>
        : m.connexion ? <>
            <div className="ligne-reglage"><span>{t("messagerie.boite")}</span><strong>{m.connexion.adresse}</strong></div>
            {m.connexion.etat === "A_RECONNECTER" && <p role="alert" className="alerte">{t("messagerie.a_reconnecter")}</p>}
            <div className="formulaire nu">
              {m.connexion.etat === "A_RECONNECTER" && <button type="button" className="principal" onClick={connecter}>{t("messagerie.reconnecter")}</button>}
              <button type="button" className="lien" onClick={() => deconnecterMessagerie().then(() => lireMessagerie().then(setM))}>{t("messagerie.deconnecter")}</button>
            </div></>
        : <div className="formulaire nu"><button type="button" className="principal" onClick={connecter}>{t("messagerie.connecter")}</button></div>}
      <p className="meta">{t("messagerie.droit")}</p>
      {erreur && <p role="alert" className="alerte">{t(`erreur.${erreur}`)}</p>}
    </div>
  );
}

export function ConnexionsVue() {
  const [c, setC] = useState<Connexions | null>(null);
  const [version, setVersion] = useState(0);
  const [erreur, setErreur] = useState<string | null>(null);
  const maj = () => lireConnexions().then(setC).catch((e) => setErreur((e as Error).message));
  useEffect(() => { maj(); }, []);
  if (erreur) return <p role="alert" className="alerte">{t(`erreur.${erreur}`)}</p>;
  if (!c) return null;
  return (
    <section aria-label={t("connexion.titre")}>
      <h2>{t("connexion.titre")}</h2>
      {!c.chiffrement && <p role="alert" className="alerte">{t("erreur.CHIFFREMENT_NON_CONFIGURE")}</p>}
      <TravauxManuels fini={() => setVersion((v) => v + 1)} />
      <JournalSynchro version={version} />
      <div className="grille trois">{c.sources.map((s) => <Source key={s.source + (s.enregistree_le ?? "")} s={s} regions={c.regions} maj={maj} />)}
        <Messagerie key={c.sources.find((s) => s.source === "MICROSOFT")?.enregistree_le ?? "m"} /></div>
    </section>
  );
}

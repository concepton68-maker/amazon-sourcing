import { FormEvent, useEffect, useState } from "react";
import { Marque } from "./Marque";
import { changerMotDePasse, confirmerEnrolement, connecter, debuterEnrolement, envoyerCode, etapeSession } from "./api";
import { t } from "./i18n";

// Étapes [RM-AMZ-075, 076] : MOT_DE_PASSE → (CHANGER_MDP) → ENROLER (QR, codes de secours) ou CODE → COMPLET.
export function Connexion({ connecte }: { connecte: () => void }) {
  const [etape, setEtape] = useState("MOT_DE_PASSE");
  const [courriel, setCourriel] = useState("");
  const [mdp, setMdp] = useState("");
  const [mdp2, setMdp2] = useState("");
  const [code, setCode] = useState("");
  const [enrol, setEnrol] = useState<{ secret: string; qr: string } | null>(null);
  const [secours, setSecours] = useState<string[] | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  const [envoi, setEnvoi] = useState(false);

  useEffect(() => { etapeSession().then((e) => { if (e && e !== "COMPLET") setEtape(e); }); }, []);
  useEffect(() => {
    if (etape === "ENROLER" && !enrol) debuterEnrolement().then(setEnrol).catch((x) => setErreur((x as Error).message));
  }, [etape, enrol]);

  const suite = (e: string) => { setErreur(null); setCode(""); if (e === "COMPLET") connecte(); else setEtape(e); };
  const agir = (f: () => Promise<void>) => async (e: FormEvent) => {
    e.preventDefault(); setErreur(null); setEnvoi(true);
    try { await f(); } catch (x) { setErreur((x as Error).message); } finally { setEnvoi(false); }
  };

  const champCode = (
    <label>{t("connexion.code")}
      <input type="text" inputMode="numeric" autoComplete="one-time-code" required maxLength={20} value={code}
        onChange={(e) => setCode(e.target.value)} /></label>);

  let contenu;
  if (secours) {
    contenu = (<>
      <h1>{t("connexion.secours_titre")}</h1>
      <p className="meta">{t("connexion.secours_aide")}</p>
      <ul className="codes-secours">{secours.map((c) => <li key={c}><code>{c}</code></li>)}</ul>
      <button type="button" className="principal" onClick={connecte}>{t("connexion.secours_ok")}</button>
    </>);
  } else if (etape === "CHANGER_MDP") {
    contenu = (<form onSubmit={agir(async () => {
      if (mdp !== mdp2) throw new Error("MOTS_DE_PASSE_DIFFERENTS");
      const r = await changerMotDePasse(mdp); setMdp(""); setMdp2(""); suite(r.etape);
    })}>
      <h1>{t("connexion.changer_titre")}</h1>
      <p className="meta">{t("connexion.regle_mdp")}</p>
      <label>{t("connexion.nouveau_mdp")}<input type="password" autoComplete="new-password" required value={mdp} onChange={(e) => setMdp(e.target.value)} /></label>
      <label>{t("connexion.confirmer_mdp")}<input type="password" autoComplete="new-password" required value={mdp2} onChange={(e) => setMdp2(e.target.value)} /></label>
      {erreur && <p role="alert" className="alerte">{t(`erreur.${erreur}`)}</p>}
      <button type="submit" className="principal" disabled={envoi}>{t("connexion.valider")}</button>
    </form>);
  } else if (etape === "ENROLER") {
    contenu = (<form onSubmit={agir(async () => { const r = await confirmerEnrolement(code); setSecours(r.codes_secours); })}>
      <h1>{t("connexion.enrolement_titre")}</h1>
      <p className="meta">{t("connexion.enrolement_aide")}</p>
      {enrol && <>
        <img className="qr" src={enrol.qr} alt={t("connexion.qr")} width={200} height={200} />
        <p className="meta">{t("connexion.cle_manuelle")} <code className="secret">{enrol.secret}</code></p>
      </>}
      {champCode}
      {erreur && <p role="alert" className="alerte">{t(`erreur.${erreur}`)}</p>}
      <button type="submit" className="principal" disabled={envoi || !enrol}>{t("connexion.valider")}</button>
    </form>);
  } else if (etape === "CODE") {
    contenu = (<form onSubmit={agir(async () => { suite((await envoyerCode(code)).etape); })}>
      <h1>{t("connexion.code_titre")}</h1>
      <p className="meta">{t("connexion.code_aide")}</p>
      {champCode}
      {erreur && <p role="alert" className="alerte">{t(`erreur.${erreur}`)}</p>}
      <button type="submit" className="principal" disabled={envoi}>{t("connexion.valider")}</button>
    </form>);
  } else {
    contenu = (<form onSubmit={agir(async () => { const r = await connecter(courriel, mdp); setMdp(""); suite(r.etape); })}>
      <h1>{t("connexion.titre")}</h1>
      <label>{t("connexion.courriel")}
        <input type="email" autoComplete="username" required value={courriel} onChange={(e) => setCourriel(e.target.value)} /></label>
      <label>{t("connexion.mdp")}
        <input type="password" autoComplete="current-password" required value={mdp} onChange={(e) => setMdp(e.target.value)} /></label>
      {erreur && <p role="alert" className="alerte">{t(`erreur.${erreur}`)}</p>}
      <button type="submit" className="principal" disabled={envoi}>{t("connexion.valider")}</button>
    </form>);
  }
  return (
    <main className="connexion">
      <div className="carte"><div className="marque-connexion"><Marque /></div>{contenu}</div>
    </main>
  );
}

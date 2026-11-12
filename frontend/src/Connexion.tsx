import { FormEvent, useState } from "react";
import { connecter } from "./api";
import { t } from "./i18n";

export function Connexion({ connecte }: { connecte: () => void }) {
  const [courriel, setCourriel] = useState("");
  const [mdp, setMdp] = useState("");
  const [erreur, setErreur] = useState<string | null>(null);
  const [envoi, setEnvoi] = useState(false);
  const valider = async (e: FormEvent) => {
    e.preventDefault();
    setErreur(null); setEnvoi(true);
    try { await connecter(courriel, mdp); setMdp(""); connecte(); }
    catch (x) { setErreur((x as Error).message); }
    finally { setEnvoi(false); }
  };
  return (
    <main className="connexion">
      <form className="carte" onSubmit={valider}>
        <span className="marque">{t("app.nom")}</span>
        <h1>{t("connexion.titre")}</h1>
        <label>{t("connexion.courriel")}
          <input type="email" autoComplete="username" required value={courriel} onChange={(e) => setCourriel(e.target.value)} /></label>
        <label>{t("connexion.mdp")}
          <input type="password" autoComplete="current-password" required value={mdp} onChange={(e) => setMdp(e.target.value)} /></label>
        {erreur && <p role="alert" className="alerte">{t(`erreur.${erreur}`)}</p>}
        <button type="submit" className="principal" disabled={envoi}>{t("connexion.valider")}</button>
      </form>
    </main>
  );
}

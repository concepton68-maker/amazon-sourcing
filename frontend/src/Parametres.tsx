import { FormEvent, useEffect, useState } from "react";
import { Params, Place, ecrireParametres, lireParametres, listerPlaces } from "./api";
import { t } from "./i18n";
import { ConnexionsVue } from "./Connexions";

const POURCENT = new Set(["roi_min", "ecart_prix_max", "retours"]);
const SEUILS = ["roi_min", "profit_min", "ventes_mois_min", "part_ventes_min", "ecart_prix_max"] as const;
const COUTS = ["envoi", "preparation", "stockage", "retours"] as const;
const STOCK = ["delai_fournisseur", "delai_reception", "marge_securite", "seuil_rupture", "seuil_surstock"] as const;
type Cle = (typeof SEUILS)[number] | (typeof COUTS)[number] | (typeof STOCK)[number];

const versSaisie = (k: string, v: number) => String(POURCENT.has(k) ? Math.round(v * 10000) / 100 : v).replace(".", ",");
const depuisSaisie = (k: string, s: string) => { const n = Number(s.replace(",", ".")); return POURCENT.has(k) ? n / 100 : n; };

export function ParametresVue() {
  const [places, setPlaces] = useState<Place[]>([]);
  const [p, setP] = useState<Params | null>(null);
  const [saisie, setSaisie] = useState<Record<string, string>>({});
  const [tva, setTva] = useState<Record<string, string>>({});
  const [etat, setEtat] = useState<string | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);

  useEffect(() => {
    listerPlaces().then(setPlaces).catch(() => setErreur("chargement"));
    lireParametres().then((x) => {
      setP(x); setTva(x.tva);
      setSaisie(Object.fromEntries([...SEUILS, ...COUTS, ...STOCK].map((k) => [k, versSaisie(k, x[k])])));
    }).catch((e) => setErreur(e.message));
  }, []);

  const enregistrer = async (e: FormEvent) => {
    e.preventDefault();
    setErreur(null); setEtat(null);
    const valeurs = Object.fromEntries([...SEUILS, ...COUTS, ...STOCK].map((k) => [k, depuisSaisie(k, saisie[k] ?? "0")])) as Record<Cle, number>;
    try {
      const r = await ecrireParametres({ ...valeurs, tva: Object.fromEntries(Object.entries(tva).filter(([, v]) => v !== "hors_taxe")) });
      setP(r); setEtat(t("parametres.enregistre", { v: r.versions }));
    } catch (x) { setErreur((x as Error).message); }
  };

  if (!p) return erreur ? <p role="alert" className="alerte">{t(`erreur.${erreur}`)}</p> : <p>{t("chargement")}</p>;
  const champ = (k: Cle) => (
    <label key={k} className="ligne-reglage">{t(`champ.${k}`)}
      <input type="text" inputMode="decimal" required value={saisie[k] ?? ""}
        onChange={(e) => setSaisie({ ...saisie, [k]: e.target.value })} /></label>
  );
  const [code, champErreur] = (erreur ?? "").split("|");
  return (
    <div className="vue">
    <form className="vue" onSubmit={enregistrer}>
      <div className="entete-vue">
        <h1>{t("parametres.titre")}</h1>
        <button type="submit" className="principal">{t("parametres.enregistrer")}</button>
      </div>
      {erreur && <p role="alert" className="alerte">{t(`erreur.${code}`, { champ: champErreur ? t(`champ.${champErreur}`) : "" })}</p>}
      {etat && <p role="status" className="succes">{etat}</p>}
      <div className="grille trois">
        <div className="carte"><h3>{t("parametres.seuils")}</h3>{SEUILS.map(champ)}</div>
        <div className="carte"><h3>{t("parametres.couts")}</h3>{COUTS.map(champ)}
          <h3 className="sous-titre">{t("parametres.stock")}</h3>{STOCK.map(champ)}</div>
        <div className="carte"><h3>{t("parametres.tva")}</h3>
          <div className="liste-tva">
            {places.map((pl) => (
              <label key={pl.code} className="ligne-reglage">{pl.domaine}
                {tva[pl.code] === "hors_taxe"
                  ? <span className="etiquette">{t("regime.hors_taxe")}</span>
                  : <select value={tva[pl.code] ?? "assujetti"} onChange={(e) => setTva({ ...tva, [pl.code]: e.target.value })}>
                      <option value="assujetti">{t("regime.assujetti")}</option>
                      <option value="non_assujetti">{t("regime.non_assujetti")}</option>
                    </select>}
              </label>
            ))}
          </div>
        </div>
      </div>
    </form>
    <ConnexionsVue />
    </div>
  );
}

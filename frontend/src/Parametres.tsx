import { FormEvent, useEffect, useState } from "react";
import { Params, Place, ecrireParametres, lireParametres, listerPlaces } from "./api";
import { t } from "./i18n";
import { ConnexionsVue } from "./Connexions";

const POURCENT = new Set(["roi_min", "ecart_prix_max", "retours", "carburant_taux"]);
const SEUILS = ["roi_min", "profit_min", "ventes_mois_min", "part_ventes_min", "ecart_prix_max"] as const;
const COUTS = ["port_fournisseur", "envoi", "preparation", "placement", "retours"] as const;
const FRAIS = ["carburant_taux", "duree_stock_mois", "stockage"] as const;
const STOCK = ["delai_fournisseur", "delai_reception", "marge_securite", "seuil_rupture", "seuil_surstock"] as const;
type Cle = (typeof SEUILS)[number] | (typeof COUTS)[number] | (typeof FRAIS)[number] | (typeof STOCK)[number];
const TOUS = [...SEUILS, ...COUTS, ...FRAIS, ...STOCK];
const RUBRIQUES = ["objectifs", "couts", "frais", "stock", "tva", "societe", "connexions"] as const;
const SOCIETE = ["raison_sociale", "adresse", "adresse_livraison", "tva_intra", "courriel", "telephone",
  "expedition_rue", "expedition_cp", "expedition_ville", "expedition_pays"] as const;
const LONGS = new Set(["adresse", "adresse_livraison"]);
type Rubrique = (typeof RUBRIQUES)[number];
const rubriqueDepuisAdresse = (): Rubrique => {
  const r = window.location.hash.split("/")[1] as Rubrique;
  return RUBRIQUES.includes(r) ? r : "objectifs";
};

const versSaisie = (k: string, v: number) => String(POURCENT.has(k) ? Math.round(v * 10000) / 100 : v).replace(".", ",");
const depuisSaisie = (k: string, s: string) => { const n = Number(s.replace(",", ".")); return POURCENT.has(k) ? n / 100 : n; };

export function ParametresVue() {
  const [places, setPlaces] = useState<Place[]>([]);
  const [p, setP] = useState<Params | null>(null);
  const [saisie, setSaisie] = useState<Record<string, string>>({});
  const [tva, setTva] = useState<Record<string, string>>({});
  const [etat, setEtat] = useState<string | null>(null);
  const [carburantActif, setCarburantActif] = useState(true);
  const [societe, setSociete] = useState<Params["societe"]>({});
  const [rubrique, setRubrique] = useState<Rubrique>(rubriqueDepuisAdresse());
  useEffect(() => {
    const suivre = () => setRubrique(rubriqueDepuisAdresse());
    window.addEventListener("hashchange", suivre);
    return () => window.removeEventListener("hashchange", suivre);
  }, []);
  const [erreur, setErreur] = useState<string | null>(null);

  useEffect(() => {
    listerPlaces().then(setPlaces).catch(() => setErreur("chargement"));
    lireParametres().then((x) => {
      setP(x); setTva(x.tva); setCarburantActif(x.carburant_actif === 1); setSociete(x.societe ?? {});
      setSaisie(Object.fromEntries(TOUS.map((k) => [k, versSaisie(k, x[k])])));
    }).catch((e) => setErreur(e.message));
  }, []);

  const enregistrer = async (e: FormEvent) => {
    e.preventDefault();
    setErreur(null); setEtat(null);
    const valeurs = Object.fromEntries(TOUS.map((k) => [k, depuisSaisie(k, saisie[k] ?? "0")])) as Record<Cle, number>;
    try {
      const r = await ecrireParametres({ ...valeurs, carburant_actif: carburantActif ? 1 : 0, societe, tva: Object.fromEntries(Object.entries(tva).filter(([, v]) => v !== "hors_taxe")) });
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
  const ref = p.reference_carburant;
  return (
    <div className="vue">
      <h1>{t("parametres.titre")}</h1>
      <div className="reglages">
        <nav className="sous-menu" aria-label={t("parametres.titre")}>
          {RUBRIQUES.map((r) => <a key={r} href={`#parametres/${r}`} aria-current={r === rubrique ? "page" : undefined}>{t(`rubrique.${r}`)}</a>)}
        </nav>
        <div className="reglages-corps">
          {rubrique === "connexions" ? <ConnexionsVue /> : (
            <form className="carte" onSubmit={enregistrer}>
              <div className="entete-vue"><h2>{t(`rubrique.${rubrique}`)}</h2>
                <button type="submit" className="principal">{t("parametres.enregistrer")}</button></div>
              {erreur && <p role="alert" className="alerte">{t(`erreur.${code}`, { champ: champErreur ? t(`champ.${champErreur}`) : "" })}</p>}
              {etat && <p role="status" className="succes">{etat}</p>}
              {rubrique === "objectifs" && SEUILS.map(champ)}
              {rubrique === "couts" && COUTS.map(champ)}
              {rubrique === "frais" && <>
                <h3 className="sous-titre">{t("rubrique.carburant")}</h3>
                <label className="ligne-reglage case-reglage"><span>{t("champ.carburant_actif")}</span>
                  <input type="checkbox" checked={carburantActif} onChange={(e) => setCarburantActif(e.target.checked)} /></label>
                {champ("carburant_taux")}
                {ref && <p className="meta">{t("parametres.reference_carburant", { taux: versSaisie("carburant_taux", ref.taux), date: ref.depuis.split("-").reverse().join("/") })}</p>}
                <h3 className="sous-titre">{t("rubrique.stockage")}</h3>
                {champ("duree_stock_mois")}{champ("stockage")}
              </>}
              {rubrique === "stock" && STOCK.map(champ)}
              {rubrique === "societe" && SOCIETE.map((k) => (                 /* [RM-AMZ-127] */
                <label key={k} className="ligne-reglage">{t(`societe.${k}`)}
                  {LONGS.has(k)
                    ? <textarea rows={3} maxLength={500} value={societe[k] ?? ""} placeholder={k === "adresse_livraison" ? t("societe.comme_adresse") : undefined}
                        onChange={(e) => setSociete({ ...societe, [k]: e.target.value })} />
                    : <input type={k === "courriel" ? "email" : "text"} maxLength={300} value={societe[k] ?? ""}
                        onChange={(e) => setSociete({ ...societe, [k]: e.target.value })} />}
                </label>))}
              {rubrique === "tva" && <div className="liste-tva">
                {places.map((pl) => (
                  <label key={pl.code} className="ligne-reglage">{pl.domaine}
                    {tva[pl.code] === "hors_taxe"
                      ? <span className="etiquette">{t("regime.hors_taxe")}</span>
                      : <select value={tva[pl.code] ?? "assujetti"} onChange={(e) => setTva({ ...tva, [pl.code]: e.target.value })}>
                          <option value="assujetti">{t("regime.assujetti")}</option>
                          <option value="non_assujetti">{t("regime.non_assujetti")}</option>
                        </select>}
                  </label>))}
              </div>}
            </form>)}
        </div>
      </div>
    </div>
  );
}

import { useEffect, useState } from "react";
import { DetailLot, ResumeLot, detailLot, listerLots } from "./api";
import { AnalyseVue } from "./Analyse";
import { SourcingVue } from "./Sourcing";
import { Connexion } from "./Connexion";
import { ParametresVue } from "./Parametres";
import { NonConnecte, deconnecter, moi } from "./api";
import { dateCourte, monnaie, pourcent, t } from "./i18n";

function signeClasse(v: string | null): string {
  if (v === null || Number(v) === 0) return "neutre";
  return Number(v) > 0 ? "positif" : "negatif";
}

function Liste({ lots, choisi, choisir }: { lots: ResumeLot[]; choisi?: string; choisir: (id: string) => void }) {
  if (!lots.length) return <p className="vide">{t("lots.vide")}</p>;
  return (
    <ul className="liste" role="list">
      {lots.map((l) => (
        <li key={l.id}>
          <button type="button" className={l.id === choisi ? "lot actif" : "lot"} aria-current={l.id === choisi}
            onClick={() => choisir(l.id)}>
            <span className="lot-nom">{l.designation ?? l.asin}</span>
            <span className="lot-meta">
              <span>{l.marketplace} · {t("lot.vendues", { vendues: l.vendues, quantite: l.quantite })}</span>
              <span className={`pastille ${signeClasse(l.ecart)}`}>{pourcent(l.roi_prevu)} → {pourcent(l.roi_reel)}</span>
            </span>
          </button>
        </li>
      ))}
    </ul>
  );
}

function Detail({ d }: { d: DetailLot }) {
  const max = Math.max(...d.causes.map((c) => Math.abs(Number(c.montant))), 0.01);
  return (
    <section className="detail" aria-labelledby="titre-lot">
      <header className="detail-tete">
        <div>
          <h2 id="titre-lot">{d.designation ?? d.asin}</h2>
          <p className="meta">{d.asin} · {d.marketplace} · {d.fournisseur ?? "—"} · {t("lot.achete_le", { date: dateCourte(d.date_achat) })}</p>
        </div>
        <span className={`statut ${d.statut}`}>{t(`statut.${d.statut}`)}</span>
      </header>

      <div className="kpis">
        <div className="kpi"><span className="kpi-l">{t("kpi.profit_reel")}</span>
          <span className="kpi-v">{monnaie(d.profit_reel, d.devise)}</span>
          <span className="kpi-s">{t("lot.vendues", { vendues: d.vendues, quantite: d.quantite })}</span></div>
        <div className="kpi"><span className="kpi-l">{t("kpi.roi")}</span>
          <span className="kpi-v">{pourcent(d.roi_prevu)} → <span className={signeClasse(d.ecart)}>{pourcent(d.roi_reel)}</span></span></div>
        <div className="kpi"><span className="kpi-l">{t("kpi.ecart")}</span>
          <span className={`kpi-v ${signeClasse(d.ecart)}`}>{monnaie(d.ecart, d.devise, true)}</span>
          <span className="kpi-s">{t("kpi.lot_entier", { montant: monnaie(d.profit_prevu_lot_entier, d.devise) })}</span></div>
        <div className="kpi"><span className="kpi-l">{t("kpi.a_encaisser")}</span>
          <span className="kpi-v">{monnaie(d.a_encaisser, d.devise)}</span></div>
      </div>

      <div className="grille">
        <div className="carte">
          <h3>{t("comparatif.titre")}</h3>
          <div className="defile">
            <table>
              <thead><tr><th scope="col">{t("comparatif.poste")}</th><th scope="col" className="num">{t("comparatif.prevu")}</th>
                <th scope="col" className="num">{t("comparatif.reel")}</th><th scope="col" className="num">{t("comparatif.ecart")}</th></tr></thead>
              <tbody>
                {d.comparatif.map((c) => (
                  <tr key={c.poste} className={c.poste === "PROFIT" ? "total" : ""}>
                    <th scope="row">{t(`poste.${c.poste}`)}</th>
                    <td className="num">{monnaie(c.prevu, d.devise)}</td>
                    <td className="num">{monnaie(c.reel, d.devise)}</td>
                    <td className={`num ${signeClasse(c.ecart)}`}>{monnaie(c.ecart, d.devise, true)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {d.vendues > 0 && <div className="carte">
          <h3>{t("causes.titre")}</h3>
          <ul className="causes" role="list">
            {d.causes.map((c) => {
              const v = Number(c.montant);
              const largeur = `${(Math.abs(v) / max) * 50}%`;
              return (
                <li key={c.cause}>
                  <span className="cause-l">{t(`cause.${c.cause}`)}</span>
                  <span className="barre" aria-hidden="true">
                    <span className={`remplissage ${signeClasse(c.montant)}`}
                      style={v < 0 ? { right: "50%", width: largeur } : { left: "50%", width: largeur }} />
                  </span>
                  <span className={`cause-v ${signeClasse(c.montant)}`}>{monnaie(c.montant, d.devise, true)}</span>
                </li>
              );
            })}
          </ul>
        </div>}
      </div>
    </section>
  );
}

function LotsVue({ lotInitial, setDemo }: { lotInitial?: string; setDemo: (d: boolean) => void }) {
  const [lots, setLots] = useState<ResumeLot[] | null>(null);
  const [orphelines, setOrphelines] = useState(0);
  const [choisi, setChoisi] = useState<string | undefined>(lotInitial);
  const [detail, setDetail] = useState<DetailLot | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);

  useEffect(() => {
    listerLots().then((r) => {
      setLots(r.lots); setDemo(r.demo); setOrphelines(r.ventes_non_rattachees);
      if (r.lots.length && !lotInitial) setChoisi(r.lots[0].id);
    }).catch((e) => setErreur(e.message));
  }, [lotInitial, setDemo]);

  useEffect(() => {
    if (!choisi) return;
    setDetail(null);
    detailLot(choisi).then(setDetail).catch((e) => setErreur(e.message));
  }, [choisi]);

  return (
    <div className="contenu">
      <aside className="colonne" aria-labelledby="titre-lots">
        <h1 id="titre-lots">{t("lots.titre")}</h1>
        {lots === null ? <p>{t("chargement")}</p> : <Liste lots={lots} choisi={choisi} choisir={setChoisi} />}
        {orphelines > 0 && <p className="alerte">{t("lots.non_rattachees", { n: orphelines })}</p>}
      </aside>
      {erreur ? <p role="alert" className="alerte">{t(erreur.startsWith("erreur.") ? erreur : `erreur.${erreur}`)}</p>
        : detail ? <Detail d={detail} /> : choisi && <p>{t("chargement")}</p>}
    </div>
  );
}

type Vue = "analyse" | "sourcing" | "lots" | "parametres";
const vueDepuisAdresse = (): Vue => {
  const h = window.location.hash;
  return h === "#lots" ? "lots" : h === "#sourcing" ? "sourcing" : h === "#parametres" ? "parametres" : "analyse";
};

export function App() {
  const [vue, setVue] = useState<Vue>(vueDepuisAdresse());
  const [demo, setDemo] = useState(false);
  const [etat, setEtat] = useState<"verification" | "requise" | "ok">("verification");
  const [avecConnexion, setAvecConnexion] = useState(false);
  const verifier = () => moi().then((m) => { setDemo(m.demo); setAvecConnexion(m.connexion); setEtat("ok"); })
    .catch((e) => setEtat(e instanceof NonConnecte ? "requise" : "ok"));
  useEffect(() => { verifier(); }, []);  // eslint-disable-line
  useEffect(() => {
    const perdu = (e: PromiseRejectionEvent) => { if (e.reason instanceof NonConnecte) setEtat("requise"); };
    window.addEventListener("unhandledrejection", perdu);
    return () => window.removeEventListener("unhandledrejection", perdu);
  }, []);
  const sortir = async () => { await deconnecter(); setEtat("requise"); };
  const [lotInitial, setLotInitial] = useState<string>();

  useEffect(() => {
    const suivre = () => setVue(vueDepuisAdresse());
    window.addEventListener("hashchange", suivre);
    return () => window.removeEventListener("hashchange", suivre);
  }, []);

  const [analyseInitiale, setAnalyseInitiale] = useState<{ code: string; prix: number }>();
  const lotCree = (id: string) => { setLotInitial(id); window.location.hash = "#lots"; };
  const analyser = (code: string, prix: number) => { setAnalyseInitiale({ code, prix }); window.location.hash = "#analyse"; };

  if (etat === "verification") return null;
  if (etat === "requise") return <Connexion connecte={verifier} />;
  return (
    <div className="page">
      <header className="barre-haut">
        <span className="marque">{t("app.nom")}</span>
        <nav aria-label="Navigation principale">
          <a href="#analyse" aria-current={vue === "analyse" ? "page" : undefined}>{t("nav.analyse")}</a>
          <a href="#sourcing" aria-current={vue === "sourcing" ? "page" : undefined}>{t("nav.sourcing")}</a>
          <a href="#lots" aria-current={vue === "lots" ? "page" : undefined}>{t("nav.lots")}</a>
          <a href="#parametres" aria-current={vue === "parametres" ? "page" : undefined}>{t("nav.parametres")}</a>
        </nav>
        {demo && <span className="badge-demo">{t("demo")}</span>}
        {avecConnexion && <button type="button" className="lien sortie" onClick={sortir}>{t("connexion.sortir")}</button>}
      </header>
      {vue === "analyse" ? <main className="contenu-plein"><AnalyseVue key={JSON.stringify(analyseInitiale ?? {})} lotCree={lotCree} initial={analyseInitiale} /></main>
        : vue === "sourcing" ? <main className="contenu-plein"><SourcingVue analyser={analyser} /></main>
        : vue === "parametres" ? <main className="contenu-plein"><ParametresVue /></main>
        : <main><LotsVue key={lotInitial ?? "lots"} lotInitial={lotInitial} setDemo={setDemo} /></main>}
    </div>
  );
}

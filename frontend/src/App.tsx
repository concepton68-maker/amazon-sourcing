import { useEffect, useState } from "react";
import { DetailLot, ResumeLot, detailLot, listerLots } from "./api";
import { AnalyseVue } from "./Analyse";
import { SourcingVue } from "./Sourcing";
import { Connexion } from "./Connexion";
import { ParametresVue } from "./Parametres";
import { StockVue } from "./Stock";
import { FournisseursVue } from "./Fournisseurs";
import { RemboursementsVue } from "./Remboursements";
import { ConformiteVue } from "./Conformite";
import { VendableVue } from "./Vendable";
import { MarcheVue } from "./Marche";
import { TableauVue } from "./Tableau";
import { RentablesVue } from "./Rentables";
import { lireTableau } from "./api";
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

type Vue = "tableau" | "rentables" | "analyse" | "sourcing" | "lots" | "stock" | "fournisseurs" | "remboursements" | "conformite" | "vendable" | "marche" | "parametres";
const vueDepuisAdresse = (): Vue => {
  const h = window.location.hash;
  return h === "#lots" ? "lots" : h === "#sourcing" ? "sourcing" : h.startsWith("#parametres") ? "parametres" : h === "#stock" ? "stock" : h === "#fournisseurs" ? "fournisseurs" : h === "#remboursements" ? "remboursements" : h === "#conformite" ? "conformite" : h === "#vendable" ? "vendable" : h === "#marche" ? "marche" : h === "#analyse" ? "analyse" : h === "#rentables" ? "rentables" : "tableau";
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
  const [bonInitial, setBonInitial] = useState<string>();
  const ouvrirBon = (id: string) => { setBonInitial(id); window.location.hash = "#fournisseurs"; };
  const [traitementInitial, setTraitementInitial] = useState<string>();
  const voirTraitement = (tid: string) => { setTraitementInitial(tid); window.location.hash = "#sourcing"; };
  const analyser = (code: string, prix: number) => { setAnalyseInitiale({ code, prix }); window.location.hash = "#analyse"; };

  const [pastilles, setPastilles] = useState<Record<string, number>>({});
  useEffect(() => {
    if (etat !== "ok") return;
    lireTableau().then((x) => setPastilles({ stock: x.a_faire.recommander, remboursements: x.a_faire.remboursements,
      conformite: x.a_faire.conformite,
      vendable: x.a_faire.deblocages ? (x.a_faire.deblocages.rayons.length || x.a_faire.deblocages.produits) : 0 })).catch(() => undefined);
  }, [etat, vue]);
  const [recherche, setRecherche] = useState("");

  if (etat === "verification") return null;
  if (etat === "requise") return <Connexion connecte={verifier} />;
  const lien = (v: Vue, icone: string) => (
    <a href={`#${v}`} aria-current={vue === v ? "page" : undefined}>
      <span className="icone" aria-hidden="true">{icone}</span>{t(`nav.${v}`)}
      {pastilles[v] ? <b className="pastille-menu">{pastilles[v]}</b> : null}</a>);
  return (
    <div className="app">
      <nav className="menu" aria-label="Navigation principale">
        <a href="#tableau" className="logo"><i aria-hidden="true" />{t("app.nom")}</a>
        <h6>{t("nav.groupe.trouver")}</h6>
        {lien("tableau", "◧")}{lien("rentables", "€")}{lien("analyse", "⌕")}{lien("vendable", "✓")}{lien("marche", "↗")}{lien("sourcing", "⇪")}
        <h6>{t("nav.groupe.gerer")}</h6>
        {lien("lots", "▣")}{lien("stock", "◫")}{lien("fournisseurs", "☰")}{lien("remboursements", "€")}{lien("conformite", "⚑")}
        <div className="bas">
          {lien("parametres", "⚙")}
          {avecConnexion && <button type="button" className="sortie" onClick={sortir}>{t("connexion.sortir")}</button>}
        </div>
      </nav>
      <div className="zone">
      <header className="haut">
        {demo && <span className="badge-demo">{t("demo")}</span>}
        <form className="recherche" role="search" onSubmit={(e) => { e.preventDefault(); if (recherche.trim()) { analyser(recherche.trim(), 0); setRecherche(""); } }}>
          <span aria-hidden="true">⌕</span>
          <input type="search" aria-label={t("nav.recherche")} placeholder={t("nav.recherche")} value={recherche}
            onChange={(e) => setRecherche(e.target.value)} maxLength={40} />
        </form>
      </header>
      {vue === "tableau" ? <main className="contenu-plein"><TableauVue /></main>
        : vue === "rentables" ? <main className="contenu-plein contenu-large"><RentablesVue analyser={analyser} /></main>
        : vue === "analyse" ? <main className="contenu-plein"><AnalyseVue key={JSON.stringify(analyseInitiale ?? {})} lotCree={lotCree} initial={analyseInitiale} /></main>
        : vue === "sourcing" ? <main className="contenu-plein"><SourcingVue key={traitementInitial ?? "s"} analyser={analyser} traitementInitial={traitementInitial} /></main>
        : vue === "parametres" ? <main className="contenu-plein"><ParametresVue /></main>
        : vue === "stock" ? <main className="contenu-plein"><StockVue ouvrirBon={ouvrirBon} /></main>
        : vue === "remboursements" ? <main className="contenu-plein"><RemboursementsVue /></main>
        : vue === "conformite" ? <main className="contenu-plein"><ConformiteVue /></main>
        : vue === "marche" ? <main className="contenu-plein"><MarcheVue analyser={(code) => analyser(code, 0)} /></main>
        : vue === "vendable" ? <main className="contenu-plein"><VendableVue analyser={(code) => analyser(code, 0)} /></main>
        : vue === "fournisseurs" ? <main className="contenu-plein"><FournisseursVue key={bonInitial ?? "f"} bonInitial={bonInitial} voirLot={lotCree} analyserTraitement={voirTraitement} /></main>
        : <main><LotsVue key={lotInitial ?? "lots"} lotInitial={lotInitial} setDemo={setDemo} /></main>}
      </div>
    </div>
  );
}

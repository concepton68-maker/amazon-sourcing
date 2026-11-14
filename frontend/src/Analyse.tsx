import { FormEvent, useEffect, useState } from "react";
import { Analyse, Params, Place, analyser, creerLot, lireParametres, listerPlaces, suivreProduit } from "./api";
import { Msg, message, monnaie, pourcent, t } from "./i18n";

const REGIMES = ["assujetti", "non_assujetti"];
const n = (v: number | null | undefined) => (v === null || v === undefined ? null : String(v));

function Liste({ titre, msgs, devise, ton }: { titre: string; msgs: Msg[]; devise: string; ton: string }) {
  if (!msgs.length) return null;
  return (
    <div className="bloc-msgs">
      <h4>{titre}</h4>
      <ul className={`msgs ${ton}`} role="list">
        {msgs.map((m, i) => <li key={m.code + i}>{message(m, devise)}</li>)}
      </ul>
    </div>
  );
}

function CreerLot({ a, cree }: { a: Analyse; cree: (id: string) => void }) {
  const [quantite, setQuantite] = useState("");
  const [fournisseur, setFournisseur] = useState("");
  const [erreur, setErreur] = useState<string | null>(null);
  const [envoi, setEnvoi] = useState(false);
  if (!a.rentabilite) return null;
  const valider = async (e: FormEvent) => {
    e.preventDefault();
    setErreur(null); setEnvoi(true);
    try { cree((await creerLot(a.jeton_analyse, Number(quantite), fournisseur)).id); }
    catch (x) { setErreur((x as Error).message); }
    finally { setEnvoi(false); }
  };
  return (
    <form className="creer-lot" onSubmit={valider}>
      <label>{t("lot.quantite")}
        <input type="number" min={1} step={1} required value={quantite} onChange={(e) => setQuantite(e.target.value)} /></label>
      <label>{t("lot.fournisseur")}
        <input type="text" maxLength={120} value={fournisseur} onChange={(e) => setFournisseur(e.target.value)} /></label>
      <button type="submit" className="principal" disabled={envoi}>{t("lot.creer")}</button>
      {erreur && <p role="alert" className="alerte">{t(`erreur.${erreur}`)}</p>}
    </form>
  );
}

// [RM-AMZ-090] ajouter le produit à la liste relevée chaque nuit
function Suivre({ asin, marketplace }: { asin: string; marketplace: string }) {
  const [fait, setFait] = useState(false);
  return <button type="button" className="lien" disabled={fait}
    onClick={() => suivreProduit(asin, marketplace).then(() => setFait(true))}>{fait ? `✓ ${t("sm.suivi")}` : `+ ${t("sm.suivre")}`}</button>;
}

const LIGNES = ["achat", "port_fournisseur", "envoi", "preparation", "placement", "commission", "fba", "cloture",
  "frais_autres", "carburant", "tva_frais", "stockage", "retours", "autres"];

// [RM-AMZ-095] coût complet ligne par ligne
function Cascade({ a }: { a: Analyse }) {
  const r = a.rentabilite!, d = a.devise;
  const lignes: [string, number, string][] = [[t("calc.prix_ttc"), a.prix_vente ?? 0, "plus"]];
  if (r.tva_collectee) lignes.push([t("calc.tva"), -r.tva_collectee, "moins"]);
  for (const k of LIGNES) {
    const v = r.detail?.[k] ?? 0;
    if (v) lignes.push([t(k === "autres" ? "calc.autres_couts" : `calc.${k}`), -v, "moins"]);
  }
  const max = Math.max(...lignes.map((l) => Math.abs(l[1])), Math.abs(r.profit), 0.01);
  return (
    <ul className="cascade">
      {lignes.map(([l, v, c]) => (
        <li key={l}><span>{l}</span><span className="piste"><i className={c} style={{ width: `${(Math.abs(v) / max) * 100}%` }} /></span>
          <span className="v">{monnaie(n(v), d, true)}</span></li>))}
      <li className="total"><span>{t("calc.profit")}</span>
        <span className="piste"><i className={r.profit > 0 ? "profit" : "perte"} style={{ width: `${(Math.abs(r.profit) / max) * 100}%` }} /></span>
        <span className={`v ${r.profit > 0 ? "positif" : "negatif"}`}>{monnaie(n(r.profit), d, true)}</span></li>
    </ul>
  );
}

function Verifs({ a }: { a: Analyse }) {
  const d = a.devise;
  return (
    <ul className="verifs">
      <li className={a.autorise ? "ok" : a.autorise === false ? "ko" : "inconnu"}>{t("verif.autorise")} : {a.autorise === null ? "—" : a.autorise ? t("oui") : t("non")}</li>
      {a.raisons.filter((m) => m.code !== "R_PRIX_ACHAT_MAX").map((m, k) => <li key={`r${k}`} className="info">{message(m, d)}</li>)}
      {a.alertes.map((m, k) => <li key={`a${k}`} className="attention">{message(m, d)}</li>)}
      {a.non_verifie.map((m, k) => <li key={`n${k}`} className="inconnu">{message(m, d)}</li>)}
    </ul>
  );
}

function Resultat({ a, cree }: { a: Analyse; cree: (id: string) => void }) {
  const r = a.rentabilite, h = a.historique, o = a.offres, d = a.devise;
  return (
    <section className="detail" aria-labelledby="titre-produit">
      <div className="carte produit-carte">
        <div className="produit-info">
          <p className="meta">{[a.marque, a.categorie, a.bsr ? `BSR ${a.bsr.toLocaleString("fr-FR")}` : null, a.asin].filter(Boolean).join(" · ")}</p>
          <h2 id="titre-produit">{a.titre ?? a.asin}</h2>
          <div className="pills">
            {a.autorise !== null && <span className={`pill ${a.autorise ? "v" : "r"}`}>{a.autorise ? t("pill.autorise") : t("pill.non_autorise")}</span>}
            {o?.nb_fba !== null && o?.nb_fba !== undefined && <span className="pill b">{t("pill.vendeurs_fba", { n: o.nb_fba })}</span>}
            {o?.amazon_vend !== null && o?.amazon_vend !== undefined && <span className={`pill ${o.amazon_vend ? "a" : "n"}`}>{o.amazon_vend ? t("pill.amazon_present") : t("pill.amazon_absent")}</span>}
            {a.unites_lot && a.unites_lot > 1 ? <span className="pill a">{t("pill.lot", { n: a.unites_lot })}</span> : null}
          </div>
          <Suivre asin={a.asin} marketplace={a.marketplace} />
        </div>
        <div className="produit-verdict">
          <span className={`verdict grand ${a.verdict}`}>{t(`verdict.${a.verdict}`)}</span>
          {r && <p className="meta">{t("kpi.prix_max", { roi: pourcent(n(r.roi_cible)) })} : <strong className="chiffre">{monnaie(n(r.prix_achat_max), d)}</strong></p>}
        </div>
      </div>

      {r && (
        <div className="kpis">
          <div className="kpi"><span className="kpi-l">{t("kpi.profit")}</span>
            <span className={`kpi-v ${r.profit > 0 ? "positif" : "negatif"}`}>{monnaie(n(r.profit), d, true)}</span>
            <span className="kpi-s">{monnaie(n(a.prix_vente), d)} · {t(`origine.${a.origine_prix}`)}</span></div>
          <div className="kpi"><span className="kpi-l">{t("kpi.roi_marge")}</span>
            <span className="kpi-v">{pourcent(n(r.roi))} · {pourcent(n(r.marge))}</span>
            <span className="kpi-s">{t("kpi.objectif", { roi: pourcent(n(r.roi_cible)) })}</span></div>
          {a.prudent ? <div className="kpi"><span className="kpi-l">{t("kpi.prudent")}</span>
            <span className={`kpi-v ${a.prudent.profit > 0 ? "" : "negatif"}`}>{monnaie(n(a.prudent.profit), d, true)}</span>
            <span className="kpi-s">{monnaie(n(a.prudent.prix_vente), d)} · {pourcent(n(a.prudent.roi))}</span></div>
            : <div className="kpi"><span className="kpi-l">{t("marche.vendeurs")}</span>
              <span className="kpi-v">{o?.nb_fba ?? "—"} · {o?.nb_fbm ?? "—"}</span>
              <span className="kpi-s">{h?.ventes_mois ? `${h.ventes_mois} / mois` : t("kpi.ventes_inconnues")}</span></div>}
        </div>
      )}

      <div className="grille deux">
        {r && (
          <div className="carte">
            <h3>{t("calc.origine")} <span className="meta">{t("calc.par_unite")}</span></h3>
            <Cascade a={a} />
            <Liste titre={t("hyp.titre")} msgs={r.hypotheses} devise={d} ton="discret" />
          </div>
        )}
        <div className="carte">
          <h3>{t("verif.titre")}</h3>
          <Verifs a={a} />
          <CreerLot a={a} cree={cree} />
        </div>
      </div>
    </section>
  );
}

export function AnalyseVue({ lotCree, initial }: { lotCree: (id: string) => void; initial?: { code: string; prix: number } }) {
  const [places, setPlaces] = useState<Place[]>([]);
  const [code, setCode] = useState(initial?.code ?? "");
  const [place, setPlace] = useState("FR");
  const [prix, setPrix] = useState(initial ? String(initial.prix).replace(".", ",") : "");
  const [ttc, setTtc] = useState(false);
  const [regime, setRegime] = useState("assujetti");
  const [taux, setTaux] = useState("");
  const [port, setPort] = useState("");
  const [analyses, setAnalyses] = useState<Analyse[]>([]);
  const [choix, setChoix] = useState(0);
  const [erreur, setErreur] = useState<string | null>(null);
  const [encours, setEncours] = useState(false);

  const [params, setParams] = useState<Params | null>(null);
  useEffect(() => {
    listerPlaces().then(setPlaces).catch(() => setErreur("chargement"));
    lireParametres().then(setParams).catch(() => undefined);
  }, []);
  // [RM-AMZ-044] régime de TVA du compte pour la place choisie (modifiable pour cette analyse)
  useEffect(() => {
    const r = params?.tva[place];
    if (r && r !== "hors_taxe") setRegime(r);
  }, [params, place]);

  const lancer = (e: FormEvent) => { e.preventDefault(); executer(code, prix); };

  useEffect(() => { if (initial) executer(initial.code, String(initial.prix)); }, [initial]);  // eslint-disable-line

  async function executer(code: string, prix: string) {
    setErreur(null); setEncours(true); setAnalyses([]);
    try {
      const r = await analyser({ code: code.trim(), marketplace: place, prix_achat: Number(prix.replace(",", ".")),
        achat_ttc: ttc, regime_tva: regime, taux_tva: taux ? Number(taux.replace(",", ".")) / 100 : null,
        port_fournisseur: port ? Number(port.replace(",", ".")) : null });
      setAnalyses(r.analyses); setChoix(0);
    } catch (x) { setErreur((x as Error).message); }
    finally { setEncours(false); }
  }

  return (
    <div className="vue">
      <h1>{t("analyse.titre")}</h1>
      <form className="formulaire" onSubmit={lancer}>
        <label className="large">{t("analyse.code")}
          <input type="text" required maxLength={40} value={code} onChange={(e) => setCode(e.target.value)} /></label>
        <label>{t("analyse.place")}
          <select value={place} onChange={(e) => setPlace(e.target.value)}>
            {places.map((p) => <option key={p.code} value={p.code}>{p.domaine}</option>)}
          </select></label>
        <label>{t("analyse.prix_achat")}
          <input type="text" inputMode="decimal" required value={prix} onChange={(e) => setPrix(e.target.value)} /></label>
        <div role="group" aria-label={t("analyse.base_prix")} className="segment">
          <button type="button" aria-pressed={!ttc} onClick={() => setTtc(false)}>{t("analyse.ht")}</button>
          <button type="button" aria-pressed={ttc} onClick={() => setTtc(true)}>{t("analyse.ttc")}</button>
        </div>
        <label>{t("analyse.regime")}
          <select value={regime} onChange={(e) => setRegime(e.target.value)}>
            {REGIMES.map((r) => <option key={r} value={r}>{t(`regime.${r}`)}</option>)}
          </select></label>
        <label className="etroit">{t("analyse.port")}
          <input type="text" inputMode="decimal" placeholder={params ? String(params.port_fournisseur).replace(".", ",") : ""}
            value={port} onChange={(e) => setPort(e.target.value)} /></label>
        <label className="etroit">{t("analyse.taux")}
          <input type="text" inputMode="decimal" value={taux} onChange={(e) => setTaux(e.target.value)} /></label>
        <button type="submit" className="principal" disabled={encours}>{encours ? t("analyse.en_cours") : t("analyse.lancer")}</button>
      </form>
      {erreur && <p role="alert" className="alerte">{t(`erreur.${erreur}`)}</p>}
      {analyses.length > 1 && (
        <div role="tablist" className="onglets">
          {analyses.map((a, i) => (
            <button key={a.asin} type="button" role="tab" aria-selected={i === choix} onClick={() => setChoix(i)}>
              {a.asin}{a.unites_lot && a.unites_lot > 1 ? ` ×${a.unites_lot}` : ""}</button>
          ))}
        </div>
      )}
      {analyses[choix] && <Resultat a={analyses[choix]} cree={lotCree} />}
    </div>
  );
}

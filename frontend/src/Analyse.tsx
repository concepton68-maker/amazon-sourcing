import { FormEvent, useEffect, useState } from "react";
import { Analyse, Place, analyser, creerLot, listerPlaces } from "./api";
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

function Resultat({ a, cree }: { a: Analyse; cree: (id: string) => void }) {
  const r = a.rentabilite, h = a.historique, o = a.offres, d = a.devise;
  const oui = (v: boolean | null | undefined) => (v === null || v === undefined ? "—" : v ? t("oui") : t("non"));
  return (
    <section className="detail" aria-labelledby="titre-produit">
      <header className="detail-tete">
        <div>
          <span className={`verdict ${a.verdict}`}>{t(`verdict.${a.verdict}`)}</span>
          <h2 id="titre-produit">{a.titre ?? a.asin}</h2>
          <p className="meta">{[a.asin, a.marque, a.categorie, a.bsr ? `BSR ${a.bsr}` : null].filter(Boolean).join(" · ")}</p>
        </div>
        <CreerLot a={a} cree={cree} />
      </header>

      {r && (
        <div className="kpis">
          <div className="kpi"><span className="kpi-l">{t("kpi.profit")}</span>
            <span className={`kpi-v ${r.profit > 0 ? "" : "negatif"}`}>{monnaie(n(r.profit), d)}</span>
            <span className="kpi-s">{monnaie(n(a.prix_vente), d)} · {t(`origine.${a.origine_prix}`)}</span></div>
          <div className="kpi"><span className="kpi-l">{t("kpi.roi_marge")}</span>
            <span className="kpi-v">{pourcent(n(r.roi))}</span><span className="kpi-s">{pourcent(n(r.marge))}</span></div>
          <div className="kpi"><span className="kpi-l">{t("kpi.prix_max", { roi: pourcent(n(r.roi_cible)) })}</span>
            <span className="kpi-v">{monnaie(n(r.prix_achat_max), d)}</span></div>
          {a.prudent && <div className="kpi"><span className="kpi-l">{t("kpi.prudent")}</span>
            <span className={`kpi-v ${a.prudent.profit > 0 ? "" : "negatif"}`}>{monnaie(n(a.prudent.profit), d)}</span>
            <span className="kpi-s">{monnaie(n(a.prudent.prix_vente), d)} · {pourcent(n(a.prudent.roi))}</span></div>}
        </div>
      )}

      <div className="grille trois">
        {r && (
          <div className="carte">
            <h3>{t("calc.titre")}</h3>
            <table><tbody>
              <tr><th scope="row">{t("calc.prix_ttc")}</th><td className="num">{monnaie(n(a.prix_vente), d)}</td></tr>
              {r.tva_collectee !== 0 && <tr><th scope="row">{t("calc.tva")}</th><td className="num">{monnaie(n(-r.tva_collectee), d)}</td></tr>}
              <tr><th scope="row">{t("calc.achat")}</th><td className="num">{monnaie(n(-r.cout_achat_net), d)}</td></tr>
              <tr><th scope="row">{t("calc.frais")}</th><td className="num">{monnaie(n(-r.frais_amazon), d)}</td></tr>
              {r.tva_frais !== 0 && <tr><th scope="row">{t("calc.tva_frais")}</th><td className="num">{monnaie(n(-r.tva_frais), d)}</td></tr>}
              {r.autres !== 0 && <tr><th scope="row">{t("calc.autres")}</th><td className="num">{monnaie(n(-r.autres), d)}</td></tr>}
              <tr className="total"><th scope="row">{t("calc.profit")}</th><td className="num">{monnaie(n(r.profit), d)}</td></tr>
            </tbody></table>
            <Liste titre={t("hyp.titre")} msgs={r.hypotheses} devise={d} ton="discret" />
          </div>
        )}
        <div className="carte">
          <h3>{t("marche.titre")}</h3>
          <dl className="faits">
            <div><dt>{t("marche.prix_moy")}</dt><dd>{monnaie(n(h?.prix_moy90), d)}</dd></div>
            <div><dt>{t("marche.min_max")}</dt><dd>{monnaie(n(h?.prix_min90), d)} / {monnaie(n(h?.prix_max90), d)}</dd></div>
            <div><dt>{t("marche.ventes")}</dt><dd>{h?.ventes_mois ?? "—"}</dd></div>
            <div><dt>{t("marche.part")}</dt><dd>{a.ventes_pour_vous ?? "—"} <span className="etiquette">{t("estimation")}</span></dd></div>
            <div><dt>{t("marche.vendeurs")}</dt><dd>{o?.nb_fba ?? "—"} · {o?.nb_fbm ?? "—"}</dd></div>
            <div><dt>{t("marche.amazon")}</dt><dd>{oui(o?.amazon_vend)}</dd></div>
          </dl>
        </div>
        <div className="carte">
          <h3>{t("verif.titre")}</h3>
          <dl className="faits"><div><dt>{t("verif.autorise")}</dt>
            <dd className={a.autorise === false ? "negatif" : a.autorise ? "positif" : ""}>{oui(a.autorise)}</dd></div></dl>
          <Liste titre={t("raisons.titre")} msgs={a.raisons.filter((m) => m.code !== "R_PRIX_ACHAT_MAX")} devise={d} ton="neutre" />
          <Liste titre={t("alertes.titre")} msgs={a.alertes} devise={d} ton="alerte" />
          <Liste titre={t("verif.non_verifie")} msgs={a.non_verifie} devise={d} ton="discret" />
        </div>
      </div>
    </section>
  );
}

export function AnalyseVue({ lotCree }: { lotCree: (id: string) => void }) {
  const [places, setPlaces] = useState<Place[]>([]);
  const [code, setCode] = useState("");
  const [place, setPlace] = useState("FR");
  const [prix, setPrix] = useState("");
  const [ttc, setTtc] = useState(false);
  const [regime, setRegime] = useState("assujetti");
  const [taux, setTaux] = useState("");
  const [analyses, setAnalyses] = useState<Analyse[]>([]);
  const [choix, setChoix] = useState(0);
  const [erreur, setErreur] = useState<string | null>(null);
  const [encours, setEncours] = useState(false);

  useEffect(() => { listerPlaces().then(setPlaces).catch(() => setErreur("chargement")); }, []);

  const lancer = async (e: FormEvent) => {
    e.preventDefault();
    setErreur(null); setEncours(true); setAnalyses([]);
    try {
      const r = await analyser({ code: code.trim(), marketplace: place, prix_achat: Number(prix.replace(",", ".")),
        achat_ttc: ttc, regime_tva: regime, taux_tva: taux ? Number(taux.replace(",", ".")) / 100 : null });
      setAnalyses(r.analyses); setChoix(0);
    } catch (x) { setErreur((x as Error).message); }
    finally { setEncours(false); }
  };

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

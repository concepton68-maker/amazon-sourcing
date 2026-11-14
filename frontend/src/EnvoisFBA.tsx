import { useEffect, useState } from "react";
import { CartonFBA, EnvoiFBA, GroupeFBA, ProblemeFBA, actionEnvoiFBA, creerEnvoiFBA, lireEnvoiFBA, lireStock, listerEnvoisFBA } from "./api";
import { dateCourte, t } from "./i18n";

// Envois FBA par l'API, partie 1 [RM-AMZ-137 à 139] : brouillon → plan → emballage → cartons.
const ETAPES = ["BROUILLON", "PLAN_CREE", "EMBALLAGE_CONFIRME", "CARTONS_ENVOYES"];

function Problemes({ liste }: { liste?: unknown }) {
  const l = (liste as ProblemeFBA[] | undefined) ?? [];
  if (!l.length) return null;
  return <ul className="liste-envois">{l.map((p, i) => (
    <li key={i} className={p.gravite === "ERROR" ? "ECHEC" : "INCERTAIN"}><strong>{t(p.gravite === "ERROR" ? "fba.erreur_amazon" : "fba.attention_amazon")}</strong> · {p.message} <span className="meta">{p.code}</span></li>))}</ul>;
}

function Nouveau({ cree }: { cree: (e: EnvoiFBA) => void }) {
  const [skus, setSkus] = useState<{ sku: string; asin: string | null; designation: string | null; disponible: number }[]>([]);
  const [qte, setQte] = useState<Record<string, string>>({});
  const [nom, setNom] = useState(`Envoi ${new Date().toLocaleDateString("fr-FR")}`);
  const [etiquette, setEtiquette] = useState("SELLER");
  const [preparation, setPreparation] = useState("NONE");
  const [erreur, setErreur] = useState<string | null>(null);
  useEffect(() => { lireStock().then((s) => setSkus(s.lignes.map((l) => ({ sku: l.sku, asin: l.asin, designation: l.designation, disponible: l.disponible })))).catch(() => undefined); }, []);
  const lignes = Object.entries(qte).filter(([, v]) => Number(v) > 0).map(([msku, v]) => ({ msku, quantite: Number(v), asin: skus.find((s) => s.sku === msku)?.asin ?? null }));
  const creer = () => { setErreur(null); creerEnvoiFBA(nom, lignes, etiquette, preparation).then(cree).catch((x) => setErreur((x as Error).message)); };
  return (
    <section className="carte">
      <div className="entete-vue"><h3>{t("fba.nouveau")}</h3>
        <button type="button" className="principal" disabled={!lignes.length || !nom.trim()} onClick={creer}>{t("fba.creer_brouillon", { n: lignes.length })}</button></div>
      <div className="formulaire nu">
        <label>{t("fba.nom")}<input value={nom} maxLength={40} onChange={(e) => setNom(e.target.value)} /></label>
        <label>{t("fba.etiquetage")}<select value={etiquette} onChange={(e) => setEtiquette(e.target.value)}>
          {["SELLER", "AMAZON", "NONE"].map((x) => <option key={x} value={x}>{t(`fba.proprio.${x}`)}</option>)}</select></label>
        <label>{t("fba.preparation")}<select value={preparation} onChange={(e) => setPreparation(e.target.value)}>
          {["NONE", "SELLER", "AMAZON"].map((x) => <option key={x} value={x}>{t(`fba.proprio.${x}`)}</option>)}</select></label>
      </div>
      {skus.length === 0 ? <p className="meta">{t("fba.aucun_sku")}</p> : (
        <div className="defile"><table className="table-compacte">
          <thead><tr><th scope="col">{t("fba.sku")}</th><th scope="col">{t("col.produit")}</th><th scope="col" className="num">{t("fba.disponible")}</th><th scope="col" className="num">{t("fba.a_envoyer")}</th></tr></thead>
          <tbody>{skus.map((s) => (
            <tr key={s.sku}><td>{s.sku}</td><td>{s.designation ?? s.asin ?? "—"}</td><td className="num">{s.disponible}</td>
              <td className="num"><input className="etroit-num" type="number" min={0} max={500000} aria-label={`${t("fba.a_envoyer")} ${s.sku}`}
                value={qte[s.sku] ?? ""} onChange={(e) => setQte({ ...qte, [s.sku]: e.target.value })} /></td></tr>))}</tbody>
        </table></div>)}
      {erreur && <p role="alert" className="alerte">{t(`erreur.${erreur}`)}</p>}
    </section>
  );
}

function Cartons({ e, groupes, envoyer }: { e: EnvoiFBA; groupes: GroupeFBA[]; envoyer: (c: CartonFBA[]) => void }) {
  const vide = (g: GroupeFBA): CartonFBA => ({ groupe: g.id, longueur: 0, largeur: 0, hauteur: 0, poids: 0, nombre: 1,
    contenu: Object.fromEntries(g.mskus.map((m) => [m, e.lignes.find((l) => l.msku === m)?.quantite ?? 0])) });
  const [cartons, setCartons] = useState<CartonFBA[]>(() => groupes.map(vide));
  const maj = (i: number, k: keyof CartonFBA, v: number) => setCartons(cartons.map((c, j) => (j === i ? { ...c, [k]: v } : c)));
  const majContenu = (i: number, m: string, v: number) => setCartons(cartons.map((c, j) => (j === i ? { ...c, contenu: { ...c.contenu, [m]: v } } : c)));
  return (
    <div className="cartons-fba">
      {groupes.map((g, gi) => (
        <div key={g.id} className="groupe-fba">
          <div className="entete-vue"><strong>{t("fba.groupe", { n: gi + 1 })}</strong>
            <span className="meta">{g.poids_max ? t("fba.poids_limites", { min: g.poids_min ?? 0, max: g.poids_max }) : ""}</span>
            <button type="button" className="lien" onClick={() => setCartons([...cartons, vide(g)])}>{t("fba.ajouter_carton")}</button></div>
          {cartons.map((c, i) => c.groupe !== g.id ? null : (
            <div key={i} className="ligne-carton">
              {(["longueur", "largeur", "hauteur"] as const).map((k) => <label key={k}>{t(`fba.${k}`)}<input type="number" min={0} step="0.1" value={c[k] || ""} onChange={(x) => maj(i, k, Number(x.target.value))} /></label>)}
              <label>{t("fba.poids")}<input type="number" min={0} step="0.01" value={c.poids || ""} onChange={(x) => maj(i, "poids", Number(x.target.value))} /></label>
              <label>{t("fba.nombre")}<input type="number" min={1} value={c.nombre} onChange={(x) => maj(i, "nombre", Number(x.target.value))} /></label>
              {g.mskus.map((m) => <label key={m}>{t("fba.par_carton", { sku: m })}<input type="number" min={0} value={c.contenu[m] ?? 0} onChange={(x) => majContenu(i, m, Number(x.target.value))} /></label>)}
              <button type="button" className="lien" onClick={() => setCartons(cartons.filter((_, j) => j !== i))}>{t("bon.retirer")}</button>
            </div>))}
        </div>))}
      <button type="button" className="principal" onClick={() => envoyer(cartons)}>{t("fba.envoyer_cartons")}</button>
    </div>
  );
}

function Detail({ id, maj }: { id: string; maj: () => void }) {
  const [e, setE] = useState<EnvoiFBA | null>(null);
  const [option, setOption] = useState<string>("");
  const [erreur, setErreur] = useState<string | null>(null);
  const [confirmer, setConfirmer] = useState(false);
  const lire = () => lireEnvoiFBA(id).then((x) => { setE(x); if (!x.en_cours) maj(); }).catch(() => undefined);
  useEffect(() => { setErreur(null); lire(); }, [id]);
  useEffect(() => { if (!e?.en_cours) return; const i = setTimeout(lire, 3000); return () => clearTimeout(i); }, [e]);
  if (!e) return null;
  const faire = (a: "creer-plan" | "confirmer-emballage" | "cartons" | "annuler", corps: unknown = {}) => {
    setErreur(null); setConfirmer(false);
    actionEnvoiFBA(e.id, a, corps).then(setE).catch((x) => setErreur((x as Error).message));
  };
  const rang = ETAPES.indexOf(e.statut);
  const options = e.donnees.options ?? [];
  return (
    <section className="carte">
      <div className="entete-vue"><div><h3>{e.nom}</h3><p className="meta">{t("fba.cree_le", { date: dateCourte(e.cree_le) })}{e.plan_id ? ` · ${e.plan_id}` : ""}</p></div>
        <span className={`statut-bon ${e.statut}`}>{t(`fba.statut.${e.statut}`)}</span></div>
      <ol className="etapes-fba">{ETAPES.map((s, i) => <li key={s} className={i < rang ? "faite" : i === rang ? "courante" : ""}>{t(`fba.etape.${s}`)}</li>)}
        <li className="a-venir">{t("fba.etape.SUITE")}</li></ol>
      {e.en_cours && <p role="status" className="en-cours"><span className="point-pulse" aria-hidden="true" /> {t("fba.en_cours")}</p>}
      {e.donnees.erreur && <p role="alert" className="alerte">{t("fba.panne")} {String(e.donnees.erreur)}</p>}
      <Problemes liste={e.donnees.probleme_plan} /><Problemes liste={e.donnees.probleme_emballage} />
      <Problemes liste={e.donnees.probleme_confirmation} /><Problemes liste={e.donnees.probleme_cartons} />
      <table className="table-compacte"><tbody>{e.lignes.map((l) => <tr key={l.msku}><td>{l.msku}</td><td className="num">{l.quantite}</td></tr>)}</tbody></table>
      {!e.en_cours && e.statut === "BROUILLON" && <div className="formulaire nu">
        <button type="button" className="principal" onClick={() => faire("creer-plan")}>{t("fba.creer_plan")}</button>
        <span className="meta">{t("fba.creer_plan_info")} <a href="#parametres/societe">{t("rubrique.societe")}</a></span></div>}
      {!e.en_cours && e.statut === "PLAN_CREE" && <div className="choix-option">
        {options.map((o, i) => (
          <label key={o.id} className="option-fba"><input type="radio" name="option" checked={option === o.id} onChange={() => setOption(o.id)} />
            <span>{t("fba.option", { n: i + 1, g: o.groupes.length })}{o.poids?.maximum ? ` · ${t("fba.poids_limites", { min: o.poids.minimum ?? 0, max: o.poids.maximum })} ${o.poids.unit ?? ""}` : ""}
              {o.frais.length ? ` · ${t("fba.frais_annonces")}` : ` · ${t("fba.sans_frais")}`}</span></label>))}
        {!confirmer ? <button type="button" className="principal" disabled={!option} onClick={() => setConfirmer(true)}>{t("fba.confirmer_emballage")}</button>
          : <div className="confirmation"><p>{t("fba.definitif")}</p>
              <button type="button" className="principal" onClick={() => faire("confirmer-emballage", { option })}>{t("fba.oui_confirmer")}</button>
              <button type="button" className="lien" onClick={() => setConfirmer(false)}>{t("bon.annuler")}</button></div>}
      </div>}
      {!e.en_cours && e.statut === "EMBALLAGE_CONFIRME" && e.donnees.groupes &&
        <Cartons e={e} groupes={e.donnees.groupes} envoyer={(c) => faire("cartons", { cartons: c })} />}
      {e.statut === "CARTONS_ENVOYES" && <p className="meta">{t("fba.suite_partie2")}</p>}
      {erreur && <p role="alert" className="alerte">{t(`erreur.${erreur}`)}</p>}
      {!e.en_cours && e.statut !== "ANNULE" && <div className="actions">
        <button type="button" className="lien" onClick={() => faire("annuler")} title={t("fba.annuler_info")}>{t("fba.annuler")}</button></div>}
    </section>
  );
}

export function EnvoisFBAVue() {
  const [envois, setEnvois] = useState<EnvoiFBA[]>([]);
  const [choisi, setChoisi] = useState<string | null>(null);
  const [nouveau, setNouveau] = useState(false);
  const charger = () => listerEnvoisFBA().then((l) => { setEnvois(l); setChoisi((c) => c ?? l[0]?.id ?? null); }).catch(() => undefined);
  useEffect(() => { charger(); }, []);
  return (
    <div className="vue">
      <div className="entete-vue"><h1>{t("fba.titre")}</h1>
        <button type="button" className="principal" onClick={() => setNouveau(!nouveau)}>{t("fba.nouveau")}</button></div>
      {nouveau && <Nouveau cree={(e) => { setNouveau(false); setChoisi(e.id); charger(); }} />}
      <div className="contenu sans-marge">
        <aside className="colonne">
          {envois.length === 0 ? <p className="meta">{t("fba.vide")}</p> : (
            <ul className="liste" role="list">{envois.map((e) => (
              <li key={e.id}><button type="button" className={e.id === choisi ? "lot actif" : "lot"} onClick={() => setChoisi(e.id)}>
                <span className="lot-nom">{e.nom}</span>
                <span className="lot-meta"><span>{e.lignes.reduce((s, l) => s + l.quantite, 0)} {t("fba.unites")}</span>
                  <span className={`statut-bon ${e.statut}`}>{t(`fba.statut.${e.statut}`)}</span></span></button></li>))}</ul>)}
        </aside>
        <div className="detail">{choisi && <Detail key={choisi} id={choisi} maj={charger} />}</div>
      </div>
    </div>
  );
}

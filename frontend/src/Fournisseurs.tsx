import { FormEvent, useEffect, useState } from "react";
import { FiltreMultiple } from "./Filtre";
import { Bon, Colonnes, Fichier, FournisseurBilan, Place, Reference, actionBon, ajouterLigneBon, ajouterReferences,
  analyserTarif, creerBon, creerFournisseur, deposerTarif, enregistrerTarif, lireAnnuaire, listerBons,
  listerFournisseurs, listerPlaces, modifierFournisseur, recevoirBon, retirerLigneBon, documentBon, modifierQuantiteBon, ApercuEnvoi, TentativeEnvoi, apercuEnvoi, envoyerParMessagerie, lireEnvois } from "./api";
import { dateCourte, monnaie, pourcent, t } from "./i18n";

const n = (v: number | null) => (v === null ? null : String(v));
const STATUTS = ["TOUS", "BROUILLON", "ENVOYE", "RECU", "ANNULE"];

// Envoi par la messagerie [RM-AMZ-130, 131] : aperçu, envoi voulu, suivi des tentatives.
function EnvoiMessagerie({ b, maj }: { b: Bon; maj: (b: Bon) => void }) {
  const [apercu, setApercu] = useState<ApercuEnvoi | null>(null);
  const [envois, setEnvois] = useState<TentativeEnvoi[]>([]);
  const [erreur, setErreur] = useState<string | null>(null);
  const [enCours, setEnCours] = useState(false);
  useEffect(() => { setApercu(null); setErreur(null); lireEnvois(b.id).then(setEnvois).catch(() => undefined); }, [b.id]);
  const ouvrir = () => { setErreur(null); apercuEnvoi(b.id).then(setApercu).catch((x) => setErreur((x as Error).message)); };
  const envoyer = () => {
    setEnCours(true); setErreur(null);
    envoyerParMessagerie(b.id, envois.length).then((r) => { maj(r.bon); setApercu(null); return lireEnvois(b.id).then(setEnvois); })
      .catch((x) => setErreur((x as Error).message)).finally(() => setEnCours(false));
  };
  const dernier = envois[envois.length - 1];
  return (
    <div className="envoi-messagerie">
      {!apercu && <button type="button" className="secondaire" onClick={ouvrir}>
        {dernier ? t("envoi.renvoyer") : t("envoi.ouvrir")}</button>}
      {apercu && <div className="apercu-envoi" role="region" aria-label={t("envoi.apercu")}>
        <dl className="faits">
          <div><dt>{t("envoi.de")}</dt><dd>{apercu.expediteur}</dd></div>
          <div><dt>{t("envoi.a")}</dt><dd>{apercu.a}</dd></div>
          {apercu.repondre_a && <div><dt>{t("envoi.repondre_a")}</dt><dd>{apercu.repondre_a}</dd></div>}
          <div><dt>{t("envoi.objet")}</dt><dd>{apercu.objet}</dd></div>
          <div><dt>{t("envoi.piece")}</dt><dd>{apercu.piece.nom} · {Math.ceil(apercu.piece.taille / 1024)} Ko</dd></div>
        </dl>
        <pre className="texte-envoi">{apercu.texte}</pre>
        <div className="formulaire nu">
          <button type="button" className="principal" disabled={enCours} onClick={envoyer}>{enCours ? t("envoi.en_cours") : t("envoi.envoyer")}</button>
          <button type="button" className="lien" onClick={() => setApercu(null)}>{t("bon.annuler")}</button>
        </div>
      </div>}
      {envois.length > 0 && <ul className="liste-envois">{envois.map((x) => (
        <li key={x.generation} className={x.etat}>
          <strong>{t(`envoi.etat.${x.etat}`)}</strong> · {dateCourte(x.le)} {new Date(x.le).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" })} · {x.a}
          {x.cause && <span className="meta"> · {t(`envoi.cause.${x.cause}`) === `envoi.cause.${x.cause}` ? x.cause : t(`envoi.cause.${x.cause}`)}</span>}
        </li>))}</ul>}
      {erreur && <p role="alert" className="alerte">{t(`erreur.${erreur}`)}</p>}
    </div>
  );
}

function DetailBon({ b, maj, voirLot }: { b: Bon; maj: (b: Bon) => void; voirLot: (id: string) => void }) {
  const [places, setPlaces] = useState<Place[]>([]);
  const [asin, setAsin] = useState(""); const [mp, setMp] = useState("FR"); const [qte, setQte] = useState("");
  const [recues, setRecues] = useState<Record<string, string>>({});
  const [erreur, setErreur] = useState<string | null>(null);
  useEffect(() => { listerPlaces().then(setPlaces).catch(() => undefined); }, []);
  useEffect(() => { setRecues(Object.fromEntries(b.lignes.map((l) => [l.id, String(l.quantite)]))); setErreur(null); }, [b]);
  const faire = async (p: Promise<Bon>) => { setErreur(null); try { maj(await p); } catch (x) { setErreur((x as Error).message); } };
  const d = b.devise ?? "EUR";
  const ajouter = (e: FormEvent) => { e.preventDefault(); faire(ajouterLigneBon(b.id, asin.trim(), mp, Number(qte))).then(() => { setAsin(""); setQte(""); }); };
  return (
    <section className="carte" aria-labelledby="titre-bon">
      <div className="entete-vue">
        <div>
          <h3 id="titre-bon">{b.reference} · {b.fournisseur?.nom}</h3>
          <p className="meta">{t("bon.cree_le", { date: dateCourte(b.cree_le) })}
            {b.envoye_le && ` · ${t("bon.envoye_le", { date: dateCourte(b.envoye_le) })}`}
            {b.recu_le && ` · ${t("bon.recu_le", { date: dateCourte(b.recu_le) })}`}</p>
        </div>
        <span className={`statut-bon ${b.statut}`}>{t(`statut_bon.${b.statut}`)}</span>
      </div>
      <div className="defile">
        <table>
          <thead><tr><th scope="col">{t("col.produit")}</th><th scope="col" className="num">{t("bon.quantite")}</th>
            <th scope="col" className="num">{t("bon.prix")}</th><th scope="col" className="num">{t("bon.montant")}</th>
            <th scope="col" className="num">{t("bon.roi")}</th>
            {b.statut === "ENVOYE" && <th scope="col" className="num">{t("bon.recue")}</th>}
            {b.statut === "RECU" && <th scope="col">{t("bon.lot")}</th>}
            {b.statut === "BROUILLON" && <th scope="col"><span className="masque">{t("bon.retirer")}</span></th>}</tr></thead>
          <tbody>
            {b.lignes.map((l) => (
              <tr key={l.id}>
                <td><div className="produit">{l.designation ?? l.asin}</div><div className="meta">{l.code ? `${t("bon.ref")} ${l.code} · ` : ""}{l.asin} · {l.marketplace}{l.unites_lot > 1 ? ` · ${t("rent.lot", { n: l.unites_lot })}` : ""}</div></td>
                <td className="num">{b.statut === "BROUILLON"
                  ? <input aria-label={`${t("bon.quantite")} ${l.asin}`} className="etroit-num" type="number" min={1} max={100000}
                      defaultValue={l.quantite} key={`${l.id}-${l.quantite}`}
                      onBlur={(e) => { const q = Number(e.target.value); if (q !== l.quantite) faire(modifierQuantiteBon(b.id, l.id, q)); }}
                      onKeyDown={(e) => { if (e.key === "Enter") (e.target as HTMLInputElement).blur(); }} />
                  : l.quantite}</td><td className="num">{monnaie(n(l.prix_unitaire), d)}</td>
                <td className="num">{monnaie(n(l.montant), d)}</td><td className="num">{pourcent(n(l.roi_prevu))}</td>
                {b.statut === "ENVOYE" && <td className="num"><input aria-label={`${t("bon.recue")} ${l.asin}`} className="etroit-num"
                  type="number" min={0} max={l.quantite} value={recues[l.id] ?? ""} onChange={(e) => setRecues({ ...recues, [l.id]: e.target.value })} /></td>}
                {b.statut === "RECU" && <td>{l.lot_id ? <button type="button" className="lien" onClick={() => voirLot(l.lot_id!)}>{t("bon.voir_lot")}</button> : "—"}</td>}
                {b.statut === "BROUILLON" && <td><button type="button" className="lien" onClick={() => faire(retirerLigneBon(b.id, l.id))}>{t("bon.retirer")}</button></td>}
              </tr>
            ))}
            <tr className="total"><th scope="row">{t("bon.montant")}</th><td /><td /><td className="num">{monnaie(n(b.montant), d)}</td>
              <td className="num">{pourcent(n(b.roi_prevu))}</td></tr>
          </tbody>
        </table>
      </div>
      {b.statut === "BROUILLON" && (
        <form className="formulaire nu" onSubmit={ajouter}>
          <label>{t("bon.asin")}<input type="text" required maxLength={20} value={asin} onChange={(e) => setAsin(e.target.value)} /></label>
          <label>{t("analyse.place")}<select value={mp} onChange={(e) => setMp(e.target.value)}>
            {places.map((p) => <option key={p.code} value={p.code}>{p.domaine}</option>)}</select></label>
          <label className="etroit">{t("bon.quantite")}<input type="number" min={1} required value={qte} onChange={(e) => setQte(e.target.value)} /></label>
          <button type="submit" className="secondaire">{t("bon.ajouter_ligne")}</button>
        </form>
      )}
      {erreur && <p role="alert" className="alerte">{t(`erreur.${erreur}`)}</p>}
      {(b.statut === "BROUILLON" || b.statut === "ENVOYE") && b.lignes.length > 0 && <EnvoiMessagerie b={b} maj={maj} />}
      <div className="actions">
        {b.lignes.length > 0 && <a className="bouton-lien" href={documentBon(b.id, "pdf")}>{t("bon.pdf")}</a>}
        {b.lignes.length > 0 && <a className="bouton-lien" href={documentBon(b.id, "xlsx")}>{t("bon.excel")}</a>}
        {b.statut === "BROUILLON" && <button type="button" className="principal" onClick={() => faire(actionBon(b.id, "envoyer"))}
          title={t("bon.marquer_info")}>{t("bon.marquer_envoye")}</button>}
        {b.statut === "ENVOYE" && <button type="button" className="principal"
          onClick={() => faire(recevoirBon(b.id, Object.fromEntries(Object.entries(recues).map(([k, v]) => [k, Number(v || 0)]))))}>{t("bon.recevoir")}</button>}
        {(b.statut === "BROUILLON" || b.statut === "ENVOYE") && <button type="button" className="secondaire" onClick={() => faire(actionBon(b.id, "annuler"))}>{t("bon.annuler")}</button>}
      </div>
    </section>
  );
}

const ROLES = ["code", "prix", "designation", "colisage", "minimum"];
const REVENTE_TON: Record<string, string> = { AUTORISEE: "v", INTERDITE: "r", A_VERIFIER: "a" };

function Revente({ r, extrait, source }: { r: string; extrait?: boolean; source?: string | null }) {
  const info = [extrait ? t("revente.a_relire") : null, source].filter(Boolean).join(" · ");
  return (
    <span className="statut-point">
      <i className={`point ${REVENTE_TON[r]}`} aria-hidden="true" />{t(`revente.court.${r}`)}
      {info && (source ? <a href={source} target="_blank" rel="noreferrer" className="info-mini" title={info}>ⓘ</a>
        : <abbr className="info-mini" title={info}>ⓘ</abbr>)}
    </span>
  );
}

// [RM-AMZ-102, 103] catalogue par fichier, colonnes mémorisées, analyse
function Catalogue({ f, changer, analyser }: { f: FournisseurBilan; changer: () => void; analyser: (tid: string) => void }) {
  const [fichier, setFichier] = useState<Fichier | null>(null);
  const [colonnes, setColonnes] = useState<Colonnes>({});
  const [carton, setCarton] = useState(false);
  const [bilan, setBilan] = useState<string | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  const deposer = (fl?: File) => { if (!fl) return; setErreur(null); setBilan(null);
    deposerTarif(f.id, fl).then((x) => { setFichier(x); setColonnes(x.colonnes); }).catch((e) => setErreur(e.message)); };
  const enregistrer = () => fichier && enregistrerTarif(f.id, fichier.fichier_id, colonnes, carton).then((r) => {
    setBilan(t("catalogue.bilan", { lignes: r.lignes, rejets: r.rejets.length, doublons: r.doublons })); setFichier(null); changer();
  }).catch((e) => setErreur(e.message));
  return (
    <div className="bloc-catalogue">
      <h3>{t("catalogue.titre")}</h3>
      {f.catalogue ? <p className="meta">{t("catalogue.etat", { lignes: f.catalogue.lignes, rejets: f.catalogue.rejets,
        fichier: f.catalogue.nom_fichier, date: dateCourte(f.catalogue.maj) })}</p> : <p className="meta">{t("catalogue.aucun")}</p>}
      <div className="actions">
        <label className="bouton-lien fichier-bouton">{f.catalogue ? t("catalogue.remplacer") : t("catalogue.charger")}
          <input type="file" accept=".csv,.txt,.xlsx" className="masque" onChange={(e) => deposer(e.target.files?.[0])} /></label>
        {f.catalogue && <button type="button" className="principal" disabled={!f.analysable}
          title={f.analysable ? undefined : t("erreur.REVENTE_INTERDITE")}
          onClick={() => analyserTarif(f.id).then((r) => analyser(r.traitement_id)).catch((e) => setErreur(e.message))}>
          {t("catalogue.analyser", { n: f.catalogue.lignes })}</button>}
      </div>
      {fichier && (
        <div className="colonnes-tarif">
          <p className="meta">{fichier.nom} · {t("catalogue.lignes_fichier", { n: fichier.nb_lignes })}</p>
          <div className="grille-roles">
            {ROLES.map((r) => (
              <label key={r}>{t(`role.${r}`)}{r === "code" || r === "prix" ? " *" : ""}
                <select value={colonnes[r] ?? ""} onChange={(e) => setColonnes({ ...colonnes, [r]: e.target.value === "" ? null : Number(e.target.value) })}>
                  <option value="">{t("sourcing.ignorer")}</option>
                  {fichier.entetes.map((h, i) => <option key={i} value={i}>{h || `#${i + 1}`}</option>)}
                </select></label>))}
          </div>
          <label className="case"><input type="checkbox" checked={carton} onChange={(e) => setCarton(e.target.checked)} />{t("catalogue.prix_carton")}</label>
          <button type="button" className="principal" disabled={colonnes.code == null || colonnes.prix == null} onClick={enregistrer}>
            {t("catalogue.enregistrer")}</button>
        </div>)}
      {bilan && <p role="status" className="succes">{bilan}</p>}
      {erreur && <p role="alert" className="alerte">{t(`erreur.${erreur}`)}</p>}
    </div>
  );
}

// [RM-AMZ-100] fiche
function Fiche({ f, changer, analyser }: { f: FournisseurBilan; changer: () => void; analyser: (tid: string) => void }) {
  const [v, setV] = useState({ pays: f.pays ?? "", site: f.site ?? "", courriel: f.courriel ?? "", delai: String(f.delai_jours),
    port: f.port_unitaire === null ? "" : String(f.port_unitaire).replace(".", ","), revente: f.revente,
    source: f.revente_source ?? "", notes: f.notes ?? "" });
  const [etat, setEtat] = useState<string | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  useEffect(() => setV({ pays: f.pays ?? "", site: f.site ?? "", courriel: f.courriel ?? "", delai: String(f.delai_jours),
    port: f.port_unitaire === null ? "" : String(f.port_unitaire).replace(".", ","), revente: f.revente,
    source: f.revente_source ?? "", notes: f.notes ?? "" }), [f.id]);  // eslint-disable-line
  const enregistrer = (e: FormEvent) => {
    e.preventDefault(); setErreur(null); setEtat(null);
    modifierFournisseur(f.id, { pays: v.pays, site: v.site, courriel: v.courriel, delai_jours: Number(v.delai),
      port_unitaire: v.port === "" ? null : Number(v.port.replace(",", ".")), revente: v.revente as FournisseurBilan["revente"],
      revente_source: v.source, notes: v.notes }).then(() => { setEtat(t("fiche.enregistree")); changer(); })
      .catch((x) => setErreur(x.message));
  };
  const champ = (k: keyof typeof v, type = "text") => (
    <label>{t(`fiche.${k}`)}<input type={type} value={v[k]} onChange={(e) => setV({ ...v, [k]: e.target.value })} /></label>);
  return (
    <section className="carte fiche-fournisseur" aria-label={f.nom}>
      <header className="detail-tete"><div><h2>{f.nom}</h2>
        <p className="meta">{[f.pays, f.reference ? t("fiche.depuis_annuaire") : null].filter(Boolean).join(" · ")}</p></div>
        <Revente r={f.revente} source={f.revente_source} /></header>
      <form className="grille-fiche" onSubmit={enregistrer}>
        {champ("pays")}{champ("site", "url")}{champ("courriel", "email")}{champ("delai", "number")}{champ("port")}
        <label>{t("fiche.revente")}<select value={v.revente} onChange={(e) => setV({ ...v, revente: e.target.value as FournisseurBilan["revente"] })}>
          {["AUTORISEE", "A_VERIFIER", "INTERDITE"].map((r) => <option key={r} value={r}>{t(`revente.${r}`)}</option>)}</select></label>
        <label className="large">{t("fiche.source")}<input type="url" value={v.source} onChange={(e) => setV({ ...v, source: e.target.value })} /></label>
        <label className="large">{t("fiche.notes")}<textarea rows={2} value={v.notes} onChange={(e) => setV({ ...v, notes: e.target.value })} /></label>
        <div className="actions"><button type="submit" className="secondaire">{t("fiche.enregistrer")}</button>
          {etat && <span role="status" className="succes">{etat}</span>}
          {erreur && <span role="alert" className="alerte">{t(`erreur.${erreur}`)}</span>}</div>
      </form>
      <Catalogue f={f} changer={changer} analyser={analyser} />
    </section>
  );
}

// [RM-AMZ-101] annuaire : sélection groupée, filtres, lignes compactes
function Annuaire({ ajoute }: { ajoute: () => void }) {
  const [refs, setRefs] = useState<Reference[]>([]);
  const [erreur, setErreur] = useState<string | null>(null);
  const [choix, setChoix] = useState<string[]>([]);
  const [cherche, setCherche] = useState("");
  const [reventes, setReventes] = useState<string[]>(["AUTORISEE", "A_VERIFIER", "INTERDITE"]);
  const [masquerAjoutes, setMasquerAjoutes] = useState(false);
  const [bilan, setBilan] = useState<string | null>(null);
  const lire = () => lireAnnuaire().then(setRefs).catch((e) => setErreur(e.message));
  useEffect(() => { lire(); }, []);
  const q = cherche.trim().toLowerCase();
  const visibles = refs.filter((r) => reventes.includes(r.revente) && !(masquerAjoutes && r.ajoute)
    && (!q || `${r.nom} ${r.pays} ${r.categories.map((c) => t(`rayon.${c}`)).join(" ")} ${r.note}`.toLowerCase().includes(q)));
  const cochables = visibles.filter((r) => !r.ajoute).map((r) => r.code);
  const tous = cochables.length > 0 && cochables.every((c) => choix.includes(c));
  const basculer = (code: string) => setChoix((l) => (l.includes(code) ? l.filter((c) => c !== code) : [...l, code]));
  const ajouter = () => ajouterReferences(choix).then((r) => {
    setBilan(t("annuaire.bilan", { n: r.ajoutes.length })); setChoix([]); lire(); ajoute();
  }).catch((e) => setErreur(e.message));
  return (
    <section className="carte annuaire">
      <div className="barre-filtres-rent">
        <input type="search" className="cherche" placeholder={t("filtre.chercher")} aria-label={t("filtre.chercher")}
          value={cherche} onChange={(e) => setCherche(e.target.value)} />
        <FiltreMultiple libelle={t("fiche.revente")} changer={setReventes}
          options={["AUTORISEE", "A_VERIFIER", "INTERDITE"].map((r) => ({ code: r, libelle: t(`revente.court.${r}`), coche: reventes.includes(r) }))} />
        <label className="case-filtre"><input type="checkbox" checked={masquerAjoutes} onChange={(e) => setMasquerAjoutes(e.target.checked)} />
          {t("annuaire.masquer_ajoutes")}</label>
        <span className="meta pousse">{t("annuaire.date", { date: refs[0] ? dateCourte(refs[0].date_lecture) : "" })}</span>
      </div>
      {choix.length > 0 && (
        <div className="barre-selection" role="region" aria-label={t("annuaire.selection")}>
          <span>{t("annuaire.selectionnes", { n: choix.length })}</span>
          <button type="button" className="principal" onClick={ajouter}>{t("annuaire.ajouter_selection", { n: choix.length })}</button>
          <button type="button" className="lien" onClick={() => setChoix([])}>{t("annuaire.vider")}</button>
        </div>)}
      {bilan && <p role="status" className="succes">{bilan}</p>}
      {erreur && <p role="alert" className="alerte">{t(`erreur.${erreur}`)}</p>}
      <div className="defile"><table className="table-compacte">
        <thead><tr>
          <th scope="col" className="case-suivi"><input type="checkbox" aria-label={t("annuaire.tout")} checked={tous}
            disabled={cochables.length === 0}
            onChange={(e) => setChoix(e.target.checked ? [...new Set([...choix, ...cochables])] : choix.filter((c) => !cochables.includes(c)))} /></th>
          <th scope="col">{t("fournisseurs.nom")}</th><th scope="col">{t("annuaire.familles")}</th>
          <th scope="col">{t("fiche.revente")}</th><th scope="col">{t("annuaire.connexion")}</th><th scope="col">{t("annuaire.acces")}</th>
        </tr></thead>
        <tbody>{visibles.map((r) => (
          <tr key={r.code} className={`${choix.includes(r.code) ? "choisie" : ""} ${r.ajoute ? "" : "cliquable"}`}
            onClick={(e) => { if (r.ajoute || (e.target as HTMLElement).closest("a, input")) return; basculer(r.code); }}>
            <td className="case-suivi">{r.ajoute ? <span className="positif" title={t("annuaire.ajoute")}>✓</span>
              : <input type="checkbox" aria-label={r.nom} checked={choix.includes(r.code)} onChange={() => basculer(r.code)} />}</td>
            <td><a className="produit" href={r.site} target="_blank" rel="noreferrer">{r.nom}</a> <span className="meta">{r.pays}</span>
              <div className="meta tronque" title={r.note}>{r.note}</div></td>
            <td className="meta" title={r.categories.map((c) => t(`rayon.${c}`)).join(", ")}>
              {r.categories.slice(0, 2).map((c) => t(`rayon.${c}`)).join(", ") || "—"}{r.categories.length > 2 ? ` +${r.categories.length - 2}` : ""}</td>
            <td><Revente r={r.revente} extrait={r.verification === "EXTRAIT"} source={r.source || null} /></td>
            <td className="sans-retour">{r.connexion === "FICHIER" && <span className="etiquette">{t("connexion.court.FICHIER")}</span>}
              {r.api && <span className="etiquette" title={t("annuaire.api_a_brancher")}>API</span>}
              {r.connexion !== "FICHIER" && !r.api && <span className="meta">—</span>}</td>
            <td className="meta tronque" title={r.acces}>{r.acces}</td>
          </tr>))}</tbody>
      </table></div>
    </section>
  );
}

export function FournisseursVue({ bonInitial, voirLot, analyserTraitement }: { bonInitial?: string; voirLot: (id: string) => void;
  analyserTraitement: (tid: string) => void }) {
  const [onglet, setOnglet] = useState<"mes" | "annuaire" | "bons">(bonInitial ? "bons" : "mes");
  const [fiche, setFiche] = useState<string | null>(null);
  const [fs, setFs] = useState<FournisseurBilan[]>([]);
  const [bons, setBons] = useState<Bon[]>([]);
  const [choisi, setChoisi] = useState<string | undefined>(bonInitial);
  const [filtre, setFiltre] = useState("TOUS");
  const [nom, setNom] = useState(""); const [delai, setDelai] = useState("7");
  const [erreur, setErreur] = useState<string | null>(null);
  const charger = () => Promise.all([listerFournisseurs().then(setFs), listerBons().then((b) => {
    setBons(b); setChoisi((c) => c ?? b[0]?.id);
  })]).catch((e) => setErreur(e.message));
  useEffect(() => { charger(); }, []);  // eslint-disable-line
  const maj = (b: Bon) => { setBons((x) => [b, ...x.filter((y) => y.id !== b.id)].sort((p, q) => q.reference.localeCompare(p.reference))); setChoisi(b.id); listerFournisseurs().then(setFs); };
  const ajouter = async (e: FormEvent) => {
    e.preventDefault(); setErreur(null);
    try { await creerFournisseur(nom, Number(delai)); setNom(""); charger(); } catch (x) { setErreur((x as Error).message); }
  };
  const bon = bons.find((b) => b.id === choisi);
  const visibles = bons.filter((b) => filtre === "TOUS" || b.statut === filtre);
  return (
    <div className="vue">
      <h1>{t("fournisseurs.titre")}</h1>
      <div className="barre-filtres"><div className="onglets-ligne" role="tablist">
        {(["mes", "annuaire", "bons"] as const).map((o) => <button key={o} type="button" role="tab" aria-selected={onglet === o}
          onClick={() => setOnglet(o)}>{t(`fournisseurs.onglet.${o}`)}</button>)}</div></div>
      {onglet === "annuaire" && <Annuaire ajoute={() => listerFournisseurs().then(setFs)} />}
      {onglet === "mes" && <>
      <section className="carte" aria-labelledby="t-f">
        <div className="defile">
          <table>
            <thead><tr><th scope="col">{t("fournisseurs.nom")}</th><th scope="col">{t("fiche.revente")}</th>
              <th scope="col">{t("catalogue.titre")}</th><th scope="col" className="num">{t("fournisseurs.achete")}</th>
              <th scope="col" className="num">{t("fournisseurs.roi")}</th><th scope="col" className="num">{t("fournisseurs.delai_reel")}</th>
              <th scope="col"><span className="masque">{t("fournisseurs.nouveau_bon")}</span></th></tr></thead>
            <tbody>{fs.map((f) => (
              <tr key={f.id} className={fiche === f.id ? "choisie" : undefined}>
                <td><button type="button" className="lien produit" onClick={() => setFiche(fiche === f.id ? null : f.id)}>{f.nom}</button>
                  <div className="meta">{[f.pays, t("fournisseurs.lots", { n: f.lots }), t("jours", { n: f.delai_jours })].filter(Boolean).join(" · ")}</div></td>
                <td><Revente r={f.revente} source={f.revente_source} /></td>
                <td className="meta">{f.catalogue ? t("catalogue.court", { n: f.catalogue.lignes, date: dateCourte(f.catalogue.maj) }) : "—"}</td>
                <td className="num">{monnaie(n(f.achete_12_mois), f.devise)}</td>
                <td className="num">{pourcent(n(f.roi_prevu))} → <span className={f.roi_reel !== null && f.roi_prevu !== null && f.roi_reel < f.roi_prevu ? "negatif" : ""}>{pourcent(n(f.roi_reel))}</span></td>
                <td className="num">{f.delai_reel_jours === null ? "—" : t("jours", { n: f.delai_reel_jours })}</td>
                <td><button type="button" className="lien" onClick={() => creerBon(f.id).then((b) => { maj(b); setOnglet("bons"); }).catch((e) => setErreur(e.message))}>{t("fournisseurs.nouveau_bon")}</button></td>
              </tr>))}</tbody>
          </table>
        </div>
        <form className="formulaire nu" onSubmit={ajouter}>
          <label>{t("fournisseurs.nom")}<input type="text" required maxLength={120} value={nom} onChange={(e) => setNom(e.target.value)} /></label>
          <label className="etroit">{t("fournisseurs.delai")}<input type="number" min={0} max={365} value={delai} onChange={(e) => setDelai(e.target.value)} /></label>
          <button type="submit" className="secondaire">{t("fournisseurs.ajouter")}</button>
        </form>
        {erreur && <p role="alert" className="alerte">{t(`erreur.${erreur}`)}</p>}
      </section>
      {fiche && fs.find((f) => f.id === fiche) && <Fiche f={fs.find((f) => f.id === fiche)!} changer={() => listerFournisseurs().then(setFs)}
        analyser={analyserTraitement} />}
      </>}
      {onglet === "bons" && <div className="contenu sans-marge">
        <aside className="colonne" aria-labelledby="t-b">
          <h2 id="t-b" className="h-colonne">{t("bons.titre")}</h2>
          <div role="group" className="onglets" aria-label={t("bons.titre")}>
            {STATUTS.map((s) => <button key={s} type="button" aria-pressed={filtre === s} onClick={() => setFiltre(s)}>
              {s === "TOUS" ? t("bons.tous") : t(`statut_bon.${s}`)}</button>)}
          </div>
          {visibles.length === 0 ? <p className="meta">{t("bons.vide")}</p> : (
            <ul className="liste" role="list">{visibles.map((b) => (
              <li key={b.id}><button type="button" className={b.id === choisi ? "lot actif" : "lot"} aria-current={b.id === choisi} onClick={() => setChoisi(b.id)}>
                <span className="lot-nom">{b.reference} · {b.fournisseur?.nom}</span>
                <span className="lot-meta"><span>{monnaie(n(b.montant), b.devise ?? "EUR")}</span>
                  <span className={`statut-bon ${b.statut}`}>{t(`statut_bon.${b.statut}`)}</span></span>
              </button></li>))}</ul>
          )}
        </aside>
        <div className="detail">{bon && <DetailBon b={bon} maj={maj} voirLot={voirLot} />}</div>
      </div>}
    </div>
  );
}

import { useEffect, useState } from "react";
import { Conformite, Coordonnees, EnregConf, FicheConf, ProduitConf, TexteConf, ajouterEnregistrement, ecrireFiche,
  lireConformite, supprimerEnregistrement } from "./api";
import { dateCourte, t } from "./i18n";
import type { Msg } from "./i18n";

type Textes = Record<string, TexteConf>;

function Alerte({ a, textes }: { a: Msg; textes: Textes }) {
  const p: Record<string, string> = {};
  for (const [k, v] of Object.entries(a.params)) p[k] = k === "filiere" ? t(`filiere.${v}`) : k === "qui" ? t(`qui.${v}`) : String(v);
  const tx = typeof a.params.texte === "string" ? textes[a.params.texte] : undefined;
  return <li>{t(`msg.${a.code}`, p)}{tx && <> · <a href={tx.url} target="_blank" rel="noreferrer">{tx.reference}</a></>}</li>;
}

function Coord({ titre, v, maj }: { titre: string; v: Coordonnees; maj: (c: Coordonnees) => void }) {
  const champ = (k: keyof Coordonnees, type = "text", max = 200) => (
    <label>{t(`conf.${k}`)}<input type={type} maxLength={max} value={v[k] ?? ""} onChange={(e) => maj({ ...v, [k]: e.target.value || null })} /></label>);
  return <fieldset className="groupe"><legend>{titre}</legend>{champ("nom")}{champ("adresse", "text", 400)}{champ("courriel", "email", 254)}</fieldset>;
}

function Fiche({ p, c, enregistre }: { p: ProduitConf; c: Conformite; enregistre: () => void }) {
  const [f, setF] = useState<FicheConf>(p.fiche);
  const [erreur, setErreur] = useState<string | null>(null);
  const [ok, setOk] = useState(false);
  const maj = (x: Partial<FicheConf>) => { setF({ ...f, ...x }); setOk(false); };
  const placesUe = p.places.filter((x) => c.places_ue.includes(x));
  const basculer = (fil: string) => maj({ filieres: f.filieres.includes(fil) ? f.filieres.filter((x) => x !== fil) : [...f.filieres, fil] });
  const sauver = () => ecrireFiche(f).then(() => { setErreur(null); setOk(true); enregistre(); }).catch((e) => setErreur(e.message));
  return (
    <div className="fiche-conf">
      <Coord titre={t("conf.fabricant")} v={f.fabricant} maj={(x) => maj({ fabricant: x })} />
      <div className="formulaire nu">
        <label>{t("conf.hors_ue")}<select value={f.fabricant_hors_ue === null ? "" : String(f.fabricant_hors_ue)}
          onChange={(e) => maj({ fabricant_hors_ue: e.target.value === "" ? null : e.target.value === "true" })}>
          <option value="">{t("conf.a_preciser")}</option><option value="false">{t("conf.non")}</option><option value="true">{t("conf.oui")}</option></select></label>
        <label className="case"><input type="checkbox" checked={f.avertissements_ok} onChange={(e) => maj({ avertissements_ok: e.target.checked })} />{t("conf.avertissements")}</label>
      </div>
      {f.fabricant_hors_ue && <Coord titre={t("conf.responsable")} v={f.responsable} maj={(x) => maj({ responsable: x })} />}
      <fieldset className="groupe"><legend>{t("conf.filieres")}</legend>
        <div className="formulaire nu">
          <label>{t("conf.producteur")}<select value={f.producteur} onChange={(e) => maj({ producteur: e.target.value })}>
            {["A_DETERMINER", "OUI", "NON"].map((x) => <option key={x} value={x}>{t(`role.${x}`)}</option>)}</select></label>
          {c.filieres.map((x) => <label key={x} className="case"><input type="checkbox" checked={f.filieres.includes(x)} onChange={() => basculer(x)} />{t(`filiere.${x}`)}</label>)}
          {f.filieres.includes("AUTRE") && <label>{t("conf.intitule")}<input type="text" maxLength={80} value={f.intitule_autre ?? ""} onChange={(e) => maj({ intitule_autre: e.target.value || null })} /></label>}
        </div>
        {f.producteur === "NON" && f.filieres.length > 0 && placesUe.length > 0 && (
          <div className="formulaire nu">
            {placesUe.flatMap((pays) => f.filieres.map((fil) => {
              const k = `${pays}:${fil}`;
              return <label key={k}>{t("conf.numero_producteur", { pays, filiere: t(`filiere.${fil}`) })}
                <input type="text" maxLength={64} value={f.numeros_producteur[k] ?? ""}
                  onChange={(e) => maj({ numeros_producteur: { ...f.numeros_producteur, [k]: e.target.value } })} /></label>;
            }))}
          </div>)}
      </fieldset>
      <div className="formulaire nu">
        {placesUe.includes("FR") && <label className="case"><input type="checkbox" checked={f.triman_ok} onChange={(e) => maj({ triman_ok: e.target.checked })} />{t("conf.triman")}</label>}
        <label>{t("conf.ce")}<select value={f.marquage_ce} onChange={(e) => maj({ marquage_ce: e.target.value })}>
          {["A_DETERMINER", "OUI", "NON_CONCERNE"].map((x) => <option key={x} value={x}>{t(`ce.${x}`)}</option>)}</select></label>
        <button type="button" className="principal" onClick={sauver}>{t("conf.enregistrer")}</button>
        {ok && <span className="meta">{t("conf.enregistre")}</span>}
      </div>
      {erreur && <p role="alert" className="alerte">{t(`erreur.${erreur}`)}</p>}
    </div>
  );
}

function LigneProduit({ p, ouvert, basculer }: { p: ProduitConf; ouvert: boolean; basculer: () => void }) {
  return (
    <tr className={ouvert ? "choisi" : undefined}>
      <td><div className="produit">{p.designation ?? p.asin}</div><div className="meta">{p.asin} · {p.places.join(" · ")}</div></td>
      <td><span className={`statut-conf ${p.statut}`}>{t(`conf.statut.${p.statut}`)}</span></td>
      <td className="num masque-tel">{p.alertes.length || "—"}</td>
      <td><button type="button" className="lien" aria-expanded={ouvert} aria-label={`${t("conf.fiche")} ${p.designation ?? p.asin}`}
        onClick={basculer}>{t("conf.fiche")}</button></td>
    </tr>
  );
}

function FicheProduit({ p, c, textes, recharger }: { p: ProduitConf; c: Conformite; textes: Textes; recharger: () => void }) {
  return (
    <section className="carte" aria-label={`${t("conf.fiche")} ${p.designation ?? p.asin}`}>
      <h2>{t("conf.fiche")} · {p.designation ?? p.asin}</h2>
      {p.alertes.length > 0 && <ul className="alertes-conf">{p.alertes.map((a, i) => <Alerte key={i} a={a} textes={textes} />)}</ul>}
      {p.statut !== "NON_COUVERT" && <Fiche key={p.asin} p={p} c={c} enregistre={recharger} />}
    </section>
  );
}

function Enregistrements({ c, textes, recharger }: { c: Conformite; textes: Textes; recharger: () => void }) {
  const [n, setN] = useState({ pays: "FR", filiere: "EMBALLAGES", numero: "", intitule: "", mandataire: "" });
  const [erreur, setErreur] = useState<string | null>(null);
  const ajouter = () => ajouterEnregistrement(n).then(() => { setErreur(null); setN({ ...n, numero: "", intitule: "", mandataire: "" }); recharger(); })
    .catch((e) => setErreur(e.message));
  const retirer = (e: EnregConf) => supprimerEnregistrement(e.cle).then(recharger).catch((x) => setErreur(x.message));
  return (
    <section className="carte" aria-label={t("conf.enregistrements")}>
      <h2>{t("conf.enregistrements")}</h2>
      {c.enregistrements.length === 0 ? <p className="meta">{t("conf.aucun_enregistrement")}</p> : (
        <div className="defile"><table>
          <thead><tr><th scope="col">{t("col.place")}</th><th scope="col">{t("conf.filiere")}</th><th scope="col">{t("conf.numero")}</th>
            <th scope="col"><span className="masque">{t("conf.retirer")}</span></th></tr></thead>
          <tbody>{c.enregistrements.map((e) => (
            <tr key={e.cle}>
              <td>{e.pays}</td>
              <td>{t(`filiere.${e.filiere}`)}{e.intitule ? ` · ${e.intitule}` : ""}
                {e.texte && textes[e.texte] && <div className="meta"><a href={textes[e.texte].url} target="_blank" rel="noreferrer">{textes[e.texte].reference}</a></div>}</td>
              <td className="coupe">{e.numero}{e.mandataire && <div className="meta">{t("conf.mandataire")} : {e.mandataire}</div>}
                {e.avertissements.length > 0 && <ul className="alertes-conf meta attention">{e.avertissements.map((a, i) => <Alerte key={i} a={a} textes={textes} />)}</ul>}</td>
              <td><button type="button" className="lien" aria-label={`${t("conf.retirer")} ${e.pays} ${t(`filiere.${e.filiere}`)}`} onClick={() => retirer(e)}>{t("conf.retirer")}</button></td>
            </tr>))}</tbody>
        </table></div>)}
      <div className="formulaire">
        <label className="etroit">{t("col.place")}<select value={n.pays} onChange={(e) => setN({ ...n, pays: e.target.value })}>
          {c.places_ue.map((x) => <option key={x} value={x}>{x}</option>)}</select></label>
        <label>{t("conf.filiere")}<select value={n.filiere} onChange={(e) => setN({ ...n, filiere: e.target.value })}>
          {c.filieres.map((x) => <option key={x} value={x}>{t(`filiere.${x}`)}</option>)}</select></label>
        {n.filiere === "AUTRE" && <label>{t("conf.intitule")}<input type="text" maxLength={80} value={n.intitule} onChange={(e) => setN({ ...n, intitule: e.target.value })} /></label>}
        <label>{t("conf.numero")}<input type="text" maxLength={64} value={n.numero} onChange={(e) => setN({ ...n, numero: e.target.value })} /></label>
        <label>{t("conf.mandataire")}<input type="text" maxLength={200} value={n.mandataire} onChange={(e) => setN({ ...n, mandataire: e.target.value })} /></label>
        <button type="button" className="principal" onClick={ajouter}>{t("conf.ajouter")}</button>
      </div>
      {erreur && <p role="alert" className="alerte">{t(`erreur.${erreur}`)}</p>}
    </section>
  );
}

export function ConformiteVue() {
  const [c, setC] = useState<Conformite | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  const [choisi, setChoisi] = useState<string | null>(null);
  const recharger = () => lireConformite().then(setC).catch((e) => setErreur(e.message));
  useEffect(() => { recharger(); }, []);
  if (erreur) return <p role="alert" className="alerte">{t(`erreur.${erreur}`)}</p>;
  if (!c) return <p>{t("chargement")}</p>;
  const textes: Textes = Object.fromEntries(c.textes.map((x) => [x.code, x]));
  return (
    <div className="vue">
      <div className="entete-vue"><h1>{t("conf.titre")}</h1><span className="meta">{t("conf.lecture", { date: dateCourte(c.date_lecture) })}</span></div>
      <div className="kpis">
        <div className="kpi"><span className="kpi-l">{t("conf.statut.A_COMPLETER")}</span><span className="kpi-v">{c.compteurs.a_completer}</span></div>
        <div className="kpi"><span className="kpi-l">{t("conf.statut.RIEN_DE_SIGNALE")}</span><span className="kpi-v">{c.compteurs.rien_de_signale}</span></div>
        <div className="kpi"><span className="kpi-l">{t("conf.statut.NON_COUVERT")}</span><span className="kpi-v">{c.compteurs.non_couverts}</span></div>
      </div>
      <section className="carte" aria-label={t("conf.produits")}>
        <h2>{t("conf.produits")}</h2>
        {c.produits.length === 0 ? <p className="meta">{t("conf.aucun_produit")}</p> : (
          <div className="defile"><table>
            <thead><tr><th scope="col">{t("col.produit")}</th><th scope="col">{t("col.suivi")}</th>
              <th scope="col" className="num masque-tel">{t("conf.points")}</th><th scope="col"><span className="masque">{t("conf.fiche")}</span></th></tr></thead>
            <tbody>{c.produits.map((p) => <LigneProduit key={p.asin} p={p} ouvert={choisi === p.asin}
              basculer={() => setChoisi(choisi === p.asin ? null : p.asin)} />)}</tbody>
          </table></div>)}
      </section>
      {choisi && c.produits.some((p) => p.asin === choisi) &&
        <FicheProduit p={c.produits.find((p) => p.asin === choisi)!} c={c} textes={textes} recharger={recharger} />}
      <Enregistrements c={c} textes={textes} recharger={recharger} />
      <section className="carte" aria-label={t("conf.textes")}>
        <h2>{t("conf.textes")}</h2>
        <ul className="textes-conf">{c.textes.map((x) => (
          <li key={x.code}><a href={x.url} target="_blank" rel="noreferrer">{x.reference}</a>
            <span className="meta"> · {t(x.verifie ? "conf.verifie" : "conf.non_verifie")}{x.note ? ` · ${t(`note.${x.note}`)}` : ""}</span></li>))}</ul>
      </section>
    </div>
  );
}

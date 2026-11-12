import { useEffect, useState } from "react";
import { CasRemb, Remboursements, lireRemboursements, suivreCas } from "./api";
import { dateCourte, monnaie, t } from "./i18n";

const n = (v: number | null) => (v === null ? null : String(v));

function texteDossier(c: CasRemb): string {
  const p: Record<string, string | number> = { ...c.faits, fnsku: c.fnsku ?? "—", sku: c.sku ?? "—", asin: c.asin ?? "—",
    commande: c.commande ?? "—", marketplace: c.marketplace, unites: c.unites ?? "—", devise: c.devise };
  return t(`dossier.${c.type}`, p);
}

function Ligne({ c, maj }: { c: CasRemb; maj: (c: CasRemb) => void }) {
  const [ouvert, setOuvert] = useState(false);
  const [numero, setNumero] = useState(c.case_id ?? "");
  const [copie, setCopie] = useState(false);
  const [erreur, setErreur] = useState<string | null>(null);
  const suivre = (statut: string) => suivreCas(c.cle, statut, numero).then(maj).catch((e) => setErreur(e.message));
  const actif = c.statut === "DETECTE" || c.statut === "DOSSIER_ENVOYE";
  return (
    <>
      <tr>
        <td><div className="produit">{t(`type.${c.type}`)}</div><div className="meta">{c.marketplace} · {c.asin ?? c.sku ?? c.fnsku}{c.commande ? ` · ${c.commande}` : ""}</div></td>
        <td className="num">{c.unites ?? "—"}</td>
        <td className="num">{monnaie(n(c.valeur_achat), c.devise)}</td>
        <td>{c.echeance ? dateCourte(c.echeance) : "—"}</td>
        <td><span className={`statut-cas ${c.statut}`}>{t(`suivi.${c.statut}`)}</span>
          {c.case_id && <div className="meta">{c.case_id}</div>}
          {c.montant_verse !== null && <div className="meta">{monnaie(n(c.montant_verse), c.devise)}</div>}</td>
        <td><button type="button" className="lien" aria-expanded={ouvert} onClick={() => setOuvert(!ouvert)}>{t("remb.dossier")}</button></td>
      </tr>
      {ouvert && (
        <tr className="dossier"><td colSpan={6}>
          <p className="texte-dossier">{texteDossier(c)}</p>
          <div className="formulaire nu">
            <button type="button" className="secondaire" onClick={() => navigator.clipboard?.writeText(texteDossier(c)).then(() => setCopie(true))}>
              {copie ? t("remb.copie") : t("remb.copier")}</button>
            {actif && <>
              <label className="etroit">{t("remb.numero_cas")}<input type="text" maxLength={40} value={numero} onChange={(e) => setNumero(e.target.value)} /></label>
              {c.statut === "DETECTE" && <button type="button" className="principal" onClick={() => suivre("DOSSIER_ENVOYE")}>{t("remb.envoye")}</button>}
              {c.statut === "DOSSIER_ENVOYE" && <>
                <button type="button" className="principal" onClick={() => suivre("REMBOURSE")}>{t("remb.rembourse")}</button>
                <button type="button" className="secondaire" onClick={() => suivre("REFUSE")}>{t("remb.refuse")}</button></>}
              <button type="button" className="secondaire" onClick={() => suivre("CLOS")}>{t("remb.clore")}</button>
            </>}
          </div>
          {erreur && <p role="alert" className="alerte">{t(`erreur.${erreur}`)}</p>}
        </td></tr>
      )}
    </>
  );
}

export function RemboursementsVue() {
  const [r, setR] = useState<Remboursements | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  useEffect(() => { lireRemboursements().then(setR).catch((e) => setErreur(e.message)); }, []);
  if (erreur) return <p role="alert" className="alerte">{t(`erreur.${erreur}`)}</p>;
  if (!r) return <p>{t("chargement")}</p>;
  const maj = (c: CasRemb) => setR({ ...r, cas: r.cas.map((x) => (x.cle === c.cle ? c : x)),
    compteurs: { ...r.compteurs, a_verifier: r.cas.filter((x) => (x.cle === c.cle ? c : x).statut === "DETECTE").length,
      en_cours: r.cas.filter((x) => (x.cle === c.cle ? c : x).statut === "DOSSIER_ENVOYE").length } });
  return (
    <div className="vue">
      <div className="entete-vue"><h1>{t("remb.titre")}</h1><span className="meta">{t("remb.source", { source: r.source_delais })}</span></div>
      <div className="kpis">
        <div className="kpi"><span className="kpi-l">{t("remb.a_verifier")}</span><span className="kpi-v">{r.compteurs.a_verifier}</span></div>
        <div className="kpi"><span className="kpi-l">{t("remb.en_cours")}</span><span className="kpi-v">{r.compteurs.en_cours}</span></div>
        <div className="kpi"><span className="kpi-l">{t("remb.verses")}</span>
          <span className="kpi-v">{r.compteurs.verses_12_mois.length ? r.compteurs.verses_12_mois.map((v) => monnaie(n(v.montant), v.devise)).join(" · ") : "—"}</span></div>
        <div className="kpi"><span className="kpi-l">{t("remb.commission")}</span><span className="kpi-v">0 %</span></div>
      </div>
      <section className="carte" aria-label={t("remb.titre")}>
        {r.cas.length === 0 ? <p className="meta">{t("remb.vide")}</p> : (
          <div className="defile">
            <table>
              <thead><tr><th scope="col">{t("col.type")}</th><th scope="col" className="num">{t("col.unites")}</th>
                <th scope="col" className="num">{t("col.valeur")}</th><th scope="col">{t("col.echeance")}</th>
                <th scope="col">{t("col.suivi")}</th><th scope="col"><span className="masque">{t("remb.dossier")}</span></th></tr></thead>
              <tbody>{r.cas.map((c) => <Ligne key={c.cle} c={c} maj={maj} />)}</tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}

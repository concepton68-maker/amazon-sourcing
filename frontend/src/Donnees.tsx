import { useEffect, useMemo, useState } from "react";
import { ajouterAuPlan, lire } from "./api";
import { monnaie, pourcent, t } from "./i18n";

// Écran « Données » [RM-AMZ-140] : chaque jeu collecté, à chercher, filtrer, trier, choisir, exporter.
type Type = "texte" | "nombre" | "monnaie" | "pourcent" | "date" | "oui_non" | "liste";
interface Colonne { cle: string; type: Type }
interface Jeu { jeu: string; colonnes: Colonne[]; lignes: Record<string, unknown>[]; tronque: boolean }
const JEUX = ["produits", "marche", "releves", "autorisations", "catalogues"];
const NUM = new Set<Type>(["nombre", "monnaie", "pourcent"]);
const CLE_VUE = "syllig-pilot-donnees";

const affiche = (v: unknown, ty: Type): string => {
  if (v === null || v === undefined || v === "") return "—";
  if (ty === "monnaie") return monnaie(String(v), "EUR");
  if (ty === "pourcent") return pourcent(String(v));
  if (ty === "nombre") return Number(v).toLocaleString("fr-FR");
  if (ty === "oui_non") return v ? t("oui") : t("non");
  if (ty === "date") return String(v).slice(0, 10).split("-").reverse().join("/");
  if (ty === "liste") { const k = `donnees.valeur.${v}`; const x = t(k); return x === k ? String(v) : x; }
  return String(v);
};

interface Filtre { min?: string; max?: string; valeurs?: string[] }

export function DonneesVue({ analyser }: { analyser: (code: string, prix: number) => void }) {
  const [nom, setNom] = useState<string>(() => { try { return localStorage.getItem(`${CLE_VUE}-jeu`) || "produits"; } catch { return "produits"; } });
  const [jeu, setJeu] = useState<Jeu | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  const [mot, setMot] = useState("");
  const [tri, setTri] = useState<{ cle: string; desc: boolean } | null>(null);
  const [filtres, setFiltres] = useState<Record<string, Filtre>>({});
  const [masquees, setMasquees] = useState<Set<string>>(new Set());
  const [ouvert, setOuvert] = useState<string | null>(null);
  const [choix, setChoix] = useState<Set<number>>(new Set());
  const [message, setMessage] = useState<string | null>(null);
  useEffect(() => {
    setJeu(null); setErreur(null); setFiltres({}); setTri(null); setChoix(new Set()); setMessage(null);
    try { localStorage.setItem(`${CLE_VUE}-jeu`, nom); } catch { /* sans stockage */ }
    lire<Jeu>(`/api/donnees/${nom}`).then(setJeu).catch((x) => setErreur((x as Error).message));
  }, [nom]);
  const cols = (jeu?.colonnes ?? []).filter((c) => !masquees.has(c.cle));
  const lignes = useMemo(() => {
    if (!jeu) return [];
    const m = mot.trim().toLowerCase();
    let l = jeu.lignes.map((x, i) => ({ x, i }));
    if (m) l = l.filter(({ x }) => jeu.colonnes.some((c) => (c.type === "texte" || c.type === "liste") && String(x[c.cle] ?? "").toLowerCase().includes(m)));
    for (const [cle, f] of Object.entries(filtres)) {
      const c = jeu.colonnes.find((y) => y.cle === cle); if (!c) continue;
      if (f.valeurs) l = l.filter(({ x }) => f.valeurs!.includes(String(x[cle] ?? "")));
      const nb = (s?: string) => (s === undefined || s.trim() === "" ? null : Number(s.replace(",", ".")) / (c.type === "pourcent" ? 100 : 1));
      const mi = nb(f.min), ma = nb(f.max);
      if (mi !== null) l = l.filter(({ x }) => x[cle] !== null && x[cle] !== undefined && Number(x[cle]) >= mi);   // absent : jamais retenu
      if (ma !== null) l = l.filter(({ x }) => x[cle] !== null && x[cle] !== undefined && Number(x[cle]) <= ma);
    }
    if (tri) {
      const c = jeu.colonnes.find((y) => y.cle === tri.cle);
      const avec = l.filter(({ x }) => x[tri.cle] !== null && x[tri.cle] !== undefined && x[tri.cle] !== "");
      const sans = l.filter(({ x }) => !(x[tri.cle] !== null && x[tri.cle] !== undefined && x[tri.cle] !== ""));
      avec.sort((a, b) => {
        const va = a.x[tri.cle], vb = b.x[tri.cle];
        const r = c && NUM.has(c.type) ? Number(va) - Number(vb) : String(va).localeCompare(String(vb), "fr");
        return tri.desc ? -r : r;
      });
      l = [...avec, ...sans];                                                                        // absent : toujours en dernier
    }
    return l;
  }, [jeu, mot, filtres, tri]);
  const valeursListe = (cle: string) => Array.from(new Set((jeu?.lignes ?? []).map((x) => String(x[cle] ?? "")))).sort();
  const basculer = (i: number) => setChoix((s) => { const n = new Set(s); if (n.has(i)) n.delete(i); else n.add(i); return n; });
  const tous = lignes.length > 0 && lignes.every(({ i }) => choix.has(i));
  const exporter = () => {
    const sep = ";";
    const echap = (s: string) => (/[";\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s);
    const texte = [cols.map((c) => echap(t(`donnees.col.${c.cle}`))).join(sep),
      ...lignes.map(({ x }) => cols.map((c) => { const v = x[c.cle]; return echap(v === null || v === undefined ? "" : NUM.has(c.type) ? String(v).replace(".", ",") : String(v)); }).join(sep))].join("\r\n");
    const url = URL.createObjectURL(new Blob(["﻿" + texte], { type: "text/csv;charset=utf-8" }));
    const a = document.createElement("a"); a.href = url; a.download = `${nom}-${new Date().toISOString().slice(0, 10)}.csv`; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 2000);
  };
  const versPlan = () => {
    const sel = lignes.filter(({ i }) => choix.has(i)).map(({ x }) => ({ origine: String(x.origine), marketplace: String(x.marketplace), code: String(x.code), asin: String(x.asin) }));
    ajouterAuPlan(sel).then((r) => { setMessage(t("plan.resultat", { n: r.ajoutees, b: r.bons.length })); setChoix(new Set()); }).catch((x) => setErreur((x as Error).message));
  };
  const actif = (cle: string) => { const f = filtres[cle]; return !!f && (!!f.valeurs || !!f.min || !!f.max); };
  return (
    <div className="vue">
      <div className="entete-vue"><h1>{t("donnees.titre")}</h1>
        <div className="actions">
          <input type="search" className="recherche-donnees" placeholder={t("donnees.chercher")} aria-label={t("donnees.chercher")} value={mot} onChange={(e) => setMot(e.target.value)} />
          {jeu && <span className="meta">{t("donnees.nombre", { n: lignes.length, total: jeu.lignes.length })}</span>}
          <button type="button" className="secondaire" disabled={!lignes.length} onClick={exporter}>{t("donnees.exporter")}</button>
        </div></div>
      <div role="tablist" className="onglets-ligne">{JEUX.map((j) => (
        <button key={j} type="button" role="tab" aria-selected={nom === j} onClick={() => setNom(j)}>{t(`donnees.jeu.${j}`)}</button>))}</div>
      <p className="meta">{t(`donnees.info.${nom}`)}</p>
      {erreur && <p role="alert" className="alerte">{t(`erreur.${erreur}`)}</p>}
      {message && <p role="status" className="succes">{message}</p>}
      {jeu && <details className="choix-colonnes"><summary>{t("donnees.colonnes")}</summary>
        <div>{jeu.colonnes.map((c) => <label key={c.cle} className="case-filtre"><input type="checkbox" checked={!masquees.has(c.cle)}
          onChange={() => setMasquees((s) => { const n = new Set(s); if (n.has(c.cle)) n.delete(c.cle); else n.add(c.cle); return n; })} />{t(`donnees.col.${c.cle}`)}</label>)}</div></details>}
      {choix.size > 0 && <div className="barre-selection"><span>{t("rent.choisis", { n: choix.size })}</span>
        {nom === "produits" && <button type="button" className="principal" onClick={versPlan}>{t("plan.ajouter")}</button>}
        <button type="button" className="lien" onClick={() => setChoix(new Set())}>{t("rent.tout_decocher")}</button></div>}
      <section className="carte">
        {!jeu ? <p className="meta">{t("chargement")}</p> : jeu.lignes.length === 0 ? <p className="meta">{t(`donnees.vide.${nom}`)}</p> : (
          <div className="defile"><table className="table-donnees">
            <thead><tr>
              <th className="case"><input type="checkbox" checked={tous} aria-label={tous ? t("rent.tout_decocher") : t("rent.tout_cocher")}
                onChange={() => setChoix(tous ? new Set() : new Set(lignes.map(({ i }) => i)))} /></th>
              {cols.map((c) => (
                <th key={c.cle} scope="col" className={NUM.has(c.type) ? "num" : undefined}
                  aria-sort={tri?.cle === c.cle ? (tri.desc ? "descending" : "ascending") : "none"}>
                  <button type="button" className={`tri ${tri?.cle === c.cle ? "actif" : ""}`}
                    onClick={() => setTri(tri?.cle === c.cle ? { cle: c.cle, desc: !tri.desc } : { cle: c.cle, desc: NUM.has(c.type) })}>
                    {t(`donnees.col.${c.cle}`)}{tri?.cle === c.cle ? (tri.desc ? " ↓" : " ↑") : ""}</button>
                  {c.type !== "texte" && <button type="button" className={`entonnoir ${actif(c.cle) ? "actif" : ""}`} aria-label={t("donnees.filtrer")}
                    title={t("donnees.filtrer")} onClick={() => setOuvert(ouvert === c.cle ? null : c.cle)}>▾</button>}
                  {ouvert === c.cle && <div className="filtre-colonne" onClick={(e) => e.stopPropagation()}>
                    {NUM.has(c.type) ? <>
                      <label>{t("donnees.min")}<input inputMode="decimal" value={filtres[c.cle]?.min ?? ""} placeholder={c.type === "pourcent" ? "%" : ""}
                        onChange={(e) => setFiltres({ ...filtres, [c.cle]: { ...filtres[c.cle], min: e.target.value } })} /></label>
                      <label>{t("donnees.max")}<input inputMode="decimal" value={filtres[c.cle]?.max ?? ""} placeholder={c.type === "pourcent" ? "%" : ""}
                        onChange={(e) => setFiltres({ ...filtres, [c.cle]: { ...filtres[c.cle], max: e.target.value } })} /></label></>
                      : <div className="valeurs">{valeursListe(c.cle).map((v) => {
                          const sel = filtres[c.cle]?.valeurs;
                          const coche = !sel || sel.includes(v);
                          return <label key={v} className="case-filtre"><input type="checkbox" checked={coche} onChange={() => {
                            const tout = valeursListe(c.cle); const cur = sel ?? tout;
                            const n = coche ? cur.filter((y) => y !== v) : [...cur, v];
                            setFiltres({ ...filtres, [c.cle]: { valeurs: n.length === tout.length ? undefined : n } });
                          }} />{affiche(v === "" ? null : c.type === "oui_non" ? v === "true" : v, c.type)}</label>; })}</div>}
                    <button type="button" className="lien" onClick={() => { const n = { ...filtres }; delete n[c.cle]; setFiltres(n); setOuvert(null); }}>{t("donnees.effacer")}</button>
                  </div>}
                </th>))}
            </tr></thead>
            <tbody>{lignes.slice(0, 2000).map(({ x, i }) => (
              <tr key={i} className={`cliquable ${choix.has(i) ? "choisie" : ""}`} onClick={() => basculer(i)}
                onDoubleClick={() => x.asin && analyser(String(x.asin), Number(x.cout_achat ?? x.prix_achat ?? 0))} title={t("rent.double_clic")}>
                <td className="case"><input type="checkbox" checked={choix.has(i)} onChange={() => basculer(i)} onClick={(e) => e.stopPropagation()} aria-label={String(x.titre ?? x.asin ?? i)} /></td>
                {cols.map((c) => <td key={c.cle} className={NUM.has(c.type) ? "num" : c.cle === "titre" || c.cle === "designation" ? "produit" : undefined}>{affiche(x[c.cle], c.type)}</td>)}
              </tr>))}</tbody>
          </table>
          {lignes.length > 2000 && <p className="meta">{t("donnees.limite", { n: lignes.length })}</p>}</div>)}
      </section>
    </div>
  );
}

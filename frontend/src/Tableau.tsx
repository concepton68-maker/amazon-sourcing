import { useEffect, useState } from "react";
import { Tableau, lireTableau } from "./api";
import { monnaie, pourcent, t } from "./i18n";

// Tableau de bord [RM-AMZ-091 à 094] : chiffres réels du compte, jamais inventés.
const m = (v: number | null | undefined, d: string) => (v === null || v === undefined ? "—" : monnaie(String(v), d));
const p = (v: number | null | undefined) => (v === null || v === undefined ? "—" : pourcent(String(v)));

function Courbe({ serie, devise }: { serie: Tableau["serie"]; devise: string }) {
  const L = 700, H = 200, G = 74, B = 22;
  const vals = serie.map((s) => s.profit);
  const max = Math.max(...vals, 0), min = Math.min(...vals, 0), e = max - min || 1;
  const y = (v: number) => 10 + ((max - v) / e) * (H - 10 - B);
  const x = (i: number) => G + (i * (L - G - 8)) / Math.max(serie.length - 1, 1);
  const ligne = vals.map((v, i) => `${i ? "L" : "M"}${x(i)} ${y(v)}`).join(" ");
  const graduations = [max, (max + min) / 2, min];
  return (
    <svg viewBox={`0 0 ${L} ${H}`} className="courbe-tableau" role="img" aria-label={t("tb.profit_jour")}>
      <defs><linearGradient id="aire" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stopColor="var(--accent)" stopOpacity=".22" /><stop offset="1" stopColor="var(--accent)" stopOpacity="0" /></linearGradient></defs>
      {graduations.map((g, k) => <g key={k}><line x1={G} x2={L - 8} y1={y(g)} y2={y(g)} stroke="var(--bord)" />
        <text x={G - 8} y={y(g) + 4} textAnchor="end" className="graduation">{new Intl.NumberFormat("fr-FR", { style: "currency", currency: devise, maximumFractionDigits: 0 }).format(g)}</text></g>)}
      <path d={`${ligne} L${x(vals.length - 1)} ${y(min)} L${x(0)} ${y(min)} Z`} fill="url(#aire)" />
      <path d={ligne} fill="none" stroke="var(--accent)" strokeWidth="2.5" />
      <text x={G} y={H - 4} className="graduation">{serie[0]?.jour.split("-").reverse().slice(0, 2).join("/")}</text>
      <text x={L - 8} y={H - 4} textAnchor="end" className="graduation">{serie[serie.length - 1]?.jour.split("-").reverse().slice(0, 2).join("/")}</text>
    </svg>
  );
}

function Tache({ ton, icone, titre, detail, lien }: { ton: string; icone: string; titre: string; detail?: string; lien?: string }) {
  const corps = <><span className={`pt ${ton}`} aria-hidden="true">{icone}</span>
    <span><span className="t">{titre}</span>{detail && <span className="s">{detail}</span>}</span></>;
  return <li>{lien ? <a href={lien}>{corps}</a> : <div>{corps}</div>}</li>;
}

export function TableauVue() {
  const [tb, setTb] = useState<Tableau | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);
  useEffect(() => { lireTableau().then(setTb).catch((x) => setErreur((x as Error).message)); }, []);
  if (erreur) return <p role="alert" className="alerte">{t(`erreur.${erreur}`)}</p>;
  if (!tb) return null;
  const d = tb.devise ?? "EUR";
  const c = tb.devise ? tb.par_devise[tb.devise] : null;
  const af = tb.a_faire;
  const autres = Object.keys(tb.par_devise).filter((x) => x !== tb.devise);
  const variation = c?.variation_ventes;
  return (
    <div className="vue">
      <h1>{t("tb.titre")}</h1>
      <div className="kpis quatre">
        <div className="kpi"><span className="kpi-l">{t("tb.ventes")}</span><span className="kpi-v">{m(c?.ventes, d)}</span>
          <span className={`kpi-s ${variation === null || variation === undefined ? "" : variation >= 0 ? "positif" : "negatif"}`}>
            {variation === null || variation === undefined ? t("tb.sans_comparaison") : `${variation >= 0 ? "▲" : "▼"} ${p(Math.abs(variation))} ${t("tb.vs_avant")}`}</span></div>
        <div className="kpi"><span className="kpi-l">{t("tb.profit")}</span><span className={`kpi-v ${c && c.profit < 0 ? "negatif" : ""}`}>{m(c?.profit, d)}</span>
          <span className="kpi-s">{tb.ventes_non_rattachees ? t("tb.non_rattachees", { n: tb.ventes_non_rattachees }) : t("tb.ventes_rattachees")}</span></div>
        <div className="kpi"><span className="kpi-l">{t("tb.roi")}</span><span className="kpi-v">{p(c?.roi)}</span>
          <span className="kpi-s">{t("tb.trente_jours")}</span></div>
        <div className="kpi"><span className="kpi-l">{t("tb.stock")}</span><span className="kpi-v">{m(c?.stock, d)}</span>
          <span className="kpi-s">{tb.unites_sans_cout ? t("tb.sans_cout", { n: tb.unites_sans_cout }) : t("tb.valeur_achat")}</span></div>
      </div>
      {autres.length > 0 && <p className="meta">{autres.map((x) => `${x} : ${m(tb.par_devise[x].ventes, x)} · ${m(tb.par_devise[x].profit, x)}`).join(" — ")}</p>}
      <div className="grille deux-un">
        <section className="carte"><h3>{t("tb.profit_jour")} <span className="meta">{t("tb.trente_jours")}</span></h3>
          {tb.serie.length ? <Courbe serie={tb.serie} devise={d} /> : <p className="meta">{t("tb.aucune_vente")}</p>}</section>
        <section className="carte"><h3>{t("tb.a_faire")}</h3>
          <ul className="taches">
            {af.recommander > 0 && <Tache ton="r" icone="!" titre={t("tb.recommander", { n: af.recommander })} lien="#stock" />}
            {af.remboursements > 0 && <Tache ton="a" icone="€" titre={t("tb.remboursements", { n: af.remboursements })}
              detail={Object.entries(af.valeur_remboursements).map(([dv, v]) => m(v, dv)).join(" · ")} lien="#remboursements" />}
            {af.conformite > 0 && <Tache ton="b" icone="⚑" titre={t("tb.conformite", { n: af.conformite })} lien="#conformite" />}
            {af.synchro === null ? <Tache ton="n" icone="…" titre={t("tb.synchro_jamais")} lien="#parametres" />
              : af.synchro.echecs.length ? <Tache ton="r" icone="×" titre={t("tb.synchro_echec")}
                detail={af.synchro.echecs.map((x) => t(`synchro.${x}`)).join(", ")} lien="#parametres" />
              : <Tache ton="v" icone="✓" titre={t("tb.synchro_ok")} detail={new Date(af.synchro.le).toLocaleString("fr-FR", { dateStyle: "short", timeStyle: "short" })} />}
          </ul></section>
      </div>
      <section className="carte"><h3>{t("tb.mouvements")} <span className="meta">{t("tb.sept_jours")}</span></h3>
        {tb.mouvements.length === 0 ? <p className="meta">{t("tb.mouvements_vide")} <a href="#marche">{t("nav.marche")}</a></p> : (
          <div className="defile"><table>
            <thead><tr><th scope="col">{t("sm.produit")}</th><th scope="col" className="num">{t("sm.prix")}</th>
              <th scope="col" className="num">{t("tb.variation")}</th><th scope="col" className="num">{t("sm.bsr")}</th></tr></thead>
            <tbody>{tb.mouvements.map((x) => (
              <tr key={x.asin}><td><a href="#marche" className="produit">{x.titre ?? x.asin}</a><div className="meta">{x.asin}</div></td>
                <td className="num">{m(x.prix, "EUR")}</td>
                <td className="num"><span className={`pastille ${x.variation >= 0 ? "positif" : "negatif"}`}>
                  {new Intl.NumberFormat("fr-FR", { style: "percent", maximumFractionDigits: 1, signDisplay: "exceptZero" }).format(x.variation)}</span></td>
                <td className="num">{x.bsr?.toLocaleString("fr-FR") ?? "—"}</td></tr>))}</tbody>
          </table></div>)}
      </section>
    </div>
  );
}

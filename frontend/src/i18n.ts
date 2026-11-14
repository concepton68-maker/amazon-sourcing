// D-AMZ-010 : aucun texte en dur. Ajouter une langue = ajouter un fichier JSON et l'enregistrer ici.
import fr from "./i18n/fr.json";

const langues: Record<string, Record<string, string>> = { fr };
export const langue = "fr";
const locale = "fr-FR";

export function t(cle: string, params: Record<string, string | number> = {}): string {
  const brut = langues[langue][cle] ?? cle;
  return brut.replace(/\{(\w+)\}/g, (_, k) => String(params[k] ?? `{${k}}`));
}

export function monnaie(valeur: string | null, devise: string, signe = false): string {
  if (valeur === null) return "—";
  return new Intl.NumberFormat(locale, {
    style: "currency", currency: devise, signDisplay: signe ? "exceptZero" : "auto",
  }).format(Number(valeur));
}

export function pourcent(valeur: string | null): string {
  if (valeur === null) return "—";
  return new Intl.NumberFormat(locale, { style: "percent", maximumFractionDigits: 0 }).format(Number(valeur));
}

export function dateCourte(iso: string): string {
  return new Intl.DateTimeFormat(locale, { day: "2-digit", month: "2-digit", year: "numeric" }).format(new Date(iso));
}

// Messages codés [RM-AMZ-027] : les paramètres sont formatés selon leur nature.
const POURCENTS = new Set(["roi", "seuil", "taux", "pct", "amplitude", "part"]);
const MONTANTS = new Set(["profit", "montant", "prix", "moyenne", "minimum"]);

export interface Msg { code: string; params: Record<string, string | number | null> }

export function message(msg: Msg, devise: string): string {
  const p: Record<string, string> = {};
  for (const [k, v] of Object.entries(msg.params)) {
    if (v === null) p[k] = "—";
    else if (POURCENTS.has(k)) p[k] = pourcent(String(v));
    else if (MONTANTS.has(k)) p[k] = monnaie(String(v), devise);
    else if (typeof v === "number") p[k] = new Intl.NumberFormat(locale).format(v);
    else p[k] = String(v);
  }
  return t(`msg.${msg.code}`, p);
}

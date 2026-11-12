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

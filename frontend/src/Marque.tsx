import { useEffect, useState } from "react";
import { MARQUE } from "./marque";
import { t } from "./i18n";

// Mot-symbole (D-AMZ-031) : le texte suit la couleur courante, le repère reste orange.
export function Marque() {
  const r = MARQUE.repere;
  return (
    <svg viewBox={MARQUE.viewBox} role="img" aria-label={t("app.nom")}>
      <path d={MARQUE.chemin} fill="currentColor" />
      <rect x={r.x} y={r.y} width={r.cote} height={r.cote} fill={MARQUE.orange} />
    </svg>
  );
}

// Bascule jour / nuit / auto (D-AMZ-032) : choix gardé dans ce navigateur ; « auto » suit l'ordinateur.
type Theme = "light" | "dark" | "auto";
const CLE = "syllig-pilot-theme";
export function lireTheme(): Theme {
  try { const v = localStorage.getItem(CLE); return v === "light" || v === "dark" ? v : "auto"; } catch { return "auto"; }
}
export function appliquerTheme(v: Theme) {
  if (v === "auto") document.documentElement.removeAttribute("data-theme");
  else document.documentElement.setAttribute("data-theme", v);
}

export function BasculeTheme() {
  const [theme, setTheme] = useState<Theme>(lireTheme);
  useEffect(() => {
    appliquerTheme(theme);
    try { if (theme === "auto") localStorage.removeItem(CLE); else localStorage.setItem(CLE, theme); } catch { /* sans stockage : choix pour la session */ }
  }, [theme]);
  const bouton = (v: Theme, icone: JSX.Element) => (
    <button type="button" aria-pressed={theme === v} onClick={() => setTheme(v)} aria-label={t(`theme.${v}`)} title={t(`theme.${v}`)}>{icone}</button>
  );
  return (
    <div className="theme-bascule" role="group" aria-label={t("theme.titre")}>
      {bouton("light", <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><circle cx="12" cy="12" r="4.5" /><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" /></svg>)}
      {bouton("dark", <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z" /></svg>)}
      {bouton("auto", <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><circle cx="12" cy="12" r="8.5" /><path d="M12 3.5a8.5 8.5 0 0 1 0 17z" fill="currentColor" /></svg>)}
    </div>
  );
}

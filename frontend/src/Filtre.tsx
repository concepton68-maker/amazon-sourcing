import { useEffect, useRef, useState } from "react";
import { t } from "./i18n";

// Filtre à choix multiples en menu déroulant : tout cocher, tout décocher, recherche si la liste est longue.
export function FiltreMultiple({ libelle, options, changer }: {
  libelle: string; options: { code: string; libelle: string; coche: boolean }[]; changer: (codes: string[]) => void }) {
  const [ouvert, setOuvert] = useState(false);
  const [cherche, setCherche] = useState("");
  const boite = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!ouvert) return;
    const dehors = (e: MouseEvent) => { if (boite.current && !boite.current.contains(e.target as Node)) setOuvert(false); };
    const echap = (e: KeyboardEvent) => { if (e.key === "Escape") setOuvert(false); };
    document.addEventListener("mousedown", dehors);
    document.addEventListener("keydown", echap);
    return () => { document.removeEventListener("mousedown", dehors); document.removeEventListener("keydown", echap); };
  }, [ouvert]);
  const coches = options.filter((o) => o.coche).map((o) => o.code);
  const visibles = options.filter((o) => o.libelle.toLowerCase().includes(cherche.trim().toLowerCase()));
  const basculer = (code: string) => changer(coches.includes(code) ? coches.filter((c) => c !== code) : [...coches, code]);
  return (
    <div className="filtre" ref={boite}>
      <button type="button" className="filtre-bouton" aria-expanded={ouvert} onClick={() => setOuvert(!ouvert)}>
        {libelle}<span className="filtre-compte">{coches.length}/{options.length}</span><span aria-hidden="true">▾</span>
      </button>
      {ouvert && (
        <div className="filtre-panneau" role="group" aria-label={libelle}>
          <div className="filtre-tete">
            <button type="button" className="lien" onClick={() => changer(options.map((o) => o.code))}>{t("filtre.tout")}</button>
            <button type="button" className="lien" onClick={() => changer([])}>{t("filtre.aucun")}</button>
          </div>
          {options.length > 10 && <input type="search" className="filtre-cherche" placeholder={t("filtre.chercher")}
            aria-label={t("filtre.chercher")} value={cherche} onChange={(e) => setCherche(e.target.value)} />}
          <div className="filtre-liste">
            {visibles.map((o) => (
              <label key={o.code}><input type="checkbox" checked={o.coche} onChange={() => basculer(o.code)} />{o.libelle}</label>))}
          </div>
        </div>)}
    </div>
  );
}

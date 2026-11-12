export interface ResumeLot {
  id: string; designation: string | null; asin: string; marketplace: string; fournisseur: string | null;
  date_achat: string; devise: string; quantite: number; vendues: number; statut: string;
  roi_prevu: string | null; roi_reel: string | null; profit_prevu: string; profit_reel: string;
  ecart: string; a_encaisser: string;
}
export interface DetailLot extends ResumeLot {
  profit_prevu_lot_entier: string;
  comparatif: { poste: string; prevu: string; reel: string | null; ecart: string | null }[];
  causes: { cause: string; montant: string }[];
  sources: string[]; version: number;
}

async function lire<T>(url: string): Promise<T> {
  const r = await fetch(url);
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail ?? "erreur.chargement");
  return r.json();
}

export const listerLots = () => lire<{ lots: ResumeLot[]; ventes_non_rattachees: number; demo: boolean }>("/api/lots");
export const detailLot = (id: string) => lire<DetailLot>(`/api/lots/${encodeURIComponent(id)}`);

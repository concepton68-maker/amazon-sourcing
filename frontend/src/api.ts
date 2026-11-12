import type { Msg } from "./i18n";

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

export interface Place { code: string; domaine: string; devise: string }
export interface Analyse {
  jeton_analyse: string; asin: string; marketplace: string; devise: string;
  titre: string | null; marque: string | null; categorie: string | null; bsr: number | null; unites_lot: number | null;
  verdict: "ACHETER" | "A_VERIFIER" | "PASSER"; origine_prix: string; prix_vente: number | null;
  rentabilite: null | { prix_vente_ht: number; tva_collectee: number; cout_achat_net: number; frais_amazon: number;
    tva_frais: number; autres: number; profit: number; roi: number | null; marge: number | null;
    prix_achat_max: number | null; roi_cible: number; regime_tva: string; hypotheses: Msg[] };
  frais_source: string | null;
  prudent: null | { prix_vente: number; profit: number; roi: number | null };
  offres: null | { nb_fba: number | null; nb_fbm: number | null; amazon_vend: boolean | null; buybox_amazon: boolean | null };
  historique: null | { prix_moy90: number | null; prix_min90: number | null; prix_max90: number | null;
    ventes_mois: number | null; chutes_bsr_30j: number | null; bsr_moy90: number | null; amazon_en_stock: number | null };
  ventes_pour_vous: number | null; autorise: boolean | null;
  raisons: Msg[]; alertes: Msg[]; non_verifie: Msg[];
}
export interface DemandeAnalyse {
  code: string; marketplace: string; prix_achat: number; achat_ttc: boolean; regime_tva: string; taux_tva: number | null;
}

async function envoyer<T>(url: string, corps: unknown): Promise<T> {
  const r = await fetch(url, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(corps) });
  if (!r.ok) {
    const d = (await r.json().catch(() => ({}))).detail;
    throw new Error(typeof d === "string" ? d : "saisie");
  }
  return r.json();
}

export const listerPlaces = () => lire<Place[]>("/api/places");
export const analyser = (d: DemandeAnalyse) => envoyer<{ analyses: Analyse[] }>("/api/analyse", d);
export const creerLot = (jeton_analyse: string, quantite: number, fournisseur: string) =>
  envoyer<{ id: string }>("/api/lots", { jeton_analyse, quantite, fournisseur: fournisseur || null });

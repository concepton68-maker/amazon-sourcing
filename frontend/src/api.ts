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

// [RM-AMZ-040] en-tête exigé sur toute requête qui modifie
const ENTETE = { "x-syllig-vente": "1" };

export class NonConnecte extends Error {}

async function lire<T>(url: string): Promise<T> {
  const r = await fetch(url, { credentials: "same-origin" });
  if (r.status === 401) throw new NonConnecte("NON_CONNECTE");
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
  const r = await fetch(url, { method: "POST", credentials: "same-origin",
    headers: { "content-type": "application/json", ...ENTETE }, body: JSON.stringify(corps) });
  if (r.status === 401 && !url.endsWith("/api/session")) throw new NonConnecte("NON_CONNECTE");
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

export type Colonnes = Record<string, number | null>;
export interface Fichier { fichier_id: string; nom: string; entetes: string[]; apercu: string[][]; nb_lignes: number; colonnes: Colonnes }
export interface LigneResultat {
  ligne: number; code: string; designation: string | null; asin: string | null; titre: string | null;
  prix_unitaire: number; unites_lot: number; cout_achat: number | null; verdict: string | null; statut: string;
  prix_vente: number | null; profit: number | null; roi: number | null; ventes_mois: number | null;
  remarques: Msg[]; raisons: Msg[]; alertes: Msg[];
}
export interface Suivi {
  statut: string; total: number; faits: number; marketplace: string; devise: string;
  compteurs: Record<string, number>; resultats: LigneResultat[];
  rejets: { ligne: number; message: Msg }[]; doublons: { ligne: number; code: string }[];
}

export async function deposerFichier(f: File): Promise<Fichier> {
  const corps = new FormData();
  corps.append("fichier", f);
  const r = await fetch("/api/sourcing/fichiers", { method: "POST", body: corps, headers: ENTETE, credentials: "same-origin" });
  if (r.status === 401) throw new NonConnecte("NON_CONNECTE");
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail ?? "chargement");
  return r.json();
}
export const lancerTraitement = (fid: string, d: { colonnes: Colonnes; marketplace: string; regime_tva: string;
  achat_ttc: boolean; prix_par_carton: boolean }) =>
  envoyer<{ traitement_id: string }>(`/api/sourcing/fichiers/${encodeURIComponent(fid)}/traitements`, d);
export const suivreTraitement = (tid: string) => lire<Suivi>(`/api/sourcing/traitements/${encodeURIComponent(tid)}`);
export const urlExport = (tid: string) => `/api/sourcing/traitements/${encodeURIComponent(tid)}/export.csv`;

export const moi = () => lire<{ compte_id: string; demo: boolean; connexion: boolean }>("/api/moi");
export const connecter = (courriel: string, mot_de_passe: string) =>
  envoyer<{ ok: boolean }>("/api/session", { courriel, mot_de_passe });
export const deconnecter = () =>
  fetch("/api/session", { method: "DELETE", headers: ENTETE, credentials: "same-origin" });

export interface Params {
  roi_min: number; profit_min: number; ventes_mois_min: number; part_ventes_min: number; ecart_prix_max: number;
  envoi: number; preparation: number; stockage: number; retours: number; tva: Record<string, string>; versions: number;
}
export const lireParametres = () => lire<Params>("/api/parametres");
export async function ecrireParametres(p: Omit<Params, "versions">): Promise<Params> {
  const r = await fetch("/api/parametres", { method: "PUT", credentials: "same-origin",
    headers: { "content-type": "application/json", ...ENTETE }, body: JSON.stringify(p) });
  if (r.status === 401) throw new NonConnecte("NON_CONNECTE");
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(typeof j.detail === "object" ? `${j.detail.code}|${j.detail.champ}` : "saisie");
  return j;
}

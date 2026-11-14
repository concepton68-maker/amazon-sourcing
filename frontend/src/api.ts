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
    prix_achat_max: number | null; roi_cible: number; regime_tva: string; hypotheses: Msg[]; detail: Record<string, number> };
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
  port_fournisseur?: number | null;
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
  envoyer<{ ok: boolean; etape: string }>("/api/session", { courriel, mot_de_passe });
export const deconnecter = () =>
  fetch("/api/session", { method: "DELETE", headers: ENTETE, credentials: "same-origin" });

export interface Params {
  roi_min: number; profit_min: number; ventes_mois_min: number; part_ventes_min: number; ecart_prix_max: number;
  envoi: number; preparation: number; stockage: number; retours: number; tva: Record<string, string>; versions: number;
  port_fournisseur: number; placement: number; duree_stock_mois: number; carburant_inclus: number;
  delai_fournisseur: number; delai_reception: number; marge_securite: number; seuil_rupture: number; seuil_surstock: number;
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

export interface LigneStock {
  marketplace: string; sku: string; asin: string | null; designation: string | null; disponible: number; en_route: number;
  reserve: number; invendable: number; vendus_30j: number; vitesse: number; couverture: number | null;
  rupture_le: string | null; a_commander: number; fournisseur: string | null; cout_unitaire: number | null;
  devise: string; alertes: Msg[];
}
export interface Stock {
  jour: string | null; lignes: LigneStock[];
  commandes: { fournisseur: string | null; lignes: number; unites: number; montant: number | null; devise: string }[];
  compteurs: { unites: number; ruptures: number; surstocks: number };
}
export const lireStock = () => lire<Stock>("/api/stock");

export interface FournisseurBilan {
  id: string; nom: string; devise: string; delai_jours: number; courriel: string | null; lots: number;
  achete_12_mois: number; roi_prevu: number | null; roi_reel: number | null; delai_reel_jours: number | null;
}
export interface LigneBonApi {
  id: string; asin: string; marketplace: string; designation: string | null; quantite: number; prix_unitaire: number;
  montant: number; roi_prevu: number | null; quantite_recue: number | null; lot_id: string | null;
}
export interface Bon {
  id: string; reference: string; statut: string; fournisseur: { id: string; nom: string; devise: string } | null;
  devise: string | null; montant: number; roi_prevu: number | null; cree_le: string; envoye_le: string | null;
  recu_le: string | null; lignes: LigneBonApi[];
}
export const listerFournisseurs = () => lire<FournisseurBilan[]>("/api/fournisseurs");
export const creerFournisseur = (nom: string, delai_jours: number) => envoyer<{ id: string }>("/api/fournisseurs", { nom, delai_jours });
export const listerBons = () => lire<Bon[]>("/api/bons");
export const creerBon = (fournisseur_id: string) => envoyer<Bon>("/api/bons", { fournisseur_id });
export const ajouterLigneBon = (id: string, asin: string, marketplace: string, quantite: number) =>
  envoyer<Bon>(`/api/bons/${id}/lignes`, { asin, marketplace, quantite });
export const actionBon = (id: string, action: "envoyer" | "annuler") => envoyer<Bon>(`/api/bons/${id}/${action}`, {});
export const recevoirBon = (id: string, quantites: Record<string, number>) =>
  envoyer<Bon & { lots_crees: string[] }>(`/api/bons/${id}/recevoir`, { quantites });
export const bonDepuisStock = (fournisseur: string) => envoyer<Bon>("/api/bons/depuis-stock", { fournisseur });
export async function retirerLigneBon(id: string, ligne: string): Promise<Bon> {
  const r = await fetch(`/api/bons/${id}/lignes/${ligne}`, { method: "DELETE", headers: ENTETE, credentials: "same-origin" });
  if (r.status === 401) throw new NonConnecte("NON_CONNECTE");
  const j = await r.json();
  if (!r.ok) throw new Error(j.detail ?? "saisie");
  return j;
}

export interface CasRemb {
  cle: string; type: string; marketplace: string; asin: string | null; sku: string | null; fnsku: string | null;
  commande: string | null; unites: number | null; valeur_achat: number | null; devise: string; detecte_le: string;
  echeance: string | null; statut: string; case_id: string | null; montant_verse: number | null; faits: Record<string, string | number>;
}
export interface Remboursements {
  cas: CasRemb[]; source_delais: string;
  compteurs: { a_verifier: number; en_cours: number; verses_12_mois: { devise: string; montant: number }[]; nb_verses_12_mois: number };
}
export const lireRemboursements = () => lire<Remboursements>("/api/remboursements");
export const suivreCas = (cle: string, statut: string, case_id?: string) =>
  envoyer<CasRemb>(`/api/remboursements/${encodeURIComponent(cle)}/suivi`, { statut, case_id: case_id ?? null });

// ------------------------------------------------------------ conformité [RM-AMZ-060 à 067]
export interface Coordonnees { nom: string | null; adresse: string | null; courriel: string | null }
export interface FicheConf {
  asin: string; fabricant: Coordonnees; fabricant_hors_ue: boolean | null; responsable: Coordonnees;
  avertissements_ok: boolean; producteur: string; filieres: string[]; intitule_autre: string | null;
  numeros_producteur: Record<string, string>; triman_ok: boolean; marquage_ce: string;
}
export interface ProduitConf { asin: string; designation: string | null; places: string[]; statut: string; alertes: Msg[]; fiche: FicheConf }
export interface EnregConf {
  cle: string; pays: string; filiere: string; numero: string; intitule: string | null; mandataire: string | null;
  texte: string | null; avertissements: Msg[];
}
export interface TexteConf { code: string; reference: string; url: string; verifie: boolean; note: string }
export interface Conformite {
  produits: ProduitConf[]; enregistrements: EnregConf[]; textes: TexteConf[]; date_lecture: string;
  places_ue: string[]; filieres: string[];
  compteurs: { a_completer: number; rien_de_signale: number; non_couverts: number };
}

async function requete<T>(methode: string, url: string, corps?: unknown): Promise<T> {
  const r = await fetch(url, { method: methode, credentials: "same-origin",
    headers: { "content-type": "application/json", ...ENTETE }, body: corps === undefined ? undefined : JSON.stringify(corps) });
  if (r.status === 401) throw new NonConnecte("NON_CONNECTE");
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(typeof j.detail === "object" && j.detail ? j.detail.code : (j.detail ?? "saisie"));
  return j;
}

export const lireConformite = () => lire<Conformite>("/api/conformite");
export const ajouterEnregistrement = (e: { pays: string; filiere: string; numero: string; intitule?: string; mandataire?: string }) =>
  requete<EnregConf>("POST", "/api/conformite/enregistrements", e);
export const supprimerEnregistrement = (cle: string) =>
  requete<{ supprime: string }>("DELETE", `/api/conformite/enregistrements/${encodeURIComponent(cle)}`);
export const ecrireFiche = (f: FicheConf) => {
  const { asin, ...corps } = f;
  return requete<FicheConf>("PUT", `/api/conformite/fiches/${encodeURIComponent(asin)}`, corps);
};

// ------------------------------------------------------------ connexions [RM-AMZ-072 à 074]
export interface SourceConnexion { source: string; champs: string[]; enregistree_le: string | null }
export interface Connexions { chiffrement: boolean; sources: SourceConnexion[]; regions: string[] }
export const lireConnexions = () => lire<Connexions>("/api/connexions");
export const ecrireConnexion = (source: string, valeurs: Record<string, string>) =>
  requete<{ enregistree: boolean }>("PUT", `/api/connexions/${source}`, valeurs);
export const retirerConnexion = (source: string) => requete<{ retiree: boolean }>("DELETE", `/api/connexions/${source}`);

// ------------------------------------------------------------ double authentification [RM-AMZ-075, 076]
export async function etapeSession(): Promise<string | null> {
  const r = await fetch("/api/session/etape", { credentials: "same-origin" });
  return r.ok ? (await r.json()).etape : null;
}
async function etapeAuth<T>(url: string, corps: unknown): Promise<T> {
  const r = await fetch(url, { method: "POST", credentials: "same-origin",
    headers: { "content-type": "application/json", ...ENTETE }, body: JSON.stringify(corps) });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(typeof j.detail === "string" ? j.detail : "saisie");
  return j;
}
export const changerMotDePasse = (nouveau: string) => etapeAuth<{ etape: string }>("/api/session/mot-de-passe", { nouveau });
export const debuterEnrolement = () => etapeAuth<{ secret: string; uri: string; qr: string }>("/api/session/enrolement", {});
export const confirmerEnrolement = (code: string) =>
  etapeAuth<{ etape: string; codes_secours: string[] }>("/api/session/enrolement/confirmer", { code });
export const envoyerCode = (code: string) => etapeAuth<{ etape: string }>("/api/session/code", { code });
export interface EtapeTest { etape: string; ok: boolean | null; statut: number | null; message: string; requete: string | null }
export const testerConnexion = (marketplace: string) =>
  requete<{ marketplace: string; etapes: EtapeTest[] }>("POST", "/api/connexions/SPAPI/test", { marketplace });
export interface TacheSynchro { tache: string; le: string; ok: boolean; message: string }
export const lireJournalSynchro = () => lire<TacheSynchro[]>("/api/synchro/journal");

// ------------------------------------------------------------ ce que je peux vendre [RM-AMZ-084, 085]
export interface ProduitSonde { asin: string; titre: string | null; bsr: number | null; categorie: string | null; statut: string }
export interface RayonSonde { code: string; statut: string; testes: number; autorises: number; approbation: number; interdits: number;
  inconnus: number; erreur: string | null; produits: ProduitSonde[] }
export interface Exploration { en_cours: boolean; progression: [number, number] | null;
  resultat: { place: string; le: string; rayons: RayonSonde[] } | null }
export const lireExploration = () => lire<Exploration>("/api/exploration");
export const lancerExploration = () => requete<{ lancee: boolean }>("POST", "/api/exploration", {});

// Historique et suivi de marché [RM-AMZ-086 à 090]
export interface Tendance { jours: number; releves: number; court: boolean; prix_dernier: number | null; prix_moyen: number | null;
  prix_min: number | null; prix_max: number | null; prix_variation: number | null; bsr_moyen: number | null;
  bsr_dernier: number | null; jours_baisse_bsr: number | null; part_amazon_vend: number | null;
  part_buybox_amazon: number | null; vendeurs_moyen: number | null }
export interface LigneMarche { asin: string; titre: string | null; marque: string | null; famille: string | null;
  dernier: string | null; prix: number | null; bsr: number | null; vendeurs: number | null; amazon_vend: boolean | null;
  tendance: Tendance }
export interface Marche { groupe: string; marketplace: string; familles: { code: string; suivie: boolean }[];
  suivis: number; produits: LigneMarche[] }
export interface HistoriqueProduit { asin: string; marketplace: string; titre: string | null; suivi: boolean;
  releves: { jour: string; prix: number | null; bsr: number | null; vendeurs: number | null; amazon_vend: boolean | null;
    buybox_amazon: boolean | null }[];
  tendances: Record<string, Tendance> }
export const lireMarche = (groupe: string) => lire<Marche>(`/api/marche?groupe=${encodeURIComponent(groupe)}`);
export const choisirFamilles = (familles: string[]) => requete<{ familles: string[] }>("PUT", "/api/marche/familles", { familles });
export const suivreProduit = (asin: string, marketplace: string) =>
  requete<{ suivi: boolean }>("POST", "/api/marche/suivi", { asin, marketplace });
export const neplusSuivre = (asin: string, marketplace: string) =>
  requete<{ suivi: boolean }>("DELETE", `/api/marche/suivi/${encodeURIComponent(marketplace)}/${encodeURIComponent(asin)}`);
export const historiqueProduit = (asin: string, marketplace: string) =>
  lire<HistoriqueProduit>(`/api/marche/produit/${encodeURIComponent(marketplace)}/${encodeURIComponent(asin)}`);

// Tableau de bord [RM-AMZ-091 à 094]
export interface ChiffresDevise { ventes: number; profit: number; stock: number; variation_ventes: number | null; roi: number | null }
export interface Tableau { devise: string | null; par_devise: Record<string, ChiffresDevise>;
  serie: { jour: string; profit: number }[]; ventes_non_rattachees: number; unites_sans_cout: number;
  a_faire: { recommander: number; remboursements: number; valeur_remboursements: Record<string, number>; conformite: number;
    synchro: { le: string; echecs: string[] } | null };
  mouvements: { asin: string; titre: string | null; variation: number; prix: number | null; bsr: number | null }[] }
export const lireTableau = () => lire<Tableau>("/api/tableau");

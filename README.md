# Outil de sourcing Amazon — étape 1 : analyse d'un produit

Analyse un produit (ASIN, EAN, UPC ou ISBN) sur **toutes les places de marché Amazon**
et donne un verdict expliqué : **ACHETER / À VÉRIFIER / PASSER**.

Ce que l'outil calcule ou vérifie :
- profit net, ROI, marge, avec la TVA selon votre régime (assujetti, non assujetti, hors taxe US/CA) ;
- **prix d'achat maximum** pour atteindre votre ROI cible (utile pour négocier) ;
- **scénario prudent** au prix moyen sur 90 jours (évite d'acheter sur un pic de prix) ;
- autorisation de vendre sur VOTRE compte (restrictions, approbation de marque) ;
- Buy Box, nombre de vendeurs FBA/FBM, présence d'Amazon ;
- historique 90 jours (prix, BSR, chutes de BSR), ventes mensuelles estimées et part estimée pour vous ;
- alertes : lots, prix instable, Amazon en stock, pic de prix.

L'outil **n'invente jamais** une donnée manquante : il la classe en « Non vérifié »
et ne donne jamais « ACHETER » dans ce cas.

## Essai immédiat (données fictives)

```bash
python -m sourcing analyse 3700000000017 --mp FR --achat 8.50 --demo
python -m sourcing comparer 3700000000017 --mp FR,DE,IT,ES,UK --achat 8.50 --demo
python -m sourcing places
```

## Utilisation réelle

```bash
pip install -r requirements.txt
cp .env.example .env   # puis remplir les clés
python -m sourcing analyse 3017620422003 --mp FR --achat 2.10 --achat-ttc
python -m sourcing analyse B0XXXXXXXX --mp DE --achat 12 --tva non_assujetti --envoi 0.40 --prep 0.20
python -m sourcing analyse 9782070612758 --mp FR --achat 4 --taux-tva 0.055   # livre : TVA réduite
python -m sourcing analyse B0XXXXXXXX --mp FR --achat 8 --json                # sortie machine
```

Options utiles : `--roi-min 0.35`, `--profit-min 4`, `--retours 0.03`, `--prix-vente 24.90`.

## Obtenir les accès

### 1. API Amazon (SP-API) — gratuite à ce jour, pour votre propre compte
1. Avoir un compte **Seller Central Professionnel**.
2. Seller Central → *Applications et services* → *Développer des applications* →
   s'inscrire comme **développeur privé** (« private developer », données de votre seul compte).
   Rôles à demander : *Product Listing*, *Pricing*, *Inventory and Order Tracking* (pas de rôle donnant accès aux données personnelles clients).
3. Créer une application (type *SP-API*), puis **Autoriser** l'application sur votre compte :
   on obtient un *refresh token* (un par région : Europe, Amérique du Nord, Extrême-Orient).
4. Récupérer *Client ID* et *Client Secret* (identifiants LWA) et votre *Merchant Token* (= `SPAPI_SELLER_ID`,
   visible dans Paramètres → Informations sur le compte → Informations sur le vendeur).

### 2. API Keepa — payante
Sur keepa.com → *API* : abonnement en jetons/minute (≈ 49 €/mois pour 20 jetons/min selon des sources tierces,
à vérifier). Une analyse de produit consomme en général 1 jeton.
Keepa ne couvre pas toutes les places de marché (voir `python -m sourcing places`) : sur NL, BE, PL, SE…
l'outil fonctionne avec SP-API seule, sans historique.

## Limites connues (à lire)
- Les clients SP-API et Keepa sont écrits d'après la documentation officielle et testés sur des réponses types,
  **pas encore sur vos vrais comptes**. Le premier essai réel servira à les valider.
- Frais : on suppose que les frais renvoyés par SP-API sont **hors TVA**. À contrôler une fois
  contre un relevé de paiement Seller Central.
- Les taux de TVA sont les taux standard ; utilisez `--taux-tva` pour les taux réduits.
- Pas de conversion de devises dans `comparer` (prix d'achat supposé dans la devise de chaque place).
- Ventes estimées = estimation (badge Amazon « achetés le mois dernier » via Keepa) ; la part « pour vous »
  suppose un partage égal entre vendeurs FBA.
- Les frais de stockage, d'entrée en entrepôt (inbound placement) et de faible stock ne sont pas encore inclus
  (option `--prep`/`--envoi` pour les approcher).

## Feuille de route
1. ✅ Analyse d'un produit, toutes places de marché.
2. Analyse en masse de fichiers fournisseurs (Excel/CSV), appariement EAN→ASIN assisté par Claude, export trié.
3. Interface web et/ou extension Chrome.
4. Version commerciale (multi-utilisateurs) — après vérification des règles Amazon (AUP 4.3/4.4) et des conditions Keepa.

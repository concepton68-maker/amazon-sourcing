# Guide : brancher votre messagerie Microsoft sur Syllig Pilot (10 minutes, une seule fois)

But : envoyer les bons de commande depuis votre propre boîte (ils restent dans vos « Éléments envoyés »).
Droit donné : **envoyer seulement**. Syllig Pilot ne lit jamais votre boîte (RM-AMZ-129).
Ne collez **jamais** de clé dans le chat : uniquement dans le site.

On réutilise l'application « Syllig » déjà enregistrée chez Microsoft pour la suite Syllig (24/10/2026).

## 1. Ajouter l'adresse de retour de Syllig Pilot
1. https://entra.microsoft.com › Identité › Applications › **Inscriptions d'applications** › **Syllig**.
2. Menu **Authentification** › plateforme **Web** › **Ajouter un URI**.
3. Collez l'adresse affichée dans Syllig Pilot (Paramètres › Connexions › Ma messagerie › « Copier »), normalement
   `https://vente.concepton.fr/api/messagerie/microsoft/retour`, puis **Enregistrer**.
   L'adresse de Syllig (compte.syllig.com) reste en place : les deux coexistent.

## 2. Créer une clé pour Syllig Pilot
1. Même application › **Certificats et secrets** › **Nouveau secret client**, description `Syllig Pilot`, 24 mois.
2. Copiez tout de suite la colonne **« Valeur »** (elle ne se réaffiche plus).
3. Notez la date d'expiration (à renouveler avant).

## 3. Coller dans Syllig Pilot
1. Paramètres › Connexions › **Application Microsoft (messagerie)** :
   - « ID d'application (client) » : l'identifiant de l'application Syllig (page « Vue d'ensemble ») ;
   - « Valeur du secret client » : la valeur copiée à l'étape 2.
2. **Enregistrer** (chiffré, jamais réaffiché).

## 4. Connecter votre boîte
1. Toujours dans Connexions › Ma messagerie : **Connecter ma messagerie Microsoft**.
2. Choisissez votre compte, acceptez (droit : envoyer des courriels).
3. Retour sur Syllig Pilot : « Messagerie connectée » et votre adresse.

## 5. Premier essai
Mettez **votre propre adresse** comme courriel d'un fournisseur de test, ouvrez un bon, « Envoyer par ma messagerie ».
Le courriel doit arriver avec le PDF du bon, et se trouver dans vos éléments envoyés.

## En cas de blocage
Notez le message affiché (ou une capture) et envoyez-le-moi. Causes connues : adresse de retour non déclarée
(« échange refusé »), clé copiée depuis « ID du secret » au lieu de « Valeur », compte d'entreprise qui exige
l'accord d'un administrateur.

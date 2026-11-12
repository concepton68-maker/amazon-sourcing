# Plan de réponse aux incidents de sécurité — Syllig Vente (GO-SHOPPING)

Version 1 du 13/11/2026 · [RM-AMZ-078] · **revue tous les 6 mois** (prochaines : 13/05/2027, 13/11/2027) et après chaque incident.

## 1. Champ

Tout événement qui menace la confidentialité, l'intégrité ou la disponibilité des **informations Amazon** (données obtenues par
l'API Selling Partner, identifiants de l'application) ou du serveur qui les héberge (`vente.concepton.fr`, VPS OVHcloud).

## 2. Rôles

| Rôle | Qui | Tâches |
|---|---|---|
| Responsable des incidents | Le dirigeant de GO-SHOPPING (seul utilisateur de l'application) | Décide, alerte Amazon et les autorités, joignable 24 h sur 24 par téléphone |
| Intervention technique | Le dirigeant, assisté de l'assistant de développement (dépôt GitHub privé) | Confinement, correction, retour à une version saine |
| Hébergeur | OVHcloud (support, KVM, sauvegardes, réinstallation) | Isolement réseau, restauration du disque |

## 3. Détection

- Journal du serveur `/var/log/syllig-vente-maj.log` : mises à jour, sauvegardes, purge, **antivirus** (hebdomadaire), sécurité.
- **fail2ban** : blocage des essais répétés sur SSH ; **pare-feu** : seules les entrées SSH, HTTP et HTTPS sont admises.
- Application : blocage après 5 échecs de connexion, double authentification obligatoire, sessions limitées (12 h d'inactivité, 30 jours).
- Alertes d'Amazon, d'OVHcloud ou de GitHub ; anomalie constatée par l'utilisateur.

## 4. Gravité

- **Incident confirmé** : accès non autorisé, fuite ou perte d'informations Amazon, identifiants exposés, logiciel malveillant.
- **Suspicion** : comportement anormal non expliqué. Une suspicion est traitée comme un incident jusqu'à preuve du contraire.

## 5. Procédure (dans l'ordre)

1. **Confiner** (dans l'heure) : retirer les identifiants SP-API dans Paramètres et **révoquer l'autorisation de l'application dans
   Seller Central** ; si le serveur est en cause, l'isoler (arrêt ou mode rescue OVHcloud) ; fermer toutes les sessions.
2. **Signaler à Amazon : courriel à security@amazon.com dans les 24 heures suivant la détection** de tout incident touchant des
   informations Amazon (nature, date, données concernées, mesures prises, contact). Le délai court même la nuit et le week-end.
3. **Autorités** : si des données personnelles sont concernées, notification à la CNIL dans les 72 heures (RGPD art. 33, **non relu
   dans cette session**).
4. **Éradiquer** : changer tous les secrets (mot de passe, double authentification, identifiants SP-API — nouveau secret client —,
   clé de chiffrement, mots de passe de la base), corriger la cause, réinstaller le serveur si nécessaire.
5. **Rétablir** depuis une version saine (dépôt GitHub) et une sauvegarde antérieure à l'incident (sauvegarde quotidienne 14 jours,
   sauvegarde OVHcloud 7 jours), puis vérifier.
6. **Tirer les leçons** dans les 7 jours : compte rendu daté ajouté à ce document (section 7), plan mis à jour.

## 6. Contacts

- Amazon : **security@amazon.com** (incidents) ; Seller Central (révocation de l'application).
- OVHcloud : espace client, support.
- CNIL : notification en ligne sur cnil.fr.

## 7. Registre des incidents et des revues

| Date | Événement | Suite |
|---|---|---|
| 13/11/2026 | Création du plan | Revue suivante le 13/05/2027 |

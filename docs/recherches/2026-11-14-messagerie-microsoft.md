# Envoi de courriels depuis la boîte Microsoft de l'utilisateur (Mail.Send) — recherche documentaire

**Date : 14/11/2026** (heure de Paris) · Sujet : une application web côté serveur (Python, client confidentiel) envoie un bon de commande en PDF à un fournisseur depuis la boîte Outlook / Microsoft 365 de l'utilisateur (comptes professionnels et personnels), avec le seul droit d'envoi.

## Règle de lecture

- **VÉRIFIÉ** : lu ce jour sur la page officielle citée (learn.microsoft.com), extrait recopié tel quel (en anglais).
- **VÉRIFIÉ (extrait)** : vu seulement dans un extrait de moteur de recherche, page non lue en entier.
- **NON VÉRIFIÉ** : non lu sur une page officielle ; à confirmer avant d'en faire une règle.
- **Analyse** : déduction de notre part à partir des faits vérifiés, pas une affirmation de Microsoft.

Pages lues (versions du 14/11/2026) :

| Réf. | Page |
| --- | --- |
| [P1] | https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-auth-code-flow |
| [P2] | https://learn.microsoft.com/en-us/entra/identity-platform/v2-protocols |
| [P3] | https://learn.microsoft.com/en-us/entra/identity-platform/refresh-tokens |
| [P4] | https://learn.microsoft.com/en-us/entra/identity-platform/access-tokens |
| [P5] | https://learn.microsoft.com/en-us/graph/permissions-reference |
| [P6] | https://learn.microsoft.com/en-us/entra/identity-platform/scopes-oidc |
| [P7] | https://learn.microsoft.com/en-us/graph/api/user-sendmail?view=graph-rest-1.0 |
| [P8] | https://learn.microsoft.com/en-us/graph/api/resources/message?view=graph-rest-1.0 |
| [P9] | https://learn.microsoft.com/en-us/graph/api/resources/fileattachment?view=graph-rest-1.0 |
| [P10] | https://learn.microsoft.com/en-us/graph/outlook-large-attachments |
| [P11] | https://learn.microsoft.com/en-us/graph/api/attachment-createuploadsession?view=graph-rest-1.0 |
| [P12] | https://learn.microsoft.com/en-us/graph/api/message-post-attachments?view=graph-rest-1.0 |
| [P13] | https://learn.microsoft.com/en-us/graph/api/user-post-messages?view=graph-rest-1.0 |
| [P14] | https://learn.microsoft.com/en-us/graph/api/message-send?view=graph-rest-1.0 |
| [P15] | https://learn.microsoft.com/en-us/graph/throttling |
| [P16] | https://learn.microsoft.com/en-us/graph/throttling-limits |
| [P17] | https://learn.microsoft.com/en-us/graph/outlook-things-to-know-about-send-mail |
| [P18] | https://learn.microsoft.com/en-us/graph/api/user-get?view=graph-rest-1.0 |
| [P19] | https://learn.microsoft.com/en-us/graph/api/resources/user?view=graph-rest-1.0 |
| [P20] | https://learn.microsoft.com/en-us/graph/tutorials/dotnet-authentication |
| [P21] | https://learn.microsoft.com/en-us/entra/identity-platform/reference-error-codes |
| [P22] | https://learn.microsoft.com/en-us/entra/identity-platform/permissions-consent-overview |
| [P23] | https://learn.microsoft.com/en-us/entra/identity-platform/reply-url |
| [P24] | https://learn.microsoft.com/en-us/entra/identity-platform/how-to-add-redirect-uri |

---

## 1. Flux d'autorisation par code avec PKCE (v2.0, `common`)

**Point de terminaison `common`** — VÉRIFIÉ [P2] : « The allowed values are **common** for both Microsoft accounts and work or school accounts, **organizations** for work or school accounts only, **consumers** for Microsoft accounts only ».

**URL d'autorisation et de jeton** — VÉRIFIÉ [P2] :
`https://login.microsoftonline.com/<issuer>/oauth2/v2.0/authorize` et `https://login.microsoftonline.com/<issuer>/oauth2/v2.0/token`.

**PKCE recommandé aussi pour un client confidentiel** — VÉRIFIÉ [P1] : « Use the auth code flow paired with Proof Key for Code Exchange (PKCE) … Standard (server-based) web application » ; `code_challenge` : « This parameter is now recommended for all application types, both public and confidential clients ».

**Exemple de requête d'autorisation** — VÉRIFIÉ [P1] :

```
https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize?
client_id=00001111-aaaa-2222-bbbb-3333cccc4444
&response_type=code
&redirect_uri=http%3A%2F%2Flocalhost%2Fmyapp%2F
&response_mode=query
&scope=https%3A%2F%2Fgraph.microsoft.com%2Fmail.read
&state=12345
&code_challenge=YTFjNjI1OWYzMzA3MTI4ZDY2Njg5M2RkNmVjNDE5YmEyZGRhOGYyM2IzNjdmZWFhMTQ1ODg3NDcxY2Nl
&code_challenge_method=S256
```

Paramètres — VÉRIFIÉ [P1] (extraits du tableau) :

| Paramètre | Extrait |
| --- | --- |
| `client_id` | « required » — « The **Application (client) ID** that the Microsoft Entra admin center – App registrations experience assigned to your app. » |
| `response_type` | « required » — « Must include `code` for the authorization code flow. » |
| `redirect_uri` | « required » — « It must exactly match one of the redirect URIs you registered in the Microsoft Entra admin center, except it must be URL-encoded. » |
| `scope` | « required » — « A space-separated list of scopes that you want the user to consent to. » |
| `response_mode` | « recommended » — `query` (« Default when requesting an access token »), `fragment`, `form_post` (« Executes a POST containing the code to your redirect URI »). |
| `state` | « recommended » — « A randomly generated unique value is typically used for preventing cross-site request forgery attacks. » ; « do not put URLs or other sensitive data directly in the state parameter ». |
| `prompt` | « optional » — « Valid values are `login`, `none`, `consent`, and `select_account`. » ; « `prompt=consent` triggers the OAuth consent dialog after the user signs in » ; « `prompt=select_account` … providing account selection experience ». |
| `code_challenge` | « Required if `code_challenge_method` is included. » |
| `code_challenge_method` | « This *SHOULD* be `S256` … The Microsoft identity platform supports both `plain` and `S256`. » |

Code d'autorisation — VÉRIFIÉ [P1] : « Authorization codes are short lived. Typically, they expire after about 1 minute. »

**Échange du code (secret + vérificateur)** — VÉRIFIÉ [P1] :

```
POST /{tenant}/oauth2/v2.0/token HTTP/1.1
Host: https://login.microsoftonline.com
Content-Type: application/x-www-form-urlencoded

client_id=…&scope=…&code=…&redirect_uri=…&grant_type=authorization_code
&code_verifier=ThisIsntRandomButItNeedsToBe43CharactersLong
&client_secret=sampleCredentia1s
```

- `redirect_uri` : « The same `redirect_uri` value that was used to acquire the `authorization_code`. »
- `code_verifier` : « Required if PKCE was used in the authorization code grant request. »
- `client_secret` : « required for confidential web apps » ; « the client secret must be URL-encoded before being sent » ; « The Basic auth pattern of instead providing credentials in the Authorization header, per RFC 6749 is also supported. »
- Recommandation : « For best security, we recommend using certificate credentials. »
- Réponse : `access_token`, `token_type` (« The only type that Microsoft Entra ID supports is `Bearer` »), `expires_in` (« How long the access token is valid, in seconds »), `refresh_token` (« **Note:** Only provided if `offline_access` scope was requested. »), `id_token` (« Only provided if `openid` scope was requested »). Exemple : `"expires_in": 3599`.

**Actualisation** — VÉRIFIÉ [P1] :

```
POST /{tenant}/oauth2/v2.0/token HTTP/1.1
client_id=…&scope=…&refresh_token=…&grant_type=refresh_token&client_secret=…
```

- `grant_type` : « Must be `refresh_token` for this leg of the authorization code flow. »
- `scope` : « The scopes requested in this leg must be equivalent to or a subset of the scopes requested in the original `authorization_code` request leg. »
- `client_secret` : « required for web apps ».

**Durées de vie**

- Jeton d'accès — VÉRIFIÉ [P4] : « The default lifetime of an access token is variable. When issued, the Microsoft identity platform assigns a random value ranging between 60-90 minutes (75 minutes on average) ». Ne pas lire le jeton : VÉRIFIÉ [P1] « Don't attempt to validate or read tokens for any API you don't own » ; [P4] « Clients should use the token response data that's returned with the access token ».
- Jeton d'actualisation — VÉRIFIÉ [P3] : « **90 days for** all other scenarios » (24 heures pour les applications monopage) ; « they can be revoked by the sign-in service at any time before their expiration ». VÉRIFIÉ [P1] : « Refresh tokens for web apps and native apps don't have specified lifetimes. Typically, the lifetimes of refresh tokens are relatively long. However, in some cases, refresh tokens expire, are revoked, or lack sufficient privileges for the action. »
- Analyse : les deux pages ne disent pas exactement la même chose (90 jours par défaut / « pas de durée spécifiée ») ; on traite donc la durée comme inconnue et on gère toujours l'échec d'actualisation par une reconnexion.

**Remplacement du jeton d'actualisation** — VÉRIFIÉ [P3] : « Refresh tokens replace themselves with a fresh token upon every use. The Microsoft identity platform doesn't revoke old refresh tokens when used to fetch new access tokens. Securely delete the old refresh token after acquiring a new one. » ; [P1] : « A new OAuth 2.0 refresh token. Replace the old refresh token with this newly acquired refresh token to ensure your refresh tokens remain valid for as long as possible. »

Analyse : à chaque actualisation, enregistrer le nouveau jeton (chiffré) et effacer l'ancien.

## 2. Portées

Toutes VÉRIFIÉ [P5] (tableaux « Delegated ») :

| Portée | DisplayText | Description | AdminConsentRequired |
| --- | --- | --- | --- |
| `Mail.Send` | « Send mail as a user » | « Allows the app to send mail as users in the organization. » | No |
| `User.Read` | « Sign in and read user profile » | « Allows users to sign-in to the app, and allows the app to read the profile of signed-in users. » | No |
| `offline_access` | « Maintain access to data you have given it access to » | « … This does not give the app any additional permissions. » | No |
| `openid` | « Sign users in » | « Allows users to sign in to the app with their work or school accounts and allows the app to see basic user profile information. » | No |
| `email` | « View users' email address » | « Allows the app to read your users' primary email address » | No |
| `profile` | « View users' basic profile » | « Allows the app to see your users' basic profile (e.g., name, picture, user name, email address) » | No |

- Comptes personnels — VÉRIFIÉ [P5] : « The *Mail.Send* delegated permission is available for consent in personal Microsoft accounts. » ; « *Mail.Send* is valid valid for both Microsoft accounts and work or school accounts. » (coquille d'origine). Même mention pour `User.Read`.
- Ce que `Mail.Send` permet — VÉRIFIÉ [P5] : « With the *Mail.Send* permission, an app can send mail and save a copy to the user's Sent Items folder, even if the app isn't granted the *Mail.ReadWrite* or *Mail.ReadWrite.Shared* permission. »
- Ce qu'il ne permet pas : la lecture relève d'autres portées. VÉRIFIÉ [P5] : les droits `Mail.ReadWrite` sont décrits « Does not include permission to send mail », ce qui montre que lecture/écriture et envoi sont des droits séparés. Analyse : aucun extrait ne dit en toutes lettres « Mail.Send ne permet pas de lire » ; la séparation se déduit des descriptions et des tableaux d'autorisations (§ 3 : créer un brouillon ou une pièce jointe exige `Mail.ReadWrite`).
- `offline_access` obligatoire pour un jeton d'actualisation — VÉRIFIÉ [P6] : « your app must explicitly request the `offline_access` scope, to receive refresh tokens ». [P5] : « you specify the *offline\_access* scope in the **scope** parameter to explicitly request a refresh token ».
- `openid email profile` — VÉRIFIÉ [P5] : « With OpenID Connect, you specify the *openid* scope to request an ID token. You can also specify the *email* scope, *profile* scope, or both to return additional claims in the ID token. »
- Une seule ressource par jeton — VÉRIFIÉ [P1] (échange du code) : « The scopes must all be from a single resource, along with OIDC scopes (`profile`, `openid`, `email`). »
- Analyse : chaîne de portées envisagée `openid email profile offline_access https://graph.microsoft.com/Mail.Send https://graph.microsoft.com/User.Read` (forme de l'URL calquée sur l'exemple `https://graph.microsoft.com/mail.read` de [P1]).

## 3. `POST /me/sendMail` (Graph v1.0)

- Autorisations — VÉRIFIÉ [P7] : Delegated (work or school account) `Mail.Send` ; Delegated (personal Microsoft account) `Mail.Send` ; « Higher privileged permissions : Not available ».
- Requête — VÉRIFIÉ [P7] : `POST /me/sendMail` ; en-têtes `Authorization: Bearer {token}` et `Content-Type` « Use `application/json` for a JSON object and `text/plain` for MIME content ».
- Corps — VÉRIFIÉ [P7] : `message` (« The message to send. Required. ») ; `saveToSentItems` (« Indicates whether to save the message in Sent Items. Specify it only if the parameter is false; default is true. Optional. »).
- Pièce jointe dans le même appel — VÉRIFIÉ [P7] : « When using JSON format, you can include a file attachment in the same **sendMail** action call. »
- Exemple 3 de [P7], VÉRIFIÉ :

```json
{
  "message": {
    "subject": "Meet for lunch?",
    "body": { "contentType": "Text", "content": "The new cafeteria is open." },
    "toRecipients": [ { "emailAddress": { "address": "meganb@contoso.com" } } ],
    "attachments": [
      {
        "@odata.type": "#microsoft.graph.fileAttachment",
        "name": "attachment.txt",
        "contentType": "text/plain",
        "contentBytes": "SGVsbG8gV29ybGQh"
      }
    ]
  }
}
```

  `ccRecipients` figure dans l'exemple 1 ; `body.contentType` vaut `"Text"` ou `"HTML"` dans les exemples.
- Champs du message — VÉRIFIÉ [P8] : `toRecipients` « The To: recipients for the message. » ; `ccRecipients` « The Cc: recipients for the message. » ; `replyTo` « The email addresses to use when replying. » ; `subject` ; `body` « It can be in HTML or text format. » ; `attachments` « The fileAttachment and itemAttachment attachments for the message. »
- Pièce jointe — VÉRIFIÉ [P9] : `contentBytes` « The base64-encoded contents of the file. » ; `contentType` « The content type of the attachment. » ; `name` « … doesn't need to be the actual file name. »
- Réponse — VÉRIFIÉ [P7] : « If successful, this method returns `202 Accepted` response code. It doesn't return anything in the response body. » ; « A `202 Accepted` response code indicates that the request has been accepted; however, it doesn't indicate that the request processing has completed. Delivery of the message is subject to Exchange Online limitations and throttling. »
- Après le 202 — VÉRIFIÉ [P17] : « When step 1 is complete, your app's direct interaction with Microsoft Graph is over. » ; en cas d'échec ensuite, « the transport process constructs a non-delivery report message and places it in the sender's Inbox ». Analyse : 202 = « accepté », pas « remis » ; un échec de remise n'arrive que dans la boîte de l'utilisateur.

**Tailles**

- 3 Mo — VÉRIFIÉ [P10] : « If the file size is under 3 MB, do a single POST on the **attachments** navigation property … If the file size is between 3 MB and 150 MB, create an upload session ». [P12] : « This operation limits the size of the attachment you can add to under 3 MB. »
- 150 Mo — VÉRIFIÉ [P10] : « you can attach files up to 150 MB to an Outlook message ».
- Session d'envoi — VÉRIFIÉ [P11] : « up to 4 MB each time » par tranche ; taille de message par défaut : « By default, this message size limit is 35 MB » (Microsoft 365, réglable par l'administrateur).
- Droits de la voie « grosse pièce jointe » — VÉRIFIÉ : créer un brouillon [P13], ajouter une pièce jointe [P12] et créer une session d'envoi [P11] exigent `Mail.ReadWrite` ; envoyer un brouillon existant [P14] exige `Mail.Send`.
- Analyse : avec `Mail.Send` seul, la seule voie est `sendMail` avec la pièce jointe dans le JSON ; la session d'envoi est hors de portée. Garder les PDF de bons de commande sous 3 Mo, et refuser l'envoi au-delà avec un message clair.
- Taille maximale de la requête `sendMail` : non trouvée sur une page de référence. Voir annexe (« 4 Mo », 413).

**Limites de débit**

- VÉRIFIÉ [P16] (« Outlook service limits », par couple application + boîte) : « 10,000 API requests in a 10-minute period » ; « Four concurrent requests » ; « 150 megabytes (MB) upload (PATCH, POST, PUT) in a 5-minute period ».
- VÉRIFIÉ [P15] : « Returns HTTP status code **429 Too Many Requests** » ; « The failed response includes the `Retry-After` response header » ; « Wait the number of seconds specified in the `Retry-After` header » ; « If no `Retry-After` header is provided by the response, we recommend implementing an exponential backoff retry policy. »
- Limites d'envoi Exchange (destinataires par jour, etc.) : page « Exchange Online limits » citée par [P7] mais non lue — NON VÉRIFIÉ.

## 4. `GET /me` (adresse de l'utilisateur)

- VÉRIFIÉ [P18] : `GET /me` ; Delegated (work or school) `User.Read` ; Delegated (personal Microsoft account) `User.Read` ; « Calling the `/me` endpoint requires a signed-in user and therefore a delegated permission. »
- Propriétés par défaut — VÉRIFIÉ [P18] : « *businessPhones, displayName, givenName, id, jobTitle, mail, mobilePhone, officeLocation, preferredLanguage, surname, userPrincipalName* ». Analyse : demander `GET /me?$select=mail,userPrincipalName,displayName`.
- `mail` — VÉRIFIÉ [P19] : « The SMTP address for the user, for example, `jeff@contoso.com`. »
- `userPrincipalName` — VÉRIFIÉ [P19] : « The UPN is an Internet-style sign-in name for the user … By convention, this value should map to the user's email name. »
- Compte personnel — VÉRIFIÉ [P20] (tutoriel officiel, commentaire de code) : « // Personal accounts, email is in UserPrincipalName » suivi de `user?.Mail ?? user?.UserPrincipalName`. Analyse : prendre `mail`, à défaut `userPrincipalName`, et afficher l'adresse à l'utilisateur pour qu'il la confirme.
- `mail` vide possible — VÉRIFIÉ (extrait) : réponse de forum Microsoft Q&A « null is a valid value for the mail property » (https://learn.microsoft.com/en-us/answers/questions/1117460/me-endpoint-sometimes-has-blank-mail-property) ; forum, pas documentation de référence.

## 5. Erreurs de consentement et de jeton

Toutes VÉRIFIÉ [P21] sauf mention :

| Code | Extrait | Sens pour nous (Analyse) |
| --- | --- | --- |
| AADSTS65001 | « DelegationDoesNotExist - The user or administrator hasn't consented to use the application with ID X. Send an interactive authorization request for this user and resource. » | Relancer la connexion interactive. |
| AADSTS65004 | « UserDeclinedConsent - User declined to consent to access the app. » | L'utilisateur a refusé ; ne rien envoyer. |
| AADSTS90094 | « AdminConsentRequired - Administrator consent is required. » | L'organisation bloque le consentement des utilisateurs : il faut son administrateur. |
| AADSTS50011 | « InvalidReplyTo - The reply address is missing, misconfigured, or doesn't match reply addresses configured for the app. » | Adresse de retour non inscrite. |
| AADSTS50148 | « The code_verifier doesn't match the code_challenge supplied in the authorization request for PKCE. » | Erreur PKCE de notre côté. |
| AADSTS54005 | « OAuth2 Authorization code was already redeemed » | Code utilisé deux fois. |
| AADSTS70008 | « ExpiredOrRevokedGrant - The refresh token has expired due to inactivity. » | Reconnexion. |
| AADSTS700082 | « The refresh token has expired due to inactivity. … the user went an extended period of time without using the application » | Reconnexion. |
| AADSTS50173 | « The provided grant has expired due to it being revoked … The user might have changed or reset their password. » | Reconnexion. |
| AADSTS700005 | « OAuth2 Authorization Code must be redeemed against same tenant it was acquired for (/common or /{tenant-ID} as appropriate) » | Utiliser `common` aux deux étapes. |

- `invalid_grant` — VÉRIFIÉ [P1] : « The authorization code or PKCE code verifier is invalid or has expired. » → « Try a new request to the `/authorize` endpoint and verify that the `code_verifier` parameter was correct. »
- `consent_required`, `interaction_required` — VÉRIFIÉ [P1] : « The client should send the user back to the `/authorize` endpoint with the correct scope to trigger consent. » ; « Retry the `/authorize` request with the same scopes. »
- `access_denied` — VÉRIFIÉ [P1] : « Resource owner denied consent ».
- Consentement administrateur — VÉRIFIÉ [P22] : « An admin might be required to grant consent on behalf of the user. » Analyse : `Mail.Send` délégué étant « AdminConsentRequired : No » [P5], le 90094 ne vient que d'un réglage de l'organisation, pas de la portée.

## 6. Ajouter une seconde adresse de redirection (Web)

- Ajout possible — VÉRIFIÉ [P24] : « Redirect URIs are configured on the **Authentication** page in the Microsoft Entra admin center. For **Web** and **Single-page applications**, you specify a redirect URI manually. » ; étape « select **Add Redirect URI** » ; plateforme **Web** : « Enter the **Redirect URI** for a web app that runs on a server. »
- Nombre maximal — VÉRIFIÉ [P23] : 256 si `signInAudience` = *AzureADMyOrg* ou *AzureADMultipleOrgs* ; **100** si « `signInAudience` field in the application manifest is set to *AzureADandPersonalMicrosoftAccount* » (notre cas : comptes pro + personnels). « The maximum number of redirect URIs can't be raised for security reasons. » ; « You can use a maximum of 256 characters for each redirect URI ».
- HTTPS — VÉRIFIÉ [P23] : « Redirect URIs must begin with the scheme `https`, with exceptions for some localhost redirect URIs. » ; « The HTTP scheme (`http://`) is supported *only* for *localhost* URIs and should be used only during active local application development and testing. »
- Correspondance exacte — VÉRIFIÉ [P1] : « It must exactly match one of the redirect URIs you registered ».
- Bonne pratique — VÉRIFIÉ [P23] : « Be sure that any unnecessary development environments/redirect URIs are not exposed in the production app. This can be done by having separate app registrations for development and production. »
- Analyse : ajouter la seconde adresse HTTPS d'amazon-sourcing à l'inscription existante est possible (largement sous 100) ; chaque application envoie sa propre `redirect_uri` exacte, à l'autorisation et à l'échange du code. Ne pas confondre avec le type `spa`, qui donne des jetons d'actualisation de 24 h [P3].

---

## Annexe — non vérifié

- **Taille maximale d'une requête `sendMail` (« 4 Mo », erreur 413)** — VÉRIFIÉ (extrait) seulement : réponses de forum Microsoft Q&A (https://learn.microsoft.com/en-us/answers/questions/1824204/graph-api-user-sendmail-request-size-limit) ; aucune page de référence lue ne fixe ce plafond pour `sendMail`. Le seuil documenté reste « under 3 MB » [P10][P12]. Analyse : base64 grossit d'environ un tiers, donc viser un PDF nettement sous 3 Mo.
- **`mail` vide pour certains comptes** — VÉRIFIÉ (extrait), forum (voir § 4).
- **Limites d'envoi Exchange Online / Outlook.com** (destinataires par jour, messages par minute) — NON VÉRIFIÉ : page « Exchange Online limits » non lue ; rien lu pour Outlook.com.
- **Écriture exacte de la portée** (`https://graph.microsoft.com/Mail.Send` vs `Mail.Send` court) — NON VÉRIFIÉ en toutes lettres ; seule la forme `https://graph.microsoft.com/mail.read` de l'exemple [P1] a été lue.
- **Durée de vie réelle du jeton d'actualisation pour un compte personnel** — NON VÉRIFIÉ au-delà de [P1]/[P3].
- **Bibliothèque MSAL Python** — NON VÉRIFIÉ ici ; [P1] recommande une bibliothèque Microsoft plutôt que des requêtes HTTP faites à la main ; [P5] signale que MSAL ajoute d'office `offline_access`, `openid`, `profile`, `email` et qu'un ajout explicite « might return an error ».

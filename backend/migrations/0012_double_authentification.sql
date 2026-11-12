-- 0012 — mots de passe avec expiration et double authentification [RM-AMZ-075, 076].
ALTER TABLE amz.utilisateurs
    ADD COLUMN mdp_change_le    timestamptz,
    ADD COLUMN totp_chiffre     bytea,
    ADD COLUMN totp_actif       boolean NOT NULL DEFAULT false,
    ADD COLUMN totp_dernier_pas bigint NOT NULL DEFAULT 0,
    ADD COLUMN codes_secours    text[] NOT NULL DEFAULT '{}';
UPDATE amz.utilisateurs SET mdp_change_le = cree_le;
ALTER TABLE amz.utilisateurs ALTER COLUMN mdp_change_le SET NOT NULL, ALTER COLUMN mdp_change_le SET DEFAULT now();
-- Les sessions ouvertes avant cette migration repassent par la double authentification.
ALTER TABLE amz.sessions ADD COLUMN niveau text NOT NULL DEFAULT 'ENROLER'
    CHECK (niveau IN ('CHANGER_MDP', 'ENROLER', 'CODE', 'COMPLET'));
DELETE FROM amz.sessions;
GRANT UPDATE (mdp_change_le, totp_chiffre, totp_actif, totp_dernier_pas, codes_secours) ON amz.utilisateurs TO amz_app;
GRANT UPDATE (niveau) ON amz.sessions TO amz_app;

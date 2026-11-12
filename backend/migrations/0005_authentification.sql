-- 0005 — utilisateurs et sessions [RM-AMZ-036 à 038].
-- Non cloisonnées par compte : lues seulement par courriel ou par empreinte de jeton, avant que le compte soit connu.
CREATE TABLE amz.utilisateurs (
    id             uuid PRIMARY KEY,
    compte_id      uuid NOT NULL REFERENCES amz.comptes(id) ON DELETE CASCADE,
    courriel       text NOT NULL UNIQUE CHECK (courriel = lower(courriel) AND courriel LIKE '%@%'),
    empreinte      text NOT NULL CHECK (empreinte LIKE '$argon2id$%'),
    echecs         integer NOT NULL DEFAULT 0,
    bloque_jusqua  timestamptz,
    cree_le        timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE amz.sessions (
    jeton_hash     char(64) PRIMARY KEY,
    utilisateur_id uuid NOT NULL REFERENCES amz.utilisateurs(id) ON DELETE CASCADE,
    compte_id      uuid NOT NULL REFERENCES amz.comptes(id) ON DELETE CASCADE,
    cree_le        timestamptz NOT NULL,
    vu_le          timestamptz NOT NULL
);
GRANT SELECT, INSERT ON amz.utilisateurs TO amz_app;
GRANT UPDATE (empreinte, echecs, bloque_jusqua) ON amz.utilisateurs TO amz_app;
GRANT SELECT, INSERT, DELETE ON amz.sessions TO amz_app;
GRANT UPDATE (vu_le) ON amz.sessions TO amz_app;

-- 0011 — identifiants des sources saisis par le vendeur, chiffrés [RM-AMZ-072 à 074], cloisonnés par compte.
CREATE TABLE amz.connexions (
    compte_id uuid NOT NULL REFERENCES amz.comptes(id) ON DELETE CASCADE,
    source    text NOT NULL CHECK (source IN ('SPAPI', 'KEEPA')),
    chiffre   bytea NOT NULL,
    maj       timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (compte_id, source)
);
ALTER TABLE amz.connexions ENABLE ROW LEVEL SECURITY;
ALTER TABLE amz.connexions FORCE  ROW LEVEL SECURITY;
CREATE POLICY par_compte ON amz.connexions
    USING (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid)
    WITH CHECK (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid);
GRANT SELECT, INSERT, DELETE ON amz.connexions TO amz_app;
GRANT UPDATE (chiffre, maj) ON amz.connexions TO amz_app;

-- 0010 — conformité Europe : enregistrements du compte et fiches produit [RM-AMZ-061, 062], cloisonnés par compte.
CREATE TABLE amz.conformite_enregistrements (
    compte_id  uuid NOT NULL REFERENCES amz.comptes(id) ON DELETE CASCADE,
    pays       char(2) NOT NULL,
    filiere    text NOT NULL CHECK (filiere IN ('EMBALLAGES', 'EEE', 'PILES', 'AUTRE')),
    intitule   text NOT NULL DEFAULT '',
    numero     text NOT NULL CHECK (length(numero) BETWEEN 1 AND 64),
    mandataire text,
    maj        timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (compte_id, pays, filiere, intitule)
);
CREATE TABLE amz.conformite_fiches (
    compte_id uuid NOT NULL REFERENCES amz.comptes(id) ON DELETE CASCADE,
    asin      text NOT NULL,
    donnees   jsonb NOT NULL,
    maj       timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (compte_id, asin)
);
ALTER TABLE amz.conformite_enregistrements ENABLE ROW LEVEL SECURITY;
ALTER TABLE amz.conformite_enregistrements FORCE  ROW LEVEL SECURITY;
ALTER TABLE amz.conformite_fiches ENABLE ROW LEVEL SECURITY;
ALTER TABLE amz.conformite_fiches FORCE  ROW LEVEL SECURITY;
CREATE POLICY par_compte ON amz.conformite_enregistrements
    USING (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid)
    WITH CHECK (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid);
CREATE POLICY par_compte ON amz.conformite_fiches
    USING (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid)
    WITH CHECK (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid);
GRANT SELECT, INSERT, DELETE ON amz.conformite_enregistrements TO amz_app;
GRANT UPDATE (numero, mandataire, maj) ON amz.conformite_enregistrements TO amz_app;
GRANT SELECT, INSERT ON amz.conformite_fiches TO amz_app;
GRANT UPDATE (donnees, maj) ON amz.conformite_fiches TO amz_app;

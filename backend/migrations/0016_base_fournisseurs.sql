-- 0016 — base de fournisseurs [RM-AMZ-100 à 103] : fiche complétée, catalogue par fichier.
ALTER TABLE amz.fournisseurs
    ADD COLUMN pays           text,
    ADD COLUMN site           text,
    ADD COLUMN categories     text[] NOT NULL DEFAULT '{}',
    ADD COLUMN port_unitaire  numeric(14,4) CHECK (port_unitaire IS NULL OR port_unitaire BETWEEN 0 AND 1000),
    ADD COLUMN revente        text NOT NULL DEFAULT 'A_VERIFIER' CHECK (revente IN ('AUTORISEE', 'INTERDITE', 'A_VERIFIER')),
    ADD COLUMN revente_source text,
    ADD COLUMN connexion      text NOT NULL DEFAULT 'AUCUNE' CHECK (connexion IN ('FICHIER', 'API', 'AUCUNE')),
    ADD COLUMN notes          text,
    ADD COLUMN reference      text,
    ADD COLUMN colonnes       jsonb;
GRANT UPDATE (pays, site, categories, port_unitaire, revente, revente_source, connexion, notes, reference, colonnes)
    ON amz.fournisseurs TO amz_app;

CREATE TABLE amz.catalogues (
    compte_id      uuid NOT NULL REFERENCES amz.comptes(id) ON DELETE CASCADE,
    fournisseur_id uuid PRIMARY KEY REFERENCES amz.fournisseurs(id) ON DELETE CASCADE,
    nom_fichier    text NOT NULL,
    lignes         integer NOT NULL,
    rejets         integer NOT NULL,
    maj            timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE amz.catalogue_lignes (
    compte_id      uuid NOT NULL REFERENCES amz.comptes(id) ON DELETE CASCADE,
    fournisseur_id uuid NOT NULL REFERENCES amz.fournisseurs(id) ON DELETE CASCADE,
    numero         integer NOT NULL,
    code           text NOT NULL,
    designation    text,
    prix           numeric(14,4) NOT NULL CHECK (prix > 0),
    colisage       integer,
    minimum        integer,
    PRIMARY KEY (fournisseur_id, code)
);
ALTER TABLE amz.catalogues ENABLE ROW LEVEL SECURITY;
ALTER TABLE amz.catalogues FORCE  ROW LEVEL SECURITY;
ALTER TABLE amz.catalogue_lignes ENABLE ROW LEVEL SECURITY;
ALTER TABLE amz.catalogue_lignes FORCE  ROW LEVEL SECURITY;
CREATE POLICY par_compte ON amz.catalogues
    USING (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid)
    WITH CHECK (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid);
CREATE POLICY par_compte ON amz.catalogue_lignes
    USING (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid)
    WITH CHECK (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid);
GRANT SELECT, INSERT, DELETE ON amz.catalogues, amz.catalogue_lignes TO amz_app;

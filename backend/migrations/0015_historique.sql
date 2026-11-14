-- 0015 — historique maison et suivi de marché [RM-AMZ-086 à 090]. Propre à chaque compte (SP-API 4.4, 4.6).
CREATE TABLE amz.familles_suivies (
    compte_id uuid NOT NULL REFERENCES amz.comptes(id) ON DELETE CASCADE,
    famille   text NOT NULL,
    PRIMARY KEY (compte_id, famille)
);
CREATE TABLE amz.suivis (
    compte_id   uuid NOT NULL REFERENCES amz.comptes(id) ON DELETE CASCADE,
    marketplace text NOT NULL,
    asin        text NOT NULL CHECK (asin ~ '^[A-Z0-9]{10}$'),
    ajoute_le   timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (compte_id, marketplace, asin)
);
CREATE TABLE amz.produits_marche (
    compte_id   uuid NOT NULL REFERENCES amz.comptes(id) ON DELETE CASCADE,
    marketplace text NOT NULL,
    asin        text NOT NULL,
    titre       text,
    marque      text,
    famille     text,
    maj         timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (compte_id, marketplace, asin)
);
CREATE TABLE amz.releves (
    compte_id     uuid NOT NULL REFERENCES amz.comptes(id) ON DELETE CASCADE,
    marketplace   text NOT NULL,
    asin          text NOT NULL,
    jour          date NOT NULL,
    prix_buybox   numeric(14,4),
    nb_fba        integer,
    nb_fbm        integer,
    amazon_vend   boolean,
    buybox_amazon boolean,
    prix_bas_fba  numeric(14,4),
    bsr           integer,
    categorie     text,
    PRIMARY KEY (compte_id, marketplace, asin, jour)
);
CREATE INDEX releves_jour ON amz.releves (compte_id, jour);
ALTER TABLE amz.familles_suivies ENABLE ROW LEVEL SECURITY;
ALTER TABLE amz.familles_suivies FORCE  ROW LEVEL SECURITY;
ALTER TABLE amz.suivis ENABLE ROW LEVEL SECURITY;
ALTER TABLE amz.suivis FORCE  ROW LEVEL SECURITY;
ALTER TABLE amz.produits_marche ENABLE ROW LEVEL SECURITY;
ALTER TABLE amz.produits_marche FORCE  ROW LEVEL SECURITY;
ALTER TABLE amz.releves ENABLE ROW LEVEL SECURITY;
ALTER TABLE amz.releves FORCE  ROW LEVEL SECURITY;
CREATE POLICY par_compte ON amz.familles_suivies
    USING (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid)
    WITH CHECK (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid);
CREATE POLICY par_compte ON amz.suivis
    USING (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid)
    WITH CHECK (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid);
CREATE POLICY par_compte ON amz.produits_marche
    USING (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid)
    WITH CHECK (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid);
CREATE POLICY par_compte ON amz.releves
    USING (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid)
    WITH CHECK (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid);
GRANT SELECT, INSERT, DELETE ON amz.familles_suivies, amz.suivis, amz.releves TO amz_app;
GRANT SELECT, INSERT ON amz.produits_marche TO amz_app;
GRANT UPDATE (titre, marque, famille, maj) ON amz.produits_marche TO amz_app;
GRANT UPDATE (prix_buybox, nb_fba, nb_fbm, amazon_vend, buybox_amazon, prix_bas_fba, bsr, categorie) ON amz.releves TO amz_app;

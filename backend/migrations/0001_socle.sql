-- 0001 — socle : comptes, lots figés, ventes réelles, taux de change.
-- Prérequis (deploy/bootstrap) : rôles amz_owner (propriétaire, migrations, purge) et amz_app (application).
-- [RM-AMZ-014] cloisonnement par compte imposé par la base (sécurité au niveau des lignes).
-- [RM-AMZ-011] un lot ne se modifie jamais (déclencheur).

CREATE SCHEMA IF NOT EXISTS amz;

CREATE TABLE amz.comptes (
    id            uuid PRIMARY KEY,
    nom           text NOT NULL,
    cree_le       timestamptz NOT NULL DEFAULT now(),
    revoque_le    date,                                  -- retrait de l'autorisation Amazon
    CHECK (nom <> '')
);

CREATE TABLE amz.lots (
    id              uuid PRIMARY KEY,
    compte_id       uuid NOT NULL REFERENCES amz.comptes(id) ON DELETE CASCADE,
    asin            text NOT NULL,
    marketplace     text NOT NULL,
    quantite        integer NOT NULL CHECK (quantite > 0),
    date_achat      date NOT NULL,
    fournisseur     text,
    devise          char(3) NOT NULL,
    prix_vente_ht   numeric(14,4) NOT NULL,
    frais_amazon    numeric(14,4) NOT NULL,
    cout_achat      numeric(14,4) NOT NULL CHECK (cout_achat >= 0),
    retours         numeric(14,4) NOT NULL DEFAULT 0,
    stockage        numeric(14,4) NOT NULL DEFAULT 0,
    autres          numeric(14,4) NOT NULL DEFAULT 0,
    sources         text[] NOT NULL DEFAULT '{}',
    version         integer NOT NULL DEFAULT 1 CHECK (version >= 1),
    remplace        uuid UNIQUE REFERENCES amz.lots(id) ON DELETE CASCADE,  -- une version n'est remplacée qu'une fois
    motif           text,
    cree_le         timestamptz NOT NULL DEFAULT now(),
    CHECK ((version = 1 AND remplace IS NULL AND motif IS NULL)
        OR (version > 1 AND remplace IS NOT NULL AND coalesce(motif, '') <> ''))
);
CREATE INDEX lots_compte_produit ON amz.lots (compte_id, asin, marketplace, date_achat);

CREATE FUNCTION amz.interdire_modification() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'RM-AMZ-011 : un lot ne se modifie pas, créer une nouvelle version'
        USING ERRCODE = 'check_violation';
END $$;
CREATE TRIGGER lots_figes BEFORE UPDATE ON amz.lots
    FOR EACH ROW EXECUTE FUNCTION amz.interdire_modification();

CREATE TABLE amz.ventes (
    id                  uuid PRIMARY KEY,
    compte_id           uuid NOT NULL REFERENCES amz.comptes(id) ON DELETE CASCADE,
    id_externe          text NOT NULL,          -- identifiant Amazon de la ligne : rend la synchronisation rejouable
    asin                text NOT NULL,
    marketplace         text NOT NULL,
    jour                date NOT NULL,
    quantite            integer NOT NULL,
    devise              char(3) NOT NULL,
    chiffre_affaires_ht numeric(14,4) NOT NULL,
    frais_amazon        numeric(14,4) NOT NULL,
    retours             numeric(14,4) NOT NULL DEFAULT 0,
    stockage            numeric(14,4) NOT NULL DEFAULT 0,
    autres              numeric(14,4) NOT NULL DEFAULT 0,
    UNIQUE (compte_id, id_externe)
);
CREATE INDEX ventes_compte_produit ON amz.ventes (compte_id, asin, marketplace, jour);

-- [RM-AMZ-015] un taux de change est daté et sourcé ; table commune (donnée publique, non liée à un compte).
CREATE TABLE amz.taux_change (
    de      char(3) NOT NULL,
    vers    char(3) NOT NULL,
    jour    date NOT NULL,
    taux    numeric(18,8) NOT NULL CHECK (taux > 0),
    source  text NOT NULL CHECK (source <> ''),
    PRIMARY KEY (de, vers, jour, source)
);

-- Cloisonnement : l'application positionne app.compte_id dans chaque transaction.
ALTER TABLE amz.lots   ENABLE ROW LEVEL SECURITY;
ALTER TABLE amz.lots   FORCE  ROW LEVEL SECURITY;
ALTER TABLE amz.ventes ENABLE ROW LEVEL SECURITY;
ALTER TABLE amz.ventes FORCE  ROW LEVEL SECURITY;
ALTER TABLE amz.comptes ENABLE ROW LEVEL SECURITY;
ALTER TABLE amz.comptes FORCE  ROW LEVEL SECURITY;

CREATE POLICY par_compte ON amz.lots
    USING (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid)
    WITH CHECK (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid);
CREATE POLICY par_compte ON amz.ventes
    USING (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid)
    WITH CHECK (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid);
CREATE POLICY par_compte ON amz.comptes
    USING (id = nullif(current_setting('app.compte_id', true), '')::uuid)
    WITH CHECK (id = nullif(current_setting('app.compte_id', true), '')::uuid);

GRANT USAGE ON SCHEMA amz TO amz_app;
GRANT SELECT, INSERT ON amz.lots, amz.ventes TO amz_app;          -- jamais UPDATE sur les lots
GRANT UPDATE (chiffre_affaires_ht, frais_amazon, retours, stockage, autres) ON amz.ventes TO amz_app;
GRANT SELECT, INSERT, UPDATE (nom, revoque_le) ON amz.comptes TO amz_app;
GRANT SELECT ON amz.taux_change TO amz_app;
-- Aucune suppression pour amz_app : la purge est faite par amz_owner (purge.py).

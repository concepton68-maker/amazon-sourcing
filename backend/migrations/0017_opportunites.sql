-- 0017 — liste des produits rentables [RM-AMZ-105], propre à chaque compte.
CREATE TABLE amz.opportunites (
    compte_id      uuid NOT NULL REFERENCES amz.comptes(id) ON DELETE CASCADE,
    origine        text NOT NULL,
    origine_nom    text NOT NULL,
    marketplace    text NOT NULL,
    code           text NOT NULL,
    asin           text NOT NULL,
    titre          text,
    designation    text,
    prix_achat     numeric(14,4),
    unites_lot     integer NOT NULL DEFAULT 1,
    cout_achat     numeric(14,4),
    prix_vente     numeric(14,4),
    profit         numeric(14,4),
    roi            numeric(14,6),
    marge          numeric(14,6),
    prix_achat_max numeric(14,4),
    verdict        text,
    vendabilite    text NOT NULL,
    motif          text,
    bsr            integer,
    nb_vendeurs    integer,
    amazon_vend    boolean,
    analyse_le     timestamptz NOT NULL,
    PRIMARY KEY (compte_id, origine, marketplace, code, asin)
);
ALTER TABLE amz.opportunites ENABLE ROW LEVEL SECURITY;
ALTER TABLE amz.opportunites FORCE  ROW LEVEL SECURITY;
CREATE POLICY par_compte ON amz.opportunites
    USING (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid)
    WITH CHECK (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid);
GRANT SELECT, INSERT, DELETE ON amz.opportunites TO amz_app;

-- 0019 — SKU dont le prix est sous le plancher [RM-AMZ-124], remplacés à chaque contrôle.
CREATE TABLE amz.alertes_prix (
    compte_id   uuid NOT NULL REFERENCES amz.comptes(id) ON DELETE CASCADE,
    marketplace text NOT NULL,
    sku         text NOT NULL,
    asin        text,
    prix        numeric(14,4) NOT NULL,
    plancher    numeric(14,4) NOT NULL,
    le          timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (compte_id, marketplace, sku)
);
ALTER TABLE amz.alertes_prix ENABLE ROW LEVEL SECURITY;
ALTER TABLE amz.alertes_prix FORCE  ROW LEVEL SECURITY;
CREATE POLICY par_compte ON amz.alertes_prix
    USING (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid)
    WITH CHECK (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid);
GRANT SELECT, INSERT, DELETE ON amz.alertes_prix TO amz_app;

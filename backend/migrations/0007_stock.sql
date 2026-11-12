-- 0007 — photos de stock quotidiennes [RM-AMZ-045], cloisonnées par compte [RM-AMZ-014].
CREATE TABLE amz.stock_photos (
    compte_id    uuid NOT NULL REFERENCES amz.comptes(id) ON DELETE CASCADE,
    marketplace  text NOT NULL,
    sku          text NOT NULL,
    jour         date NOT NULL,
    asin         text,
    designation  text,
    disponible   integer NOT NULL CHECK (disponible >= 0),
    en_route     integer NOT NULL CHECK (en_route >= 0),
    reserve      integer NOT NULL DEFAULT 0,
    invendable   integer NOT NULL DEFAULT 0,
    PRIMARY KEY (compte_id, marketplace, sku, jour)
);
ALTER TABLE amz.stock_photos ENABLE ROW LEVEL SECURITY;
ALTER TABLE amz.stock_photos FORCE  ROW LEVEL SECURITY;
CREATE POLICY par_compte ON amz.stock_photos
    USING (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid)
    WITH CHECK (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid);
GRANT SELECT, INSERT ON amz.stock_photos TO amz_app;
GRANT UPDATE (asin, designation, disponible, en_route, reserve, invendable) ON amz.stock_photos TO amz_app;

-- 0004 — mémoire des appariements code fournisseur → ASIN [RM-AMZ-034], cloisonnée par compte [RM-AMZ-014].
CREATE TABLE amz.appariements (
    compte_id   uuid NOT NULL REFERENCES amz.comptes(id) ON DELETE CASCADE,
    marketplace text NOT NULL,
    code        text NOT NULL,
    asins       text[] NOT NULL,
    vu_le       timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (compte_id, marketplace, code)
);
ALTER TABLE amz.appariements ENABLE ROW LEVEL SECURITY;
ALTER TABLE amz.appariements FORCE  ROW LEVEL SECURITY;
CREATE POLICY par_compte ON amz.appariements
    USING (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid)
    WITH CHECK (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid);
GRANT SELECT, INSERT, UPDATE (asins, vu_le) ON amz.appariements TO amz_app;

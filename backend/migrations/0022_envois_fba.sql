-- 0022 — envois FBA par l'API Fulfillment Inbound [RM-AMZ-137 à 139], cloisonnés par compte.
CREATE TABLE amz.envois_fba (
    id          uuid PRIMARY KEY,
    compte_id   uuid NOT NULL REFERENCES amz.comptes(id) ON DELETE CASCADE,
    nom         text NOT NULL CHECK (nom <> '' AND length(nom) <= 40),
    marketplace text NOT NULL,
    lignes      jsonb NOT NULL,
    etiquette   text NOT NULL CHECK (etiquette IN ('SELLER', 'AMAZON', 'NONE')),
    preparation text NOT NULL CHECK (preparation IN ('SELLER', 'AMAZON', 'NONE')),
    statut      text NOT NULL,
    plan_id     text,
    donnees     jsonb NOT NULL DEFAULT '{}',
    cree_le     timestamptz NOT NULL,
    maj         timestamptz NOT NULL
);
ALTER TABLE amz.envois_fba ENABLE ROW LEVEL SECURITY;
ALTER TABLE amz.envois_fba FORCE  ROW LEVEL SECURITY;
CREATE POLICY par_compte ON amz.envois_fba
    USING (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid)
    WITH CHECK (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid);
GRANT SELECT, INSERT ON amz.envois_fba TO amz_app;
GRANT UPDATE (statut, plan_id, donnees, maj) ON amz.envois_fba TO amz_app;

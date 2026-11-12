-- 0006 — paramètres du compte, versionnés en ajout seul [RM-AMZ-042, 043], cloisonnés par compte [RM-AMZ-014].
CREATE TABLE amz.parametres (
    compte_id  uuid NOT NULL REFERENCES amz.comptes(id) ON DELETE CASCADE,
    version    integer NOT NULL CHECK (version >= 1),
    valeurs    jsonb NOT NULL,
    cree_le    timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (compte_id, version)
);
ALTER TABLE amz.parametres ENABLE ROW LEVEL SECURITY;
ALTER TABLE amz.parametres FORCE  ROW LEVEL SECURITY;
CREATE POLICY par_compte ON amz.parametres
    USING (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid)
    WITH CHECK (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid);
GRANT SELECT, INSERT ON amz.parametres TO amz_app;          -- jamais UPDATE ni DELETE : ajout seul

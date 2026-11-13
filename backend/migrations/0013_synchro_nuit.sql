-- 0013 — synchronisation de nuit [RM-AMZ-080] et état sans donnée de compte [RM-AMZ-081].
CREATE TABLE amz.synchro_curseurs (
    compte_id uuid NOT NULL REFERENCES amz.comptes(id) ON DELETE CASCADE,
    tache     text NOT NULL,
    curseur   timestamptz NOT NULL,
    PRIMARY KEY (compte_id, tache)
);
CREATE TABLE amz.synchro_journal (
    compte_id uuid NOT NULL REFERENCES amz.comptes(id) ON DELETE CASCADE,
    tache     text NOT NULL,
    debut     timestamptz NOT NULL,
    fin       timestamptz NOT NULL,
    ok        boolean NOT NULL,
    message   text NOT NULL DEFAULT ''
);
CREATE INDEX synchro_journal_tache_fin ON amz.synchro_journal (tache, fin DESC);
ALTER TABLE amz.synchro_curseurs ENABLE ROW LEVEL SECURITY;
ALTER TABLE amz.synchro_curseurs FORCE  ROW LEVEL SECURITY;
ALTER TABLE amz.synchro_journal ENABLE ROW LEVEL SECURITY;
ALTER TABLE amz.synchro_journal FORCE  ROW LEVEL SECURITY;
CREATE POLICY par_compte ON amz.synchro_curseurs
    USING (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid)
    WITH CHECK (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid);
CREATE POLICY par_compte ON amz.synchro_journal
    USING (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid)
    WITH CHECK (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid);
GRANT SELECT, INSERT ON amz.synchro_curseurs, amz.synchro_journal TO amz_app;
GRANT UPDATE (curseur) ON amz.synchro_curseurs TO amz_app;
-- Dernier passage par tâche, tous comptes confondus : ni identifiant, ni message, ni nombre.
CREATE FUNCTION amz.etat_synchros() RETURNS TABLE (tache text, fin timestamptz, ok boolean)
    LANGUAGE sql STABLE SECURITY DEFINER SET search_path = amz, pg_temp AS $$
    SELECT DISTINCT ON (j.tache) j.tache, j.fin, j.ok FROM amz.synchro_journal j ORDER BY j.tache, j.fin DESC
$$;
REVOKE ALL ON FUNCTION amz.etat_synchros() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION amz.etat_synchros() TO amz_app;

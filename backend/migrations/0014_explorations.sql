-- 0014 — dernier sondage « ce que je peux vendre » par compte [RM-AMZ-085].
CREATE TABLE amz.explorations (
    compte_id uuid PRIMARY KEY REFERENCES amz.comptes(id) ON DELETE CASCADE,
    resultat  jsonb NOT NULL,
    maj       timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE amz.explorations ENABLE ROW LEVEL SECURITY;
ALTER TABLE amz.explorations FORCE  ROW LEVEL SECURITY;
CREATE POLICY par_compte ON amz.explorations
    USING (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid)
    WITH CHECK (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid);
GRANT SELECT, INSERT ON amz.explorations TO amz_app;
GRANT UPDATE (resultat, maj) ON amz.explorations TO amz_app;

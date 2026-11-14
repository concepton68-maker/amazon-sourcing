-- 0021 — messagerie Microsoft [RM-AMZ-129 à 131].
ALTER TABLE amz.connexions DROP CONSTRAINT connexions_source_check;
ALTER TABLE amz.connexions ADD CONSTRAINT connexions_source_check
    CHECK (source IN ('SPAPI', 'KEEPA', 'MICROSOFT', 'MESSAGERIE'));

-- Une ligne par tentative d'envoi d'un bon, en ajout seul (ni mise à jour ni effacement par l'application).
CREATE TABLE amz.envois_bon (
    id          bigserial PRIMARY KEY,
    compte_id   uuid NOT NULL REFERENCES amz.comptes(id) ON DELETE CASCADE,
    bon_id      uuid NOT NULL REFERENCES amz.bons_commande(id),
    generation  integer NOT NULL CHECK (generation >= 1),
    destinataire text NOT NULL,
    objet       text NOT NULL,
    empreinte   char(64) NOT NULL,
    taille      integer NOT NULL,
    etat        text NOT NULL CHECK (etat IN ('ENVOYE', 'ECHEC', 'INCERTAIN')),
    cause       text,
    expediteur  text,
    le          timestamptz NOT NULL DEFAULT now(),
    UNIQUE (bon_id, generation)
);
ALTER TABLE amz.envois_bon ENABLE ROW LEVEL SECURITY;
ALTER TABLE amz.envois_bon FORCE  ROW LEVEL SECURITY;
CREATE POLICY par_compte ON amz.envois_bon
    USING (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid)
    WITH CHECK (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid);
GRANT SELECT, INSERT ON amz.envois_bon TO amz_app;
GRANT USAGE ON SEQUENCE amz.envois_bon_id_seq TO amz_app;

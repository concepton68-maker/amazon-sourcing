-- 0008 — fournisseurs et bons de commande [RM-AMZ-049 à 051], cloisonnés par compte [RM-AMZ-014].
CREATE TABLE amz.fournisseurs (
    id          uuid PRIMARY KEY,
    compte_id   uuid NOT NULL REFERENCES amz.comptes(id) ON DELETE CASCADE,
    nom         text NOT NULL CHECK (nom <> '' AND length(nom) <= 120),
    devise      char(3) NOT NULL,
    delai_jours integer NOT NULL CHECK (delai_jours BETWEEN 0 AND 365),
    courriel    text,
    cree_le     timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX fournisseurs_nom ON amz.fournisseurs (compte_id, lower(nom));

CREATE TABLE amz.bons_commande (
    id             uuid PRIMARY KEY,
    compte_id      uuid NOT NULL REFERENCES amz.comptes(id) ON DELETE CASCADE,
    numero         integer NOT NULL CHECK (numero >= 1),
    fournisseur_id uuid NOT NULL REFERENCES amz.fournisseurs(id),
    statut         text NOT NULL CHECK (statut IN ('BROUILLON', 'ENVOYE', 'RECU', 'ANNULE')),
    lignes         jsonb NOT NULL DEFAULT '[]',
    cree_le        timestamptz NOT NULL,
    envoye_le      timestamptz,
    recu_le        date,
    annule_le      timestamptz,
    UNIQUE (compte_id, numero)
);

-- [RM-AMZ-050] lignes figées hors brouillon (réception : seules quantités reçues et lots ajoutés),
-- statut terminal (REÇU, ANNULÉ) définitif.
CREATE FUNCTION amz.garde_bon() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF OLD.statut IN ('RECU', 'ANNULE') THEN
        RAISE EXCEPTION 'RM-AMZ-050 : bon % définitif', OLD.statut USING ERRCODE = 'check_violation';
    END IF;
    IF OLD.statut = 'ENVOYE' AND NEW.statut = 'ENVOYE' AND NEW.lignes <> OLD.lignes THEN
        RAISE EXCEPTION 'RM-AMZ-050 : lignes figées après envoi' USING ERRCODE = 'check_violation';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER bons_gardes BEFORE UPDATE ON amz.bons_commande FOR EACH ROW EXECUTE FUNCTION amz.garde_bon();

ALTER TABLE amz.lots ADD COLUMN bon_commande uuid REFERENCES amz.bons_commande(id);

ALTER TABLE amz.fournisseurs ENABLE ROW LEVEL SECURITY;
ALTER TABLE amz.fournisseurs FORCE  ROW LEVEL SECURITY;
ALTER TABLE amz.bons_commande ENABLE ROW LEVEL SECURITY;
ALTER TABLE amz.bons_commande FORCE  ROW LEVEL SECURITY;
CREATE POLICY par_compte ON amz.fournisseurs
    USING (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid)
    WITH CHECK (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid);
CREATE POLICY par_compte ON amz.bons_commande
    USING (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid)
    WITH CHECK (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid);
GRANT SELECT, INSERT ON amz.fournisseurs, amz.bons_commande TO amz_app;
GRANT UPDATE (devise, delai_jours, courriel) ON amz.fournisseurs TO amz_app;
GRANT UPDATE (statut, lignes, envoye_le, recu_le, annule_le) ON amz.bons_commande TO amz_app;

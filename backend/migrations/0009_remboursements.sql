-- 0009 — remboursements FBA : versements lus chez Amazon et cas suivis [RM-AMZ-054 à 059], cloisonnés par compte.
CREATE TABLE amz.remboursements_verses (
    compte_id        uuid NOT NULL REFERENCES amz.comptes(id) ON DELETE CASCADE,
    reimbursement_id text NOT NULL,
    jour             date,
    case_id          text,
    commande         text,
    sku              text,
    fnsku            text,
    asin             text,
    devise           char(3),
    montant          numeric(14,4),
    quantite         integer NOT NULL DEFAULT 0,
    PRIMARY KEY (compte_id, reimbursement_id)
);
CREATE TABLE amz.remboursements_cas (
    compte_id     uuid NOT NULL REFERENCES amz.comptes(id) ON DELETE CASCADE,
    cle           text NOT NULL,
    type          text NOT NULL,
    marketplace   text NOT NULL,
    asin          text, sku text, fnsku text, commande text,
    unites        integer,
    valeur_achat  numeric(14,4),
    devise        char(3) NOT NULL,
    detecte_le    date NOT NULL,
    echeance      date,
    statut        text NOT NULL CHECK (statut IN ('DETECTE', 'DOSSIER_ENVOYE', 'REMBOURSE', 'REFUSE', 'CLOS')),
    case_id       text,
    montant_verse numeric(14,4),
    faits         jsonb NOT NULL DEFAULT '{}',
    PRIMARY KEY (compte_id, cle)
);
ALTER TABLE amz.remboursements_verses ENABLE ROW LEVEL SECURITY;
ALTER TABLE amz.remboursements_verses FORCE  ROW LEVEL SECURITY;
ALTER TABLE amz.remboursements_cas ENABLE ROW LEVEL SECURITY;
ALTER TABLE amz.remboursements_cas FORCE  ROW LEVEL SECURITY;
CREATE POLICY par_compte ON amz.remboursements_verses
    USING (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid)
    WITH CHECK (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid);
CREATE POLICY par_compte ON amz.remboursements_cas
    USING (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid)
    WITH CHECK (compte_id = nullif(current_setting('app.compte_id', true), '')::uuid);
GRANT SELECT, INSERT ON amz.remboursements_verses, amz.remboursements_cas TO amz_app;
GRANT UPDATE (jour, case_id, commande, sku, fnsku, asin, devise, montant, quantite) ON amz.remboursements_verses TO amz_app;
GRANT UPDATE (type, marketplace, asin, sku, fnsku, commande, unites, valeur_achat, devise, echeance, statut, case_id,
              montant_verse, faits) ON amz.remboursements_cas TO amz_app;

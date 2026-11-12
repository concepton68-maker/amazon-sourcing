-- 0002 — ventes : commande (rattachement des ajustements, RM-AMZ-019), montant différé (RM-AMZ-023),
-- empreinte de la ligne Amazon (contrôle de rejouabilité, RM-AMZ-017). Aucune donnée d'acheteur (RM-AMZ-022).
ALTER TABLE amz.ventes ADD COLUMN commande  text;
ALTER TABLE amz.ventes ADD COLUMN differe   boolean NOT NULL DEFAULT false;
ALTER TABLE amz.ventes ADD COLUMN empreinte text;
CREATE INDEX ventes_commande ON amz.ventes (compte_id, commande) WHERE commande IS NOT NULL;
GRANT UPDATE (differe, empreinte) ON amz.ventes TO amz_app;

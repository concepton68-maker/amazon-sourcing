-- 0020 — prévision figée à l'analyse, reprise par le plan d'achat [RM-AMZ-125].
ALTER TABLE amz.opportunites ADD COLUMN prevision jsonb;
-- [RM-AMZ-116] l'ajout au fil de l'eau remplace une ligne existante (INSERT … ON CONFLICT DO UPDATE) :
-- le droit de mise à jour manquait depuis 0017, l'ajout était refusé par la base.
GRANT UPDATE ON amz.opportunites TO amz_app;

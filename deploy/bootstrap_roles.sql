-- À exécuter une fois par un administrateur Postgres, avant les migrations.
-- Les mots de passe ne sont JAMAIS écrits ici : ils sont posés hors dépôt (ALTER ROLE … PASSWORD).
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'amz_owner') THEN
        -- propriétaire des tables, applique les migrations, fait la purge : contourne le cloisonnement
        CREATE ROLE amz_owner LOGIN BYPASSRLS;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'amz_app') THEN
        -- rôle de l'application : soumis au cloisonnement par compte, aucune suppression
        CREATE ROLE amz_app LOGIN NOBYPASSRLS;
    END IF;
END $$;
-- Puis : CREATE DATABASE amz OWNER amz_owner;

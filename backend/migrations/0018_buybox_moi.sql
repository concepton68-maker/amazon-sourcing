-- 0018 — détenteur de la Buy Box : vous ou non [RM-AMZ-118].
ALTER TABLE amz.releves ADD COLUMN buybox_moi boolean;
GRANT UPDATE (buybox_moi) ON amz.releves TO amz_app;

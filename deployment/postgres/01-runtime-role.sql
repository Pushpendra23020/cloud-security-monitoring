-- Run as the migration/database-owner role. The application connection can
-- then SET ROLE to this non-login role without retaining schema-owner rights.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'cloud_security_runtime') THEN
        CREATE ROLE cloud_security_runtime
            NOLOGIN
            NOSUPERUSER
            NOCREATEDB
            NOCREATEROLE
            NOREPLICATION
            NOBYPASSRLS;
    END IF;
END
$$;

ALTER ROLE cloud_security_runtime
    NOLOGIN
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    NOREPLICATION
    NOBYPASSRLS;

REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO cloud_security_runtime;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public
    TO cloud_security_runtime;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public
    TO cloud_security_runtime;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO cloud_security_runtime;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO cloud_security_runtime;
GRANT cloud_security_runtime TO CURRENT_USER;

-- Fresh local research instance only. Run psql as the PostgreSQL administrator.
-- Stop before touching any pre-existing role/database. Password prompts are not echoed.
\set ON_ERROR_STOP on
CREATE ROLE stargate_migrator LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE;
\password stargate_migrator
CREATE ROLE stargate_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE;
\password stargate_app
CREATE DATABASE stargate_local OWNER stargate_migrator;
REVOKE ALL ON DATABASE stargate_local FROM PUBLIC;
GRANT CONNECT, TEMPORARY ON DATABASE stargate_local TO stargate_app;
\connect stargate_local
CREATE EXTENSION vector;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO stargate_app;

# FROM postgres:17-alpine -- Use pgvector version directly instead.
FROM pgvector/pgvector:pg17

# This is probably redundant but leave it here so we remember how to easily activate extensions...
COPY init_pgvector.sql /docker-entrypoint-initdb.d/

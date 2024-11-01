# FROM postgres:17-alpine -- Use pgvector version directly instead.
FROM pgvector/pgvector:pg17

# This is probably redundant...
COPY init_pgvector.sql /docker-entrypoint-initdb.d/

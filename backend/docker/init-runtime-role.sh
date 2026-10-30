#!/bin/sh
set -eu

# The image runs this only for a new local database volume. Existing installations
# provision the equivalent least-privilege role through their DBA process.
psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  --set=runtime_password="$HUB_RUNTIME_PASSWORD" \
  --set=plataforma_password="$HUB_PLATAFORMA_PASSWORD" \
  --command="CREATE ROLE hub_runtime LOGIN PASSWORD :'runtime_password';" \
  --command="CREATE ROLE hub_plataforma LOGIN PASSWORD :'plataforma_password';"

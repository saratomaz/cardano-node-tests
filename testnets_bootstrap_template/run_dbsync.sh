#! /usr/bin/env nix-shell
#! nix-shell -i bash --pure --keep CARDANO_NODE_SOCKET_PATH --keep PGHOST --keep PGPORT --keep PGUSER --keep PGPASSFILE --keep DBSYNC_REPO -p postgresql
# shellcheck shell=bash

set -uo pipefail

SOCKET_PATH="$(readlink -m "$CARDANO_NODE_SOCKET_PATH")"
STATE_CLUSTER="${SOCKET_PATH%/*}"

export PGPASSFILE="$STATE_CLUSTER/pgpass"
export PGHOST="${PGHOST:-localhost}"
export PGPORT="${PGPORT:-5432}"
export PGUSER="${PGUSER:-postgres}"

exec "$DBSYNC_REPO/db-sync-node/bin/cardano-db-sync" --config "$STATE_CLUSTER/dbsync-config.yaml" --socket-path "$CARDANO_NODE_SOCKET_PATH" --state-dir "$STATE_CLUSTER/db-sync" --schema-dir "$DBSYNC_REPO/schema"

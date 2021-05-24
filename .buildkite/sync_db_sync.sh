#! /usr/bin/env nix-shell
#! nix-shell -i bash -p niv nix gnumake gnutar coreutils adoptopenjdk-jre-bin curl git
#! nix-shell -I nixpkgs=./nix
# shellcheck shell=bash

set -xeuo pipefail

REPODIR="$PWD"

WORKDIR="/scratch/workdir"
rm -rf "$WORKDIR"
mkdir -p "$WORKDIR"

# update to latest cardano-node
niv update

pushd "$WORKDIR"

# build dbsync
git clone --depth 1 git@github.com:input-output-hk/cardano-db-sync.git
pushd cardano-db-sync
nix-build -A cardano-db-sync-extended -o db-sync-node-extended
export DBSYNC_REPO="$PWD"
popd

cd "$REPODIR"

# set postgres env variables
export PGHOST=localhost
export PGUSER=postgres
export PGPORT=5432

# start and setup postgres
./scripts/postgres-start.sh "$WORKDIR/postgres" -k
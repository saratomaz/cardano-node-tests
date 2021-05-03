#!/usr/bin/env bash

: "${sshkey:=/run/keys/buildkite-ssh-iohk-devops-private}"
echo "Authenticating push using SSH with $sshkey"
export GIT_SSH_COMMAND="ssh -i $sshkey -F /dev/null"
remote="git@github.com:input-output-hk/cardano-node-tests.git"

git config pull.rebase true
git pull origin master

git add sync_tests/sync_results.db
git add sync_tests/csv_files
git commit -m "added sync values for"
git push origin master

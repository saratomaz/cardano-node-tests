#!/usr/bin/env bash

: "${sshkey:=/run/keys/buildkite-ssh-iohk-devops-private}"
echo "Authenticating push using SSH with $sshkey"
export GIT_SSH_COMMAND="ssh -i $sshkey -F /dev/null"
remote="git@github.com:input-output-hk/cardano-node-tests.git"

git fetch origin
git merge origin/dorin/sync_test1
git status
git pull

git add sync_tests/sync_tests_results.db
git add sync_tests/csv_files
git commit -m "added sync test values"
git push origin master

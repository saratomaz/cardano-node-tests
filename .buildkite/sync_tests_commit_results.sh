#!/usr/bin/env bash

git remote add origin git@github.com:input-output-hk/cardano-node-tests.git


echo "----------------"
git remote -v
echo "----------------"


git remote set-url origin git@github.com:input-output-hk/cardano-node-tests.git

: "${sshkey:=/run/keys/buildkite-ssh-iohk-devops-private}"
echo "Authenticating push using SSH with $sshkey"
export GIT_SSH_COMMAND="ssh -i $sshkey -F /dev/null"
remote="git@github.com:input-output-hk/cardano-node-tests.git"

echo "pwd: $PWD"
git remote -v
echo "aaa: $(ls -l)"

git fetch origin
git merge origin/dorin/sync_test1

git add sync_tests/sync_tests_results.db
git add sync_tests/csv_files

git commit -m "added sync test values"
git push upstream HEAD:dorin/sync_test1 --force

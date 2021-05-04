#!/usr/bin/env bash

#: "${sshkey:=/run/keys/buildkite-ssh-iohk-devops-private}"
#echo "Authenticating push using SSH with $sshkey"
#export GIT_SSH_COMMAND="ssh -i $sshkey -F /dev/null"
#remote="git@github.com:input-output-hk/cardano-node-tests.git"

echo "pwd: $PWD"

git config --global user.name "sync_tests"
git config --global user.email "action@github.com"
#git remote add origin https://github.com/input-output-hk/cardano-node-tests.git

echo "000000000000000000000000"
git fetch origin
echo "111111111111111111"
git merge origin/dorin/sync_test1
echo "3333333333333333333"

git add sync_tests/sync_tests_results.db
git add sync_tests/csv_files
echo "444444444444444444444"
#
#git whatchanged --diff-filter=A
#echo "22222222222222222222"

git commit -m "added sync test values"
echo "55555555555555555555"

#git push origin dorin/sync_test1
git push origin HEAD --force
echo "66666666666666666666666"

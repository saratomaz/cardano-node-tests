#!/usr/bin/env bash

git config --global user.name "sync_tests"
git config --global user.email "action@github.com"

git config pull.rebase true
git pull origin master

git add sync_tests/sync_results.db
git add sync_tests/csv_files
git commit -m "added sync values for"
git push origin master

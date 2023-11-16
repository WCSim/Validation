#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
export ValidationPath=$SCRIPT_DIR

echo 'Use to ensure all commits are present in the validation plot update'
echo 'Usage:'
echo 'check_commits.sh [PR NUMBER]'
echo

#get the commits from the PR
echo 'Looking at PR:' $1
gh pr view $1 --json commits > commits

#check all jobs have run & made it into the PR
python3.8 check_commits.py

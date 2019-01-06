#!/bin/bash
DOTTY_DIR="$(cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd)"
REPO_DIR=$DOTTY_DIR/..
cat $REPO_DIR/.dottyrc.json|jq -r '.copy|to_entries[]|[.key,.value]|@tsv'

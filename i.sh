#!/bin/bash
DOTTY_DIR="$(cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd)"
REPO_DIR=$DOTTY_DIR/..
RC=$REPO_DIR/.dottyrc.json
#cat $RC|jq -r '.copy|to_entries[]|[.key,.value]|@tsv' | awk -F'\t' '{print "mv "$1" "$2}' | sed '/^$/d' | xargs -n3 -I{} maybe sh -c '{}'
install_cmd=`cat $RC|jq -r '.install_cmd'`
# install with install_cmd
cat $RC|jq -r '.install|@tsv'|sed 's/\t/ /g'|xargs -L 1 -I{} sh -c $install_cmd' {}' #| awk -F'\t' '{print "mv "$1" "$2}' | sed '/^$/d' | xargs -n3 -I{} maybe sh -c '{}'

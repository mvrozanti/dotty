#!/bin/bash
cat ../.dottyrc.json|jq -r '.copy|to_entries[]|[.key,.value]|@tsv'

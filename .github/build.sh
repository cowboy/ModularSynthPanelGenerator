#!/usr/bin/env bash

set -o errexit
set -o pipefail
set -o nounset
# set -o xtrace

VERSION=$(jq --raw-output '.release.tag_name' "$GITHUB_EVENT_PATH")

sed -i "s/(in-development)/$VERSION/" ModularSynthPanelGenerator.manifest

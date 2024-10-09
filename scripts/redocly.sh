#!/bin/bash
set -eux

pnpm i
pnpm exec redocly build-docs --output redocly/index.html openapi.Sourcegraph.Latest.yaml
pnpm exec redocly build-docs --output redocly/internal-api/index.html openapi.SourcegraphInternal.Latest.yaml

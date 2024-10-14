# changelog-summary

This example demonstrates how to render a unified diff from two git commits/revisions/tags.

First, make sure you have Node v22.9.0 installed, or Bun.

Next, make sure you are authenticated to Sourcegraph.

```
export SRC_ACCESS_TOKEN=<your token>
export SRC_ENDPOINT=https://sourcegraph.com
```

Next, install dependencies:

```bash
npm install
# or
bun install
```

To run:

```bash
npm run start # Requires Node v22.9.0 for --experimental-strip-types
# or
bun run bun:start
```

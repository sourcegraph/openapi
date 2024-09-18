# Example Python client for Sourcegraph Cody Chat (5.6)

First, set the following environment variables:

```
export SRC_ACCESS_TOKEN=<your access token>
export SRC_ENDPOINT=<your Sourcegraph endpoint>
```

Next, install [`uv`](https://pypi.org/project/uv/).

Finally, run the script:

```
uv run cody_chat.py --context-repo github.com/sourcegraph/cody --message 'what is the agent?'
```

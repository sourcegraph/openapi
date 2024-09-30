# Example Python client library for Sourcegraph Cody Chat (5.7)

First, set the following environment variables:

```
export SRC_ACCESS_TOKEN=<your access token>
export SRC_ENDPOINT=<your Sourcegraph endpoint>
```

Then you can use the library in your python project:
```
>>> client = CodyAPIClient()
>>> models = client.get_models()
>>> response = client.chat("Hello, Cody!")

>>> async_client = AsyncCodyAPIClient()
>>> models = await async_client.get_models()
>>> response = await async_client.chat("Hello, Cody!")
```

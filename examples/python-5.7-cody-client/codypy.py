"""
Cody API Client Module

This module provides both synchronous and asynchronous clients for
interacting with the Cody HTTP API. It allows users to communicate with
various Large Language Models (LLMs) through Sourcegraph's Cody service.

The module includes two main classes:
1. CodyAPIClient: A synchronous client for making API calls.
2. AsyncCodyAPIClient: An asynchronous client for making API calls.

Both clients provide methods to:
- Retrieve available LLM models
- Send chat messages (both streaming and non-streaming)
- Handle API responses

The module also includes utility functions for testing both synchronous
and asynchronous implementations.

Additional API documentation:
https://sourcegraph.github.io/openapi/elements/internal-api/#/operations/Completions_chatCompletions
https://sourcegraph.github.io/openapi/elements/#/operations/CodyService_context

Classes:
    Message: Represents an OpenAPI message model.
    CodyAPIClient: Synchronous Cody API client.
    AsyncCodyAPIClient: Asynchronous Cody API client.

Functions:
    test_sync: Test function for synchronous client.
    test_async: Test function for asynchronous client.

Constants:
    DEFAULT_LLM: Default LLM model used for API calls.
    LLMModels: Type alias for supported LLM models.

Usage:
    # Synchronous usage
    client = CodyAPIClient()
    models = client.get_models()
    response = client.chat("Hello, Cody!")

    # Asynchronous usage
    async_client = AsyncCodyAPIClient()
    models = await async_client.get_models()
    response = await async_client.chat("Hello, Cody!")

Note:
    This module requires the following environment variables to be set:
    - SRC_ACCESS_TOKEN: Access token for the Sourcegraph API
    - SRC_ENDPOINT: Sourcegraph API endpoint

Examples:
>>> from codypy import AsyncCodyAPIClient, CodyAPIClient
>>> help(CodyAPIClient)
>>> help(AsyncCodyAPIClient)
"""

import asyncio
import logging
import os
from typing import Literal, TypeAlias

import aiohttp
import pydantic_core as pd
import requests
from pydantic import BaseModel


LLMModels: TypeAlias = Literal[
    "anthropic::2023-06-01::claude-3-sonnet",
    "anthropic::2023-06-01::claude-3.5-sonnet",
    "anthropic::2023-06-01::claude-3-opus",
    "anthropic::2023-06-01::claude-3-haiku",
    "fireworks::v1::starcoder",
    "fireworks::v1::deepseek-coder-v2-lite-base",
    "google::v1::gemini-1.5-pro-latest",
    "google::v1::gemini-1.5-flash-latest",
    "mistral::v1::mixtral-8x7b-instruct",
    "mistral::v1::mixtral-8x22b-instruct",
    "openai::2024-02-01::gpt-4o",
    "openai::2024-02-01::gpt-4-turbo",
    "openai::2024-02-01::gpt-3.5-turbo",
]
DEFAULT_LLM = "anthropic::2023-06-01::claude-3.5-sonnet"


class Message(BaseModel):
    """OpenAPI message model"""

    content: str | list[dict[str, str]]
    role: Literal["user", "assistant"] = "user"


class CodyAPIClient:
    """Cody API Client

    Usage:
    >>> from codypy import CodyAPIClient
    # If you have SRC_ACCESS_TOKEN and SRC_ENDPOINT set as envvar
    >>> client = CodyAPIClient()
    # Alternatively passing token and endpoint directly
    >>> client = CodyAPIClient(access_token, server_endpoint)
    # Get available models
    >>> models = client.get_models()
    >>> print("Available models:", models)
    # Send a chat message
    >>> response = client.chat("What is the capital of France?")
    >>> print("Chat response:", response['choices'][0]['message']['content'])
    # Send a streaming chat message
    >>> stream_response = client.chat_stream("Tell me a joke")
    >>> print("Streaming response:", stream_response)
    """

    def __init__(self, access_token: str = "", server_endpoint: str = ""):
        self.access_token = access_token or os.getenv("SRC_ACCESS_TOKEN")
        self.server_endpoint = server_endpoint or os.getenv("SRC_ENDPOINT")
        if not self.access_token:
            raise ValueError(
                "You must either pass 'access_token' explicitly or "
                "set 'SRC_ACCESS_TOKEN' environment variable."
            )
        if not self.server_endpoint:
            raise ValueError(
                "You must either pass 'server_endpoint' explicitly "
                "or set 'SRC_ENDPOINT' environment variable."
            )
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"token {self.access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "codypy-5.7",
            }
        )
        self.logger = logging.getLogger(__name__)

    def _make_request(self, method: str, uri: str, timeout: int = 10, **kwargs):
        """Make a generic request via the session"""
        url = self.server_endpoint + uri

        resp = self.session.request(method, url, timeout=timeout, **kwargs)
        try:
            resp.raise_for_status()
            if kwargs.get("stream"):
                # The completions streaming API returns data in server-sent
                # events format. We only need to capture the last "completion"
                # event with which is followed by a "done" event with empty data.
                # Practically this is the last line starting with r'^data: {"'
                last_response = ""
                for line in resp.iter_lines(decode_unicode=True):
                    if line.startswith('data: {"'):
                        last_response = line[6:]
                # last_response should look like:
                # '{"completion": "... some answer ...", "stopReason": "stop"}'
                data = pd.from_json(last_response)
                if "completion" not in data:
                    raise ValueError("Received unexpected API response")
                return data["completion"]
            return resp.json()
        except Exception as exc:
            self.logger.exception(
                "Failed during API call: %r - %s", exc, getattr(resp, "text")
            )
            raise

    def get_models(self):
        """Retrieve list of supported LLM models"""
        return self._make_request(method="get", uri="/.api/llm/models")["data"]

    def chat(
        self,
        message: str | list[Message],
        model: LLMModels = DEFAULT_LLM,
        max_completion_tokens: int = 4000,
    ):
        """Send Chat message to the new non-streaming LLM API"""

        if isinstance(message, str):
            messages = [Message(content=message)]
        else:
            messages = message

        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "max_tokens": max_completion_tokens,
        }
        return self._make_request(
            method="post", uri="/.api/llm/chat/completions", data=pd.to_json(payload)
        )

    def chat_stream(
        self,
        query: str,
        model: LLMModels = DEFAULT_LLM,
        max_completion_tokens: int = 4000,
    ) -> str:
        """Send a Chat message using the streaming LLM API"""

        params = {
            "api-version": 1,
            "client-name": "codypy",
            "client-version": "5.7",
        }
        payload = {
            "model": model,
            "messages": [{"speaker": "human", "text": query}],
            "maxTokensToSample": max_completion_tokens,
        }
        return self._make_request(
            method="post",
            uri="/.api/completions/stream",
            stream=True,
            params=params,
            json=payload,
        )

    def get_context(
        self,
        repos: str | list[str],
        query: str,
        code_results_count: int = 15,
        text_results_count: int = 5,
    ):
        """Returns a list of source code locations (aka. "context") that
        are relevant to the given natural language query and list of
        repos.

        :param repos: List of repos names to use for context. Soemthing
            like "gitlab.com/coolproject/reponame".
        :param query: String, The natural language query to find relevant
            context from the provided list of repos.
        :param code_results_count: Int, The number of results to return
            from source code. Should be between 0 and 100.
        :param text_results_count: Int, The number of results to return
            from text sources like Markdown. Should be between 0 and 100.
        """

        if isinstance(repos, str):
            repos = [{"name": repos}]
        else:
            repos = [{"name": x} for x in repos]

        payload = {
            "repos": repos,
            "query": query,
            "codeResultsCount": code_results_count,
            "textResultsCount": text_results_count,
        }
        return self._make_request(method="post", uri="/.api/cody/context", json=payload)


class AsyncCodyAPIClient:
    """Async Cody API Client

    Usage:
    >>> import asyncio
    >>> from codypy import AsyncCodyAPIClient
    >>> loop = asyncio.new_event_loop()
    >>> client = AsyncCodyAPIClient()
    # Get available models
    >>> models = loop.run_until_complete(client.get_models())
    >>> print("Available models:", models)
    # Send a chat message
    >>> response = loop.run_until_complete(client.chat("What is the capital of France?"))
    >>> print("Chat response:", response['choices'][0]['message']['content'])
    # Send a streaming chat message
    >>> stream_response = loop.run_until_complete(client.chat_stream("Tell me a joke"))
    >>> print("Streaming response:", stream_response)
    """

    def __init__(self, access_token: str = "", server_endpoint: str = ""):
        self.access_token = access_token or os.getenv("SRC_ACCESS_TOKEN")
        self.server_endpoint = server_endpoint or os.getenv("SRC_ENDPOINT")
        if not self.access_token:
            raise ValueError(
                "You must either pass 'access_token' explicitly or "
                "set 'SRC_ACCESS_TOKEN' environment variable."
            )
        if not self.server_endpoint:
            raise ValueError(
                "You must either pass 'server_endpoint' explicitly "
                "or set 'SRC_ENDPOINT' environment variable."
            )
        self.headers = {
            "Authorization": f"token {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "codypy-5.7",
        }
        self.logger = logging.getLogger(__name__)

    async def _make_request(self, method: str, uri: str, timeout: int = 10, **kwargs):
        """Make a generic async request"""
        url = self.server_endpoint + uri

        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                stream = kwargs.pop("stream", None)
                async with session.request(
                    method, url, timeout=timeout, **kwargs
                ) as resp:
                    resp.raise_for_status()
                    if stream:
                        # Handle streaming response
                        last_response = ""
                        async for line in resp.content:
                            line = line.decode("utf-8").strip()
                            if line.startswith('data: {"'):
                                last_response = line[6:]
                        data = pd.from_json(last_response)
                        if "completion" not in data:
                            raise ValueError("Received unexpected API response")
                        return data["completion"]
                    return await resp.json()
            except Exception as exc:
                self.logger.exception(
                    "Failed during API call: %r - %s", exc, getattr(resp, "text", "")
                )
                raise

    async def get_models(self):
        """Retrieve list of supported LLM models"""
        result = await self._make_request(method="get", uri="/.api/llm/models")
        return result["data"]

    async def chat(self, message: str | list[Message], model: LLMModels = DEFAULT_LLM):
        """Send Chat message to the new non-streaming LLM API"""
        if isinstance(message, str):
            messages = [Message(content=message)]
        else:
            messages = message

        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "max_tokens": 4000,
        }
        return await self._make_request(
            method="post", uri="/.api/llm/chat/completions", data=pd.to_json(payload)
        )

    async def chat_stream(self, query: str, model: LLMModels = DEFAULT_LLM) -> str:
        """Send a Chat message using the streaming LLM API"""
        params = {
            "api-version": 1,
            "client-name": "codypy",
            "client-version": "5.7",
        }
        payload = {
            "model": model,
            "messages": [{"speaker": "human", "text": query}],
            "maxTokensToSample": 4000,
        }
        return await self._make_request(
            method="post",
            uri="/.api/completions/stream",
            stream=True,
            params=params,
            json=payload,
        )

    async def get_context(
        self,
        repos: str | list[str],
        query: str,
        code_results_count: int = 15,
        text_results_count: int = 5,
    ):
        """Returns a list of source code locations (aka. "context") that
        are relevant to the given natural language query and list of
        repos.

        :param repos: List of repos names to use for context. Soemthing
            like "gitlab.com/coolproject/reponame".
        :param query: String, The natural language query to find relevant
            context from the provided list of repos.
        :param code_results_count: Int, The number of results to return
            from source code. Should be between 0 and 100.
        :param text_results_count: Int, The number of results to return
            from text sources like Markdown. Should be between 0 and 100.
        """

        if isinstance(repos, str):
            repos = [{"name": repos}]
        else:
            repos = [{"name": x} for x in repos]

        payload = {
            "repos": repos,
            "query": query,
            "codeResultsCount": code_results_count,
            "textResultsCount": text_results_count,
        }
        return await self._make_request(
            method="post", uri="/.api/cody/context", json=payload
        )


def test_sync():
    """Testing synchronous code"""
    api = CodyAPIClient()

    # Testing models
    models = api.get_models()
    assert isinstance(models, list)
    assert isinstance(models[0], dict)
    assert DEFAULT_LLM in {x["id"] for x in models}

    # Testing steaming chat
    q = "Today is Monday. Reply the day of tomorrow without punctiation."
    resp = api.chat_stream(q)
    assert resp == "Tuesday"

    q = "Today is Friday. Reply the day of tomorrow without punctiation."
    resp = api.chat_stream(q, model="openai::2024-02-01::gpt-4o")
    assert resp == "Saturday"

    # Testing non-streaming chat
    q = "Today is Monday. Reply the day of tomorrow without punctiation."
    resp = api.chat(q)
    assert resp["choices"][0]["message"]["content"] == "Tuesday"

    q = "Today is Friday. Reply the day of tomorrow without punctiation."
    resp = api.chat(q, model="openai::2024-02-01::gpt-4o")
    assert resp["choices"][0]["message"]["content"] == "Saturday"

    # Testing repo context
    resp = api.get_context(
        repos="gitlab.com/oriordan/codypy",
        query="What is this repo about?",
    )
    assert isinstance(resp, dict)
    assert len(resp["results"]) > 15

    print("All sync test passed!")


async def test_async():
    """Testing asynchronous code"""
    api = AsyncCodyAPIClient()

    # Testing models
    models = await api.get_models()
    assert isinstance(models, list)
    assert isinstance(models[0], dict)
    assert DEFAULT_LLM in {x["id"] for x in models}

    # Testing streaming chat
    q = "Today is Monday. Reply the day of tomorrow without punctiation."
    resp = await api.chat_stream(q)
    assert resp == "Tuesday"

    q = "Today is Friday. Reply the day of tomorrow without punctiation."
    resp = await api.chat_stream(q, model="openai::2024-02-01::gpt-4o")
    assert resp == "Saturday"

    # Testing non-streaming chat
    q = "Today is Monday. Reply the day of tomorrow without punctiation."
    resp = await api.chat(q)
    assert resp["choices"][0]["message"]["content"] == "Tuesday"

    q = "Today is Friday. Reply the day of tomorrow without punctiation."
    resp = await api.chat(q, model="openai::2024-02-01::gpt-4o")
    assert resp["choices"][0]["message"]["content"] == "Saturday"

    # Testing repo context
    resp = await api.get_context(
        repos="gitlab.com/oriordan/codypy",
        query="What is this repo about?",
    )
    assert isinstance(resp, dict)
    assert len(resp["results"]) > 15

    print("All async tests passed!")


if __name__ == "__main__":
    test_sync()
    asyncio.run(test_async())


# Sourcegraph Chat API

A FastAPI-based REST API that provides OpenAI-compatible endpoints for interacting with Sourcegraph's AI chat capabilities.

## Features

- OpenAI-compatible REST API endpoints
- Support for multiple AI models
- Streaming and non-streaming chat completions
- CORS enabled for cross-origin requests
- Comprehensive error handling and logging
- Environment-based configuration

## Prerequisites

- Python 3.7+
- FastAPI
- Uvicorn
- Valid Sourcegraph access token
- Sourcegraph instance with LLM capabilities

## Environment Variables

Required environment variables:
- `SRC_ACCESS_TOKEN`: Your Sourcegraph access token
- `SRC_ENDPOINT`: Your Sourcegraph instance URL
- `PORT`: Server port (default: 8000)

## API Endpoints

### GET /v1/models
Lists available AI models in OpenAI-compatible format.

**Response:**

{
    "object": "list",
    "data": [
        {
            "id": "model_id",
            "object": "model",
            "created": 0,
            "owned_by": "sourcegraph"
        }
    ]
}


### POST /v1/chat/completions
Creates chat completions using the specified model.

**Request Body:**

{
    "model": "string",
    "messages": [
        {
            "role": "string",
            "content": "string"
        }
    ],
    "temperature": 0.7,
    "max_tokens": 8000,
    "stream": false
}


**Response:**

{
    "id": "string",
    "object": "chat.completion",
    "created": 0,
    "model": "string",
    "system_fingerprint": "",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "string",
                "content": "string"
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0
    }
}


## Running the Server


python api.py


The server will start on the specified port (default: 8000).

## Error Handling

The API includes comprehensive error handling and logging:
- Environment variable validation
- API request error handling
- Model availability checking
- Request validation using Pydantic models

## Logging

The application uses Python's built-in logging module with INFO level logging for:
- Server startup
- Model selection
- Request processing
- API responses
- Error conditions

# Import necessary libraries and modules
from fastapi import FastAPI, HTTPException  # FastAPI framework and exception handling
from fastapi.middleware.cors import CORSMiddleware  # CORS handling middleware
from pydantic import BaseModel  # Pydantic for data validation and parsing
from typing import List, Optional, Dict, Any  # Type annotations for improved readability
import os  # Access environment variables
import sys  # System-specific functions and parameters
import time  # Time management functions
import json  # JSON data manipulation
import requests  # HTTP requests
import logging  # Logging for application monitoring
import uuid  # Unique ID generation

# Initialize logging for application monitoring
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define Pydantic models for structured request and response handling
class Message(BaseModel):
    """Model for representing a message within a chat session."""
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    """Model for handling chat completion request payloads."""
    model: Optional[str] = None
    messages: List[Message]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 8000
    stream: Optional[bool] = False

class ChatCompletionResponse(BaseModel):
    """Model for structuring responses from chat completions."""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    system_fingerprint: str = ""
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]

# Define main class to handle interactions with Sourcegraph's API
class SourcegraphChat:
    def __init__(self):
        """Initializes SourcegraphChat by reading required environment variables."""
        self.token = os.getenv('SRC_ACCESS_TOKEN')  # Token for authentication
        self.endpoint = os.getenv('SRC_ENDPOINT')  # Sourcegraph API endpoint
        
        # Verify that the environment variables are set
        if not self.token or not self.endpoint:
            logger.error("Missing required environment variables: SRC_ACCESS_TOKEN and/or SRC_ENDPOINT")
            sys.exit(1)
            
        # Headers for API requests
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'token {self.token}'
        }
        # Get the default model for chat completions
        self.model = self.get_default_model()
        logger.info(f"Initialized SourcegraphChat with model: {self.model}")

    def get_default_model(self) -> str:
        """Fetches available models and sets a default model."""
        logger.info("Fetching available models...")
        try:
            response = requests.get(
                f"{self.endpoint}/.api/llm/models",
                headers=self.headers
            )
            response.raise_for_status()
            models = response.json()['data']
            
            # Choose a recommended model or fallback to the first available
            default_model = "anthropic::2023-06-01::claude-3.5-sonnet"
            selected_model = next(
                (model['id'] for model in models if model['id'] == default_model),
                models[0]['id']  # Fallback to first model if default not found
            )
            logger.info(f"Selected model: {selected_model}")
            return selected_model
        except Exception as e:
            logger.error(f"Error fetching models: {str(e)}")
            raise

    def send_message(self, messages: List[Dict[str, str]], stream: bool = False, model: Optional[str] = None) -> Dict:
        """Sends a message to the chat completion API and returns the response."""
        logger.info(f"Processing messages: {messages}")
    
        payload = {
            "messages": messages,
            "model": model or self.model,  # Use specified model or default
            "max_tokens": 4000,
            "temperature": 0.7,
            "stream": stream
        }
    
        try:
            response = requests.post(
                f"{self.endpoint}/.api/llm/chat/completions",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
        
            result = response.json()
            logger.info(f"AI Response: {result['choices'][0]['message']['content']}")
            return result
        except Exception as e:
            logger.error(f"Error during API call: {str(e)}")
            raise

# FastAPI app setup
app = FastAPI()

# Enable CORS to allow cross-origin requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Sourcegraph Chat instance
chat_instance = SourcegraphChat()

@app.get("/v1/models")
async def list_models():
    """Endpoint to list available models in an OpenAI-compatible format."""
    logger.info("Fetching available models")
    try:
        response = requests.get(
            f"{chat_instance.endpoint}/.api/llm/models",
            headers=chat_instance.headers
        )
        response.raise_for_status()
        models = response.json()['data']
        
        logger.info(f"Available models: {[model['id'] for model in models]}")
        return {
            "object": "list",
            "data": [
                {
                    "id": model["id"],
                    "object": "model",
                    "created": model.get("created", 0),
                    "owned_by": model.get("owned_by", "sourcegraph")
                }
                for model in models
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(request: ChatCompletionRequest):
    """Handles requests for creating chat completions."""
    try:
        logger.info(f"Processing chat completion request with model: {request.model or chat_instance.model}")
        
        # Prepare messages in the expected format
        messages = [message.dict() for message in request.messages]
        
        response = chat_instance.send_message(
            messages=messages,
            stream=request.stream,
            model=request.model  # Use requested model if provided
        )
        
        # Format response to match OpenAI-compatible structure
        formatted_response = {
            "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": request.model or chat_instance.model,
            "system_fingerprint": "",
            "choices": [{
                "index": 0,
                "message": response['choices'][0]['message'],
                "finish_reason": "stop"
            }],
            "usage": response.get('usage', {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            })
        }
        
        return formatted_response
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Run the application with Uvicorn
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv('PORT', 8000))
    logger.info(f"Starting uvicorn server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)

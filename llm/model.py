# File: llm/model.py
# --- UPDATED for OpenAI-Compatible API ---

import httpx
import os
from core.config import OLLAMA_BASE_URL, LLM_MODEL_NAME

class LanguageModel:
    def __init__(self):
        self.base_url = OLLAMA_BASE_URL
        self.model_name = LLM_MODEL_NAME
        
        # This is the standard endpoint for OpenAI-compatible servers
        self.api_endpoint = "/v1/chat/completions" 
        self.full_url = f"{self.base_url.rstrip('/') if self.base_url else ''}{self.api_endpoint}"
        
        print(f"LanguageModel initialized to use model '{self.model_name}' at '{self.full_url}'")

    async def generate_response(self, prompt: str) -> str:
        if not self.base_url or not self.model_name:
            error_msg = "Error: OLLAMA_BASE_URL or LLM_MODEL_NAME is not configured in .env file."
            print(error_msg)
            return error_msg

        headers = {
            "Content-Type": "application/json",
        }

        # This is the standard OpenAI-compatible payload structure
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.0, # Use low temperature for predictable and accurate SQL
            "stream": False
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                print(f"Sending request to OpenAI-compatible server at {self.full_url}...")
                response = await client.post(self.full_url, headers=headers, json=payload)
                
                # Raise an error if the request was unsuccessful
                response.raise_for_status() 
                
                response_data = response.json()
                
                # This is how we parse the content from a standard chat completion response
                content = response_data.get('choices', [{}])[0].get('message', {}).get('content', '')
                
                if not content:
                    print(f"Warning: LLM returned an empty response. Full response data: {response_data}")
                    return "Error: Received an empty response from the model."
                
                return content.strip()

        except httpx.RequestError as e:
            print(f"Error communicating with LLM service: {e}")
            return "Error: Could not connect to the language model service."
        except Exception as e:
            print(f"An unexpected error occurred in LLM interaction: {e}")
            return "Error: An unexpected error occurred while generating the response."
import requests
import json
from typing import Optional, Dict, Any, Union
from flask import current_app

DEFAULT_MODEL = "mixtral-8x7b-32768"
API_BASE_URL = "https://api.groq.com/openai/v1/chat/completions"
REQUEST_TIMEOUT = 30
DEFAULT_MAX_TOKENS = 1500
DEFAULT_TEMPERATURE = 0.5

def call_cloud_llm_api(
    prompt: str,
    api_key: str,
    system_prompt: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = DEFAULT_TEMPERATURE,
    json_mode: bool = False
) -> Optional[Union[str, Dict[str, Any]]]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    try:
        response = requests.post(
            API_BASE_URL,
            headers=headers,
            json=payload,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        response_data = response.json()

        if response_data.get("choices") and len(response_data["choices"]) > 0:
            message = response_data["choices"][0].get("message")
            if message and message.get("content"):
                content = message["content"].strip()
                
                if json_mode:
                    try:
                        parsed_json = json.loads(content)
                        return parsed_json
                    except json.JSONDecodeError as json_err:
                        current_app.logger.error(f"LLM API Error: Failed to decode JSON response. Error: {json_err}. Content: {content}")
                        return None
                else:
                    return content

        current_app.logger.error(f"LLM API call returned unexpected structure: {response_data}")
        return None

    except requests.exceptions.Timeout:
        current_app.logger.error(f"Error: LLM API call timed out after {REQUEST_TIMEOUT} seconds.")
        return None
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error calling LLM API: {e}")
        return None
    except Exception as e:
        current_app.logger.error(f"An unexpected error occurred during LLM API call: {e}")
        return None 
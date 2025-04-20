import requests
import json
import time
from typing import Optional, Dict, Any, Union
from flask import current_app

DEFAULT_MODEL = "llama-3.3-70b-versatile"
API_BASE_URL = "https://api.groq.com/openai/v1/chat/completions"
REQUEST_TIMEOUT = 30
DEFAULT_MAX_TOKENS = 1500
DEFAULT_TEMPERATURE = 0.5

# Rate Limiting Config
RPM_LIMIT = 30 # Requests Per Minute limit (for reference)
TPM_LIMIT = 6000 # Tokens Per Minute limit

# Estimate based on ~10 initial calls + 1 refinement call per minute
TARGET_CALLS_PER_MINUTE = 11 
# Average tokens *allowed* per call to stay under TPM: TPM_LIMIT / TARGET_CALLS_PER_MINUTE
# avg_allowed_tokens = 6000 / 11 ~= 545 - This is VERY LOW, high risk of exceeding TPM!

MIN_DELAY_SECONDS = 60.0 / TARGET_CALLS_PER_MINUTE # approx 5.5 seconds

# NOTE: This faster delay significantly increases the risk of hitting the TPM limit (6000).
# Monitor API usage and potentially increase delay or use a model with higher TPM if needed.

# Module-level variable to track last call time
# NOTE: Still assumes single-process server for this simple implementation.
last_api_call_time: float = 0.0

def call_cloud_llm_api(
    prompt: str,
    api_key: str,
    system_prompt: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = DEFAULT_TEMPERATURE,
    json_mode: bool = False
) -> Optional[Union[str, Dict[str, Any]]]:
    global last_api_call_time

    # --- Rate Limiting --- 
    current_time = time.monotonic()
    time_since_last = current_time - last_api_call_time
    wait_time = MIN_DELAY_SECONDS - time_since_last 

    if wait_time > 0:
        current_app.logger.debug(f"Rate limiting: waiting {wait_time:.2f}s (Target: {TARGET_CALLS_PER_MINUTE}/min - TPM limit risk!)...")
        time.sleep(wait_time)
    
    last_api_call_time = time.monotonic()
    # ---------------------
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    if json_mode:
        messages.append({"role": "assistant", "content": "```json"})

    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    if json_mode:
        payload["stop"] = "```"

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
                        if content.startswith("```json"):
                            content = content[len("```json"):].strip()
                        if content.endswith("```"):
                            content = content[:-len("```")].strip()
                            
                        return json.loads(content)
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
        if e.response is not None:
            current_app.logger.error(f"Error calling LLM API: {e}. Status: {e.response.status_code}. Response: {e.response.text}")
        else:
            current_app.logger.error(f"Error calling LLM API: {e}")
        return None
    except Exception as e:
        current_app.logger.error(f"An unexpected error occurred during LLM API call: {e}")
        return None 
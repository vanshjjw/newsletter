import os
import requests
import json
from typing import List, Dict, Optional

# --- Configuration ---
# Consider making these environment variables or configurable
DEFAULT_MODEL = "mixtral-8x7b-32768" # Example Groq model
API_BASE_URL = "https://api.groq.com/openai/v1/chat/completions"
REQUEST_TIMEOUT = 30 # seconds

# --- Helper Functions ---

def chunk_text(text: str, max_chunk_size: int = 2000) -> List[str]:
    """Splits text into semantic chunks based on paragraphs, respecting max size.

    Args:
        text: The plain text to chunk.
        max_chunk_size: An approximate maximum character size for each chunk.

    Returns:
        A list of text chunks.
    """
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:
        if not paragraph.strip():
            continue

        # If adding the next paragraph exceeds the limit, store the current chunk
        if len(current_chunk) + len(paragraph) + 2 > max_chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = paragraph
        # Otherwise, add the paragraph to the current chunk
        else:
            if current_chunk:
                current_chunk += "\n\n" + paragraph
            else:
                current_chunk = paragraph

    # Add the last remaining chunk
    if current_chunk:
        chunks.append(current_chunk.strip())

    # Further split very large chunks if necessary (simple split)
    final_chunks = []
    for chunk in chunks:
        if len(chunk) > max_chunk_size:
            # Simple split, could be improved
            parts = [chunk[i:i+max_chunk_size] for i in range(0, len(chunk), max_chunk_size)]
            final_chunks.extend(parts)
        else:
            final_chunks.append(chunk)
            
    return final_chunks


def call_cloud_llm_api(prompt: str, api_key: str, model: str = DEFAULT_MODEL) -> Optional[str]:
    """Calls the configured cloud LLM API (Groq OpenAI-compatible format).

    Args:
        prompt: The prompt to send to the LLM.
        api_key: The API key for authentication.
        model: The specific LLM model to use.

    Returns:
        The LLM's response content as a string, or None if an error occurs.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 300, # Limit response size
        "temperature": 0.7, # Adjust creativity vs consistency
    }

    try:
        response = requests.post(
            API_BASE_URL,
            headers=headers,
            json=payload,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

        data = response.json()

        # Extract content based on OpenAI-compatible structure
        if data.get("choices") and len(data["choices"]) > 0:
            message = data["choices"][0].get("message")
            if message and message.get("content"):
                return message["content"].strip()
        print(f"Warning: LLM API response missing expected content. Response: {data}")
        return None # Or raise an error

    except requests.exceptions.RequestException as e:
        print(f"Error calling LLM API: {e}")
        # Consider more specific error handling (timeout, connection error, etc.)
        return None
    except json.JSONDecodeError:
        print(f"Error decoding LLM API JSON response: {response.text}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during LLM API call: {e}")
        return None


# --- Main Summarization Logic ---

def generate_chunk_summary(chunk: str, api_key: str, model: str = DEFAULT_MODEL) -> Optional[str]:
    """Generates a bite-sized summary for a single text chunk."""
    # You can refine this prompt
    prompt = f"""Generate a very short, engaging, single-sentence summary (like a headline or tweet, max 25 words) for the following newsletter content chunk. Capture the main topic clearly and concisely. Output only the summary sentence itself, nothing else.

    Content Chunk:
    ---
    {chunk}
    ---

    Summary:"""
    return call_cloud_llm_api(prompt, api_key, model)


def summarize_newsletter_content(plain_text: str, api_key: Optional[str]) -> List[Dict[str, str]]:
    """Orchestrates the layered summarization process for the entire text.

    Args:
        plain_text: The cleaned-up text content of the newsletter.
        api_key: The API key for the LLM provider.

    Returns:
        A list of dictionaries, where each dictionary contains:
        {'summary': 'The generated summary sentence.', 'original_chunk': 'The text chunk it was based on.'}
        Returns an empty list if the API key is missing or summarization fails globally.
    """
    if not api_key:
        print("Error: LLM API key is not configured.")
        # Return structure indicating failure, or raise?
        return [{"error": "API key missing", "details": "LLM API key not found in environment variables."}]

    chunks = chunk_text(plain_text)
    summaries = []

    if not chunks:
        print("Warning: No text chunks found after processing.")
        return []

    for i, chunk in enumerate(chunks):
        print(f"Summarizing chunk {i+1}/{len(chunks)}...")
        summary = generate_chunk_summary(chunk, api_key, model=DEFAULT_MODEL)

        if summary:
            summaries.append({
                "summary": summary,
                "original_chunk": chunk # Include original chunk for context/future use
            })
        else:
            print(f"Failed to generate summary for chunk {i+1}.")
            # Option: Add placeholder, skip, or add error info
            summaries.append({
                "summary": "[Summary generation failed for this chunk]",
                "original_chunk": chunk
            })

    return summaries

# Example Usage (for testing)
if __name__ == '__main__':
    # Load .env file for local testing if it exists
    try:
        from dotenv import load_dotenv
        if load_dotenv():
            print("Loaded .env file")
        else:
            print("No .env file found or it's empty.")
    except ImportError:
        print("dotenv library not found, skipping .env load.")
        
    test_api_key = os.environ.get("GROQ_API_KEY") # Or your specific key variable name

    if not test_api_key:
        print("Error: GROQ_API_KEY environment variable not set. Cannot run test.")
    else:
        print("API Key found, proceeding with test...")
        # Example Text
        sample_text = """
        Introduction to Machine Learning

        Machine learning (ML) is a field of inquiry devoted to understanding and building methods that 'learn' – that is, methods that leverage data to improve performance on some set of tasks. It is seen as a part of artificial intelligence.

        Applications of ML

        ML algorithms are used in a wide variety of applications, such as in medicine, email filtering, speech recognition, and computer vision, where it is difficult or unfeasible to develop conventional algorithms to perform the needed tasks.

        Supervised Learning

        This is one of the most common types. You train the model on labeled data. For example, predicting house prices based on features like size and location. The labels are the historical prices.

        Unsupervised Learning

        Here, the data is unlabeled. The goal is to find structure in the data, like grouping similar customers based on purchasing behavior. Clustering is a common technique.

        Conclusion

        Machine learning is a powerful tool with diverse applications, constantly evolving with new algorithms and techniques. Understanding the basics of supervised and unsupervised learning is key.
        """

        print(f"--- Input Text ---\n{sample_text}\n--------------------")

        chunked = chunk_text(sample_text)
        print(f"--- Chunked Text ({len(chunked)} chunks) ---")
        for idx, c in enumerate(chunked):
             print(f"Chunk {idx+1}:\n{c}\n---")
             
        print("--- Calling Summarizer ---")
        results = summarize_newsletter_content(sample_text, test_api_key)

        print("\n--- Summarization Results ---")
        if results and "error" in results[0]:
             print(f"Error during summarization: {results[0]['error']} - {results[0]['details']}")
        elif not results:
             print("Summarization returned no results.")
        else:
            for i, item in enumerate(results):
                print(f"Result {i+1}:")
                print(f"  Summary: {item['summary']}")
                # print(f"  Original: {item['original_chunk'][:100]}...") # Optionally print part of original
                print("-" * 10)

        print("--- Test Complete ---") 
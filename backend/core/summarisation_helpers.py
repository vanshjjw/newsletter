from typing import List, Dict, Optional, Any
from flask import current_app

from .text_processor import chunk_text
from .llm_api import call_cloud_llm_api, DEFAULT_MODEL

CHUNK_GROUP_SIZE = 4

def generate_chunk_summary(chunk: str, api_key: str, model: str = DEFAULT_MODEL) -> Optional[str]:
    prompt = f"""Analyze the following newsletter content. Generate a single, concise, engaging sentence (maximum 25 words, like a tweet or headline) that captures the absolute main point or topic. Focus on the core message.

    --- CONTENT START ---
    {chunk}
    --- CONTENT END ---

    Concise Summary Sentence:"""
    
    return call_cloud_llm_api(prompt=prompt, api_key=api_key, model=model)



def generate_group_summary(combined_chunk_text: str, api_key: str, model: str = DEFAULT_MODEL) -> Optional[Dict[str, Any]]:
    system_prompt = "You are an expert at extracting key information from text sections. Analyze the provided text and identify the main topic, a concise summary, and any relevant hyperlinks. Provide the output strictly in JSON format."
    
    prompt = f"""Analyze the following text block from a newsletter. Extract the primary topic and summarize it concisely. Also, list the most important and directly relevant hyperlinks found within this specific text block.

    The text block may contain Markdown-style links like [link text](URL).

    Provide your response as a JSON object with the following exact keys:
    - "heading": A short, relevant title for the main topic (string, max 10 words).
    - "summary": A concise summary of the main topic (string, max 100 words).
    - "links": A JSON array of URL strings that are directly relevant to the summary. Include only the most important 1-3 links. If no relevant links are found, provide an empty array [].

    --- TEXT BLOCK START ---
    {combined_chunk_text}
    --- TEXT BLOCK END ---

    JSON Output:"""

    result = call_cloud_llm_api(
        prompt=prompt,
        api_key=api_key,
        model=model,
        system_prompt=system_prompt,
        json_mode=True, 
        max_tokens=5000
    )


    if isinstance(result, dict):
        if "heading" in result and "summary" in result and "links" in result and isinstance(result["links"], list):
            return result
        else:
            current_app.logger.error(f"LLM response for group summary problem. Response: {result}")
            return None
    else:
        current_app.logger.error(f"Failed to get valid JSON response for group summary. Raw response: {result}")
        return None



def refine_and_deduplicate_summaries_llm(summary_items: List[Dict[str, Any]], api_key: str, model: str = DEFAULT_MODEL) -> List[Dict[str, Any]]:
    if not summary_items:
        return []

    # Format the list of JSON objects for the prompt
    input_json_strings = []
    for i, item in enumerate(summary_items):
        try:
            item_str = f"Item {i+1}:\nHeading: {item.get('heading', 'N/A')}\nSummary: {item.get('summary', 'N/A')}\nLinks: {item.get('links', [])}"
            input_json_strings.append(item_str)
        except Exception as e:
            current_app.logger.warning(f"Skipping item {i+1} due to formatting issue: {e}")
            continue
            
    input_text = "\n\n".join(input_json_strings)
    if not input_text:
         current_app.logger.warning("No valid summary items to refine.")
         return []

    system_prompt = "You are an expert editor specializing in consolidating information from multiple preliminary summaries into a final, concise, non-redundant list suitable for a news feed. Ensure the output is a valid JSON array."

    prompt = f"""Review the following list of extracted newsletter items, each containing a heading, summary, and related links. Some items may be redundant, or cover the same core topic.

    Your task is to:
    1. Identify the distinct key topics/points covered across all items.
    2. For each distinct topic, consolidate the information into **one single** final item.
    3. Create a final 'heading' (max 10 words) and 'summary' (max 80 words) for each consolidated topic.
    4. Compile a 'links' list for each final item, containing only the **unique and most relevant** URLs from the input items related to that topic (max 3-4 links per item).
    5. Ensure the final list contains only unique and informative items.
    6. Aim for roughly **4-10 final items**.
    7. Output **only** a valid JSON array where each element is a JSON object with the exact keys "heading", "summary", and "links".

    --- INPUT ITEMS ---
    {input_text}
    --- END INPUT ITEMS ---

    Refined JSON Array Output:"""

    refined_result = call_cloud_llm_api(
        prompt=prompt, 
        api_key=api_key, 
        model=model, 
        system_prompt=system_prompt,
        json_mode=True, 
        max_tokens=5000
    )


    if isinstance(refined_result, list):
        validated_list = []
        for item in refined_result:
             if isinstance(item, dict) and "heading" in item and "summary" in item and "links" in item and isinstance(item["links"], list):
                  validated_list.append(item)
             else:
                  current_app.logger.warning(f"Refined summary item has incorrect format, discarding: {item}")
        return validated_list
        
    elif isinstance(refined_result, dict) and "final_summaries" in refined_result and isinstance(refined_result["final_summaries"], list):
         current_app.logger.info("LLM wrapped refined summaries in a dictionary key.")
         validated_list = []
         for item in refined_result["final_summaries"]:
             if isinstance(item, dict) and "heading" in item and "summary" in item and "links" in item and isinstance(item["links"], list):
                  validated_list.append(item)
             else:
                  current_app.logger.warning(f"Refined summary item (wrapped) has incorrect format, discarding: {item}")
         return validated_list
    else:
        current_app.logger.error(f"LLM call for refining summaries failed or returned unexpected format. Response: {refined_result}")
        fallback_list = []
        for item in summary_items:
            if isinstance(item, dict) and "heading" in item and "summary" in item and "links" in item:
                fallback_list.append({"heading": item["heading"], "summary": item["summary"], "links": item.get("links", [])})
        return fallback_list



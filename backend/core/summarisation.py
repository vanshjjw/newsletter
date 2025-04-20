from typing import Optional, List, Dict, Any
from flask import current_app
import math 
import os 
import json 
from datetime import datetime 

from .text_processor import chunk_text
from .llm_api import DEFAULT_MODEL
from .summarisation_helpers import generate_group_summary, refine_and_deduplicate_summaries_llm


TARGET_INITIAL_GROUPS = 15
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'output')

def summarize_newsletter(plain_text: str, api_key: Optional[str]) -> List[Dict[str, Any]]:
    if not api_key:
        current_app.logger.error("LLM API key is not configured.")
        return [{"error": "API key missing", "details": "LLM API key not found."}]

    if not plain_text:
        current_app.logger.warning("No plain text provided for summarization.")
        return []

    individual_chunks = chunk_text(plain_text)
    if not individual_chunks:
        current_app.logger.warning("No text chunks found after processing.")
        return []

    num_chunks = len(individual_chunks)
    if num_chunks == 0:
        return []

    dynamic_group_size = max(1, math.ceil(num_chunks / TARGET_INITIAL_GROUPS))
    total_groups = math.ceil(num_chunks / dynamic_group_size)

    initial_summaries = []
    for i in range(0, num_chunks, dynamic_group_size):
        chunk_group = individual_chunks[i:i + dynamic_group_size]
        group_number = (i // dynamic_group_size) + 1
        combined_chunk = "\n\n".join(chunk_group)

        current_app.logger.info(f"Generating initial summary for group {group_number}/{total_groups}...")
        summary = generate_group_summary(combined_chunk, api_key, model=DEFAULT_MODEL)

        if summary:
            initial_summaries.append(summary)
        else:
            current_app.logger.error(f"Failed to generate initial summary for group {group_number}.")

    if not initial_summaries:
        return [{"error": "Summarization Failed", "details": "Could not generate initial summaries."}]

    current_app.logger.info(f"Refining {len(initial_summaries)} initial summaries...")
    final_summaries = refine_and_deduplicate_summaries_llm(initial_summaries, api_key, model=DEFAULT_MODEL)

    if not final_summaries:
        current_app.logger.warning("Final summary list is empty after refinement.")
        return []

 
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        output_filename = os.path.join(OUTPUT_DIR, f"summary_{timestamp}.json")
        
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(final_summaries, f, indent=4, ensure_ascii=False)
        current_app.logger.info(f"Successfully saved final summaries to {output_filename}")

    except Exception as e:
        current_app.logger.error(f"Failed to save final summaries to file: {e}")

    return final_summaries 
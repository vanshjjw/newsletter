from typing import Optional, List, Dict, Any
from flask import current_app

from .text_processor import chunk_text
from .llm_api import DEFAULT_MODEL
from .summarisation_helpers import generate_group_summary, refine_and_deduplicate_summaries_llm


CHUNK_GROUP_SIZE = 4

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


    initial_summaries = []
    groups = (len(individual_chunks) + CHUNK_GROUP_SIZE - 1) // CHUNK_GROUP_SIZE
    
    for i in range(0, len(individual_chunks), CHUNK_GROUP_SIZE):
        
        chunk_group = individual_chunks[i:i + CHUNK_GROUP_SIZE]
        group_number = (i // CHUNK_GROUP_SIZE) + 1
        combined_chunk = "\n\n".join(chunk_group)

        current_app.logger.info(f"Generating initial summary for group {group_number}/{groups}...")
        summary = generate_group_summary(combined_chunk, api_key, model=DEFAULT_MODEL)

        if summary and not summary.startswith("["):
            initial_summaries.append(summary)
        else:
            current_app.logger.error(f"Failed to generate initial summary for group {group_number}.")

    if not initial_summaries:
        return [{"error": "Summarization Failed"}]
        
        
    current_app.logger.info(f"Refining {len(initial_summaries)} initial summaries...")
    final_summaries = refine_and_deduplicate_summaries_llm(initial_summaries, api_key, model=DEFAULT_MODEL)
    
    if not final_summaries:
         current_app.logger.warning("Final summary list is empty after refinement.")
         return []
         
    return [{"final_summaries": final_summaries}] 
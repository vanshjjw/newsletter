from typing import List

def chunk_text(text: str) -> List[str]:
    if not text:
        return []
 
    chunks = [chunk.strip() for chunk in text.split('\n\n') if chunk.strip()]
    return chunks

# Newsletter Summarization Approaches Considered

This document outlines different strategies discussed for summarizing newsletter content effectively, specifically addressing the challenge of topics potentially being split across chunk boundaries.

## Goal

Generate a list of concise, non-redundant, bite-sized summaries representing the key points of a newsletter for display in a feed.

## Challenge

Simple text chunking (e.g., splitting by paragraphs) can divide a single logical topic across multiple chunks. Summarizing these chunks independently can lead to fragmented or duplicate summaries in the final output.

## Approaches

### 1. Initial Multi-Stage Proposal (User Suggestion)

*   **Workflow:**
    1.  LLM Pass 1: Entire text -> General topic summary.
    2.  LLM Pass 2: Use topic summary as system prompt + summarize grouped chunks.
    3.  LLM Pass 3: Collate/refine group summaries.
*   **Pros:** Attempts to provide global context.
*   **Cons:** High risk of hitting token limits (Pass 1), unconventional system prompt use, risk of quality degradation summarizing summaries (Pass 3), high latency/cost (3 LLM calls).

### 2. Refined Prompt + Basic Deduplication (Considered)

*   **Workflow:**
    1.  Pre-process HTML -> Clean Text.
    2.  Chunk text (simple paragraph splits).
    3.  Group consecutive chunks (e.g., 4-5).
    4.  LLM Pass (One per group): Use a refined prompt asking the LLM to identify **multiple** distinct key points within the combined chunk group and generate a concise summary sentence **for each**. 
    5.  Collect all generated summary sentences from all groups.
    6.  Post-processing: Apply a **backend deduplication algorithm** (e.g., using string similarity like Jaccard index or semantic similarity via embeddings) to filter out highly similar/redundant summaries.
*   **Pros:**
    *   **Efficiency:** Only one LLM call per chunk group (fewer calls than Option 1 or 4).
    *   **Direct Summarization:** Summaries generated directly from source text sections, potentially higher quality than summarizing summaries.
    *   **Handles Duplicates:** Directly addresses the redundancy problem via post-processing.
    *   **Lower Complexity (than Semantic Chunking):** Avoids heavy NLP libraries for initial chunking.
*   **Cons:**
    *   Requires implementing and tuning the deduplication logic.
    *   Basic deduplication might miss some semantic duplicates; advanced methods add complexity/dependencies (e.g., `sentence-transformers`).

### 3. Semantic Chunking (Considered)

*   **Workflow:**
    1.  Use advanced NLP techniques (e.g., sentence embeddings, NLP libraries like spaCy) to chunk the text, trying to keep related content together.
    2.  Group these 'smarter' chunks.
    3.  Summarize grouped chunks (one LLM call per group).
*   **Pros:** Addresses the chunk boundary problem at the source. Potentially highest quality summaries.
*   **Cons:** High implementation complexity, potentially slow, adds heavy dependencies.

### 4. LLM-Based Deduplication (To Be Implemented)

*   **Workflow:**
    1.  Pre-process HTML -> Clean Text.
    2.  Chunk text (simple paragraph splits).
    3.  Group consecutive chunks (e.g., 4-5).
    4.  LLM Pass 1 (One per group): Generate a **single** summary for the combined chunk group.
    5.  Collect all generated summaries.
    6.  LLM Pass 2 (Final Pass): Send the **list** of collected summaries to the LLM with a prompt asking it to review, deduplicate, merge, and refine them into a final list of unique, concise summaries.
*   **Pros:**
    *   Leverages LLM for complex task of semantic deduplication.
    *   Potentially simpler backend logic than implementing similarity metrics.
*   **Cons:**
    *   **Latency/Cost:** Requires an additional LLM call for the final deduplication step.
    *   **Quality Risk:** Asking the LLM to process/summarize *already summarized* text can lead to information loss or degradation compared to summarizing source text.
    *   **Prompt Sensitivity:** Success heavily relies on the effectiveness of the final deduplication prompt.

## Decision (Current)

Documenting Option 2 for future reference if latency/cost with Option 4 becomes an issue. Proceeding with implementing **Option 4 (LLM-Based Deduplication)**. 
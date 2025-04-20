## What I'm Trying to Build

Okay, so I get way too many email newsletters and never read them. The idea here is to build a simple app where I can dump all those subscriptions without messing up my main inbox.

In short: Turn annoying newsletters into a personalized, quick-to-read feed. Mix-up content as well to make it dynamic and not feel like literature review.

The user interface is key here.

## Implementation Ideas

1. The app gives me a special email address (like `user@app.whatever`)

2.  I sign up for newsletters with this address (keep my actual inbox clutter-free)

3.  The backend grabs those emails, tries to pull out the actual articles, and then (the important part!) uses some AI magic to hopefully create really short summaries/headlines. This creates the feed.

4.  The frontend is a simple React app (mobile-first!) that shows these summaries like a TikTok/Reels feed, so I can scroll through the useful bits quickly.

5. I want to do something cool with the feed is displayed, the order of content and how to provide more info when the user wants to read more.


## Questions

*   How best to parse email content without AI?

*   User accounts complexity?

*   What's the best way to implement the "read more" functionality?

*   What's the best way to actually receive the emails (SendGrid, Mailgun, self-hosted)?

*   ...more


## Implemented Features

**Backend (Flask)**

*   **Code Structure:** Refactored into a `core` directory (`html_parser.py`, `text_processor.py`, `llm_api.py`, `summarisation.py`, `summarisation_helpers.py`) for better separation of concerns.
*   **HTML Processing (`core/html_parser.py`):**
    *   Parses HTML using `BeautifulSoup`.
    *   Replaces `<a>` tags with Markdown-like `[Text](URL)` format, resolving relative URLs.
    *   Extracts and cleans text content from relevant HTML tags.
    *   Filters boilerplate/short snippets.
*   **Text Processing (`core/text_processor.py`):**
    *   Splits the cleaned text into initial chunks based on paragraphs (`\n\n`).
*   **LLM Summarization Workflow (`core/summarisation.py`, `core/summarisation_helpers.py`):
    *   **Grouping:** Dynamically groups initial text chunks to target ~15 initial processing groups.
    *   **LLM Pass 1 (Initial Extraction):** For each group, calls the LLM API (Groq, configured via `.env`, currently `llama3-70b-8192` via `llm_api.py`) requesting structured JSON output (`{heading, summary, links[]}`). Uses prompts designed for direct, news-feed style output.
    *   **LLM Pass 2 (Refinement & Deduplication):** Collects the structured items from Pass 1 and sends them to the LLM in a second call. Uses a prompt instructing the LLM to act as a "ruthless editor", consolidating topics, removing redundancy/low-impact content, and generating a final list (target 3-6 items) of refined JSON objects (`{heading, summary, links[]}`).
*   **LLM API Interaction (`core/llm_api.py`):
    *   Handles calls to the Groq API.
    *   Supports requesting and parsing structured JSON output using assistant prefill and stop sequences.
    *   Implements client-side rate limiting based on estimated TPM (Tokens Per Minute) to prevent API errors.
*   **Output Saving (`core/summarisation.py`):
    *   Saves the final list of structured summary items to a timestamped JSON file in `backend/output/` for logging/debugging.
*   **API Endpoint (`app.py`):
    *   `/api/process-sample` (GET): Orchestrates the full pipeline (HTML parse -> Text chunk -> LLM Pass 1 -> LLM Pass 2 -> Save output) for a hardcoded sample email file.
    *   Returns the final list of structured summary items (`[{heading, summary, links[]}, ...]`).
    *   `/` endpoint for basic health check.
*   **Configuration:** Uses `.env` file for API key (`GROQ_API_KEY`).

**Frontend (React + TypeScript - Needs Update)**

*   The existing frontend (`frontend/src/App.tsx`, `frontend/src/services/api.ts`) is **outdated**.
*   It currently fetches and displays only plain text from an older version of the `/api/process-sample` endpoint.
*   **Needs significant updates** to:
    *   Handle the new API response format: `List[Dict[str, Any]]` where each dict has `heading`, `summary`, `links`.
    *   Render the structured data as a feed (headings, summaries, clickable links).
    *   Implement the desired mobile-first, TikTok/Reels style scrolling UI.

**Overall Summary:** The backend has been significantly enhanced with a two-stage LLM summarization pipeline using a cloud API, producing structured output with headings and links. It includes rate limiting and saves results. The core logic is refactored. The frontend now requires updates to consume and display this richer data format and implement the target UI.


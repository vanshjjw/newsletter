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

Based on the current codebase (as of initial review):

**Backend (Flask - `backend/app.py`, `backend/processing/html_processor.py`)**

*   **HTML Processing:**
    *   Uses `BeautifulSoup` to parse HTML email content.
    *   Replaces link tags (`<a>`) with a `[Link Text](Absolute URL)` format.
    *   Extracts text from common content tags (headings, paragraphs, list items, etc.).
    *   Applies basic filtering to remove short snippets and common boilerplate text (e.g., unsubscribe links, privacy policies).
    *   Combines extracted text into a single block.
*   **API Endpoints:**
    *   `/api/process-manual` (POST): Accepts raw HTML via JSON and returns processed plain text.
    *   `/api/process-sample` (GET): Reads a local sample email file, processes it, and returns the plain text.
*   **CORS:** Enabled for `http://localhost:3000` to allow frontend requests.

**Frontend (React + TypeScript - `frontend/src/App.tsx`, `frontend/src/services/api.ts`)**

*   **API Interaction:** Contains a service function to call the backend's `/api/process-sample` endpoint.
*   **Display:**
    *   Fetches the processed sample email content on component load.
    *   Shows loading and error states.
    *   Displays the received plain text content from the backend.

**Summary:** The basic pipeline for fetching a *sample* email, processing its HTML on the backend to extract and clean text, and displaying that text on the frontend is functional.


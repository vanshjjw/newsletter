from bs4 import BeautifulSoup, NavigableString
from urllib.parse import urljoin # Needed again for resolving links

# Define tags likely to contain the main content
CONTENT_TAGS = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li', 'td', 'div'] # Maybe remove span for now

# Keywords to filter out small text snippets likely irrelevant
# (More aggressive filtering might be needed)
SNIPPET_FILTER_KEYWORDS = [
    "unsubscribe", "view in browser", "privacy policy", "forward this email",
    "sent to", "email address", "©", "copyright", "all rights reserved",
    "click here", "read more", "learn more", "view online", "preferences",
    # Add short, generic phrases often found in footers/buttons
]
MIN_SNIPPET_LENGTH = 15 # Minimum length for a text snippet to be considered potentially relevant

def process_html_content(html_content: str) -> dict:
    """Parses HTML, replaces links with [Text](URL), extracts text, filters, combines.
    Args:
        html_content: The raw HTML string.
    Returns:
        A dictionary containing the combined plain_text with inline links.
    """
    if not html_content:
        return {"error": "HTML content is empty"}

    try:
        soup = BeautifulSoup(html_content, 'lxml')
        
        # --- Find base URL for resolving relative links --- 
        base_url = None
        base_tag = soup.find('base', href=True)
        if base_tag:
            base_url = base_tag['href']
        # -------------------------------------------------

        # --- Replace <a> tags with [Text](URL) format --- 
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href'].strip()
            text = a_tag.get_text(strip=True)
            
            # Skip empty hrefs, anchors, or javascript
            if not href or href.startswith('#') or href.startswith('javascript:'):
                # Replace the tag with just its text content
                a_tag.replace_with(NavigableString(text))
                continue

            # Use link text, fallback to href if text is empty
            link_display_text = text if text else href 
            
            # Resolve relative URLs
            absolute_href = href
            if base_url:
                try:
                    absolute_href = urljoin(base_url, href)
                except ValueError:
                    pass # Keep original href if join fails

            # Create the new string representation
            link_replacement_text = f" [{link_display_text}]({absolute_href}) " # Add spaces for separation
            
            # Replace the <a> tag with the new string
            # Using NavigableString ensures it's treated as text later
            a_tag.replace_with(NavigableString(link_replacement_text))
        # -----------------------------------------------

        # --- Extract text from specified tags on the MODIFIED soup ---
        search_area = soup
        extracted_texts = []
        for tag_name in CONTENT_TAGS:
            for tag in search_area.find_all(tag_name):
                # Extract text, which now includes the [Text](URL) replacements
                text = tag.get_text(separator=' ', strip=True)

                if not text or len(text) < MIN_SNIPPET_LENGTH:
                    continue
                    
                # Filter out snippets likely containing only boilerplate/links
                lower_text = text.lower()
                if any(keyword in lower_text for keyword in SNIPPET_FILTER_KEYWORDS):
                    # More sophisticated check needed? Maybe allow if text is much longer?
                    # For now, filter aggressively if keyword found.
                    continue 

                # Basic check to avoid adding text that is ONLY a URL
                # (This is imperfect, as URL might be part of a sentence)
                if text.startswith('http://') or text.startswith('https://'):
                    # Check if it's ONLY the URL (strip trailing slashes etc)
                    # This heuristic might need refinement
                    if len(text.split()) == 1:
                         continue

                extracted_texts.append(text)
        
        # Simple deduplication in case of nested tags causing repetition
        unique_texts = list(dict.fromkeys(extracted_texts))

        # Combine the filtered texts into a single blob
        combined_text = "\n\n".join(unique_texts)

        return {
            "plain_text": combined_text,
            "plain_text_length": len(combined_text)
            # Add back link extraction later if needed, separated from text
        }
    except Exception as e:
        print(f"Error processing HTML: {e}")
        return {"error": f"Failed to process HTML: {e}"}




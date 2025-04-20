from bs4 import BeautifulSoup, NavigableString
from urllib.parse import urljoin
from typing import Dict, List, Union


CONTENT_TAGS: List[str] = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li', 'td', 'div']

SNIPPET_FILTER_KEYWORDS: List[str] = [
    "unsubscribe", 
    "view in browser", 
    "privacy policy", 
    "forward this email",
    "sent to", 
    "email address", 
    "©", "copyright", 
    "all rights reserved",
    "click here", 
    "read more", 
    "learn more", 
    "view online", 
    "preferences",
]

MIN_SNIPPET_LENGTH: int = 15

def parse_html_to_text(html_content: str) -> Dict[str, Union[str, int]]:
    if not html_content:
        return {"error": "HTML content is empty"}

    try:
        soup = BeautifulSoup(html_content, 'lxml')

        base_url = None
        base_tag = soup.find('base', href=True)
        if base_tag:
            base_url = base_tag['href']

        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href'].strip()
            text = a_tag.get_text(strip=True)

            if not href or href.startswith('#') or href.startswith('javascript:'):
                if text:
                     a_tag.replace_with(NavigableString(text))
                else:
                     a_tag.decompose()
                continue

            link_display_text = text if text else href

            absolute_href = href
            if base_url:
                try:
                    absolute_href = urljoin(base_url, href)
                except ValueError:
                    pass

            link_replacement_text = f" [{link_display_text}]({absolute_href}) "

            a_tag.replace_with(NavigableString(link_replacement_text))

        search_area = soup
        extracted_texts = []
        for tag_name in CONTENT_TAGS:
            for tag in search_area.find_all(tag_name):
                text = tag.get_text(separator=' ', strip=True)

                if not text or len(text) < MIN_SNIPPET_LENGTH:
                    continue

                lower_text = text.lower()
                if any(keyword in lower_text for keyword in SNIPPET_FILTER_KEYWORDS):
                    continue

                if text.startswith('http://') or text.startswith('https://'):
                     if len(text.split()) <= 2:
                          continue

                extracted_texts.append(text)

        unique_texts = list(dict.fromkeys(extracted_texts))

        combined_text = "\n\n".join(unique_texts)

        return {
            "plain_text": combined_text,
            "plain_text_length": len(combined_text)
        }
        
    except Exception as e:
        return {"error": f"Failed to parse HTML: {e}"} 
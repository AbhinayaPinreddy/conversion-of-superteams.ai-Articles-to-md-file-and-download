import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def fetch_html(url: str) -> str:
    """
    Fetch HTML content from a URL
    """
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()
    return response.text


def extract_article(html: str):
    """
    Extract the main article content from HTML
    """
    soup = BeautifulSoup(html, "html.parser")

    # Try known structured containers first
    selectors = [
        ("article", {}),
        ("main", {}),
        ("div", {"class": "prose"}),
        ("div", {"class": "markdown"}),
        ("div", {"class": "blog-content"}),
        ("div", {"class": "content"}),
    ]

    article = None

    for tag, attrs in selectors:
        article = soup.find(tag, attrs)
        if article and len(article.get_text(strip=True)) > 200:
            print(f"Found article using: {tag} {attrs}")
            break

    # Fallback: choose largest meaningful block
    if not article:
        print("Using fallback: selecting largest content block")

        candidates = soup.find_all(["div", "section"])

        def score(tag):
            text_len = len(tag.get_text(strip=True))
            p_count = len(tag.find_all("p"))
            return text_len + (p_count * 50)

        article = max(candidates, key=score, default=None)

    if not article:
        raise Exception("Could not find article content")

    # Remove unwanted elements
    for tag in article([
        "script",
        "style",
        "button",
        "nav",
        "footer",
        "header",
        "aside",
        "form",
        "noscript"
    ]):
        tag.decompose()

    # Remove very small/noisy elements
    for tag in article.find_all(True):
        if tag.name in ["div", "span"]:
            # Do not delete pieces that live inside code blocks; many pages
            # wrap portions of code (including quoted strings) in spans.
            if tag.find_parent(["pre", "code"]) is not None:
                continue
            text = tag.get_text(strip=True)
            if len(text) < 20 and not tag.find(["img", "code", "pre"]):
                tag.decompose()

    return article
from urllib.parse import urljoin

def fix_image_urls(article, base_url):
    for img in article.find_all("img"):
        src = img.get("src") or img.get("data-src")
        if src:
            img["src"] = urljoin(base_url, src)
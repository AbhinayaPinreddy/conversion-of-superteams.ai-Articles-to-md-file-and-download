from markdownify import markdownify as md
from bs4.element import Tag
from bs4 import NavigableString
import re


def handle_code_blocks(article):
    """
    Deprecated: code blocks are now handled directly in convert_to_markdown.
    Left here as a no-op to keep the public API stable.
    """
    return


def convert_to_markdown(article):
    """
    Convert the extracted article HTML to Markdown.

    We handle <pre> blocks ourselves so that code is preserved exactly as it
    appears in the HTML (including strings, indentation, etc.), instead of
    letting markdownify try to reconstruct it.
    """
    # Important: Do NOT insert markdown fences directly into the HTML string
    # before calling markdownify. markdownify will escape/normalize text
    # inside those fences, which can break indentation.
    #
    # Instead, replace each <pre> with a placeholder token, run markdownify,
    # then replace the tokens with raw fenced code (verbatim).
    placeholders: dict[str, str] = {}

    for i, pre in enumerate(article.find_all("pre")):
        code_tag = pre.find("code")
        lang_from_class = ""
        if code_tag:
            code_text = code_tag.get_text()
            classes = code_tag.get("class", [])
            for c in classes:
                if c.startswith("language-"):
                    lang_from_class = c.replace("language-", "")
                    break
        else:
            code_text = pre.get_text()

        guessed = guess_code_language(code_text)
        lang = guessed if guessed else lang_from_class

        code_text = (code_text or "").rstrip("\n")
        fence = f"\n```{lang}\n{code_text}\n```\n"

        # Use a token with no characters markdownify tends to escape.
        token = f"CODEBLOCKTOKEN{i}"
        placeholders[token] = fence
        pre.replace_with(NavigableString(token))

    markdown = md(str(article), heading_style="ATX")
    for token, fence in placeholders.items():
        markdown = markdown.replace(token, fence)

    return markdown


def guess_code_language(code_text: str) -> str:
    """
    Guess code language for syntax highlighting when no language class exists.
    Keeps output minimal: returns "python", "javascript", "bash", "sql" or "".
    """
    s = (code_text or "").strip()
    if not s:
        return ""

    # SQL
    if re.search(r"^\s*(SELECT|INSERT|UPDATE|DELETE)\b", s, flags=re.IGNORECASE | re.MULTILINE):
        return "sql"

    # Bash / shell
    if re.search(r"^\s*#!/bin/(ba)?sh\b", s, flags=re.IGNORECASE | re.MULTILINE):
        return "bash"
    if re.search(r"^\s*(sudo|apt-get|yum|brew|export|echo|cd)\b", s, flags=re.IGNORECASE | re.MULTILINE):
        return "bash"
    if re.search(r"(^|\n)\s*\$\s+[a-zA-Z0-9_-]+", s):
        return "bash"

    # JavaScript / TypeScript
    if re.search(r"\b(const|let|var|function|class|=>)\b", s):
        if re.search(r"\b(console\.log|require\s*\(|module\.exports|fetch\s*\(|axios|document\.|window\.)\b", s):
            return "javascript"
        # If it's mostly JS-like keywords, still tag it.
        if "=>" in s or "function " in s or re.search(r"class\s+\w+\s*{", s):
            return "javascript"

    # Python
    if re.search(r"^\s*(async\s+def|def)\s+\w+\s*\(", s, flags=re.MULTILINE):
        return "python"
    if re.search(r"^\s*(elif|except|finally|with|return|yield|import|from)\b", s, flags=re.MULTILINE):
        # Don't confuse JS imports/exports: "from X import Y" is more Python.
        if re.search(r"^\s*from\s+\S+\s+import\s+\S+", s, flags=re.MULTILINE) or "print(" in s:
            return "python"
        # If it includes multiple Python-only constructs, assume Python.
        if re.search(r"^\s*(elif|except|yield)\b", s, flags=re.MULTILINE) or re.search(r"\bawait\b", s):
            return "python"
    if "print(" in s or "np." in s or "np.frombuffer" in s:
        return "python"

    return ""


def shrink_superteams_logo(markdown: str, width_px: int = 140) -> str:
    """
    Shrink only Superteams-related images (logo) in the generated Markdown.

    We detect them by matching `alt` text containing "Superteams" so we don't
    affect the article's content images.
    """

    def html_img(alt: str, src: str) -> str:
        alt_escaped = alt.replace('"', "&quot;")
        return f'<img src="{src}" alt="{alt_escaped}" width="{width_px}" />'

    # Replace link-wrapped images: [![alt](src)](href)
    link_img_pat = re.compile(
        r"\[!\[(?P<alt>[^\]]*?)\]\((?P<src>[^)]+)\)\]\((?P<href>[^)]+)\)",
        re.MULTILINE,
    )

    def link_img_repl(m: re.Match) -> str:
        alt = m.group("alt")
        if "superteams" not in alt.lower():
            return m.group(0)
        return f'[{html_img(alt, m.group("src"))}]({m.group("href")})'

    markdown = link_img_pat.sub(link_img_repl, markdown)

    # Replace plain images: ![alt](src)
    img_pat = re.compile(r"!\[(?P<alt>[^\]]*?)\]\((?P<src>[^)]+)\)", re.MULTILINE)

    def img_repl(m: re.Match) -> str:
        alt = m.group("alt")
        if "superteams" not in alt.lower():
            return m.group(0)
        return html_img(alt, m.group("src"))

    return img_pat.sub(img_repl, markdown)


def trim_markdown_tail(markdown: str) -> str:
    """
    Remove non-article sections (e.g., "More from our Editors", newsletter CTAs)
    that sometimes get included in the extracted container.
    """
    markers = [
        "## Want to Scale Your Business with AI",
        "## More from our Editors",
        "## Subscribe to receive articles right in your inbox",
    ]

    authors_idx = markdown.find("## Authors")
    search_from = authors_idx if authors_idx != -1 else 0

    cut_at = None
    for marker in markers:
        idx = markdown.find(marker, search_from)
        if idx != -1 and (cut_at is None or idx < cut_at):
            cut_at = idx

    if cut_at is None:
        return markdown

    return markdown[:cut_at].rstrip() + "\n"


def normalize_heading_breaks(markdown: str) -> str:
    """
    Ensure headings start on their own line.

    Sometimes markdownify outputs \"...](link)## Heading\" on a single line.
    This splits such cases so the heading becomes:

        ...](link)

        ## Heading
    """
    # Insert a blank line before any heading marker that immediately
    # follows a closing parenthesis on the same line.
    pattern = re.compile(r"\)(?=##\s)")
    return pattern.sub(")\n\n", markdown)
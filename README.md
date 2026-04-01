# HTML to Markdown

Convert web articles (blog posts, documentation pages) into clean **Markdown** files: headings, images, links, and code blocks with preserved indentation and language tags for syntax highlighting.

## Features

- **Fetches** a page by URL and **extracts** the main article body (`article`, `main`, or heuristic fallback).
- **Resolves** image URLs relative to the page.
- **Converts** HTML to Markdown with sensible handling for:
  - Code blocks (`<pre>` / `<code>`) with fenced blocks and guessed language (`python`, `javascript`, etc.) when the site does not label them correctly.
  - Placeholder-based conversion so **indentation inside code fences is not stripped**.
- **Post-processing**: trims footer sections (e.g. “More from our Editors”, newsletter), normalizes headings that were glued to links, and optionally shrinks Superteams-branded logo images in the output.

## Requirements

- Python 3.10+ (recommended)
- Dependencies listed in `requirements.txt`

## Setup

```bash
cd html_to_md
python -m venv venv
```

**Windows**

```powershell
venv\Scripts\activate
pip install -r requirements.txt
```

**macOS / Linux**

```bash
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

### Web app (Streamlit)

```bash
streamlit run app.py
```

1. Open the URL shown in the terminal (usually `http://localhost:8501`).
2. Paste an **article URL** and click **Convert to Markdown**.
3. Preview the result, copy text, or **download** the generated `.md` file.



## Project layout

| File | Role |
|------|------|
| `app.py` | Streamlit UI: URL input, preview, download |
| `extractor.py` | HTTP fetch + BeautifulSoup article extraction + cleanup |
| `converter.py` | HTML → Markdown, code fences, language guess, tail trim, logo size, heading fixes |
| `utils.py` | Absolute URLs for images |
| `requirements.txt` | Python dependencies |

## Notes

- Output quality depends on how the source site structures HTML. Some pages may need a larger or different extraction strategy in `extractor.py`.
- **Syntax colors** in previews depend on your editor or viewer (e.g. VS Code / Cursor Markdown preview); fenced blocks use language tags like ` ```python ` when detection succeeds.
- The **Superteams logo** shrinker targets images whose `alt` text contains “Superteams”. Adjust `shrink_superteams_logo` in `converter.py` if you use this for other sites.

## License

Add your license here if applicable.

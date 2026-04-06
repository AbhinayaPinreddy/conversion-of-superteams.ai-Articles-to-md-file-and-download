import streamlit as st
from urllib.parse import urlparse
from extractor import fetch_html, extract_article
from converter import (
    convert_to_markdown,
    trim_markdown_tail,
    shrink_superteams_logo,
    normalize_heading_breaks,
)
from utils import fix_image_urls

# ---------------------------
# Page config (MUST be first Streamlit command)
# ---------------------------
st.set_page_config(
    page_title="HTML → Markdown Converter",
    layout="wide"
)

#  HIDE TOOLBAR (Deploy + menu)
st.markdown("""
<style>
/* Hide Deploy + menu */
[data-testid="stToolbar"] {
    display: none !important;
}

/* Remove header spacing */
[data-testid="stHeader"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Helper: Generate filename
# ---------------------------
def generate_filename(url):
    path = urlparse(url).path.strip("/")
    name = path.split("/")[-1] if path else "article"
    return f"{name}.md"


# ---------------------------
# UI
# ---------------------------
st.title(" HTML to Markdown Converter")
st.caption("Convert blog articles into clean Markdown (with images + code blocks)")

# Input
url = st.text_input(" Enter Article URL")

# Convert button
if st.button("Convert to Markdown"):

    if not url:
        st.warning("Please enter a URL")
        st.stop()

    try:
        progress = st.progress(0)

        # Step 1
        progress.progress(20)
        html = fetch_html(url)

        # Step 2
        progress.progress(40)
        article = extract_article(html)

        # Step 3
        progress.progress(60)
        fix_image_urls(article, url)

        # Step 4
        progress.progress(75)
        markdown = convert_to_markdown(article)

        # Step 5
        progress.progress(90)
        markdown = trim_markdown_tail(markdown)
        markdown = normalize_heading_breaks(markdown)

        progress.progress(100)

        st.success(" Conversion successful!")

        filename = generate_filename(url)

        # Layout
        col1, col2 = st.columns(2)

        with col1:
            st.subheader(" Preview")
            st.markdown(markdown)

        with col2:
            st.subheader(" Raw Markdown")
            st.code(markdown, language="markdown")

        # ---------------------------
        # DOWNLOAD BUTTON 
        # ---------------------------
        st.download_button(
            label=" Download Markdown File",
            data=markdown,
            file_name=filename,
            mime="text/markdown"
        )

        # Optional: Copy button
        st.text_area(" Copy Markdown", markdown, height=200)

    except Exception as e:
        st.error(f" Error: {str(e)}")

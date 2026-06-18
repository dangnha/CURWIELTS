from bs4 import BeautifulSoup
from pathlib import Path


def parse_html_content(html: str) -> str:
    """Extract clean text from HTML-formatted content."""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "img"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    return "\n".join(lines)


def chunk_text(text: str, max_chunk_size: int = 500) -> list[str]:
    """Split text into chunks of approximately max_chunk_size words."""
    paragraphs = text.split("\n\n")
    chunks = []
    current = []
    current_size = 0

    for para in paragraphs:
        words = para.split()
        para_size = len(words)

        if current_size + para_size > max_chunk_size and current:
            chunks.append("\n\n".join(current))
            current = []
            current_size = 0

        current.append(para)
        current_size += para_size

    if current:
        chunks.append("\n\n".join(current))

    return chunks if chunks else [text]

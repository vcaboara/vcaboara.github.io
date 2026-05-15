"""Extract PDF content to markdown for knowledge base."""
import logging
from pypdf import PdfReader
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


def extract_pdf_to_md(pdf_path: str, output_path: str, title: str = None):
    """Extract text from PDF and save as markdown."""
    reader = PdfReader(pdf_path)

    content = []
    if title:
        content.append(f"# {title}\n\n")

    content.append(f"*Extracted from: {Path(pdf_path).name}*\n\n---\n\n")

    for i, page in enumerate(reader.pages, 1):
        text = page.extract_text()
        if text.strip():
            content.append(f"## Page {i}\n\n{text}\n\n")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(''.join(content))

    logger.info(f"Extracted {len(reader.pages)} pages to {output_path}")


if __name__ == "__main__":
    # Extract Tech Brief
    extract_pdf_to_md(
        "Arboreum_Tech_Brief.pdf",
        "knowledge-base/ip-context/tech-brief.md",
        "Arboreum Technology Brief"
    )

    # Extract AIF Pillars
    extract_pdf_to_md(
        "Arboreum Impact Foundation (AIF) Pillars.pdf",
        "knowledge-base/ip-context/aif-pillars.md",
        "Arboreum Impact Foundation (AIF) Pillars"
    )

    logger.info("\nPDF extraction complete")

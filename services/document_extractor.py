import time
import re
from typing import Tuple, Dict
from azure.ai.documentintelligence.models import DocumentContentFormat

class DocumentExtractor:
    """
    Handles PDF -> markdown extraction using Azure Document Intelligence prebuilt-layout model.
    Extracts only relevant sections based on predefined headings.
    """

    # Required headings to extract
    REQUIRED_HEADINGS = [
        "Agreement for IT Projects and Services",
        "Subcontractors",
        "Central Points of Contact/Project Management",
        "Place of performance",
        "Remuneration/Invoicing",
        "Invoicing",
        "Invoice address",
        "Data Protection1",
        "Term",
        "Start Date",
        "End Date",
        "Termination for Convenience",
        "Attachment 1: Service Description",
        "Attachment 2: Milestones",
        "Attachment 3: Rate Card",
        "Attachment 4: Data Processing Agreement",
        "Attachment 5: Information Security Requirements",
        "Attachment 6: Regulatory requirements",
        "General implementing provisions",
        "Human Rights",
        "Entire Agreement"
    ]

    def __init__(self, client):
        self.client = client
        escaped_headings = [re.escape(h) for h in self.REQUIRED_HEADINGS]
        self.heading_pattern = "|".join(escaped_headings)

    def extract_text(self, pdf_bytes: bytes) -> Tuple[str, int, float]:
        """
        Extract relevant sections from PDF bytes in markdown format.
        Returns tuple: (markdown_text, page_count, extraction_time_seconds)
        """
        start_time = time.time()

        # Begin analysis with markdown output
        poller = self.client.begin_analyze_document(
            model_id="prebuilt-layout",
            body=pdf_bytes,
            features=["keyValuePairs"],
            output_content_format=DocumentContentFormat.MARKDOWN,
        )
        result = poller.result()

        markdown_text = result.content if hasattr(result, 'content') else ""
        page_count = len(result.pages) if hasattr(result, 'pages') and result.pages else 0

        # Extract only required sections
        sections = self._extract_sections_from_markdown(markdown_text)
        final_markdown = self._build_final_markdown(sections)

        extraction_time = time.time() - start_time
        return final_markdown, page_count, extraction_time

    def _extract_sections_from_markdown(self, md_text: str) -> Dict[str, str]:
        """
        Extracts markdown headings and the content that follows until the next heading.
        Returns a dictionary of {heading: content}.
        """
        sections = {}
        pattern = rf"(?P<title>{self.heading_pattern})\s*(?P<content>.*?)(?=(?:{self.heading_pattern})|$)"

        matches = re.finditer(pattern, md_text, flags=re.S | re.IGNORECASE)

        for m in matches:
            title = m.group("title").strip()
            content = m.group("content").strip()
            normalized_title = self._clean_heading(title)
            sections[normalized_title] = content

        return sections


    def _clean_heading(self, heading: str) -> str:
        """
        Normalize headings by removing extra characters and whitespace.
        """
        return heading.replace(".", "").strip()
    
    def extract_service_description(self, md_text: str) -> str:
        """
        Extracts everything between Attachment 1 and Attachment 2 using flexible patterns.
        Works even when formatting varies.
        """
        # Match any version of "Attachment 1" and "Attachment 2"
        start_pattern = r"attachment\s*1[^a-zA-Z0-9]*service\s*description"
        end_pattern = r"attachment\s*2"

        start_match = re.search(start_pattern, md_text, flags=re.I)
        if not start_match:
            return "*Service Description not found*"

        start_index = start_match.start()  # capture content AFTER heading

        # Search end after start_index only
        end_match = re.search(end_pattern, md_text[start_index:], flags=re.I)
        if end_match:
            end_index = start_index + end_match.start()
        else:
            end_index = len(md_text)

        extracted = md_text[start_index:end_index].strip()

        print(extracted)
        return extracted if extracted else "*Service Description is empty*"


    def _build_final_markdown(self, sections: Dict[str, str]) -> str:
        """
        Build final markdown document from extracted sections.
        """
        if not sections:
            return "# Extracted Sections\n\n*No matching sections found.*\n"

        md = "# Extracted Sections\n\n"
        for title, content in sections.items():
            md += f"## {title}\n\n{content}\n\n"


        return md

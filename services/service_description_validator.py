# service_description_validator.py

import os
import re
import json
import time
from typing import Tuple, Dict, Any

class ServiceDescriptionValidator:
    """
    Compares contract service description against a static reference (Fieldglass) embedded here.
    Returns JSON with modified sections, validation status, and optional timing/usage info.
    """

    # -------------------------
    # Embed reference markdown directly
    # -------------------------
    with open("fieldglass_service_description.md", "r", encoding="utf-8") as f:
        FIELDGLASS_REF_MD = f.read()


    def __init__(self, client, chat_model: str = None, temperature: float = 0.0):
        self.client = client
        self.model = chat_model or os.getenv("AZURE_OPENAI_MODEL", "gpt-4o")
        self.temperature = temperature

    # -------------------------
    # Text Cleaning & Section Extraction
    # -------------------------
    @staticmethod
    def clean_text_preserve_headings(text: str) -> str:
        if not isinstance(text, str):
            return ""
        def replace_pageheader(match):
            return f"\n{match.group(1)}\n"
        text = re.sub(r'<!--\s*PageHeader\s*=\s*["\'](.*?)["\']\s*-->', replace_pageheader, text)
        text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
        text = re.sub(r'<figure.*?>.*?</figure>', '', text, flags=re.DOTALL | re.I)
        text = re.sub(r'^\s*(Logo|Footer|Confidential)\s*$', '', text, flags=re.M | re.I)
        return text.strip()

    @classmethod
    def extract_reference_sections(cls):
        return cls._extract_sections_from_text(cls.FIELDGLASS_REF_MD)

    @staticmethod
    def _extract_sections_from_text(md_text: str):
        clean_text = ServiceDescriptionValidator.clean_text_preserve_headings(md_text)
        headings = list(re.finditer(r'^(#{1,6})\s*(.+?)\s*$', clean_text, flags=re.M))
        sections = []
        for i, h in enumerate(headings):
            title = h.group(2).strip()
            start = h.end()
            end = headings[i+1].start() if i+1 < len(headings) else len(clean_text)
            content = clean_text[start:end].strip()
            sections.append((title, content))
        return sections

    @classmethod
    def extract_contract_sections(cls, contract_text: str, ref_headings: list) -> dict:
        contract_text = cls.clean_text_preserve_headings(contract_text)
        paragraphs = [p.strip() for p in re.split(r'\n\n+', contract_text) if p.strip()]
        aligned_sections = {}
        start_idx = 0
        num_paragraphs = len(paragraphs)

        for i, heading in enumerate(ref_headings):
            heading_lower = heading.lower()
            found_idx = None
            for j in range(start_idx, num_paragraphs):
                p_clean = re.sub(r'^#+\s*', '', paragraphs[j]).strip().lower()
                if p_clean == heading_lower:
                    found_idx = j
                    break
            if found_idx is None:
                aligned_sections[heading] = ""
                continue
            # Find next heading
            end_idx = num_paragraphs
            for next_heading in ref_headings[i+1:]:
                next_lower = next_heading.lower()
                for j in range(found_idx+1, num_paragraphs):
                    p_clean = re.sub(r'^#+\s*', '', paragraphs[j]).strip().lower()
                    if p_clean == next_lower:
                        end_idx = j
                        break
                if end_idx != num_paragraphs:
                    break
            section_text = "\n\n".join(paragraphs[found_idx+1:end_idx]).strip()
            aligned_sections[heading] = section_text
            start_idx = end_idx

        return aligned_sections

    # -------------------------
    # GPT-based comparison
    # -------------------------
    def compare_section_with_gpt(self, ref_heading: str, ref_text: str, con_text: str) -> dict:
        section_label = ref_heading
        ref_excerpt = (ref_text or "").strip()[:3000]
        con_excerpt = (con_text or "").strip()[:3000]

        prompt = f"""
You are a contract comparison assistant.

Compare the meaning of the following two sections:

Reference heading: {ref_heading}
Reference text:
\"\"\"{ref_excerpt}\"\"\" 

Contract text:
\"\"\"{con_excerpt}\"\"\" 

Instructions:
- Ignore formatting differences, punctuation, spacing, and trivial words like "Internal", 'Intetteahal',"Inteteahal", "Draft", "Confidential".
- Only detect meaningful semantic differences.
- Mention Contract text as contract document and reference text as FieldGlass document
- Return strictly JSON:

{{
  "section": "{ref_heading}",
  "status": "Match" or "Modified",
  "difference_summary": "short summary of the difference"
}}
"""

        start_time = time.time()
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a precise and helpful contract comparison assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=self.temperature,
            max_tokens=400
        )
        content = response.choices[0].message.content
        try:
            json_text = re.search(r'\{.*\}', content, re.DOTALL)
            if json_text:
                result_json = json.loads(json_text.group())
            else:
                result_json = {
                    "section": section_label,
                    "status": "Modified",
                    "difference_summary": content.replace("\n", " ")[:400]
                }
        except json.JSONDecodeError:
            result_json = {
                "section": section_label,
                "status": "Modified",
                "difference_summary": content.replace("\n", " ")[:400]
            }

        return result_json

    # -------------------------
    # Main validation method
    # -------------------------
    def validate_service_description(self, contract_md_text: str) -> Dict[str, Any]:
        """
        Compare contract service description with the embedded Fieldglass reference.

        Returns:
            {
                "validation_status": "Correct" or "Mismatch" or "Missing",
                "modified_sections": [
                    {"section": "...", "status": "Modified", "difference_summary": "..."},
                    ...
                ]
            }
        """
        # First check if Attachment 1: Service Description exists
        if not re.search(r"attachment\s*1[^a-zA-Z0-9]*service\s*description", contract_md_text, flags=re.I):
            return {
                "validation_status": "Missing",
                "modified_sections": []
            }

        # Extract reference and contract sections
        ref_sections = self.extract_reference_sections()
        ref_headings = [h for h, _ in ref_sections]
        contract_sections = self.extract_contract_sections(contract_md_text, ref_headings)

        modified_results = []

        for heading, ref_text in ref_sections:
            con_text = contract_sections.get(heading, "")
            if not con_text.strip():
                continue

            parsed = self.compare_section_with_gpt(heading, ref_text, con_text)
            if parsed.get("status") == "Modified":
                modified_results.append(parsed)

        validation_status = "Correct" if not modified_results else "Mismatch"

        return {
            "validation_status": validation_status,
            "modified_sections": modified_results
        }

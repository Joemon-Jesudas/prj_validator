import os
import requests
from urllib.parse import quote


def safe_quote(value):
    if value is None:
        return ""
    return quote(str(value))


def extract_value(field):
    """
    Converts ServiceNow field to clean string:
    - {'display_value': 'John', 'value': 'abcd'} → "John"
    - "John" → "John"
    - None → ""
    """
    if isinstance(field, dict):
        return field.get("display_value") or field.get("value") or ""
    return str(field) if field else ""


class ServiceNowClient:

    def __init__(self):
        self.instance = os.getenv("SERVICENOW_INSTANCE")
        self.user = os.getenv("SERVICENOW_USER")
        self.password = os.getenv("SERVICENOW_PASS")

        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    def get_record(self, request_number: str):
        q = safe_quote(request_number)

        url = (
            f"{self.instance}/api/now/table/u_project_validator"
            f"?sysparm_query=u_number={q}"
            f"&sysparm_limit=1&sysparm_display_value=all"
        )

        resp = requests.get(url, auth=(self.user, self.password), headers=self.headers)

        if resp.status_code != 200:
            raise RuntimeError(resp.text)

        result = resp.json().get("result", [])
        if not result:
            return None, None

        raw = result[0]

        # Normalize sys_id
        sys_id = extract_value(raw.get("sys_id"))

        # CLEAN METADATA (Unpacked + string-only)
        cleaned = {
            "request_number": extract_value(raw.get("u_number")),
            "pr_requestor_number": extract_value(raw.get("u_pr_requestor_number")),
            "pr_start_date": extract_value(raw.get("u_pr_start_date")),
            "requested_for": extract_value(raw.get("u_requested_for")),
            "requested_by": extract_value(raw.get("u_requested_by")),
            "supplier_id": extract_value(raw.get("u_supplier_id")),
            "fieldglass_checklist_id": extract_value(raw.get("u_fieldglass_checklist_id")),
            "fieldglass_checklist_approval_date": extract_value(raw.get("u_fieldglass_checklist_approval_date")),
            "remuneration_details": extract_value(raw.get("u_remuneration_details")),
            "sys_id": sys_id
        }

        return raw, cleaned

    def download_attachment_bytes(self, record_sys_id):
        q = safe_quote(record_sys_id)

        meta_url = f"{self.instance}/api/now/attachment?sysparm_query=table_sys_id={q}&sysparm_limit=1"

        meta = requests.get(meta_url, auth=(self.user, self.password), headers=self.headers)

        if meta.status_code != 200:
            raise RuntimeError(meta.text)

        attachments = meta.json().get("result", [])
        if not attachments:
            return None

        dl_url = attachments[0]["download_link"]

        file_resp = requests.get(dl_url, auth=(self.user, self.password))

        if file_resp.status_code != 200:
            raise RuntimeError("Failed to download attachment")

        return {
            "file_name": attachments[0]["file_name"],
            "bytes": file_resp.content
        }

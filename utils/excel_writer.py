
import pandas as pd
import io

def convert_validation_to_excel(result_json: dict):
    """
    Converts the JSON result into a standardized Excel sheet:
    Columns: validation_item | extracted_value | status
    """
    rows = []

    def add_row(item, value, status):
        rows.append({
            "validation_item": item,
            "extracted_value": value,
            "status": status
        })

    # Flatten all validation items
    def process_section(section_name, section_data):
        if section_data is None:
            return

        for key, value in section_data.items():
            if isinstance(value, dict):
                # Nested dictionary (take status + meaningful values)
                status = value.get("validation_status") or value.get("status") or "N/A"
                extracted = str({k: v for k, v in value.items() if k not in ["validation_status", "status"]})
                add_row(f"{section_name}.{key}", extracted, status)

            else:
                # Normal string values
                add_row(f"{section_name}.{key}", str(value), "N/A")

    for section, data in result_json.items():
        process_section(section, data)

    df = pd.DataFrame(rows)

    # Convert to Excel in-memory
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Validation")

    buffer.seek(0)
    return buffer

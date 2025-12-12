def get_status_style(status: str) -> str:
    """Map validation status to CSS class."""
    if status in ["Correct", "Found"]:
        return "validation-correct"
    if status in ["Mismatch", "Not found"]:
        return "validation-mismatch"
    return "validation-missing"
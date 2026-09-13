from src.utils.exceptions import ValidationError

ALLOWED_CATEGORIES = {"Sales", "Support", "Billing", "Technical", "Other"}
ALLOWED_PRIORITIES = {"Low", "Medium", "High", "Urgent"}
ALLOWED_OWNERS = {"Sales Team", "Client Success", "Finance", "Engineering"}

def validate_classification(result: dict):
    if not isinstance(result, dict):
        raise ValidationError("Classification result is not a dictionary")
    
    category = result.get("category")
    if category not in ALLOWED_CATEGORIES:
        raise ValidationError(f"Invalid category: '{category}'. Expected one of {ALLOWED_CATEGORIES}")

    priority = result.get("priority")
    if priority not in ALLOWED_PRIORITIES:
        raise ValidationError(f"Invalid priority: '{priority}'. Expected one of {ALLOWED_PRIORITIES}")

    owner = result.get("owner")
    if owner not in ALLOWED_OWNERS:
        raise ValidationError(f"Invalid owner: '{owner}'. Expected one of {ALLOWED_OWNERS}")

    if not result.get("summary") or not isinstance(result.get("summary"), str):
        raise ValidationError("Missing or invalid summary")

    if not result.get("priority_reason") or not isinstance(result.get("priority_reason"), str):
        raise ValidationError("Missing or invalid priority_reason")

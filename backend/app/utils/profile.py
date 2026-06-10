import re


def derive_name_from_email(email: str) -> str:
    match = re.match(r"^([^@]+)", email.strip())
    if match and match.group(1).strip():
        return match.group(1).strip()
    return email.strip()

"""Mascheramento superficiale per demo, NON anonimizzazione irreversibile."""
import re


def mask_contacts(text: str) -> str:
    text = re.sub(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", "[EMAIL]", text)
    text = re.sub(r"(?<!\w)(?:\+39[ -]?)?(?:\d[ -]?){9,11}(?!\w)", "[TELEFONO]", text)
    return text

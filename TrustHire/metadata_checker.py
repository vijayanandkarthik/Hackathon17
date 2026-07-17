from pypdf import PdfReader
from datetime import datetime

SUSPICIOUS_TOOLS = ["photoshop", "microsoft word", "canva", "gimp", "paint", "illustrator"]

def _parse_pdf_date(date_str):
    if not date_str:
        return None
    try:
        cleaned = date_str.replace("D:", "").split("+")[0].split("-")[0].split("Z")[0]
        return datetime.strptime(cleaned[:14], "%Y%m%d%H%M%S")
    except Exception:
        return None

def check_pdf_metadata(pdf_path):
    flags = []
    try:
        reader = PdfReader(pdf_path)
        meta = reader.metadata
    except Exception:
        flags.append("Could not read PDF metadata (file may be corrupted or non-standard)")
        return flags

    if not meta:
        flags.append("No metadata found in PDF — unusual for a system-issued certificate")
        return flags

    creation_date = _parse_pdf_date(meta.get("/CreationDate"))
    mod_date = _parse_pdf_date(meta.get("/ModDate"))

    if creation_date and mod_date:
        diff_seconds = (mod_date - creation_date).total_seconds()
        if diff_seconds > 60:
            flags.append(f"File was modified {int(diff_seconds)} seconds after creation — possible post-issue editing")

    producer = str(meta.get("/Producer", "")).lower()
    creator = str(meta.get("/Creator", "")).lower()
    for tool in SUSPICIOUS_TOOLS:
        if tool in producer or tool in creator:
            flags.append(f"PDF shows signs of editing with '{tool.title()}' — uncommon for official certificates")
            break

    return flags
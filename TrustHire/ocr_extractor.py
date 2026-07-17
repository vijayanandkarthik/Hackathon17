import re
import cv2
import numpy as np
import pytesseract
from pdf2image import convert_from_path

def preprocess_image(image_path_or_array):
    if isinstance(image_path_or_array, str):
        img = cv2.imread(image_path_or_array)
    else:
        img = image_path_or_array
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh

def extract_text_from_image(image_path):
    processed = preprocess_image(image_path)
    return pytesseract.image_to_string(processed)

def extract_text_from_pdf(pdf_path):
    pages = convert_from_path(pdf_path, dpi=300)
    full_text = ""
    for page in pages:
        page_array = cv2.cvtColor(np.array(page), cv2.COLOR_RGB2BGR)
        processed = preprocess_image(page_array)
        full_text += pytesseract.image_to_string(processed) + "\n"
    return full_text

def extract_text(file_path):
    if file_path.lower().endswith(".pdf"):
        return extract_text_from_pdf(file_path)
    return extract_text_from_image(file_path)

def extract_fields(raw_text):
    text = raw_text.replace("\n", " ")
    fields = {"name": None, "course": None, "cert_id": None, "date": None, "raw_text": raw_text.strip()}

    cert_id_match = re.search(r"(?:certificate\s*(?:id|no|number)|cert\s*(?:id|no))[:\s\-]*([A-Za-z0-9\-\/]{4,25})", text, re.IGNORECASE)
    if cert_id_match:
        fields["cert_id"] = cert_id_match.group(1).strip()

    name_match = re.search(r"certify that\s+([A-Z][A-Za-z\.\s]{2,40}?)(?:\s+has|\s+of|\s+from|\s+successfully)", text, re.IGNORECASE)
    if name_match:
        fields["name"] = name_match.group(1).strip()

    course_match = re.search(r"(?:completing|completed|for the course|internship in|course on)\s+(?:the\s+)?(?:course\s+)?(?:on\s+)?[\"']?([A-Za-z0-9 \-,&]{4,60}?)[\"']?(?:\s+with|\s+offered|\s+during|\.|,|\n)", text, re.IGNORECASE)
    if course_match:
        fields["course"] = course_match.group(1).strip()

    date_match = re.search(r"\b(\d{1,2}[\/\-\s](?:\d{1,2}|[A-Za-z]{3,9})[\/\-\s]\d{2,4})\b", text)
    if date_match:
        fields["date"] = date_match.group(1).strip()

    return fields

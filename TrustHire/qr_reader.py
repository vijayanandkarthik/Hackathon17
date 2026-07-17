import cv2
import numpy as np
from pyzbar.pyzbar import decode
from pdf2image import convert_from_path

def read_qr_from_image(image_path_or_array):
    if isinstance(image_path_or_array, str):
        img = cv2.imread(image_path_or_array)
    else:
        img = image_path_or_array
    decoded_objects = decode(img)
    results = []
    for obj in decoded_objects:
        try:
            results.append(obj.data.decode("utf-8"))
        except Exception:
            continue
    return results

def read_qr_from_pdf(pdf_path):
    pages = convert_from_path(pdf_path, dpi=300)
    all_results = []
    for page in pages:
        page_array = cv2.cvtColor(np.array(page), cv2.COLOR_RGB2BGR)
        all_results.extend(read_qr_from_image(page_array))
    return all_results

def read_qr(file_path):
    if file_path.lower().endswith(".pdf"):
        return read_qr_from_pdf(file_path)
    return read_qr_from_image(file_path)

def is_verification_link(qr_value):
    return isinstance(qr_value, str) and qr_value.strip().lower().startswith(("http://", "https://"))
from fuzzywuzzy import fuzz

FIELD_WEIGHTS = {"name": 35, "course": 25, "cert_id": 30, "date": 10}
MATCH_THRESHOLD = 85
PARTIAL_THRESHOLD = 60

def compare_field(claimed, extracted):
    if not claimed or not extracted:
        return 0, "missing"
    score = fuzz.token_sort_ratio(str(claimed).lower().strip(), str(extracted).lower().strip())
    if score >= MATCH_THRESHOLD:
        status = "match"
    elif score >= PARTIAL_THRESHOLD:
        status = "partial"
    else:
        status = "mismatch"
    return score, status

def compute_trust_score(claimed_details, extracted_fields, qr_verified=None, metadata_flags=None):
    breakdown = {}
    weighted_total = 0
    max_possible = sum(FIELD_WEIGHTS.values())

    for field, weight in FIELD_WEIGHTS.items():
        claimed_val = claimed_details.get(field)
        extracted_val = extracted_fields.get(field)
        score, status = compare_field(claimed_val, extracted_val)
        breakdown[field] = {"claimed": claimed_val, "extracted": extracted_val, "similarity": score, "status": status}
        weighted_total += (score / 100) * weight

    base_score = round((weighted_total / max_possible) * 100)

    qr_adjustment = 10 if qr_verified is True else -15 if qr_verified is False else -5
    metadata_flags = metadata_flags or []
    metadata_adjustment = -10 * len(metadata_flags)

    final_score = max(0, min(100, base_score + qr_adjustment + metadata_adjustment))

    if final_score >= 80:
        verdict, emoji = "Verified", "✅"
    elif final_score >= 50:
        verdict, emoji = "Needs Review", "⚠️"
    else:
        verdict, emoji = "High Risk", "❌"

    return {"trust_score": final_score, "verdict": verdict, "verdict_emoji": emoji,
            "field_breakdown": breakdown, "qr_verified": qr_verified, "metadata_flags": metadata_flags}
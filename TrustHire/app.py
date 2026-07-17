"""
app.py
------
Streamlit front-end for the Skill Certificate Verifier.
Single-check mode: user uploads one certificate + claimed details,
gets back a Trust Score with a field-by-field breakdown.
"""

import streamlit as st
import tempfile
import os

from ocr_extractor import extract_text, extract_fields
from matcher import compute_trust_score
from qr_reader import read_qr, is_verification_link
from metadata_checker import check_pdf_metadata

st.set_page_config(page_title="Skill Certificate Verifier", page_icon="🎓", layout="centered")

st.title("🎓 Skill Certificate Verifier")
st.caption("Upload a certificate and enter the claimed details to check for mismatches or fraud risk.")

st.divider()

# ---------- Input form ----------
col1, col2 = st.columns(2)

with col1:
    claimed_name = st.text_input("Claimed Name")
    claimed_course = st.text_input("Claimed Course / Internship Title")

with col2:
    claimed_cert_id = st.text_input("Claimed Certificate ID (optional)")
    claimed_date = st.text_input("Claimed Completion Date (optional)")

uploaded_file = st.file_uploader(
    "Upload Certificate (PDF, JPG, or PNG)",
    type=["pdf", "jpg", "jpeg", "png"]
)

verify_clicked = st.button("🔍 Verify Certificate", type="primary", use_container_width=True)

st.divider()

# ---------- Verification logic ----------
if verify_clicked:
    if not uploaded_file:
        st.error("Please upload a certificate file first.")
    elif not claimed_name or not claimed_course:
        st.error("Please fill in at least the claimed name and course.")
    else:
        with st.spinner("Reading certificate and comparing details..."):
            # Save uploaded file to a temp path so OCR/QR/metadata functions can read it
            suffix = os.path.splitext(uploaded_file.name)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded_file.getbuffer())
                tmp_path = tmp.name

            try:
                # OCR extraction
                raw_text = extract_text(tmp_path)
                extracted = extract_fields(raw_text)

                # QR code check
                qr_results = read_qr(tmp_path)
                verify_link = next((r for r in qr_results if is_verification_link(r)), None)
                qr_verified = True if verify_link else None

                # PDF metadata check (only applies to PDF uploads)
                metadata_flags = []
                if tmp_path.lower().endswith(".pdf"):
                    metadata_flags = check_pdf_metadata(tmp_path)

                claimed_details = {
                    "name": claimed_name,
                    "course": claimed_course,
                    "cert_id": claimed_cert_id,
                    "date": claimed_date,
                }

                result = compute_trust_score(
                    claimed_details, extracted, qr_verified=qr_verified, metadata_flags=metadata_flags
                )
            finally:
                os.remove(tmp_path)

        # ---------- Results display ----------
        score = result["trust_score"]
        st.subheader(f"{result['verdict_emoji']} Trust Score: {score}/100 — {result['verdict']}")
        st.progress(score / 100)

        st.markdown("### Field-by-field comparison")
        for field, data in result["field_breakdown"].items():
            status_icon = {"match": "✅", "partial": "⚠️", "mismatch": "❌", "missing": "❌"}[data["status"]]
            st.markdown(
                f"{status_icon} **{field.replace('_', ' ').title()}** — {data['similarity']}% similarity  \n"
                f"&nbsp;&nbsp;&nbsp;&nbsp;Claimed: `{data['claimed'] or '—'}`  \n"
                f"&nbsp;&nbsp;&nbsp;&nbsp;Extracted: `{data['extracted'] or '—'}`"
            )

        st.markdown("### QR code check")
        if verify_link:
            st.success("✅ QR code found — verification link detected")
            st.markdown(f"[🔗 Verify with issuer]({verify_link})")
        else:
            st.info("ℹ️ No QR code found on this certificate — cannot auto-verify via issuer link.")

        st.markdown("### PDF metadata check")
        if uploaded_file.name.lower().endswith(".pdf"):
            if result["metadata_flags"]:
                for flag in result["metadata_flags"]:
                    st.warning(f"⚠️ {flag}")
            else:
                st.success("✅ No metadata red flags found.")
        else:
            st.info("ℹ️ Metadata check only applies to PDF uploads.")

        with st.expander("📄 View raw OCR text extracted from certificate"):
            st.text(extracted.get("raw_text", "No text extracted."))

        if score < 80:
            st.warning("This certificate needs manual review before being accepted.")
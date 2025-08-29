import io
import time
import requests
import pandas as pd
import streamlit as st

# --- Config ---
API_URL = "http://127.0.0.1:8000/upload-calendar/"

st.set_page_config(
    page_title="BondSense AI - Excel Uploader", page_icon="📄", layout="centered"
)
st.title("📄 Upload Excel → FastAPI")
st.caption("Send an .xlsx file to the API for parsing & DB insert.")

# --- File uploader ---
uploaded = st.file_uploader("Choose Excel file (.xlsx)", type=["xlsx"])
sheet_name = st.text_input(
    "Sheet name (optional)",
    value="",
    help="Leave blank it System will update.",
)

# --- Preview + validation ---
df_preview_container = st.empty()


def read_preview(file_bytes: bytes, sheet: str | None) -> pd.DataFrame | None:
    try:
        with io.BytesIO(file_bytes) as bio:
            if sheet and sheet.strip():
                return pd.read_excel(bio, sheet_name=sheet.strip())
            return pd.read_excel(bio)
    except Exception as e:
        st.warning(f"Could not read Excel preview: {e}")
        return None


if uploaded:
    st.info(f"Selected: **{uploaded.name}** ({uploaded.size} bytes)")
    preview_df = read_preview(
        uploaded.read(), sheet_name if sheet_name.strip() else None
    )
    uploaded.seek(0)  # reset stream for actual upload
    if preview_df is not None:
        st.subheader("Preview (first 10 rows)")
        st.dataframe(preview_df.head(10), width="stretch")

# --- Upload button ---
col1, col2 = st.columns([1, 3])
with col1:
    upload_btn = st.button("Upload to API", type="primary", disabled=uploaded is None)

status = st.empty()


def post_excel_to_api(file_obj) -> dict:
    # Use requests to send multipart/form-data
    files = {
        "file": (
            uploaded.name,
            file_obj,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }
    # Retry logic
    last_exc = None
    for attempt in range(1, 4):
        try:
            resp = requests.post(API_URL, files=files, timeout=60)
            if resp.headers.get("content-type", "").startswith("application/json"):
                return {
                    "status_code": resp.status_code,
                    "json": resp.json(),
                }
            return {"status_code": resp.status_code, "text": resp.text}
        except requests.RequestException as e:
            last_exc = e
            time.sleep(0.8 * attempt)  # backoff
    raise RuntimeError(f"Upload failed after retries: {last_exc}")


if upload_btn:
    if not uploaded:
        status.error("Please select a file first.")
    else:
        with st.spinner("Uploading to API…"):
            try:
                # IMPORTANT: read bytes anew for the real upload
                file_bytes = uploaded.read()
                uploaded.seek(0)
                result = post_excel_to_api(io.BytesIO(file_bytes))
                if result.get("ok"):
                    st.success(f"Success (HTTP {result['status_code']})")
                    payload = result.get("json") or {}
                    st.json(payload)
                else:
                    st.error(f"API Error (HTTP {result['status_code']})")
                    if "json" in result:
                        st.json(result["json"])
                    else:
                        st.code(result.get("text", ""), language="bash")
            finally:
                uploaded.seek(0)  # reset in case you want to preview again

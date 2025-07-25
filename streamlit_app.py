import streamlit as st
import pandas as pd
import re
import json
from io import StringIO

st.set_page_config(page_title="Dictionary‑Based Text Classification", page_icon="📄", layout="wide")

st.title("📄 Dictionary‑Based Text Classification")
st.markdown(
    """
Upload a **CSV** file containing a **Statement** column, tweak the keyword dictionaries
on the left, and download a CSV with an extra **labels** column.
    """
)

# ---------------------------------------------------------------------------
# 1  Define & edit the dictionaries ─────────────────────────────────────────
# ---------------------------------------------------------------------------

def default_dictionaries():
    """Return the starter keyword dictionaries."""
    return {
        "urgency_marketing": [
            "limited", "limited time", "limited run", "limited edition", "order now",
            "last chance", "hurry", "while supplies last", "before they're gone",
            "selling out", "selling fast", "act now", "don't wait", "today only",
            "expires soon", "final hours", "almost gone",
        ],
        "exclusive_marketing": [
            "exclusive", "exclusively", "exclusive offer", "exclusive deal",
            "members only", "vip", "special access", "invitation only",
            "premium", "privileged", "limited access", "select customers",
            "insider", "private sale", "early access",
        ],
    }

st.sidebar.header("🔧 Keyword Dictionaries (JSON)")

# Show editable JSON text area with defaults
raw_dict_json = st.sidebar.text_area(
    label="Edit the dictionaries below (JSON format). Keys are labels; values are lists of keywords.",
    value=json.dumps(default_dictionaries(), indent=2),
    height=400,
)

# Parse the JSON safely
try:
    user_dict = json.loads(raw_dict_json)
    # Ensure every value is a list (convert single strings → list)
    for k, v in user_dict.items():
        if isinstance(v, str):
            user_dict[k] = [v]
    dict_error = None
except Exception as e:
    user_dict = {}
    dict_error = str(e)

if dict_error:
    st.sidebar.error(f"❌ JSON Error: {dict_error}")

# ---------------------------------------------------------------------------
# 2  Helper functions ───────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

def compile_patterns(dictionaries):
    """Compile regex patterns for each keyword respecting word boundaries."""
    compiled = {}
    for label, vocab in dictionaries.items():
        patterns = []
        for term in vocab:
            # If term contains whitespace, compile as a plain substring (case‑insensitive)
            if " " in term:
                patterns.append(re.compile(re.escape(term), flags=re.I))
            else:
                patterns.append(re.compile(rf"\b{re.escape(term)}\b", flags=re.I))
        compiled[label] = patterns
    return compiled


def classify_text(text, compiled):
    """Return a comma‑separated list of dictionary labels found in *text*."""
    if pd.isna(text):
        return ""
    hits = [label for label, patterns in compiled.items() if any(p.search(text) for p in patterns)]
    return ",".join(hits)


# ---------------------------------------------------------------------------
# 3  Upload CSV ─────────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------
uploaded_file = st.file_uploader("📤 Upload your CSV", type=["csv"])

if uploaded_file is not None and not dict_error:
    # Read the CSV into a DataFrame
    try:
        df = pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"❌ Could not read CSV: {e}")
        st.stop()

    if "Statement" not in df.columns:
        st.error("❌ Your CSV must contain a 'Statement' column.")
        st.stop()

    # Compile dictionaries
    compiled = compile_patterns({k: set(v) for k, v in user_dict.items()})

    # Classify
    with st.spinner("Classifying…"):
        df["labels"] = df["Statement"].astype(str).apply(lambda t: classify_text(t, compiled))

    st.success("✅ Classification complete!")

    # Show a preview
    st.subheader("🔍 Preview of Results")
    st.dataframe(df.head(50), use_container_width=True)

    # Download button for full CSV
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download classified_output.csv",
        data=csv_bytes,
        file_name="classified_output.csv",
        mime="text/csv",
    )

    # Show dictionary stats
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Dictionary Stats")
    for label, vocab in user_dict.items():
        st.sidebar.write(f"- **{label}**: {len(vocab)} keywords")

elif uploaded_file is None:
    st.info("👈 Upload a CSV from the sidebar to begin.")

import streamlit as st
import requests

API_BASE = "http://localhost:8000"

st.set_page_config(page_title="MCP Regulation Manager", layout="wide")
st.title("📜 MCP Regulation Manager + Violation Checker")

# --- Cache Helpers ---
@st.cache_data(ttl=5)
def fetch_regulations():
    try:
        r = requests.get(f"{API_BASE}/get-regulations", timeout=5)
        return r.json() if r.ok else []
    except Exception as e:
        st.error(f"Failed to fetch regulations: {e}")
        return []

@st.cache_data(ttl=5)
def fetch_code_rules():
    try:
        r = requests.get(f"{API_BASE}/get-code-rules", timeout=5)
        return r.json() if r.ok else []
    except Exception as e:
        st.error(f"Failed to fetch code rules: {e}")
        return []

def add_regulation(regulation):
    try:
        r = requests.post(f"{API_BASE}/add-regulations", json=[regulation])
        if r.ok:
            st.success(f"✅ Added: {regulation['id']}")
            st.cache_data.clear()
        else:
            st.error(f"❌ {r.status_code}: {r.text}")
    except Exception as e:
        st.error(f"❌ Failed to add regulation: {e}")

def add_code_rule(code_rule):
    try:
        r = requests.post(f"{API_BASE}/add-code-rules", json=[code_rule])
        if r.ok:
            st.success(f"✅ Added: {code_rule['id']}")
            st.cache_data.clear()
        else:
            st.error(f"❌ {r.status_code}: {r.text}")
    except Exception as e:
        st.error(f"❌ Failed to add code rule: {e}")

def delete_regulation(reg_id):
    try:
        r = requests.delete(f"{API_BASE}/delete-regulations", params={"regulation_id": reg_id})
        if r.ok:
            st.success(f"🗑️ Deleted: {reg_id}")
            st.cache_data.clear()
        else:
            st.error(f"❌ {r.status_code}: {r.text}")
    except Exception as e:
        st.error(f"❌ Failed to delete: {e}")
        
def delete_code_rule(rule_id):
    try:
        r = requests.delete(f"{API_BASE}/delete-code-rules", params={"code_rule_id": rule_id})
        if r.ok:
            st.success(f"🗑️ Deleted: {rule_id}")
            st.cache_data.clear()
        else:
            st.error(f"❌ {r.status_code}: {r.text}")
    except Exception as e:
        st.error(f"❌ Failed to delete: {e}")

# ============================
# ➕ Regulation Manager Section
# ============================
with st.expander("⚙️ Manage Regulations", expanded=True):
    # --- Add Regulation Form ---
    with st.form("reg_form", clear_on_submit=True):
        col1, col2 = st.columns([1, 3])
        with col1:
            reg_id = st.text_input("Regulation ID", placeholder="e.g., GDPR-5")
        with col2:
            description = st.text_area("Description", placeholder="What should this regulation enforce?")
        if st.form_submit_button("Add"):
            if reg_id.strip() and description.strip():
                add_regulation({"id": reg_id.strip(), "description": description.strip()})
            else:
                st.warning("Please provide both ID and description.")

    # --- Display Regulations ---
    regulations = fetch_regulations()
    st.subheader("📄 Current Regulations")
    if not regulations:
        st.info("No regulations currently defined.")
    else:
        for reg in regulations:
            col1, col2, col3 = st.columns([1.5, 6, 1])
            col1.markdown(f"**{reg['id']}**")
            col2.markdown(reg["description"])
            if col3.button("🗑️", key=f"del_{reg['id']}"):
                delete_regulation(reg["id"])
                st.experimental_rerun()

# ============================
# 📝 Code Rules Manager Section
# ============================
st.markdown("---")
with st.expander("⚙️ Manage Code Rules", expanded=True):
    # --- Add Code Rule Form ---
    with st.form("rule_form", clear_on_submit=True):
        col1, col2 = st.columns([1, 3])
        with col1:
            rule_id = st.text_input("Code Rule ID", placeholder="e.g., PERF-1")
        with col2:
            rule_description = st.text_area("Description", placeholder="What should this code rule enforce?")
        if st.form_submit_button("Add"):
            if rule_id.strip() and rule_description.strip():
                add_code_rule({"id": rule_id.strip(), "description": rule_description.strip()})
            else:
                st.warning("Please provide both ID and description.")

    # --- Display Code Rules ---
    code_rules = fetch_code_rules()
    st.subheader("📄 Current Code Rules")
    if not code_rules:
        st.info("No code rules currently defined.")
    else:
        for rule in code_rules:
            col1, col2, col3 = st.columns([1.5, 6, 1])
            col1.markdown(f"**{rule['id']}**")
            col2.markdown(rule["description"])
            if col3.button("🗑️", key=f"del_rule_{rule['id']}"):
                delete_code_rule(rule["id"])
                st.experimental_rerun()

# ============================
# 🧪 Violation Checker Section
# ============================
st.markdown("---")
st.header("🧪 Check Violations in Uploaded Code")

uploaded_file = st.file_uploader("Upload a Python file to check:", type=["py"])

if uploaded_file and st.button("🚨 Run Check"):
    try:
        with st.spinner("Analyzing..."):
            files = {"file": uploaded_file}
            r = requests.post(f"{API_BASE}/check-violations", files=files)

        if r.ok:
            result = r.json()
            st.success(f"✅ `{result['filename']}` analyzed. Found {result['total_violations']} violation(s).")

            for v in result["violations"]:
                severity_color = {
                    "low": "🟢",
                    "medium": "🟠",
                    "high": "🔴"
                }.get(v["severity"], "⚪")
                st.markdown(
                    f"{severity_color} **[{v['regulation_id']}]** "
                    f"Lines `{v['start_line']}-{v['end_line']}`\n\n"
                    f"> {v['description']}"
                )
        else:
            st.error(f"❌ {r.status_code}: {r.text}")
    except Exception as e:
        st.error(f"❌ Failed to check violations: {e}")

import streamlit as st
import requests
import base64

API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="Galileo Indemnity",
    page_icon="logo.svg",
    layout="wide"
)

# Apply custom Inter font
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@100..900&display=swap');
html, body, [class*="st-"], [data-testid="stSidebar"] {
    font-family: 'Inter', sans-serif !important;
}
.container {
    display: flex;
}
.logo-text {
    font-weight:600 !important;
    font-size:44px !important;
    color: #644DF9 !important;
    margin-top: -20px !important;
}
/* targets all st.info / warning / error boxes */
div[role="alert"] {
    background-color: #E9E7FF !important;
    border-left: 4px solid #644DF9 !important;
    border: 1px solid #644DF9 !important; /* Corrected from 'border: #644DF9 !important;' */
}
/* For the form containers */
div[data-testid="stExpander"] div[data-testid="stForm"] {
    background-color: #f9f9f9;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 25px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
}

/* For each item card in the lists (rows created by st.columns after a subheader) */
div[data-testid="stExpander"] div[data-testid="stHorizontalBlock"]:not(div[data-testid="stForm"] div[data-testid="stHorizontalBlock"]) {
    background-color: #ffffff;
    border: 1px solid #e7e7e7;
    border-radius: 8px;
    padding: 15px;
    margin-bottom: 15px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    display: flex;
    align-items: center;
}

/* Adjust font size for expander labels */
div[data-testid="stExpander"] summary {
    font-size: 1.3em !important;
    font-weight: 600 !important;
}

/* Adjust font size for subheaders within expanders */
div[data-testid="stExpander"] h3 {
    font-size: 1.05em !important;
    font-weight: 500 !important;
    margin-top: 20px !important;
    margin-bottom: 15px !important;
}
</style>
""", unsafe_allow_html=True)

# load and base64-encode your SVG
svg = base64.b64encode(open("logo.svg", "rb").read()).decode()

st.sidebar.markdown(
    f"""
    <div style="text-align: center; width: 100%;">
      <img src="data:image/svg+xml;base64,{svg}" width="120" style="display: inline-block;" />
    </div>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    f"""
    <div class="container">
        <p class="logo-text">Galileo Indemnity</p>
    </div>
    """,
    unsafe_allow_html=True
)


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
    st.subheader("📋 Current Regulations")
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
    st.subheader("📋 Current Code Rules")
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
st.header("🧪 Check Code for Legal Violations and Code Rules")

uploaded_file = st.file_uploader("Upload a Python file to check:", type=["py"])

check_col1, check_col2 = st.columns(2)

check_regulations = check_col1.checkbox("Check Regulatory Violations", value=True)
check_code_rules = check_col2.checkbox("Check Code Violations", value=True)

if uploaded_file and st.button("🚨 Run Check", type="primary"):
    # Track total violations for summary
    total_violations = 0
    
    # Check Regulatory Violations
    if check_regulations:
        try:
            with st.spinner("Analyzing regulatory violations..."):
                files = {"file": uploaded_file}
                r = requests.post(f"{API_BASE}/check-violations", files=files)

            if r.ok:
                result = r.json()
                total_violations += result['total_violations']
                
                if result['total_violations'] > 0:
                    with st.expander(f"📋 Regulatory Violations ({result['total_violations']})", expanded=True):
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
                    st.success("No regulatory violations found! ✅")
            else:
                st.error(f"❌ Regulation check failed: {r.status_code}: {r.text}")
        except Exception as e:
            st.error(f"❌ Failed to check regulatory violations: {e}")

    # Check Code Rule Violations
    if check_code_rules:
        try:
            with st.spinner("Analyzing code rule violations..."):
                # Reset the file position for reuse
                uploaded_file.seek(0)
                files = {"file": uploaded_file}
                r = requests.post(f"{API_BASE}/check-code-violations", files=files)

            if r.ok:
                result = r.json()
                total_violations += result.get('total_violations', 0)
                
                if result.get('total_violations', 0) > 0:
                    with st.expander(f"🔍 Code Rule Violations ({result.get('total_violations', 0)})", expanded=True):
                        for v in result.get("violations", []):
                            severity_color = {
                                "low": "🟢",
                                "medium": "🟠",
                                "high": "🔴"
                            }.get(v.get("severity", "medium"), "⚪")
                            st.markdown(
                                f"{severity_color} **[{v.get('code_rule_id', 'UNKNOWN')}]** "
                                f"Lines `{v.get('start_line', 0)}-{v.get('end_line', 0)}`\n\n"
                                f"> {v.get('description', 'No description')}"
                            )
                else:
                    st.success("No code rule violations found! ✅")
            else:
                st.error(f"❌ Code rule check failed: {r.status_code}: {r.text}")
        except Exception as e:
            st.error(f"❌ Failed to check code rule violations: {e}")
    
    # Check for LLM Cost Analysis
    try:
        with st.spinner("Analyzing LLM cost..."):
            # Reset the file position for reuse
            uploaded_file.seek(0)
            files = {"file": uploaded_file}
            r = requests.post(f"{API_BASE}/check-cost", files=files)

        if r.ok:
            result = r.json()
            total_calls = result.get('total_calls', 0)
            
            if total_calls > 0:
                # Format the cost with 6 decimal places
                total_cost = "${:,.6f}".format(result.get('total_estimated_cost', 0))
                
                with st.expander(f"💰 LLM Cost Analysis - {total_cost} for {total_calls} calls", expanded=True):
                    for call in result.get("llm_calls", []):
                        call_cost = "${:,.6f}".format(call.get('estimated_cost', 0))
                        st.markdown(
                            f"**Model: {call.get('model', 'unknown')}** ({call.get('call_type', 'unknown')}) - {call_cost}\n\n"
                            f"Lines `{call.get('start_line', 0)}-{call.get('end_line', 0)}`\n\n"
                            f"• Input tokens: {call.get('estimated_input_tokens', 0):,}\n"
                            f"• Output tokens: {call.get('estimated_output_tokens', 0):,}\n\n"
                            f"> {call.get('description', 'No description')}"
                        )
                        st.markdown("---")
            else:
                st.info("No LLM API calls detected in this code.")
        else:
            st.warning(f"⚠️ Cost analysis not available: {r.status_code}")
    except Exception as e:
        st.warning(f"⚠️ Cost analysis failed: {e}")
    
    # Show final summary
    if total_violations > 0:
        st.warning(f"⚠️ Total violations found: {total_violations}")
    elif check_regulations or check_code_rules:
        st.success("✅ No violations found in the code!")

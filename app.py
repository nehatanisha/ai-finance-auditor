import streamlit as fancy_ui
import pandas as pd
from core.extractor import Invoice, Contract, extract_invoice_from_text, extract_text_from_pdf
from core.auditor import verify_billing

# 1. Page Configuration MUST be the first Streamlit command executed
fancy_ui.set_page_config(
    page_title="PulsePoint Finance Auditor", page_icon="📊", layout="wide")

# 2. Custom HTML/CSS theme styling configuration block
fancy_ui.markdown("""
    <style>
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    h1, h2, h3 {
        color: #58a6ff !important;
    }
    .stButton>button {
        background-color: #238636 !important;
        color: white !important;
        border-radius: 6px;
        border: none;
    }
    .stButton>button:hover {
        background-color: #2ea043 !important;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Initialize session state variables with clean fallback defaults
if "invoice_num" not in fancy_ui.session_state:
    fancy_ui.session_state["invoice_num"] = "INV-99821"
if "vendor_invoice" not in fancy_ui.session_state:
    fancy_ui.session_state["vendor_invoice"] = "Apex Logistics"
if "quantity" not in fancy_ui.session_state:
    fancy_ui.session_state["quantity"] = 120
if "total_charged" not in fancy_ui.session_state:
    fancy_ui.session_state["total_charged"] = 6500.0

# Initialize historical logging list in session memory
if "audit_history" not in fancy_ui.session_state:
    fancy_ui.session_state["audit_history"] = []

# --- MAIN CONTENT AREA ---

# --- STEP 1: AI AUTOMATED INGESTION SECTION ---
fancy_ui.header("🤖 AI Automated Invoice & Contract Extractor")
fancy_ui.markdown(
    "Drop your vendor invoice PDF document below to let the AI process it.")

# File uploader drag-and-drop container block
uploaded_pdf = fancy_ui.file_uploader(
    "Upload Vendor Invoice (PDF format)", type=["pdf"])

# If a file is uploaded, process it immediately!
if uploaded_pdf is not None:
    if fancy_ui.button("🧠 Extract and Process PDF Document", use_container_width=True):
        with fancy_ui.spinner("Extracting structural text from PDF layers..."):
            try:
                # 1. Strip the raw strings out of the uploaded PDF file (Page 1)
                extracted_raw_text = extract_text_from_pdf(uploaded_pdf)

                # 2. Feed that stripped text directly into your Groq AI function
                ai_extracted_invoice = extract_invoice_from_text(
                    extracted_raw_text)

                # 3. Stage results into session state so the sidebar updates automatically
                fancy_ui.session_state["invoice_num"] = ai_extracted_invoice.invoice_number
                fancy_ui.session_state["vendor_invoice"] = ai_extracted_invoice.vendor_name
                fancy_ui.session_state["quantity"] = ai_extracted_invoice.quantity_billed
                fancy_ui.session_state["total_charged"] = ai_extracted_invoice.final_amount

                fancy_ui.success(
                    "🎯 AI successfully parsed the PDF! Metrics are now staged in the sidebar.")
            except Exception as e:
                fancy_ui.error(f"Error handling document: {e}")

fancy_ui.markdown("---")

# --- SIDEBAR / DATA ENTRY ---
fancy_ui.sidebar.header("📝 Document Context Details")
fancy_ui.sidebar.markdown("Verify or adjust the document data fields below:")

# Core Input Form Fields synced dynamically with AI session memory data
invoice_num = fancy_ui.sidebar.text_input(
    "Invoice Number", value=fancy_ui.session_state.get("invoice_num"))
vendor_invoice = fancy_ui.sidebar.text_input(
    "Vendor Name (Invoice)", value=fancy_ui.session_state.get("vendor_invoice"))
quantity = fancy_ui.sidebar.number_input(
    "Quantity Billed", min_value=0, value=fancy_ui.session_state.get("quantity"), step=1)
total_charged = fancy_ui.sidebar.number_input(
    "Total Amount Billed ($)", min_value=0.0, value=fancy_ui.session_state.get("total_charged"), step=10.0)

fancy_ui.sidebar.markdown("---")
fancy_ui.sidebar.subheader("🔒 Legal Agreement Context")

# Static Baseline parameters for comparison rules
contract_id = fancy_ui.sidebar.text_input("Contract ID Reference", "CON-4401")
vendor_contract = fancy_ui.sidebar.text_input(
    "Vendor Name (Contract)", "Apex Logistics")
agreed_rate = fancy_ui.sidebar.number_input(
    "Agreed Rate Per Unit ($)", min_value=0.0, value=50.0, step=1.0)

# --- STEP 3: FINANCIAL AUDITING EXECUTION ENGINE ---
fancy_ui.subheader("🚀 Audit Reconciliation Verification")
fancy_ui.markdown(
    "Click the execution button to reconcile the invoice metrics against your legal agreement frameworks.")

if fancy_ui.button("Run Compliance Audit Matcher", type="primary", use_container_width=True):
    invoice_obj = Invoice(
        invoice_number=invoice_num,
        vendor_name=vendor_invoice,
        quantity_billed=int(quantity),
        unit_price_charged=float(
            total_charged / (quantity if quantity > 0 else 1)),
        total_tax=0.0,
        final_amount=float(total_charged),
        currency="USD"
    )

    contract_obj = Contract(
        contract_id=contract_id,
        vendor_name=vendor_contract,
        agreed_rate_per_unit=float(agreed_rate),
        currency="USD"
    )

    with fancy_ui.spinner("Reconciling database metrics..."):
        try:
            audit_logs = verify_billing(invoice_obj, contract_obj)

            # Prepare data variables to push into historical memory logs
            status_label = "🚨 Flagged Anomaly" if audit_logs["is_flagged"] else "✅ Cleared Pass"
            savings_tracked = audit_logs["overcharge_delta"] if audit_logs["is_flagged"] else 0.0

            # Record log entry dictionary snapshot
            new_log = {
                "Invoice ID": invoice_num,
                "Vendor Name": vendor_invoice,
                "Total Billed": f"${float(total_charged):,.2f}",
                "Audit Status": status_label,
                "Leakage Saved": f"${savings_tracked:,.2f}"
            }

            # Append entry into active live state context list
            fancy_ui.session_state["audit_history"].append(new_log)

            # Display the result cards neatly on the interface dashboard
            if audit_logs["is_flagged"]:
                fancy_ui.error(
                    f"🚨 Billing Anomaly Detected! Flag: {audit_logs['reason']}")

                fancy_ui.metric(label="Calculated Expected Amount",
                                value=f"${audit_logs['expected_amount']:.2f}")
                fancy_ui.metric(label="Overcharge Discrepancy Amount",
                                value=f"${audit_logs['overcharge_delta']:.2f}", delta=f"${audit_logs['overcharge_delta']:.2f}", delta_color="inverse")

                fancy_ui.markdown("---")
                fancy_ui.subheader("✉️ Generated Vendor Dispute Email")

                from core.extractor import generate_dispute_email
                draft_text = generate_dispute_email(
                    invoice_num=invoice_num,
                    vendor_name=vendor_invoice,
                    contract_id=contract_id,
                    expected=audit_logs['expected_amount'],
                    billed=float(total_charged),
                    delta=audit_logs['overcharge_delta']
                )
                fancy_ui.code(draft_text, language="text")

            else:
                fancy_ui.success(
                    "✅ Audit Compliance Cleared! The billed amounts perfectly match the legal rate parameters.")
        except Exception as e:
            fancy_ui.error(f"Execution Error: {e}")

# --- STEP 4: HISTORICAL AUDIT DASHBOARD LOG ---
fancy_ui.markdown("---")
fancy_ui.subheader("📈 Session Audit History & Metrics Tracking")

if fancy_ui.session_state["audit_history"]:
    # Convert history lists into an optimized Pandas DataFrame layout
    history_df = pd.DataFrame(fancy_ui.session_state["audit_history"])

    # Display the structured data matrix as a beautiful interactive table interface
    fancy_ui.dataframe(history_df, use_container_width=True, hide_index=True)

    # Simple button control to wipe active state logs clean if needed
    if fancy_ui.button("🗑️ Clear Log History"):
        fancy_ui.session_state["audit_history"] = []
        fancy_ui.rerun()
else:
    fancy_ui.info(
        "No audit executions processed during this session yet. Staged audit history will build up automatically down here.")

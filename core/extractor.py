import fitz  # This is PyMuPDF
import os
import json
from pydantic import BaseModel
from groq import Groq

# 1. PDF Text Extraction Helper Function


def extract_text_from_pdf(pdf_file) -> str:
    """Reads an uploaded PDF file but only pulls text from the first page to keep within token limits."""
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")

    # Check if the document has any pages
    if len(doc) > 0:
        # Get text ONLY from the first page (index 0)
        first_page_text = doc[0].get_text() + "\n"
        return first_page_text.strip()

    return ""

# 2. Schema Definitions


class PurchaseOrder(BaseModel):
    po_number: str
    vendor_name: str
    total_amount: float
    currency: str


class Contract(BaseModel):
    contract_id: str
    vendor_name: str
    agreed_rate_per_unit: float
    currency: str


class Invoice(BaseModel):
    invoice_number: str
    vendor_name: str
    quantity_billed: int
    unit_price_charged: float
    total_tax: float
    final_amount: float
    currency: str

# 3. Main AI Agent Extraction Function


def extract_invoice_from_text(raw_text: str) -> Invoice:
    """Passes unstructured string data into Llama 3.3 via Groq, forcing it to parse details into our Invoice schema."""

    # 🛑 Safety check: If the text is empty (scanned image / broken read), return an empty structure immediately
    if not raw_text or len(raw_text.strip()) < 5:
        return Invoice(
            invoice_number="NOT_FOUND",
            vendor_name="No text found in PDF layers",
            quantity_billed=0,
            unit_price_charged=0.0,
            total_tax=0.0,
            final_amount=0.0,
            currency="USD"
        )

    # 🔒 SAFE: Look inside your computer's secret environment variables for the password key.
    # The actual password string is gone from this file!
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        # If your terminal forgets the password, it will gracefully stop instead of crashing
        return Invoice(
            invoice_number="ERROR",
            vendor_name="Missing GROQ_API_KEY in system environment settings",
            quantity_billed=0,
            unit_price_charged=0.0,
            total_tax=0.0,
            final_amount=0.0,
            currency="USD"
        )

    client = Groq(api_key=api_key)

    system_instruction = (
        "You are an expert financial auditor extraction agent. Your job is to read unstructured text "
        "from an invoice or vendor email, identify the key metrics, and return them as a strict JSON object.\n"
        "Your response must perfectly match these keys:\n"
        '{"invoice_number": string, "vendor_name": string, "quantity_billed": integer, "unit_price_charged": float, "total_tax": float, "final_amount": float, "currency": string}\n'
        "Do not include any markdown styling, conversational pleasantries, formatting fences, or commentary outside the raw JSON structure."
    )

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Extract metrics from this document text:\n\n{raw_text}"}
            ],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"},
            temperature=0.1
        )

        raw_json_output = chat_completion.choices[0].message.content.strip()

        # Clean up any potential markdown backticks ```json if the model accidentally includes them
        if raw_json_output.startswith("```"):
            raw_json_output = raw_json_output.split("```")[1]
            if raw_json_output.startswith("json"):
                raw_json_output = raw_json_output[4:]

        parsed_data = json.loads(raw_json_output)

    except Exception as e:
        # Fallback dictionary if json decode fails or API drops connection
        parsed_data = {}

    return Invoice(
        invoice_number=str(parsed_data.get("invoice_number", "UNKNOWN")),
        vendor_name=str(parsed_data.get("vendor_name", "UNKNOWN")),
        quantity_billed=int(parsed_data.get("quantity_billed", 0)),
        unit_price_charged=float(parsed_data.get("unit_price_charged", 0.0)),
        total_tax=float(parsed_data.get("total_tax", 0.0)),
        final_amount=float(parsed_data.get("final_amount", 0.0)),
        currency=str(parsed_data.get("currency", "USD"))
    )


def generate_dispute_email(invoice_num, vendor_name, contract_id, expected, billed, delta) -> str:
    """Generates a professional email template to dispute an overcharge."""
    email_template = f"""
Subject: DISPUTE: Billing Discrepancy on Invoice {invoice_num} / Contract {contract_id}

Dear Accounts Payable / Billing Team,

I hope this email finds you well. 

We recently received and processed Invoice {invoice_num} from your team regarding services provided by {vendor_name}. Upon reconciling this document against our active contract agreement ({contract_id}), we noticed a billing variance.

Here is the breakdown of the discrepancy detected by our automated systems:
- Actual Billed Amount: ${billed:,.2f}
- Contractual Expected Amount: ${expected:,.2f}
- Overcharge Discrepancy: ${delta:,.2f}

Per our legal rate terms under {contract_id}, the calculated expected total does not match the figure provided on your invoice. Could you please review this statement on your end and issue a corrected or revised invoice reflecting the contracted pricing?

Thank you for your prompt attention to this matter. We look forward to resolving this quickly.

Best regards,
[Your Name / Procurement Operations]
"""
    return email_template.strip()

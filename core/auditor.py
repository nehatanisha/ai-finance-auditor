# core/auditor.py

def verify_billing(invoice, contract):
    """
    Verifies the billing by comparing the expected total amount with the final amount.

    Args:
    - invoice (object): The invoice object containing quantity_billed and final_amount.
    - contract (object): The contract object containing agreed_rate_per_unit.

    Returns:
    - dict: A dictionary containing discrepancy status, overcharged amount, expected amount, and a reason message.
    """

    # Calculate the expected total amount
    expected_amount = invoice.quantity_billed * contract.agreed_rate_per_unit

    # Compare the expected amount with the final amount
    if expected_amount != invoice.final_amount:
        # Calculate the overcharged amount
        overcharged_amount = abs(invoice.final_amount - expected_amount)

        # Return a dictionary showing a billing discrepancy with the keys app.py expects
        return {
            "is_flagged": True,
            "expected_amount": expected_amount,
            "overcharge_delta": overcharged_amount,
            "reason": f"Expected amount is ${expected_amount:.2f}, but you were billed ${invoice.final_amount:.2f}."
        }
    else:
        # Return a dictionary showing no billing discrepancy
        return {
            "is_flagged": False
        }

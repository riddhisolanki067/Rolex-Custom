"""Payment Entry overrides for Rolex India.

Problem
-------
On a *sales* Payment Entry (party_type == "Customer"), India Compliance
populates the GST fields (company_address/company_gstin, customer_address/
billing_address_gstin/gst_category, place_of_supply) ONLY on the client, and
ONLY via asynchronous ``frappe.call`` triggers (party / company change).
India Compliance's server-side ``validate`` does not set them.

If the async callback lands *after* the user hits Save, it re-writes those
fields on the just-saved document, so the form flips to "Not Saved / Update"
even though nothing was really changed by the user.

Fix
---
Populate the same fields server-side at ``validate`` so the persisted document
already carries the exact values India Compliance would compute. Any late
client-side callback then sets an identical value -> no change -> no dirty flag.

Notes
-----
* Only fills fields that are still empty, so an explicit user choice is never
  overwritten.
* Mirrors the fetch_from cascade (gstin/gst_category come from the linked
  Address) and reuses India Compliance's own logic for ``place_of_supply`` so
  the server value matches the client value exactly.
* Wrapped defensively: a GST lookup failure must never block a payment save.
"""

import frappe
from frappe.contacts.doctype.address.address import get_default_address


def set_sales_gst_details(doc, method=None):
    if doc.party_type != "Customer":
        return

    # --- Company address + GSTIN (company_gstin fetch_from company_address.gstin)
    if not doc.company_address:
        doc.company_address = get_default_address("Company", doc.company)
    if doc.company_address and not doc.company_gstin:
        doc.company_gstin = frappe.db.get_value("Address", doc.company_address, "gstin")

    # --- Customer address + billing GSTIN + GST category (mirror fetch_from cascade)
    if not doc.customer_address:
        doc.customer_address = get_default_address("Customer", doc.party)
    if doc.customer_address:
        addr = (
            frappe.db.get_value(
                "Address", doc.customer_address, ["gstin", "gst_category"], as_dict=True
            )
            or {}
        )
        if not doc.billing_address_gstin:
            doc.billing_address_gstin = addr.get("gstin")
        if not doc.gst_category:
            doc.gst_category = addr.get("gst_category")

    # --- Place of supply: reuse India Compliance's own logic so it matches the
    #     value the client would set for the same address/company.
    if not doc.place_of_supply:
        try:
            from india_compliance.gst_india.overrides.payment_entry import (
                update_party_details,
            )

            details = update_party_details(
                frappe._dict(
                    {
                        "company": doc.company,
                        "party_type": doc.party_type,
                        "customer": doc.party,
                        "customer_address": doc.customer_address,
                        "company_gstin": doc.company_gstin,
                    }
                ),
                "Payment Entry",
                doc.company,
            )
            if details and details.get("place_of_supply"):
                doc.place_of_supply = details["place_of_supply"]
        except Exception:
            frappe.log_error(title="rolex_custom: PE place_of_supply lookup failed")

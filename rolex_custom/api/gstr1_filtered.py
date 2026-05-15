import frappe
from india_compliance.gst_india.doctype.gstr_1.gstr_1_export import get_gstr_1_json


# Map of Gov JSON keys to keep — check yours with:
# python -c "from india_compliance.gst_india.utils.gstr_1 import GovJsonKey; print({k.name: k.value for k in GovJsonKey})"
ALLOWED_CATEGORIES = {"b2cs", "b2cl", "hsn", "doc_det"}


@frappe.whitelist()
def get_filtered_gstr1_json(company_gstin, year, month_or_quarter):
    frappe.has_permission("GSTR-1", throw=True)

    result = get_gstr_1_json(
        company_gstin=company_gstin,
        year=year,
        month_or_quarter=month_or_quarter,
        include_uploaded=False,
        delete_missing=False,
    )

    if not result or not result.get("data"):
        frappe.throw("No GSTR-1 data found. Please generate first.")

    full_data = result["data"]

    # Keep only required categories + top-level metadata
    filtered = {
        k: v for k, v in full_data.items()
        if k in ALLOWED_CATEGORIES
        or not isinstance(v, (list, dict))  # preserve gstin, fp, gt, version etc.
    }

    return {"data": filtered, "filename": f"GSTR1_B2C_HSN_{company_gstin}_{month_or_quarter}_{year}.json"}
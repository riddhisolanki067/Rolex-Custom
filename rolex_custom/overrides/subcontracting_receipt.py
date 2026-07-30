"""Subcontracting Receipt on_submit: stamp DC-closed back on the source Job DCs.

For each Job-DC reference row (link_doctype == "Stock Entry") the user ticked
"DC Closed" on, set custom_dc_closed on that Send-to-Subcontractor Stock Entry.
Deferred to submit (per Riddhi) so a submitted DC is only mutated once the receipt
is committed. custom_dc_closed is allow_on_submit, so the write is legal.
"""

import frappe
from frappe.utils import today


def on_submit(doc, method=None):
	for row in doc.get("doc_references") or []:
		if row.get("link_doctype") != "Stock Entry":
			continue
		if not (row.get("custom_dc_closed") and row.get("link_name")):
			continue
		if frappe.db.get_value("Stock Entry", row.link_name, "custom_dc_closed"):
			continue
		frappe.db.set_value(
			"Stock Entry",
			row.link_name,
			{"custom_dc_closed": 1, "custom_dc_closed_on": today()},
			update_modified=False,
		)
		frappe.msgprint(
			frappe._("Marked Job DC {0} as DC Closed.").format(frappe.bold(row.link_name)),
			alert=True,
			indicator="green",
		)

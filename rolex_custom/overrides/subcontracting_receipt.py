"""Subcontracting Receipt document events.

on_submit: for every Job-DC row (doc_references) the user ticked "DC Closed",
stamp custom_dc_closed on the source Send-to-Subcontractor Stock Entry. Deferred
to submit (not the moment of ticking) so a submitted DC is only mutated once the
receipt is actually committed. custom_dc_closed is allow_on_submit, so writing it
on the submitted DC is legal.
"""

import frappe
from frappe.utils import today


def on_submit(doc, method=None):
	for row in doc.get("doc_references") or []:
		if not (row.get("dc_closed") and row.get("job_dc")):
			continue
		already = frappe.db.get_value("Stock Entry", row.job_dc, "custom_dc_closed")
		if already:
			continue
		frappe.db.set_value(
			"Stock Entry",
			row.job_dc,
			{
				"custom_dc_closed": 1,
				"custom_dc_closed_on": row.get("dc_closed_on") or today(),
			},
			update_modified=False,
		)
		frappe.msgprint(
			frappe._("Marked Job DC {0} as DC Closed.").format(
				frappe.bold(row.job_dc)
			),
			alert=True,
			indicator="green",
		)

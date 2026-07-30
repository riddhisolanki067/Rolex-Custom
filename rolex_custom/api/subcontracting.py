"""Server helper for the Subcontracting Receipt Job-DC batch pull (task 3).

`api/` is a namespace package (no __init__.py) — matches combined_print.py /
gstr1_filtered.py.
"""

import frappe


@frappe.whitelist()
def get_dc_rm_batches(job_dc):
	"""Batch numbers of the raw materials sent on one Job DC (Stock Entry), per item."""
	if not job_dc:
		return []
	return frappe.get_all(
		"Stock Entry Detail",
		filters={"parent": job_dc, "batch_no": ["is", "set"]},
		fields=["item_code", "batch_no", "qty"],
	)

"""Server methods for the Subcontracting Receipt Job-DC reference feature.

`api/` is a namespace package (no __init__.py) — matches combined_print.py /
gstr1_filtered.py. Whitelisted methods are addressed as
`rolex_custom.api.subcontracting.<fn>`.
"""

import frappe
from frappe.utils import flt


@frappe.whitelist()
def get_job_dcs(subcontracting_orders):
	"""Return the OPEN Send-to-Subcontractor Stock Entries (Job DCs) for the given
	Subcontracting Order(s), i.e. submitted DCs that are NOT yet marked DC-closed.

	Task 1: a DC with custom_dc_closed ticked is excluded from the fetch.
	`subcontracting_orders` is a JSON list (as sent from the client).
	"""
	scos = frappe.parse_json(subcontracting_orders) or []
	scos = [s for s in scos if s]
	if not scos:
		return []

	dcs = frappe.get_all(
		"Stock Entry",
		filters={
			"purpose": "Send to Subcontractor",
			"docstatus": 1,
			"subcontracting_order": ["in", scos],
		},
		fields=[
			"name",
			"posting_date",
			"subcontracting_order",
			"supplier",
			"custom_dc_closed",
		],
		order_by="posting_date asc, name asc",
	)

	out = []
	for d in dcs:
		if d.custom_dc_closed:  # excludes 1; keeps 0 and NULL — task 1
			continue
		total = frappe.db.sql(
			"SELECT SUM(qty) FROM `tabStock Entry Detail` WHERE parent=%s",
			(d.name,),
		)[0][0]
		out.append(
			{
				"job_dc": d.name,
				"posting_date": str(d.posting_date) if d.posting_date else None,
				"subcontracting_order": d.subcontracting_order,
				"supplier": d.supplier,
				"total_qty": flt(total),
				"dc_closed": 0,
			}
		)
	return out


@frappe.whitelist()
def get_dc_rm_batches(job_dc):
	"""Return the batch numbers of the raw materials sent on ONE Job DC, per item.

	Used by the per-row "Pull Batches -> RM" button (task 3) to carry batches into
	the Subcontracting Receipt's supplied_items (RM consumption) table.
	"""
	if not job_dc:
		return []
	return frappe.get_all(
		"Stock Entry Detail",
		filters={"parent": job_dc, "batch_no": ["is", "set"]},
		fields=["item_code", "batch_no", "qty"],
	)

"""Add the DC-Closed flag to the Send-to-Subcontractor Job DC (Stock Entry).

Idempotent (create_custom_fields, update=True). custom_dc_closed drives the
Pending Job DC reports and the "exclude closed DCs" filter layered on India
Compliance's Subcontracting Receipt fetch (see
rolex_custom.overrides.subcontracting_transaction).

NOTE: an earlier version of this patch also repurposed IC's Subcontracting
Receipt doc_references table into a custom Job-DC table — that was wrong (the
button/table belong to India Compliance). The repurpose is reverted by
rolex_custom.patches.restore_ic_subcontracting_receipt_fields.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	fields = {
		"Stock Entry": [
			{
				"fieldname": "custom_dc_closed",
				"label": "DC Closed (Material Returned)",
				"fieldtype": "Check",
				"insert_after": "subcontracting_order",
				"allow_on_submit": 1,
				"in_standard_filter": 1,
				"depends_on": "eval:doc.purpose=='Send to Subcontractor'",
				"description": (
					"Tick when ALL material sent on this Job DC has been received "
					"back / consumed. Drives the Pending Job DC reports and hides the "
					"DC from the Subcontracting Receipt fetch."
				),
			},
			{
				"fieldname": "custom_dc_closed_on",
				"label": "DC Closed On",
				"fieldtype": "Date",
				"insert_after": "custom_dc_closed",
				"allow_on_submit": 1,
				"read_only": 1,
				"depends_on": "eval:doc.custom_dc_closed",
			},
		],
	}
	create_custom_fields(fields, update=True)
	frappe.clear_cache(doctype="Stock Entry")

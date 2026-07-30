"""Add per-row DC controls to the Subcontracting Receipt references table.

India Compliance's `doc_references` table uses the core `Dynamic Link` child, so
these two columns are added to `Dynamic Link` (they will also appear in other
Dynamic Link grids, but the button/checkbox behaviour is wired only on the
Subcontracting Receipt form, in public/js/subcontracting_receipt.js):

  * custom_dc_closed   - tick a fetched Job DC row; on receipt submit the source
                         Stock Entry's custom_dc_closed is stamped (task 2).
  * custom_pull_batches - button that pulls that Job DC's RM batches into the
                          supplied_items (RM consumption) table (task 3).

Idempotent (create_custom_fields, update=True).
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	create_custom_fields(
		{
			"Dynamic Link": [
				{
					"fieldname": "custom_dc_closed",
					"label": "DC Closed",
					"fieldtype": "Check",
					"insert_after": "link_name",
					"in_list_view": 1,
				},
				{
					"fieldname": "custom_pull_batches",
					"label": "Pull Batches → RM",
					"fieldtype": "Button",
					"insert_after": "custom_dc_closed",
					"in_list_view": 1,
				},
			]
		},
		update=True,
	)
	frappe.clear_cache(doctype="Dynamic Link")
	frappe.clear_cache(doctype="Subcontracting Receipt")

"""Subcontracting Job-DC reference feature — custom fields.

Idempotent (create_custom_fields, update=True), so it is safe on both a fresh
local site and the live Frappe Cloud site where some of these fields already
exist (created earlier directly on the instance):

  * Stock Entry.custom_dc_closed / custom_dc_closed_on  — the "DC Closed" flag on
    the Send-to-Subcontractor Job DC (allow_on_submit; DCs are submitted docs).
  * Subcontracting Receipt.section_break_ref_doc / fetch_original_doc_ref /
    doc_references — repurposes the existing "Original Document References" table
    into the Job-DC table by pointing it at the `Subcontracting Job DC` child
    DocType (was the generic `Dynamic Link`).
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
					"back / consumed. Drives the Pending Job DC reports and hides "
					"the DC from the Subcontracting Receipt fetch."
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
		"Subcontracting Receipt": [
			{
				"fieldname": "section_break_ref_doc",
				"label": "Job DC References",
				"fieldtype": "Section Break",
				"insert_after": "bill_date",
				"depends_on": "eval:doc.is_return !== 1",
			},
			{
				"fieldname": "fetch_original_doc_ref",
				"label": "Fetch Job DCs",
				"fieldtype": "Button",
				"insert_after": "section_break_ref_doc",
			},
			{
				"fieldname": "doc_references",
				"label": "Job DC References",
				"fieldtype": "Table",
				"options": "Subcontracting Job DC",
				"insert_after": "fetch_original_doc_ref",
			},
		],
	}

	create_custom_fields(fields, update=True)
	frappe.clear_cache(doctype="Stock Entry")
	frappe.clear_cache(doctype="Subcontracting Receipt")

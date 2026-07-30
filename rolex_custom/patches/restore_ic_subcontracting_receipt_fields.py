"""Undo the earlier wrong repurpose of India Compliance's Subcontracting Receipt
"Original Document References" table.

A previous patch changed IC's doc_references field (options Dynamic Link ->
custom "Subcontracting Job DC" child) and relabelled the button/section, and a
custom child DocType `Subcontracting Job DC` was created. IC owns these fields;
this restores them to IC's exact definitions and removes the stray DocType so the
native IC "Fetch Original Document Reference" flow works again.

Idempotent: on a site that never had the wrong version, every step is a no-op.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	# 1. Restore IC's Subcontracting Receipt fields to their original definitions
	#    (values copied from india_compliance gst_india/constants/custom_fields.py).
	ic_fields = {
		"Subcontracting Receipt": [
			{
				"fieldname": "section_break_ref_doc",
				"label": "References",
				"fieldtype": "Section Break",
				"insert_after": "bill_date",
				"depends_on": "eval:doc.is_return !== 1",
			},
			{
				"fieldname": "fetch_original_doc_ref",
				"label": "Fetch Original Document Reference",
				"fieldtype": "Button",
				"insert_after": "section_break_ref_doc",
			},
			{
				"fieldname": "doc_references",
				"label": "Original Document References",
				"fieldtype": "Table",
				"insert_after": "fetch_original_doc_ref",
				"options": "Dynamic Link",
			},
		],
	}
	create_custom_fields(ic_fields, update=True)

	# 2. Drop the stray custom child DocType (and its table) if it exists. The
	#    doc_references field no longer points at it (restored to Dynamic Link),
	#    so any stray test rows are orphaned test data — safe to remove.
	if frappe.db.exists("DocType", "Subcontracting Job DC"):
		frappe.delete_doc("DocType", "Subcontracting Job DC", force=1, ignore_permissions=True)

	# The DocType record may already have been removed by the orphan-doctype sweep
	# during model sync, leaving the physical table behind — drop it explicitly.
	frappe.db.sql_ddl("DROP TABLE IF EXISTS `tabSubcontracting Job DC`")

	frappe.clear_cache(doctype="Subcontracting Receipt")

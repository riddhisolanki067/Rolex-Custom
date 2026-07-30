"""Exclude DC-closed Job DCs from India Compliance's Subcontracting Receipt fetch.

India Compliance owns the "Fetch Original Document Reference" button + the
`doc_references` (Dynamic Link) table on Subcontracting Receipt. Its client script
calls `get_relevant_references`, which returns the relevant Stock Entries (Send-to-
Subcontractor Job DCs) and Subcontracting Receipts for the receipt's supplier /
supplied items / SCOs.

We only add ONE rule on top: a Stock Entry (Job DC) whose custom_dc_closed is
ticked must not be fetched. Implemented by wrapping IC's whitelisted method via
`override_whitelisted_methods` and post-filtering its result — IC's own scoping is
left completely intact, so nothing changes for non-closed DCs.
"""

import frappe

from india_compliance.gst_india.overrides import subcontracting_transaction as ic


def _closed_dc_names(names):
	if not names:
		return set()
	return set(
		frappe.get_all(
			"Stock Entry",
			filters={"name": ["in", list(names)], "custom_dc_closed": 1},
			pluck="name",
		)
	)


@frappe.whitelist()
def get_relevant_references(filters=None):
	# Direct import call -> IC's real function (override_whitelisted_methods only
	# affects frappe.call dispatch, not direct imports, so no recursion).
	refs = ic.get_relevant_references(filters)

	stock_entries = refs.get("Stock Entry") or []
	closed = _closed_dc_names(stock_entries)
	if closed:
		refs["Stock Entry"] = [name for name in stock_entries if name not in closed]

	return refs

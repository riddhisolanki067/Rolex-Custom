# Copyright (c) 2026, q and contributors
# Pending Job DC rollup per subcontractor, driven by Stock Entry.custom_dc_closed.

import frappe
from frappe.utils import flt


def execute(filters=None):
	filters = filters or {}
	return get_columns(), get_data(filters)


def get_columns():
	return [
		{"label": "Subcontractor", "fieldname": "supplier", "fieldtype": "Link", "options": "Supplier", "width": 240},
		{"label": "DCs Sent", "fieldname": "dcs_sent", "fieldtype": "Int", "width": 90},
		{"label": "DCs Closed", "fieldname": "dcs_closed", "fieldtype": "Int", "width": 100},
		{"label": "DCs Pending", "fieldname": "dcs_pending", "fieldtype": "Int", "width": 110},
		{"label": "Qty With Subcontractor", "fieldname": "qty_pending", "fieldtype": "Float", "width": 200},
	]


def get_data(filters):
	conditions = "se.docstatus = 1 AND se.purpose = 'Send to Subcontractor'"
	params = {}
	if filters.get("supplier"):
		conditions += " AND se.supplier = %(supplier)s"
		params["supplier"] = filters.get("supplier")
	if filters.get("from_date"):
		conditions += " AND se.posting_date >= %(from_date)s"
		params["from_date"] = filters.get("from_date")
	if filters.get("to_date"):
		conditions += " AND se.posting_date <= %(to_date)s"
		params["to_date"] = filters.get("to_date")

	rows = frappe.db.sql(
		"""
		SELECT se.supplier,
			COUNT(DISTINCT se.name) AS dcs_sent,
			COUNT(DISTINCT CASE WHEN se.custom_dc_closed = 1 THEN se.name END) AS dcs_closed,
			COUNT(DISTINCT CASE WHEN IFNULL(se.custom_dc_closed, 0) = 0 THEN se.name END) AS dcs_pending,
			SUM(CASE WHEN IFNULL(se.custom_dc_closed, 0) = 0 THEN sed.qty ELSE 0 END) AS qty_pending
		FROM `tabStock Entry` se
		INNER JOIN `tabStock Entry Detail` sed ON sed.parent = se.name
		WHERE """ + conditions + """
		GROUP BY se.supplier
		ORDER BY dcs_pending DESC
		""",
		params,
		as_dict=True,
	)
	for r in rows:
		r["qty_pending"] = flt(r["qty_pending"])
	return rows

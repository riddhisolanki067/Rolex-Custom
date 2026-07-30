# Copyright (c) 2026, q and contributors
# Line-list register of Send-to-Subcontractor Job DCs with Pending/Closed status.

import frappe
from frappe.utils import flt


def execute(filters=None):
	filters = filters or {}
	return get_columns(), get_data(filters)


def get_columns():
	return [
		{"label": "Job DC", "fieldname": "job_dc", "fieldtype": "Link", "options": "Stock Entry", "width": 170},
		{"label": "Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
		{"label": "Subcontractor", "fieldname": "supplier", "fieldtype": "Link", "options": "Supplier", "width": 220},
		{"label": "Subcon Order", "fieldname": "sco", "fieldtype": "Link", "options": "Subcontracting Order", "width": 160},
		{"label": "Qty Sent", "fieldname": "qty_sent", "fieldtype": "Float", "width": 110},
		{"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 90},
		{"label": "Closed On", "fieldname": "closed_on", "fieldtype": "Date", "width": 100},
	]


def get_data(filters):
	conditions = "se.docstatus = 1 AND se.purpose = 'Send to Subcontractor'"
	params = {}
	if filters.get("supplier"):
		conditions += " AND se.supplier = %(supplier)s"
		params["supplier"] = filters.get("supplier")
	if filters.get("status") == "Pending":
		conditions += " AND IFNULL(se.custom_dc_closed, 0) = 0"
	elif filters.get("status") == "Closed":
		conditions += " AND IFNULL(se.custom_dc_closed, 0) = 1"

	rows = frappe.db.sql(
		"""
		SELECT se.name AS job_dc, se.posting_date, se.supplier,
			se.subcontracting_order AS sco,
			SUM(sed.qty) AS qty_sent,
			IF(IFNULL(se.custom_dc_closed, 0) = 1, 'Closed', 'Pending') AS status,
			se.custom_dc_closed_on AS closed_on
		FROM `tabStock Entry` se
		INNER JOIN `tabStock Entry Detail` sed ON sed.parent = se.name
		WHERE """ + conditions + """
		GROUP BY se.name
		ORDER BY se.posting_date DESC, se.name DESC
		""",
		params,
		as_dict=True,
	)
	for r in rows:
		r["qty_sent"] = flt(r["qty_sent"])
	return rows

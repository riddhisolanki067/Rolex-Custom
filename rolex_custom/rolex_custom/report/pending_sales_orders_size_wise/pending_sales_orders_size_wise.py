# Copyright (c) 2026, Rolex India and contributors

import re

import frappe
from frappe import _
from frappe.utils import cint, date_diff, flt, getdate, nowdate, strip_html


GENERIC_ITEM_TERMS = (
	"ss rod",
	"ss rods",
	"black steel",
	"bright steel",
	"en31",
	"hchcr",
	"steel tube",
	"steel tubes",
	"plate",
	"plates",
)


def execute(filters=None):
	filters = frappe._dict(filters or {})
	data = _get_data(filters)
	return _get_columns(), data, None, None, _get_report_summary(data)


def _get_columns():
	return [
		{"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 210},
		{"label": _("Sales Order"), "fieldname": "sales_order", "fieldtype": "Link", "options": "Sales Order", "width": 145},
		{"label": _("Order Date"), "fieldname": "order_date", "fieldtype": "Date", "width": 100},
		{"label": _("Delivery Date"), "fieldname": "delivery_date", "fieldtype": "Date", "width": 105},
		{"label": _("Item"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 150},
		{"label": _("Size / Material Description"), "fieldname": "size_description", "fieldtype": "Data", "width": 250},
		{"label": _("Ordered Qty"), "fieldname": "ordered_qty", "fieldtype": "Float", "width": 105},
		{"label": _("Delivered Qty"), "fieldname": "delivered_qty", "fieldtype": "Float", "width": 110},
		{"label": _("Pending Qty"), "fieldname": "pending_qty", "fieldtype": "Float", "width": 105},
		{"label": _("UOM"), "fieldname": "uom", "fieldtype": "Link", "options": "UOM", "width": 75},
		{"label": _("Delay"), "fieldname": "delay_days", "fieldtype": "Int", "width": 90},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 125},
	]


def _get_data(filters):
	conditions = [
		"so.docstatus = 1",
		"so.company = %(company)s",
		"so.status NOT IN ('Completed', 'Closed', 'Cancelled')",
		"(soi.qty - IFNULL(soi.delivered_qty, 0)) > 0.000001",
	]
	params = {"company": filters.company, "today": nowdate()}

	if filters.customer:
		conditions.append("so.customer = %(customer)s")
		params["customer"] = filters.customer
	if filters.item_code:
		conditions.append("soi.item_code = %(item_code)s")
		params["item_code"] = filters.item_code
	if filters.from_date:
		conditions.append("so.transaction_date >= %(from_date)s")
		params["from_date"] = filters.from_date
	if filters.to_date:
		conditions.append("COALESCE(soi.delivery_date, so.delivery_date) <= %(to_date)s")
		params["to_date"] = filters.to_date
	if cint(filters.overdue_only):
		conditions.append("COALESCE(soi.delivery_date, so.delivery_date) < %(today)s")

	rows = frappe.db.sql(
		f"""
		SELECT
			so.customer,
			so.name AS sales_order,
			so.transaction_date AS order_date,
			COALESCE(soi.delivery_date, so.delivery_date) AS delivery_date,
			soi.item_code,
			soi.item_name,
			soi.description,
			soi.qty AS ordered_qty,
			IFNULL(soi.delivered_qty, 0) AS delivered_qty,
			(soi.qty - IFNULL(soi.delivered_qty, 0)) AS pending_qty,
			soi.uom,
			so.status
		FROM `tabSales Order` so
		INNER JOIN `tabSales Order Item` soi ON soi.parent = so.name
		WHERE {' AND '.join(conditions)}
		ORDER BY so.customer, COALESCE(soi.delivery_date, so.delivery_date), so.name, soi.idx
		""",
		params,
		as_dict=True,
	)

	today = getdate(params["today"])
	for row in rows:
		row.ordered_qty = flt(row.ordered_qty)
		row.delivered_qty = flt(row.delivered_qty)
		row.pending_qty = flt(row.pending_qty)
		row.size_description = _get_size_description(row)
		delivery_date = getdate(row.delivery_date) if row.delivery_date else None
		row.is_overdue = cint(bool(delivery_date and delivery_date < today))
		row.delay_days = date_diff(today, delivery_date) if row.is_overdue else 0

	return rows


def _get_size_description(row):
	identity = f"{row.item_code or ''} {row.item_name or ''}".lower().replace("_", " ").replace("-", " ")
	identity = re.sub(r"\s+", " ", identity)
	use_description = any(term in identity for term in GENERIC_ITEM_TERMS)
	value = row.description if use_description and row.description else row.item_name
	return re.sub(r"\s+", " ", strip_html(value or row.item_code or "")).strip()


def _get_report_summary(data):
	orders = {row.sales_order for row in data}
	overdue_orders = {row.sales_order for row in data if row.is_overdue}
	customers = {row.customer for row in data}
	return [
		{"value": len(orders), "indicator": "Blue", "label": _("Open Sales Orders"), "datatype": "Int"},
		{"value": len(overdue_orders), "indicator": "Red" if overdue_orders else "Green", "label": _("Overdue Orders"), "datatype": "Int"},
		{"value": len(customers), "indicator": "Green", "label": _("Customers"), "datatype": "Int"},
		{"value": len(data), "indicator": "Orange", "label": _("Pending Size Lines"), "datatype": "Int"},
	]

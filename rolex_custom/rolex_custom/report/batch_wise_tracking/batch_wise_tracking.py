# Copyright (c) 2026
# For complete Batch Lifecycle Traceability Report

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"label": "Posting Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
        {"label": "Item", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 150},
        {"label": "Batch", "fieldname": "batch_no", "fieldtype": "Link", "options": "Batch", "width": 130},
        {"label": "Warehouse", "fieldname": "warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 150},
        {"label": "Voucher Type", "fieldname": "voucher_type", "fieldtype": "Data", "width": 140},
        {"label": "Voucher No", "fieldname": "voucher_no", "fieldtype": "Dynamic Link", "options": "voucher_type", "width": 160},
        {"label": "Party Type", "fieldname": "party_type", "fieldtype": "Data", "width": 110},
        {"label": "Party", "fieldname": "party", "fieldtype": "Data", "width": 150},
        {"label": "Qty In", "fieldname": "qty_in", "fieldtype": "Float", "width": 90},
        {"label": "Qty Out", "fieldname": "qty_out", "fieldtype": "Float", "width": 90},
        {"label": "Balance Qty", "fieldname": "balance_qty", "fieldtype": "Float", "width": 110},
    ]


def get_data(filters):
    conditions = "where sle.batch_no is not null"

    if filters.get("batch_no"):
        conditions += " and sle.batch_no = %(batch_no)s"

    if filters.get("item_code"):
        conditions += " and sle.item_code = %(item_code)s"

    sle_list = frappe.db.sql(f"""
        select
            sle.posting_date,
            sle.item_code,
            sle.batch_no,
            sle.warehouse,
            sle.voucher_type,
            sle.voucher_no,
            sle.actual_qty,
            sle.qty_after_transaction
        from `tabStock Ledger Entry` sle
        {conditions}
        order by sle.posting_date, sle.posting_time
    """, filters, as_dict=1)

    data = []

    for row in sle_list:
        party_type = ""
        party = ""

        # Purchase
        if row.voucher_type == "Purchase Receipt":
            party = frappe.db.get_value("Purchase Receipt", row.voucher_no, "supplier")
            party_type = "Supplier"

        # Sales
        elif row.voucher_type == "Delivery Note":
            party = frappe.db.get_value("Delivery Note", row.voucher_no, "customer")
            party_type = "Customer"

        elif row.voucher_type == "Sales Invoice":
            party = frappe.db.get_value("Sales Invoice", row.voucher_no, "customer")
            party_type = "Customer"

        # Stock Entry (Manufacturing / Transfer)
        elif row.voucher_type == "Stock Entry":
            se = frappe.db.get_value("Stock Entry", row.voucher_no, ["stock_entry_type"], as_dict=1)
            if se:
                party_type = "Stock Entry Type"
                party = se.stock_entry_type

        qty_in = flt(row.actual_qty) if row.actual_qty > 0 else 0
        qty_out = abs(flt(row.actual_qty)) if row.actual_qty < 0 else 0

        data.append({
            "posting_date": row.posting_date,
            "item_code": row.item_code,
            "batch_no": row.batch_no,
            "warehouse": row.warehouse,
            "voucher_type": row.voucher_type,
            "voucher_no": row.voucher_no,
            "party_type": party_type,
            "party": party,
            "qty_in": qty_in,
            "qty_out": qty_out,
            "balance_qty": row.qty_after_transaction
        })

    return data
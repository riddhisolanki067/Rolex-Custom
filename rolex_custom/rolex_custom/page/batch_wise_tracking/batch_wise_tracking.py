import frappe

@frappe.whitelist()
def get_batch_main(batch_no):

    data = []

    records = frappe.db.sql("""
        SELECT
            sbb.posting_date,
            sbb.voucher_type,
            sbb.voucher_no,
            sbb.type_of_transaction as transaction_type,
            sbb.total_qty as qty,
            sbb.item_code
        FROM `tabSerial and Batch Bundle` sbb
        JOIN `tabSerial and Batch Entry` sbe ON sbe.parent = sbb.name
        WHERE sbe.batch_no = %s
        ORDER BY sbb.posting_date
    """, batch_no, as_dict=1)

    for r in records:

        party = ""
        

        if r.voucher_type == "Purchase Receipt":
            party = frappe.db.get_value("Purchase Receipt", r.voucher_no, "supplier")

        elif r.voucher_type == "Purchase Invoice":
            party = frappe.db.get_value("Purchase Invoice", r.voucher_no, "supplier")

    

        data.append({
            "date": r.posting_date,
            "item": r.item_code,
            "type": r.transaction_type,
            "qty": r.qty,
            "voucher_type": r.voucher_type,
            "voucher_no": r.voucher_no,
            "party": party
        })

    return data



import frappe

@frappe.whitelist()
def get_fg_details(stock_entry):

    data = {
        "fg": [],
        "sales": []
    }

    # FG + Scrap
    fg = frappe.db.sql("""
        SELECT
            item_code,
            batch_no,
            t_warehouse as warehouse,
            qty,
            is_finished_item
        FROM `tabStock Entry Detail`
        WHERE parent = %s
    """, stock_entry, as_dict=1)

    data["fg"] = fg

    # FG Batches
    fg_batches = [f.batch_no for f in fg if f.is_finished_item]

    if fg_batches:
        sales = frappe.db.sql("""
            SELECT
                dn.customer,
                dn.name as invoice,
                dni.qty,
                dni.batch_no
            FROM `tabDelivery Note Item` dni
            JOIN `tabDelivery Note` dn ON dn.name = dni.parent
            WHERE dni.batch_no IN %(batches)s
        """, {"batches": tuple(fg_batches)}, as_dict=1)

        data["sales"] = sales

    return data
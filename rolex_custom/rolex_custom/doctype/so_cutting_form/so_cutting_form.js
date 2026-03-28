// Copyright (c) 2026, q and contributors
// For license information, please see license.txt
frappe.ui.form.on('Sales Order Item', {
    qty: function(frm, cdt, cdn) {
        console.log("qty changed");
        calculate_amount(frm, cdt, cdn);
    },
    rate: function(frm, cdt, cdn) {
        calculate_amount(frm, cdt, cdn);
    }
});

function calculate_amount(frm, cdt, cdn) {
    console.log("Calculating amount");
    let row = frappe.get_doc(cdt, cdn);
    if(row.qty && row.rate) {
        console.log("qty and rate are present");
        let amount = row.qty * row.rate;
        console.log("Calculated amount: " + amount);
        frappe.model.set_value(cdt, cdn, 'amount', amount);
        frm.refresh_field('items');
    
 }
}

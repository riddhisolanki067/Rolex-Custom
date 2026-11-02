frappe.query_reports["Rolex Party Outstanding"] = {
    filters: [
        {fieldname: "company", label: __("Company"), fieldtype: "Link", options: "Company", default: frappe.defaults.get_user_default("Company") || "Rolex India", reqd: 1},
        {fieldname: "party_type", label: __("Party Type"), fieldtype: "Select", options: "Customer\nSupplier", default: "Customer", reqd: 1,
            on_change: async function () {
                await frappe.query_report.set_filter_value("party", "");
                await frappe.query_report.refresh();
            }},
        {fieldname: "party", label: __("Party"), fieldtype: "Dynamic Link", options: "party_type",
            get_options: function () { return frappe.query_report.get_filter_value("party_type"); }},
        {fieldname: "report_date", label: __("As On Date"), fieldtype: "Date", default: frappe.datetime.get_today(), reqd: 1},
        {fieldname: "overdue_only", label: __("Overdue Only"), fieldtype: "Check", default: 0}
    ],
    formatter: function (value, row, column, data, default_formatter) {
        if (column.fieldname === "payment_trace") {
            if (!data || data.voucher_type !== "Purchase Invoice" || !data.payment_trace) return "";
            return data.payment_trace.split(", ").map(function (receipt) {
                const query = new URLSearchParams({company: frappe.query_report.get_filter_value("company"), purchase_receipt: receipt, as_of_date: frappe.query_report.get_filter_value("report_date")});
                const href = "/desk/query-report/Material%20Receipt%20Brief%20Trace?" + query.toString();
                return '<a href="' + frappe.utils.escape_html(href) + '" target="_blank" rel="noopener">' + frappe.utils.escape_html(receipt) + '</a>';
            }).join("<br>");
        }
        value = default_formatter(value, row, column, data);
        if (column.fieldname === "invoice_no" && data && data.our_voucher && data.voucher_type) {
            const payload = encodeURIComponent(JSON.stringify({
                invoice_no: data.invoice_no || data.our_voucher,
                voucher_type: data.voucher_type,
                our_voucher: data.our_voucher,
                invoice_date: data.invoice_date,
                invoice_amount: flt(data.invoice_amount),
                pending_amount: flt(data.pending_amount),
                currency: data.currency,
                settlements: data.settlement_entries || [],
                difference: flt(data.settlement_difference)
            }));
            return '<a href="#" style="font-weight:600" onclick="open_party_settlement(\'' + payload + '\');return false;">' + frappe.utils.escape_html(data.invoice_no || data.our_voucher) + '</a>';
        }
        if (column.fieldname === "due_date" && data && data.due_date && flt(data.pending_amount) > 0) {
            const report_date = frappe.query_report.get_filter_value("report_date");
            if (report_date && frappe.datetime.get_diff(report_date, data.due_date) > 0) return '<span style="color:#c0392b;font-weight:600">' + value + '</span>';
        }
        return value;
    }
};


window.open_party_settlement = function (encoded) {
    const detail = JSON.parse(decodeURIComponent(encoded));
    const currency = detail.currency || frappe.defaults.get_default("currency") || "INR";
    const money = value => format_currency(Math.abs(flt(value)), currency);
    const signed = value => (flt(value) < 0 ? "− " : "+ ") + money(value);
    const doc_link = (type, name, label) => {
        if (!type || !name) return frappe.utils.escape_html(label || "");
        const route = "/app/" + frappe.router.slug(type) + "/" + encodeURIComponent(name);
        return '<a href="' + route + '" target="_blank" rel="noopener">' + frappe.utils.escape_html(label || name) + '</a>';
    };
    const adjustments = (detail.settlements || []).filter(row => Math.abs(flt(row.amount)) > 0.0001);
    const adjustment_rows = adjustments.length ? adjustments.map(row => {
        const reference = row.voucher_no ? doc_link(row.voucher_type, row.voucher_no, row.voucher_no) : "";
        const date = row.posting_date ? frappe.datetime.str_to_user(row.posting_date) : "";
        return '<tr><td style="padding:7px 8px;border-top:1px solid var(--border-color);"><div style="font-weight:500;">' + frappe.utils.escape_html(row.label || "Adjustment") + '</div><div class="text-muted small">' + reference + (date ? ' · ' + frappe.utils.escape_html(date) : '') + '</div></td><td style="padding:7px 8px;border-top:1px solid var(--border-color);text-align:right;white-space:nowrap;">' + signed(row.amount) + '</td></tr>';
    }).join("") : '<tr><td colspan="2" class="text-muted" style="padding:8px;border-top:1px solid var(--border-color);">No settlement adjustments as on the selected date.</td></tr>';
    const invoice_link = doc_link(detail.voucher_type, detail.our_voucher, detail.invoice_no);
    const invoice_date = detail.invoice_date ? frappe.datetime.str_to_user(detail.invoice_date) : "";
    const html = '<div style="max-width:520px;">' +
        '<div style="margin-bottom:12px;"><div><b>' + __("Invoice") + ':</b> ' + invoice_link + '</div><div><b>' + __("Date") + ':</b> ' + frappe.utils.escape_html(invoice_date) + '</div></div>' +
        '<table style="width:100%;"><tbody>' +
        '<tr><td style="padding:8px;font-weight:600;">' + __("Original Invoice Amount") + '</td><td style="padding:8px;text-align:right;font-weight:600;white-space:nowrap;">' + money(detail.invoice_amount) + '</td></tr>' +
        '<tr><td colspan="2" style="padding:10px 8px 4px;font-weight:600;">' + __("Adjustments") + '</td></tr>' + adjustment_rows +
        '<tr><td style="padding:10px 8px;border-top:2px solid var(--border-color);font-weight:700;">' + __("Pending Amount") + '</td><td style="padding:10px 8px;border-top:2px solid var(--border-color);text-align:right;font-weight:700;white-space:nowrap;">' + money(detail.pending_amount) + '</td></tr>' +
        '<tr><td style="padding:4px 8px;" class="text-muted">' + __("Difference") + '</td><td style="padding:4px 8px;text-align:right;white-space:nowrap;" class="text-muted">' + money(detail.difference) + '</td></tr>' +
        '</tbody></table></div>';
    const dialog = new frappe.ui.Dialog({title: __("Invoice Settlement"), size: "small", fields: [{fieldtype: "HTML", fieldname: "settlement_html"}]});
    dialog.fields_dict.settlement_html.$wrapper.html(html);
    dialog.show();
};

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
    },

    get_pdf_format: async function (report) {
        const esc = value => frappe.utils.escape_html(String(value == null ? "" : value));
        const filters = report.get_filter_values ? report.get_filter_values() : {};
        const party_type = filters.party_type || "Customer";
        const selected_party = filters.party || "";
        const currency = "INR";
        const money = value => format_currency(flt(value), currency);
        const date = value => value ? frappe.datetime.str_to_user(value) : "";
        const rows = (report.data || []).filter(row => row && !row.is_total_row && row.invoice_no);
        const show_party = !selected_party;

        let total_invoice = 0;
        let total_pending = 0;
        rows.forEach(row => {
            total_invoice += flt(row.invoice_amount);
            total_pending += flt(row.pending_amount);
        });

        const summary = (report.raw_data && report.raw_data.report_summary) || [];
        const advance_summary = summary.find(item => /Advances/i.test(item.label || ""));
        const advances = advance_summary ? flt(advance_summary.value) : 0;
        const pending_label = party_type === "Supplier" ? __("Payable") : __("Receivable");
        const advance_label = party_type === "Supplier" ? __("Supplier Advances") : __("Customer Advances");

        const party_heading = selected_party
            ? `<div><b>${esc(party_type)}:</b> ${esc(selected_party)}</div>`
            : `<div><b>${esc(party_type)}:</b> ${__("All")}</div>`;

        const body_rows = rows.length ? rows.map((row, index) => `
            <tr>
                <td class="center">${index + 1}</td>
                ${show_party ? `<td>${esc(row.party)}</td>` : ""}
                <td class="nowrap">${esc(date(row.invoice_date))}</td>
                <td>${esc(row.invoice_no)}</td>
                <td class="amount">${esc(money(row.invoice_amount))}</td>
                <td class="amount">${esc(money(row.pending_amount))}</td>
                <td class="nowrap">${esc(date(row.due_date))}</td>
            </tr>`).join("") : `
            <tr><td colspan="${show_party ? 7 : 6}" class="center muted">${__("No outstanding invoices for the selected filters.")}</td></tr>`;

        return `
            <style>
                .rolex-outstanding-print { font-family: Arial, sans-serif; color: #111; font-size: 10.5pt; }
                .rolex-outstanding-print .company { text-align: center; border-bottom: 2px solid #222; padding-bottom: 8px; }
                .rolex-outstanding-print .company h1 { font-size: 20pt; margin: 0 0 4px; letter-spacing: .3px; }
                .rolex-outstanding-print .company p { margin: 2px 0; line-height: 1.35; }
                .rolex-outstanding-print .title { text-align: center; font-size: 14pt; font-weight: 700; margin: 14px 0 10px; }
                .rolex-outstanding-print .context { display: flex; justify-content: space-between; gap: 16px; margin-bottom: 10px; line-height: 1.5; }
                .rolex-outstanding-print .summary { width: 100%; margin: 8px 0 12px; border-collapse: collapse; }
                .rolex-outstanding-print .summary td { width: 33.33%; border: 1px solid #bbb; padding: 7px 9px; text-align: center; }
                .rolex-outstanding-print .summary .label { font-size: 9pt; color: #555; }
                .rolex-outstanding-print .summary .value { font-size: 11pt; font-weight: 700; margin-top: 3px; }
                .rolex-outstanding-print .details { width: 100%; border-collapse: collapse; }
                .rolex-outstanding-print .details thead { display: table-header-group; }
                .rolex-outstanding-print .details th { background: #ececec; border: 1px solid #999; padding: 6px 7px; font-weight: 700; }
                .rolex-outstanding-print .details td { border: 1px solid #bbb; padding: 6px 7px; vertical-align: top; }
                .rolex-outstanding-print .amount { text-align: right; white-space: nowrap; }
                .rolex-outstanding-print .center { text-align: center; }
                .rolex-outstanding-print .nowrap { white-space: nowrap; }
                .rolex-outstanding-print .muted { color: #666; }
                .rolex-outstanding-print .total-row td { border-top: 2px solid #333; font-weight: 700; }
                .rolex-outstanding-print .bank { margin-top: 16px; border: 1px solid #999; padding: 9px 11px; page-break-inside: avoid; }
                .rolex-outstanding-print .bank-title { font-weight: 700; margin-bottom: 5px; }
                .rolex-outstanding-print .regards { margin-top: 22px; line-height: 1.5; page-break-inside: avoid; }
                @page { size: A4 portrait; margin: 12mm; }
            </style>
            <div class="rolex-outstanding-print">
                <div class="company">
                    <h1>Rolex India</h1>
                    <p>Plot No. 182 (P) and 183 (P), SY. 208, Gamanagatti 2nd Stage Industrial Area,<br>Village Gamanagatti, Hubballi - 580025, Karnataka, India</p>
                    <p><b>Email:</b> rolexindiahbl@gmail.com &nbsp; | &nbsp; <b>GSTIN:</b> 29ABFFR5985B1ZU</p>
                </div>

                <div class="title">${__("Party Outstanding Statement")}</div>
                <div class="context">
                    <div>${party_heading}<div><b>${__("Company")}:</b> ${esc(filters.company || "Rolex India")}</div></div>
                    <div style="text-align:right"><b>${__("As On Date")}:</b> ${esc(date(filters.report_date))}<br><b>${__("Overdue Only")}:</b> ${filters.overdue_only ? __("Yes") : __("No")}</div>
                </div>

                <table class="summary">
                    <tr>
                        <td><div class="label">${__("Total Invoice Amount")}</div><div class="value">${esc(money(total_invoice))}</div></td>
                        <td><div class="label">${pending_label}</div><div class="value">${esc(money(total_pending))}</div></td>
                        <td><div class="label">${advance_label}</div><div class="value">${esc(money(advances))}</div></td>
                    </tr>
                </table>

                <table class="details">
                    <thead><tr>
                        <th style="width:5%">#</th>
                        ${show_party ? `<th>${__("Party")}</th>` : ""}
                        <th>${__("Date")}</th>
                        <th>${__("Voucher No.")}</th>
                        <th class="amount">${__("Invoice Amount")}</th>
                        <th class="amount">${__("Pending Amount")}</th>
                        <th>${__("Due Date")}</th>
                    </tr></thead>
                    <tbody>
                        ${body_rows}
                        <tr class="total-row">
                            <td colspan="${show_party ? 4 : 3}" class="amount">${__("Total")}</td>
                            <td class="amount">${esc(money(total_invoice))}</td>
                            <td class="amount">${esc(money(total_pending))}</td>
                            <td></td>
                        </tr>
                    </tbody>
                </table>

                <div class="bank">
                    <div class="bank-title">${__("Bank Details")}</div>
                    <div><b>${__("Bank")}:</b> Axis Bank Ltd</div>
                    <div><b>${__("Account No.")}:</b> 923030012699608 &nbsp; | &nbsp; <b>${__("IFSC")}:</b> UITB0000129</div>
                    <div><b>${__("Account Type")}:</b> BANK OD A/C</div>
                </div>

                <div class="regards">Regards,<br><b>Rolex India</b></div>
            </div>`;
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

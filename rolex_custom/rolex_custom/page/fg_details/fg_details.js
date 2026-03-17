frappe.pages['fg-details'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'FG Details',
		single_column: true
	});
	let stock_entry = frappe.route_options?.stock_entry;

	console.log("Stock Entry:", stock_entry);

    let container = $(`
        <div>
            <h4>Finished Goods</h4>
            <div id="fg"></div>

            <h4>Sales</h4>
            <div id="sales"></div>
        </div>
    `).appendTo(page.body);

    frappe.call({
        method: "rolex_custom.rolex_custom.page.fg_details.fg_details.get_fg_details",
        args: { stock_entry },
        callback(r) {

            let d = r.message;

            // FG TABLE
            let fg_html = `<table class="table table-bordered">
                <tr><th>Item</th><th>Batch</th><th>Warehouse</th><th>Qty</th></tr>`;

            d.fg.forEach(f => {
                fg_html += `<tr>
                    <td>${f.item_code}</td>
                    <td>${f.batch_no || ''}</td>
                    <td>${f.warehouse}</td>
                    <td>${f.qty}</td>
                </tr>`;
            });

            fg_html += `</table>`;
            $("#fg").html(fg_html);

            // SALES TABLE
            let sales_html = `<table class="table table-bordered">
                <tr><th>Customer</th><th>Invoice</th><th>Qty</th></tr>`;

            d.sales.forEach(s => {
                sales_html += `<tr>
                    <td>${s.customer}</td>
                    <td>${s.invoice}</td>
                    <td>${s.qty}</td>
                </tr>`;
            });

            sales_html += `</table>`;
            $("#sales").html(sales_html);
			  $("<style>")
        .prop("type", "text/css")
        .html(`
            .fg-container {
                padding: 20px;
            }

            .fg-table th {
                background: #f5f7fa;
                font-weight: 600;
            }

            .fg-table {
                margin-bottom: 25px;
                border-radius: 8px;
                overflow: hidden;
            }

            h4 {
                margin-top: 20px;
                font-weight: 600;
                color: #2c3e50;
            }
        `)
        .appendTo("head");

        }
    });

}
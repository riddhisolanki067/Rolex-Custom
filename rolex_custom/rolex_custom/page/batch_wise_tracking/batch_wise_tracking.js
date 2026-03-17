frappe.pages['batch-wise-tracking'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Batch Wise Tracking',
		single_column: true
	});
	 let batch = page.add_field({
        label: 'Batch',
        fieldtype: 'Link',
        options: 'Batch'
    });

    let container = $(`
        <div class="trace-container">
            <div id="table_area"></div>
        </div>
    `).appendTo(page.body);

    page.set_primary_action("Load", () => {
        load_data(batch.get_value());
    });


    function load_data(batch_no) {

        frappe.call({
            method: "rolex_custom.rolex_custom.page.batch_wise_tracking.batch_wise_tracking.get_batch_main",
            args: { batch_no },
            callback(r) {

                let rows = r.message;
                let html = build_table(rows);
                $("#table_area").html(html);
            }
        });
    }


    function build_table(data) {

        let html = `
        <table class="table table-bordered trace-table">
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Item</th>
                    <th>Type</th>
                    <th>Qty</th>
                    <th>Voucher Type</th>
                    <th>Voucher No</th>
                    <th>Party</th>
                    <th>FG Details</th>
                </tr>
            </thead>
            <tbody>
        `;

        data.forEach(d => {

            let btn = "";

            if (d.voucher_type === "Stock Entry") {
                btn = `<button class="btn btn-sm btn-primary view-fg"
                            data-name="${d.voucher_no}">
                            View
                        </button>`;
            }

            html += `
                <tr>
                    <td>${d.date}</td>
                    <td>${d.item}</td>
                    <td>${d.type}</td>
                    <td>${d.qty}</td>
                    <td>${d.voucher_type}</td>
                    <td>${d.voucher_no}</td>
                    <td>${d.party || ''}</td>
                    <td>${btn}</td>
                </tr>
            `;
        });

        html += `</tbody></table>`;
        return html;
    }


    // CLICK EVENT
    $(document).on("click", ".view-fg", function() {
        let name = $(this).data("name");
		console.log(name)
		frappe.route_options = {
			stock_entry: name
		};
		frappe.set_route("fg-details");    });
}